from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from docint_workbench.database import connect, init_db
from docint_workbench.extraction import detect_document_type, extract_fields, extract_fields_with_provider
from docint_workbench.observability import log_event, metrics
from docint_workbench.schemas import (
    AuditEvent,
    DocumentResult,
    ExportResult,
    FieldResult,
    ProcessingJobResult,
    QueueMetrics,
    ReviewQueuePartition,
    SummaryMetrics,
    ValidationResult,
)
from docint_workbench.validation import validate_fields


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class DocumentWorkbenchService:
    def __init__(
        self,
        database_path: Path,
        low_confidence_threshold: float,
        evaluation_set_path: Path,
        database_backend: str = "sqlite",
        database_url: str = "",
        llm_provider: str = "mock",
        openai_api_key: str = "",
        openai_model: str = "gpt-4o-mini",
        azure_openai_endpoint: str = "",
        azure_openai_key: str = "",
        azure_openai_chat_deployment: str = "",
        queue_max_attempts: int = 3,
        queue_retry_base_seconds: int = 5,
        queue_retry_max_seconds: int = 300,
        logger: Any | None = None,
    ) -> None:
        self.database_path = database_path
        self.database_backend = database_backend
        self.database_url = database_url
        self.low_confidence_threshold = low_confidence_threshold
        self.evaluation_set_path = evaluation_set_path
        self.llm_provider = llm_provider
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_key = azure_openai_key
        self.azure_openai_chat_deployment = azure_openai_chat_deployment
        self.queue_max_attempts = max(1, int(queue_max_attempts))
        self.queue_retry_base_seconds = max(1, int(queue_retry_base_seconds))
        self.queue_retry_max_seconds = max(self.queue_retry_base_seconds, int(queue_retry_max_seconds))
        self.logger = logger
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            init_db(conn)

    def process_document(self, file_name: str, content: str, requested_type: str, actor: str = "system") -> DocumentResult:
        document_id = f"doc_{uuid4().hex[:12]}"
        now = _utc_now()
        document_type = detect_document_type(content, requested_type)
        try:
            extracted = list(
                extract_fields_with_provider(
                    content=content,
                    document_type=document_type,
                    llm_provider=self.llm_provider,
                    openai_api_key=self.openai_api_key,
                    openai_model=self.openai_model,
                    azure_openai_endpoint=self.azure_openai_endpoint,
                    azure_openai_key=self.azure_openai_key,
                    azure_openai_chat_deployment=self.azure_openai_chat_deployment,
                )
            )
            metrics.inc("docint_extraction_provider_calls_total", provider=self.llm_provider)
        except Exception as exc:
            extracted = list(extract_fields(content, document_type))
            metrics.inc("docint_extraction_provider_failures_total", provider=self.llm_provider)
            if self.logger:
                log_event(
                    self.logger,
                    "warning",
                    "provider_extraction_fallback",
                    provider=self.llm_provider,
                    error=str(exc),
                    document_type=document_type,
                )
        validations = validate_fields(document_type, extracted)

        requires_review = False
        mapped_fields: list[dict[str, Any]] = []
        for field in extracted:
            field_review = field.confidence < self.low_confidence_threshold
            requires_review = requires_review or field_review
            mapped_fields.append(
                {
                    "key": field.key,
                    "value": field.value,
                    "confidence": round(field.confidence, 3),
                    "requires_review": field_review,
                    "validator_status": "pass" if field.value else "fail",
                    "validator_message": "field extracted" if field.value else "field missing",
                }
            )

        validation_entries = [{"status": status, "message": message} for status, message in validations]
        if any(entry["status"] == "fail" for entry in validation_entries):
            requires_review = True

        confidence_average = round(
            sum(field["confidence"] for field in mapped_fields) / max(len(mapped_fields), 1),
            3,
        )

        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    id, file_name, document_type, status, confidence_average,
                    requires_review, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    file_name,
                    document_type,
                    "processed",
                    confidence_average,
                    int(requires_review),
                    now,
                    now,
                ),
            )

            for field in mapped_fields:
                conn.execute(
                    """
                    INSERT INTO extracted_fields (
                        document_id, field_key, field_value, confidence,
                        requires_review, validator_status, validator_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        field["key"],
                        field["value"],
                        field["confidence"],
                        int(field["requires_review"]),
                        field["validator_status"],
                        field["validator_message"],
                    ),
                )

            for validation in validation_entries:
                conn.execute(
                    "INSERT INTO validations (document_id, status, message) VALUES (?, ?, ?)",
                    (document_id, validation["status"], validation["message"]),
                )

            conn.commit()
            self._insert_audit_event(
                conn=conn,
                document_id=document_id,
                event_type="document_processed",
                actor=actor,
                detail=f"Processed {file_name} as {document_type}",
            )
            conn.commit()

        return self.get_document(document_id)

    def enqueue_document(self, file_name: str, content: str, requested_type: str, actor: str) -> ProcessingJobResult:
        job_id = f"job_{uuid4().hex[:12]}"
        now = _utc_now()
        document_type = detect_document_type(content, requested_type)
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            conn.execute(
                """
                INSERT INTO processing_jobs (
                    id, file_name, content, document_type, status, requested_by,
                    worker_id, attempt_count, document_id, last_error,
                    created_at, updated_at, next_run_at, started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    file_name,
                    content,
                    document_type,
                    "pending",
                    actor,
                    None,
                    0,
                    None,
                    None,
                    now,
                    now,
                    now,
                    None,
                    None,
                ),
            )
            conn.commit()
        return self.get_processing_job(job_id)

    def list_processing_jobs(
        self,
        status: str | None = None,
        document_type: str | None = None,
        limit: int = 100,
    ) -> list[ProcessingJobResult]:
        query = """
            SELECT id FROM processing_jobs
            WHERE 1 = 1
        """
        params: list[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if document_type:
            query += " AND document_type = ?"
            params.append(document_type)
        query += " ORDER BY updated_at DESC, created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self.get_processing_job(row["id"]) for row in rows]

    def queue_metrics(self) -> QueueMetrics:
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            pending = conn.execute("SELECT COUNT(*) AS count FROM processing_jobs WHERE status = 'pending'").fetchone()["count"]
            in_progress = conn.execute("SELECT COUNT(*) AS count FROM processing_jobs WHERE status = 'in_progress'").fetchone()["count"]
            completed = conn.execute("SELECT COUNT(*) AS count FROM processing_jobs WHERE status = 'completed'").fetchone()["count"]
            failed = conn.execute("SELECT COUNT(*) AS count FROM processing_jobs WHERE status = 'failed'").fetchone()["count"]
            dead_letter = conn.execute("SELECT COUNT(*) AS count FROM processing_jobs WHERE status = 'dead_letter'").fetchone()["count"]
        return QueueMetrics(
            pending_jobs=int(pending),
            in_progress_jobs=int(in_progress),
            completed_jobs=int(completed),
            failed_jobs=int(failed),
            dead_letter_jobs=int(dead_letter),
        )

    def get_processing_job(self, job_id: str) -> ProcessingJobResult:
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            row = conn.execute("SELECT * FROM processing_jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                raise KeyError(f"Processing job not found: {job_id}")
        return ProcessingJobResult(
            job_id=row["id"],
            file_name=row["file_name"],
            document_type=row["document_type"],
            status=row["status"],
            requested_by=row["requested_by"],
            attempt_count=int(row["attempt_count"]),
            document_id=row["document_id"],
            worker_id=row["worker_id"],
            last_error=row["last_error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            next_run_at=datetime.fromisoformat(row["next_run_at"]) if row["next_run_at"] else None,
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )

    def process_next_job(self, worker_id: str = "worker-local") -> ProcessingJobResult | None:
        now = _utc_now()
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            job = conn.execute(
                """
                SELECT id, file_name, content, document_type, requested_by, attempt_count
                FROM processing_jobs
                WHERE status = 'pending' AND (next_run_at IS NULL OR next_run_at <= ?)
                ORDER BY COALESCE(next_run_at, created_at) ASC, created_at ASC
                LIMIT 1
                """,
                (now,),
            ).fetchone()
            if not job:
                return None

            updated = conn.execute(
                """
                UPDATE processing_jobs
                SET status = 'in_progress', worker_id = ?, attempt_count = ?, updated_at = ?, started_at = ?, last_error = NULL
                WHERE id = ? AND status = 'pending'
                """,
                (worker_id, int(job["attempt_count"]) + 1, now, now, job["id"]),
            )
            if int(getattr(updated, "rowcount", 0) or 0) != 1:
                conn.commit()
                return None
            conn.commit()

        try:
            document = self.process_document(
                file_name=job["file_name"],
                content=job["content"],
                requested_type=job["document_type"],
                actor=f"queue:{worker_id}",
            )
        except Exception as exc:
            self._mark_job_failed(
                job["id"],
                worker_id=worker_id,
                error=str(exc),
                attempt_count=int(job["attempt_count"]) + 1,
            )
            return self.get_processing_job(job["id"])

        self._mark_job_completed(job["id"], worker_id=worker_id, document_id=document.document_id)
        return self.get_processing_job(job["id"])

    def _mark_job_completed(self, job_id: str, worker_id: str, document_id: str) -> None:
        now = _utc_now()
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            conn.execute(
                """
                UPDATE processing_jobs
                SET status = 'completed', worker_id = ?, document_id = ?, updated_at = ?, completed_at = ?, last_error = NULL
                WHERE id = ?
                """,
                (worker_id, document_id, now, now, job_id),
            )
            conn.commit()

    def _mark_job_failed(self, job_id: str, worker_id: str, error: str, attempt_count: int) -> None:
        now = _utc_now()
        if attempt_count < self.queue_max_attempts:
            retry_seconds = min(
                self.queue_retry_base_seconds * (2 ** max(attempt_count - 1, 0)),
                self.queue_retry_max_seconds,
            )
            next_run_at = (datetime.now(tz=timezone.utc) + timedelta(seconds=retry_seconds)).isoformat()
            status = "pending"
            completed_at: str | None = None
        else:
            next_run_at = None
            status = "dead_letter"
            completed_at = now
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            conn.execute(
                """
                UPDATE processing_jobs
                SET status = ?, worker_id = ?, updated_at = ?, completed_at = ?, next_run_at = ?, last_error = ?
                WHERE id = ?
                """,
                (status, worker_id, now, completed_at, next_run_at, error[:2000], job_id),
            )
            conn.commit()

    def list_documents(self) -> list[DocumentResult]:
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            rows = conn.execute("SELECT id FROM documents ORDER BY created_at DESC").fetchall()
        return [self.get_document(row["id"]) for row in rows]

    def list_review_queue(self, document_type: str | None = None) -> list[DocumentResult]:
        query = "SELECT id FROM documents WHERE requires_review = 1"
        params: tuple[Any, ...] = ()
        if document_type:
            query += " AND document_type = ?"
            params = (document_type,)
        query += " ORDER BY updated_at DESC, created_at DESC"
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            rows = conn.execute(query, params).fetchall()
        return [self.get_document(row["id"]) for row in rows]

    def review_queue_partitions(self, allowed_types: tuple[str, ...] | None = None) -> list[ReviewQueuePartition]:
        query = """
            SELECT document_type, COUNT(*) AS total_documents, AVG(confidence_average) AS average_confidence
            FROM documents
            WHERE requires_review = 1
        """
        params: tuple[Any, ...] = ()
        if allowed_types and "*" not in allowed_types:
            placeholders = ",".join("?" for _ in allowed_types)
            query += f" AND document_type IN ({placeholders})"
            params = tuple(allowed_types)
        query += " GROUP BY document_type ORDER BY total_documents DESC, document_type ASC"
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            ReviewQueuePartition(
                document_type=row["document_type"],
                total_documents=int(row["total_documents"]),
                average_confidence=round(float(row["average_confidence"] or 0.0), 3),
            )
            for row in rows
        ]

    def get_document(self, document_id: str) -> DocumentResult:
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            document = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
            if not document:
                raise KeyError(f"Document not found: {document_id}")

            fields = conn.execute(
                """
                SELECT field_key, field_value, confidence, requires_review, validator_status, validator_message
                FROM extracted_fields WHERE document_id = ? ORDER BY id
                """,
                (document_id,),
            ).fetchall()
            validations = conn.execute(
                "SELECT status, message FROM validations WHERE document_id = ? ORDER BY id",
                (document_id,),
            ).fetchall()

        return DocumentResult(
            document_id=document["id"],
            file_name=document["file_name"],
            document_type=document["document_type"],
            status=document["status"],
            confidence_average=float(document["confidence_average"]),
            requires_review=bool(document["requires_review"]),
            created_at=datetime.fromisoformat(document["created_at"]),
            updated_at=datetime.fromisoformat(document["updated_at"]),
            fields=[
                FieldResult(
                    key=field["field_key"],
                    value=field["field_value"],
                    confidence=float(field["confidence"]),
                    requires_review=bool(field["requires_review"]),
                    validator_status=field["validator_status"],
                    validator_message=field["validator_message"],
                )
                for field in fields
            ],
            validations=[ValidationResult(status=v["status"], message=v["message"]) for v in validations],
        )

    def review_document(self, document_id: str, updates: dict[str, str], actor: str = "reviewer") -> DocumentResult:
        now = _utc_now()
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            for key, value in updates.items():
                conn.execute(
                    """
                    UPDATE extracted_fields
                    SET field_value = ?, requires_review = 0, validator_status = 'pass', validator_message = 'review override'
                    WHERE document_id = ? AND field_key = ?
                    """,
                    (value, document_id, key),
                )
            conn.execute(
                "UPDATE documents SET requires_review = 0, updated_at = ? WHERE id = ?",
                (now, document_id),
            )
            self._insert_audit_event(
                conn=conn,
                document_id=document_id,
                event_type="review_override",
                actor=actor,
                detail=f"Updated fields: {', '.join(sorted(updates.keys()))}",
            )
            conn.commit()
        return self.get_document(document_id)

    def export_document(self, document_id: str, export_format: str, actor: str = "reviewer") -> ExportResult:
        document = self.get_document(document_id)
        field_map = {field.key: field.value for field in document.fields}

        if export_format == "json":
            import json

            payload = {
                "document_id": document.document_id,
                "file_name": document.file_name,
                "document_type": document.document_type,
                "fields": field_map,
                "validations": [validation.model_dump() for validation in document.validations],
            }
            result = ExportResult(document_id=document_id, export_format="json", content=json.dumps(payload, indent=2))
            self._record_export_audit(document_id, "json", actor)
            return result

        if export_format == "csv":
            stream = io.StringIO()
            writer = csv.writer(stream)
            writer.writerow(["document_id", "file_name", "document_type", "field_key", "field_value"])
            for key, value in field_map.items():
                writer.writerow([document.document_id, document.file_name, document.document_type, key, value])
            result = ExportResult(document_id=document_id, export_format="csv", content=stream.getvalue())
            self._record_export_audit(document_id, "csv", actor)
            return result

        raise ValueError("export_format must be 'json' or 'csv'")

    def summary_metrics(self) -> SummaryMetrics:
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            total = conn.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]
            processed = conn.execute("SELECT COUNT(*) AS count FROM documents WHERE status = 'processed'").fetchone()["count"]
            review_required = conn.execute("SELECT COUNT(*) AS count FROM documents WHERE requires_review = 1").fetchone()["count"]
            avg_confidence = conn.execute("SELECT AVG(confidence_average) AS avg_conf FROM documents").fetchone()["avg_conf"]

        return SummaryMetrics(
            total_documents=int(total),
            processed_documents=int(processed),
            review_required_documents=int(review_required),
            average_confidence=round(float(avg_confidence or 0.0), 3),
        )

    def list_audit_events(self, document_id: str | None = None) -> list[AuditEvent]:
        query = """
            SELECT id, document_id, event_type, actor, detail, created_at
            FROM audit_events
        """
        params: tuple[Any, ...] = ()
        if document_id:
            query += " WHERE document_id = ?"
            params = (document_id,)
        query += " ORDER BY created_at DESC, id DESC"
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            AuditEvent(
                id=row["id"],
                document_id=row["document_id"],
                event_type=row["event_type"],
                actor=row["actor"],
                detail=row["detail"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def _record_export_audit(self, document_id: str, export_format: str, actor: str) -> None:
        with connect(
            self.database_path,
            database_backend=self.database_backend,
            database_url=self.database_url,
        ) as conn:
            self._insert_audit_event(
                conn=conn,
                document_id=document_id,
                event_type=f"export_{export_format}",
                actor=actor,
                detail=f"Exported document as {export_format}",
            )
            conn.commit()

    @staticmethod
    def _insert_audit_event(
        conn: Any,
        document_id: str,
        event_type: str,
        actor: str,
        detail: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO audit_events (document_id, event_type, actor, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document_id, event_type, actor, detail, _utc_now()),
        )
