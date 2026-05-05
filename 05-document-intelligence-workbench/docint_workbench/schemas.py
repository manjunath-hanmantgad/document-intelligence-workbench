from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DocumentType = Literal["invoice", "contract", "unknown"]


class ProcessDocumentRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    document_type: DocumentType = "unknown"


class ReviewFieldUpdate(BaseModel):
    key: str
    value: str


class ReviewRequest(BaseModel):
    updates: list[ReviewFieldUpdate]


class FieldResult(BaseModel):
    key: str
    value: str
    confidence: float
    requires_review: bool
    validator_status: str
    validator_message: str


class ValidationResult(BaseModel):
    status: Literal["pass", "fail"]
    message: str


class DocumentResult(BaseModel):
    document_id: str
    file_name: str
    document_type: DocumentType
    status: str
    confidence_average: float
    requires_review: bool
    created_at: datetime
    updated_at: datetime
    fields: list[FieldResult]
    validations: list[ValidationResult]


class ExportResult(BaseModel):
    document_id: str
    export_format: Literal["json", "csv"]
    content: str


class SummaryMetrics(BaseModel):
    total_documents: int
    processed_documents: int
    review_required_documents: int
    average_confidence: float


class EvaluationCase(BaseModel):
    name: str
    document_type: DocumentType
    content: str
    expected_fields: dict[str, str]


class EvaluationResult(BaseModel):
    total_cases: int
    passed_cases: int
    pass_rate: float
    average_field_match_rate: float


class AuditEvent(BaseModel):
    id: int
    document_id: str
    event_type: str
    actor: str
    detail: str
    created_at: datetime


class ReviewQueuePartition(BaseModel):
    document_type: DocumentType
    total_documents: int
    average_confidence: float


JobStatus = Literal["pending", "in_progress", "completed", "failed", "dead_letter"]


class EnqueueDocumentRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    document_type: DocumentType = "unknown"


class ProcessingJobResult(BaseModel):
    job_id: str
    file_name: str
    document_type: DocumentType
    status: JobStatus
    requested_by: str
    attempt_count: int
    document_id: str | None
    worker_id: str | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    next_run_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None


class QueueMetrics(BaseModel):
    pending_jobs: int
    in_progress_jobs: int
    completed_jobs: int
    failed_jobs: int
    dead_letter_jobs: int
