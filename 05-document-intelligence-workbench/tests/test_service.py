from pathlib import Path
from types import MethodType
from datetime import datetime, timezone

from docint_workbench.database import connect
from docint_workbench.service import DocumentWorkbenchService


def test_process_review_and_export(tmp_path: Path) -> None:
    service = DocumentWorkbenchService(
        database_path=tmp_path / "service.db",
        low_confidence_threshold=0.9,
        evaluation_set_path=tmp_path / "evaluation.json",
    )

    content = """Vendor: Apex Office Supplies
Invoice Number: INV-2026-0042
Invoice Date: 2026-04-29
Subtotal: 1250.00
Tax: 125.00
Total: 1300.00
Currency: USD
"""

    result = service.process_document("invoice-bad.txt", content, "invoice")
    assert result.requires_review is True

    updated = service.review_document(result.document_id, {"total": "1375.00"})
    assert updated.requires_review is False

    export_csv = service.export_document(result.document_id, "csv")
    assert "document_id,file_name,document_type,field_key,field_value" in export_csv.content

    metrics = service.summary_metrics()
    assert metrics.total_documents == 1

    queue = service.list_review_queue(document_type="invoice")
    assert len(queue) == 0

    audit_events = service.list_audit_events(result.document_id)
    event_types = {event.event_type for event in audit_events}
    assert "document_processed" in event_types
    assert "review_override" in event_types
    assert "export_csv" in event_types


def test_queue_enqueue_and_worker_processing(tmp_path: Path) -> None:
    service = DocumentWorkbenchService(
        database_path=tmp_path / "queue.db",
        low_confidence_threshold=0.9,
        evaluation_set_path=tmp_path / "evaluation.json",
    )
    job = service.enqueue_document(
        file_name="invoice-queue.txt",
        content="Vendor: A\nInvoice Number: I-1\nInvoice Date: 2026-05-01\nSubtotal: 100\nTax: 10\nTotal: 110\nCurrency: USD",
        requested_type="invoice",
        actor="tester",
    )
    assert job.status == "pending"
    queued = service.list_processing_jobs(status="pending")
    assert queued and queued[0].job_id == job.job_id

    processed = service.process_next_job(worker_id="worker-test")
    assert processed is not None
    assert processed.status == "completed"
    assert processed.document_id is not None

    done = service.get_processing_job(job.job_id)
    assert done.status == "completed"
    assert done.worker_id == "worker-test"


def test_queue_retry_and_dead_letter(tmp_path: Path) -> None:
    service = DocumentWorkbenchService(
        database_path=tmp_path / "queue-retry.db",
        low_confidence_threshold=0.9,
        evaluation_set_path=tmp_path / "evaluation.json",
        queue_max_attempts=2,
        queue_retry_base_seconds=1,
        queue_retry_max_seconds=2,
    )
    job = service.enqueue_document(
        file_name="invoice-fail.txt",
        content="Vendor: A\nInvoice Number: I-2\nInvoice Date: 2026-05-01\nSubtotal: 100\nTax: 10\nTotal: 110\nCurrency: USD",
        requested_type="invoice",
        actor="tester",
    )

    def fail_process(self: DocumentWorkbenchService, file_name: str, content: str, requested_type: str, actor: str = "system") -> object:
        raise RuntimeError("forced queue failure")

    service.process_document = MethodType(fail_process, service)

    first = service.process_next_job(worker_id="worker-retry")
    assert first is not None
    assert first.status == "pending"
    assert first.last_error is not None
    assert first.next_run_at is not None

    # Force immediate second attempt to avoid waiting in test runtime.
    now = datetime.now(tz=timezone.utc).isoformat()
    with connect(service.database_path, database_backend=service.database_backend, database_url=service.database_url) as conn:
        conn.execute("UPDATE processing_jobs SET next_run_at = ? WHERE id = ?", (now, job.job_id))
        conn.commit()

    second = service.process_next_job(worker_id="worker-retry")
    assert second is not None
    assert second.status == "dead_letter"
    assert second.last_error is not None
    assert second.completed_at is not None
