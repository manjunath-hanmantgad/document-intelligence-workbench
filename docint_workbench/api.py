from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import time
from typing import Any
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse
from jwt import InvalidTokenError, PyJWKClient

from docint_workbench.config import ROLE_SCOPE_DEFAULTS, get_settings
from docint_workbench.evaluation import run_evaluation
from docint_workbench.observability import configure_logging, log_event, metrics
from docint_workbench.parsing import ParsingError, parse_uploaded_document
from docint_workbench.schemas import (
    AuditEvent,
    DocumentResult,
    EnqueueDocumentRequest,
    EvaluationResult,
    ExportResult,
    ProcessingJobResult,
    ProcessDocumentRequest,
    QueueMetrics,
    ReviewQueuePartition,
    ReviewRequest,
    SummaryMetrics,
)
from docint_workbench.service import DocumentWorkbenchService

settings = get_settings()
logger = configure_logging(settings.log_level)
service = DocumentWorkbenchService(
    database_path=settings.database_path,
    low_confidence_threshold=settings.low_confidence_threshold,
    evaluation_set_path=Path("demo/evaluation_set.json"),
    database_backend=settings.database_backend,
    database_url=settings.database_url,
    llm_provider=settings.llm_provider,
    openai_api_key=settings.openai_api_key,
    openai_model=settings.openai_model,
    azure_openai_endpoint=settings.azure_openai_endpoint,
    azure_openai_key=settings.azure_openai_key,
    azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
    queue_max_attempts=settings.queue_max_attempts,
    queue_retry_base_seconds=settings.queue_retry_base_seconds,
    queue_retry_max_seconds=settings.queue_retry_max_seconds,
    logger=logger,
)
app = FastAPI(title=settings.app_name)
oidc_jwks_client: PyJWKClient | None = None
oidc_jwks_client_url: str | None = None


@app.middleware("http")
async def request_observability(request: Request, call_next: Any) -> Any:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        metrics.inc("docint_http_requests_total", method=request.method, path=request.url.path, status="500")
        metrics.observe("docint_http_request_duration_seconds", time.perf_counter() - start, method=request.method, path=request.url.path)
        log_event(
            logger,
            "error",
            "http_request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=500,
        )
        raise
    duration = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    metrics.inc("docint_http_requests_total", method=request.method, path=request.url.path, status=str(status_code))
    metrics.observe("docint_http_request_duration_seconds", duration, method=request.method, path=request.url.path)
    log_event(
        logger,
        "info",
        "http_request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response


@dataclass(frozen=True)
class ReviewerContext:
    actor: str
    role: str
    scopes: tuple[str, ...]


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization bearer token")
    scheme, _, token = authorization.partition(" ")
    if scheme.strip().lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Authorization must be a Bearer token")
    return token.strip()


def _resolve_role_from_claim(value: Any) -> str:
    candidates: list[str] = []
    if isinstance(value, str):
        candidates = [part.strip().lower() for part in value.replace(",", " ").split() if part.strip()]
    elif isinstance(value, list):
        candidates = [str(part).strip().lower() for part in value if str(part).strip()]
    for role in candidates:
        if role in settings.oidc_role_scope_map:
            return role
    if candidates:
        return candidates[0]
    return "ops"


def _scopes_for_role(role: str) -> tuple[str, ...]:
    return settings.oidc_role_scope_map.get(role, ROLE_SCOPE_DEFAULTS.get(role, ("invoice", "contract", "unknown")))


def _decode_oidc_claims(token: str) -> dict[str, Any]:
    global oidc_jwks_client, oidc_jwks_client_url

    algorithms = tuple(settings.oidc_algorithms)
    if not algorithms:
        raise HTTPException(status_code=500, detail="OIDC_ALGORITHMS must be configured")

    if any(algorithm.upper().startswith("HS") for algorithm in algorithms):
        if not settings.oidc_hs256_shared_secret:
            raise HTTPException(status_code=500, detail="OIDC_HS256_SHARED_SECRET must be configured for HS algorithms")
        key: str | Any = settings.oidc_hs256_shared_secret
    else:
        if not settings.oidc_jwks_url:
            raise HTTPException(status_code=500, detail="OIDC_JWKS_URL must be configured for asymmetric algorithms")
        if oidc_jwks_client is None or oidc_jwks_client_url != settings.oidc_jwks_url:
            oidc_jwks_client = PyJWKClient(settings.oidc_jwks_url, cache_keys=True)
            oidc_jwks_client_url = settings.oidc_jwks_url
        key = oidc_jwks_client.get_signing_key_from_jwt(token).key

    options = {
        "require": ["exp"],
        "verify_aud": bool(settings.oidc_audience),
        "verify_iss": bool(settings.oidc_issuer),
    }
    claims: dict[str, Any] = jwt.decode(
        token,
        key=key,
        algorithms=list(algorithms),
        audience=settings.oidc_audience or None,
        issuer=settings.oidc_issuer or None,
        options=options,
    )
    return claims


def _reviewer_identity_from_oidc(authorization: str | None) -> ReviewerContext:
    token = _extract_bearer_token(authorization)
    try:
        claims = _decode_oidc_claims(token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive guard for provider/network failures
        raise HTTPException(status_code=401, detail="OIDC authentication failed") from exc

    subject = str(claims.get(settings.oidc_subject_claim, "")).strip()
    if not subject:
        raise HTTPException(status_code=401, detail=f"Bearer token missing '{settings.oidc_subject_claim}' claim")
    role = _resolve_role_from_claim(claims.get(settings.oidc_role_claim))
    subject_hash = sha256(subject.encode("utf-8")).hexdigest()[:12]
    return ReviewerContext(actor=f"oidc:{role}:{subject_hash}", role=role, scopes=_scopes_for_role(role))


def reviewer_identity(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ReviewerContext:
    if not settings.auth_enabled:
        return ReviewerContext(actor="anonymous", role="ops", scopes=("invoice", "contract", "unknown"))
    if settings.auth_mode == "oidc":
        return _reviewer_identity_from_oidc(authorization)
    if settings.auth_mode != "api_key":
        raise HTTPException(status_code=500, detail=f"Unsupported AUTH_MODE '{settings.auth_mode}'")
    if not x_api_key or x_api_key not in settings.reviewer_api_keys:
        raise HTTPException(status_code=401, detail="Unauthorized reviewer API key")
    role = settings.reviewer_role_map.get(x_api_key, "ops")
    scopes = settings.reviewer_scope_map.get(x_api_key, ("invoice", "contract", "unknown"))
    return ReviewerContext(actor=f"reviewer:{role}:{x_api_key[-4:]}", role=role, scopes=scopes)


def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    if not settings.auth_enabled:
        return
    if settings.auth_mode == "oidc":
        context = _reviewer_identity_from_oidc(authorization)
        if context.role != "admin" and "*" not in context.scopes:
            raise HTTPException(status_code=403, detail="Admin role required")
        return
    if settings.auth_mode != "api_key":
        raise HTTPException(status_code=500, detail=f"Unsupported AUTH_MODE '{settings.auth_mode}'")
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized admin token")


def ensure_scope(context: ReviewerContext, document_type: str) -> None:
    if "*" in context.scopes:
        return
    if document_type not in context.scopes:
        raise HTTPException(
            status_code=403,
            detail=f"Reviewer scope does not include document type '{document_type}'",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.post("/documents/process", response_model=DocumentResult)
def process_document(request: ProcessDocumentRequest, reviewer: ReviewerContext = Depends(reviewer_identity)) -> DocumentResult:
    if len(request.content) > settings.max_upload_chars:
        raise HTTPException(status_code=400, detail="Document content exceeds MAX_UPLOAD_CHARS")
    ensure_scope(reviewer, request.document_type)
    return service.process_document(request.file_name, request.content, request.document_type, actor=reviewer.actor)


@app.post("/documents/process-async", response_model=ProcessingJobResult)
def process_document_async(
    request: EnqueueDocumentRequest,
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> ProcessingJobResult:
    if len(request.content) > settings.max_upload_chars:
        raise HTTPException(status_code=400, detail="Document content exceeds MAX_UPLOAD_CHARS")
    ensure_scope(reviewer, request.document_type)
    return service.enqueue_document(
        file_name=request.file_name,
        content=request.content,
        requested_type=request.document_type,
        actor=reviewer.actor,
    )


@app.post("/documents/upload", response_model=DocumentResult)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query(default="unknown", pattern="^(unknown|invoice|contract)$"),
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> DocumentResult:
    ensure_scope(reviewer, document_type)
    payload = await file.read()
    if len(payload) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="File payload exceeds MAX_UPLOAD_BYTES")

    try:
        text = parse_uploaded_document(
            file.filename or "uploaded-document",
            payload,
            settings.enable_local_ocr,
            azure_document_intelligence_endpoint=settings.azure_document_intelligence_endpoint,
            azure_document_intelligence_key=settings.azure_document_intelligence_key,
        )
    except ParsingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(text) > settings.max_upload_chars:
        raise HTTPException(status_code=400, detail="Parsed text exceeds MAX_UPLOAD_CHARS")

    return service.process_document(file.filename or "uploaded-document", text, document_type, actor=reviewer.actor)


@app.get("/documents", response_model=list[DocumentResult])
def list_documents(_: ReviewerContext = Depends(reviewer_identity)) -> list[DocumentResult]:
    return service.list_documents()


@app.get("/documents/review-queue", response_model=list[DocumentResult])
def review_queue(
    document_type: str | None = Query(default=None, pattern="^(unknown|invoice|contract)$"),
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> list[DocumentResult]:
    if document_type:
        ensure_scope(reviewer, document_type)
        return service.list_review_queue(document_type=document_type)
    allowed = set(reviewer.scopes)
    if "*" in allowed:
        return service.list_review_queue()
    queue: list[DocumentResult] = []
    for doc_type in sorted(allowed):
        queue.extend(service.list_review_queue(document_type=doc_type))
    queue.sort(key=lambda document: document.updated_at, reverse=True)
    return queue


@app.get("/documents/review-queue/partitions", response_model=list[ReviewQueuePartition])
def review_queue_partitions(
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> list[ReviewQueuePartition]:
    if "*" in reviewer.scopes:
        return service.review_queue_partitions()
    allowed = tuple(sorted(set(reviewer.scopes)))
    return service.review_queue_partitions(allowed_types=allowed)


@app.get("/jobs", response_model=list[ProcessingJobResult])
def list_jobs(
    status: str | None = Query(default=None, pattern="^(pending|in_progress|completed|failed|dead_letter)$"),
    document_type: str | None = Query(default=None, pattern="^(unknown|invoice|contract)$"),
    limit: int = Query(default=100, ge=1, le=500),
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> list[ProcessingJobResult]:
    if document_type:
        ensure_scope(reviewer, document_type)
        return service.list_processing_jobs(status=status, document_type=document_type, limit=limit)
    jobs = service.list_processing_jobs(status=status, document_type=None, limit=limit)
    if "*" in reviewer.scopes:
        return jobs
    return [job for job in jobs if job.document_type in reviewer.scopes]


@app.get("/jobs/{job_id}", response_model=ProcessingJobResult)
def get_job(job_id: str, reviewer: ReviewerContext = Depends(reviewer_identity)) -> ProcessingJobResult:
    try:
        job = service.get_processing_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    ensure_scope(reviewer, job.document_type)
    return job


@app.get("/documents/{document_id}", response_model=DocumentResult)
def get_document(document_id: str, reviewer: ReviewerContext = Depends(reviewer_identity)) -> DocumentResult:
    try:
        doc = service.get_document(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    ensure_scope(reviewer, doc.document_type)
    return doc


@app.post("/documents/{document_id}/review", response_model=DocumentResult)
def review_document(
    document_id: str,
    request: ReviewRequest,
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> DocumentResult:
    try:
        existing = service.get_document(document_id)
        ensure_scope(reviewer, existing.document_type)
        updates = {item.key: item.value for item in request.updates}
        return service.review_document(document_id, updates, actor=reviewer.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/documents/{document_id}/export", response_model=ExportResult)
def export_document(
    document_id: str,
    export_format: str = Query(pattern="^(json|csv)$"),
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> ExportResult:
    try:
        existing = service.get_document(document_id)
        ensure_scope(reviewer, existing.document_type)
        return service.export_document(document_id, export_format, actor=reviewer.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/metrics/summary", response_model=SummaryMetrics)
def metrics_summary(_: ReviewerContext = Depends(reviewer_identity)) -> SummaryMetrics:
    return service.summary_metrics()


@app.get("/metrics/queue", response_model=QueueMetrics)
def metrics_queue(_: ReviewerContext = Depends(reviewer_identity)) -> QueueMetrics:
    return service.queue_metrics()


@app.get("/metrics/prometheus")
def metrics_prometheus(_: ReviewerContext = Depends(reviewer_identity)) -> PlainTextResponse:
    return PlainTextResponse(metrics.render_prometheus(), media_type="text/plain; version=0.0.4")


@app.get("/audit/events", response_model=list[AuditEvent])
def audit_events(
    document_id: str | None = None,
    reviewer: ReviewerContext = Depends(reviewer_identity),
) -> list[AuditEvent]:
    events = service.list_audit_events(document_id=document_id)
    if "*" in reviewer.scopes:
        return events
    return [
        event for event in events if service.get_document(event.document_id).document_type in reviewer.scopes
    ]


@app.post("/evaluation/run", response_model=EvaluationResult)
def evaluation_run(_: None = Depends(require_admin)) -> EvaluationResult:
    eval_path = Path("demo/evaluation_set.json")
    if not eval_path.exists():
        raise HTTPException(status_code=404, detail="Evaluation set not found at demo/evaluation_set.json")
    return run_evaluation(eval_path)
