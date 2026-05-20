# The Architecture Behind Document Intelligence Workbench: Sync, Async, and Why Both Matter

*Document Intelligence Workbench — A practitioner's build log | Post 2 of 6*

---

Document processing does not have a single performance profile. Some documents arrive one at a time from an operator submitting through a dashboard. Others arrive in bulk from an upstream system pushing a batch of invoices at end of day. Designing a pipeline for one profile while ignoring the other produces a system that works in demos but breaks under real operational load.

Document Intelligence Workbench supports both: a synchronous path that processes a single document inline and returns the extracted record immediately, and an asynchronous path that queues the document for background processing and returns a job ID. The two paths share the same extraction, validation, confidence scoring, and review routing logic. What differs is when the caller receives the result.

---

## The two processing paths and when to use each

**Synchronous processing (`POST /documents/process`)** processes the document inline within the API request. The caller receives the extracted record, confidence scores, validation status, and review-required flag in the response. This path is appropriate for low-volume interactive submission — an operator uploading a single contract through the dashboard, a system posting one invoice at a time and immediately inspecting the result.

**Asynchronous processing (`POST /documents/process-async`)** enqueues the document for background processing and returns a job ID immediately. The caller polls `GET /jobs?status=pending` or inspects the job record later to retrieve the result. This path is appropriate for high-volume batch submission, where blocking on each document would add unacceptable latency to the submitting system.

Both paths write to the same SQLite or PostgreSQL metadata store. The review queue (`GET /documents/review-queue`), the export endpoints, the audit trail, and the dashboard reflect records from both paths without distinction.

---

## How the async queue works

```
POST /documents/process-async
           ↓
    Job record created (status: pending)
    Job ID returned to caller
           ↓
    Background worker polls queue
           ↓
    Worker calls extraction + validation pipeline
           ↓
    Result persisted (status: completed or failed)
    Confidence and review-required flags set
           ↓
    Record appears in review-queue if flagged
```

The worker runs as a separate process (`scripts/run_queue_worker.py --continuous --poll-seconds 2`). In the forward Azure deployment, this maps to a Container Apps replica or a Functions-based worker triggered by queue messages.

---

## Retry policy and dead-letter behavior

The queue is not a fire-and-forget mechanism. Jobs that fail during processing are retried with exponential backoff — configurable through `QUEUE_RETRY_BASE_SECONDS` and `QUEUE_RETRY_MAX_SECONDS`. After a configurable number of attempts (`QUEUE_MAX_ATTEMPTS`), a job is moved to dead-letter status rather than silently dropped.

Dead-letter status is visible in `GET /jobs?status=dead_letter`. An operator can inspect the failure reason, correct the document or configuration, and resubmit. The failed job does not disappear. It is auditable.

This matters in production document processing: a batch of invoices where some fail extraction due to a malformed field should not silently reduce the processed count. Every failure should be visible and traceable.

Queue depth and job status distributions are exposed through `GET /metrics/queue`, which reports pending, processing, completed, failed, and dead-letter counts. This is the operational heartbeat for a batch processing environment.

---

## The full component map

**FastAPI service (`docint_workbench/api.py`).** Handles synchronous processing, async job submission, file upload (`POST /documents/upload`), review queue access, reviewer correction (`POST /documents/{id}/review`), and export. Health probes at `GET /health`.

**Background worker (`scripts/run_queue_worker.py`).** Continuously polls for pending jobs, runs the extraction and validation pipeline, and updates job status. Operates independently of the API process — a worker crash does not affect the API's ability to accept new submissions.

**Extraction profile.** Deterministic field parser for invoices and contracts. Configurable to use OpenAI or Azure OpenAI extraction adapters through `LLM_PROVIDER`. Falls back to deterministic mode when no provider is configured.

**Validation workflow.** Applies business rules after extraction: arithmetic consistency for invoices (subtotal + tax = total), date ordering for contracts (effective date before expiry date), required field presence for both types. Validation failures set the review-required flag independently of confidence scores.

**Review dashboard (`dashboard/app.py`).** Streamlit interface for reviewers to inspect flagged records, correct fields, and approve documents for export. The dashboard calls the FastAPI layer — it does not read the database directly.

**Metrics endpoints.** Three levels of operational visibility: `GET /metrics/summary` for document-level aggregates, `GET /metrics/queue` for queue state, and `GET /metrics/prometheus` for Prometheus-compatible scraping.

---

## The local-to-Azure component mapping

| Local | Azure |
|---|---|
| Synchronous + async FastAPI | Azure Container Apps: API service |
| Queue worker process | Container Apps: background worker replica |
| SQLite metadata store | Azure PostgreSQL or Cosmos DB |
| Local file extraction | Azure AI Document Intelligence |
| Deterministic LLM mock | Azure OpenAI |
| Local markdown documents | Azure Blob Storage |
| Environment variables | Azure Key Vault |
| File logs | Application Insights |

Every local component has a direct Azure counterpart. Switching is environment configuration — not a code change.

---

## Current limits

- The background worker is a polling process. A queue backend (Azure Service Bus, Redis) would replace polling with event-driven invocation for lower latency between submission and processing.
- Docker runtime files are included for containerized validation. End-to-end Docker testing requires a Docker-enabled environment.
- The OCR path via Tesseract is configuration-enabled but requires Tesseract to be installed locally. Azure AI Document Intelligence is the production path for layout-aware document parsing.
- Multi-instance worker deployment requires coordination to avoid duplicate job processing. A distributed queue backend resolves this.

---

## Next engineering step

Submit five documents through `POST /documents/process-async` in rapid succession, then poll `GET /metrics/queue` to observe the pending and processing counts while the worker runs. Confirm that dead-letter status appears correctly when a deliberately malformed document exceeds the retry limit.

---

## One question for you

In your current document processing system, when a batch job fails mid-run, how do you identify which specific documents failed, why they failed, and what the current retry status is?

---

*Next post: Three design decisions that shaped the pipeline — why deterministic extraction before LLM providers, why validation is a separate stage from extraction, and why reviewer scope mapping is built into the auth model.*
