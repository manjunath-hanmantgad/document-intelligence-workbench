# API Reference

Base URL: `http://127.0.0.1:8005`

## Endpoints

- `GET /health`: service health and runtime environment.
- `POST /documents/process`: process a document payload.
- `POST /documents/process-async`: enqueue a document payload for background processing.
- `POST /documents/upload`: upload a file (`txt`, `pdf`, `docx`, `png`, `jpg`, `tiff`) and process extracted text.
- `GET /documents`: list processed documents.
- `GET /jobs`: list background jobs, optional `status` and `document_type` filters.
- `GET /jobs/{job_id}`: get one background job.
- `GET /documents/review-queue`: list review-required documents, optional `document_type` filter.
- `GET /documents/review-queue/partitions`: grouped review workload by document domain.
- `GET /documents/{document_id}`: get one processed document.
- `POST /documents/{document_id}/review`: submit reviewer field overrides.
- `GET /documents/{document_id}/export?export_format=json|csv`: export extracted fields.
- `GET /metrics/summary`: summary metrics for operations monitoring.
- `GET /metrics/queue`: queue depth and background processing counts.
- `GET /metrics/prometheus`: Prometheus-compatible counters and latency aggregates.
- `GET /audit/events`: reviewer audit trail, optional `document_id` query filter.
- `POST /evaluation/run`: execute reference-data extraction evaluation (admin authorization required).

## Auth Headers

- `X-API-Key`: required for reviewer endpoints when `AUTH_ENABLED=true` and `AUTH_MODE=api_key`.
- `Authorization: Bearer <token>`: required for reviewer endpoints when `AUTH_ENABLED=true` and `AUTH_MODE=oidc`.
- `X-Admin-Token`: required for `/evaluation/run` when `AUTH_MODE=api_key`.
- `Authorization: Bearer <admin token>`: required for `/evaluation/run` when `AUTH_MODE=oidc` (role must map to admin scope).
- `REVIEWER_ROLE_MAP` maps reviewer keys to roles (`ops`, `finance`, `legal`, `admin`) for role-aware audit actors and default scopes.
- `REVIEWER_SCOPE_MAP` constrains reviewer keys to document domains (for example `invoice` or `contract`) and can override role defaults.
- `OIDC_ROLE_SCOPE_MAP` maps token roles to allowed document domains for OIDC mode.

## Queue Job Lifecycle

- `pending`: queued or scheduled for retry (`next_run_at` determines the next eligible processing time).
- `in_progress`: currently claimed by a worker.
- `completed`: processed successfully and linked to `document_id`.
- `dead_letter`: terminal failure after max retry attempts.

## Example Process Request

```json
{
  "file_name": "invoice-record.txt",
  "document_type": "invoice",
  "content": "Vendor: Apex Office Supplies\nInvoice Number: INV-2026-0042\n..."
}
```
