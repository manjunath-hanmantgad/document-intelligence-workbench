# Runbook — Document Intelligence Workbench

## Service overview
Document Intelligence Workbench processes invoice/contract documents, extracts fields, validates outputs, and manages reviewer queues. If this service degrades, extraction workflows, async processing, and review operations are impacted.

## Health checks
| Endpoint | Expected | What it means |
|---|---|---|
| `GET /health` | `200` with `{"status":"ok",...}` | API process is alive |
| `GET /metrics/summary` | `200` summary payload | Aggregate operational metrics are readable |
| `GET /metrics/queue` | `200` queue metrics payload | Async queue state is accessible |
| `GET /metrics/prometheus` | `200` text payload | Prometheus scraping path is healthy |

## Common failure scenarios

### Reviewer auth failures
**Symptom:** reviewer endpoints return `401`/`403`.
**Action:**
1. Confirm `AUTH_ENABLED`, `AUTH_MODE`, and reviewer credentials in `.env`.
2. For API-key mode, validate `X-API-Key` exists in configured key map.
3. For OIDC mode, verify issuer/audience/JWKS settings.

### Queue backlog or dead-letter growth
**Symptom:** `/metrics/queue` shows increasing pending/dead-letter counts.
**Action:**
1. Start worker: `python scripts/run_queue_worker.py --continuous`
2. Check queue retry settings: `QUEUE_MAX_ATTEMPTS`, `QUEUE_RETRY_BASE_SECONDS`, `QUEUE_RETRY_MAX_SECONDS`.
3. Inspect failed jobs via `GET /jobs?status=dead_letter`.

### Extraction quality regressions
**Symptom:** more documents enter review queue due to low confidence or validation failures.
**Action:**
1. Run `POST /evaluation/run`.
2. Inspect extraction/validation logic with sample payloads.
3. Review recent corrections through `GET /audit/events`.

### Upload parsing failures
**Symptom:** `/documents/upload` returns `400` parsing errors.
**Action:**
1. Confirm supported file type (`txt`, `pdf`, `docx`, `png`, `jpg`, `tiff`).
2. Check size limits (`MAX_UPLOAD_BYTES`, `MAX_UPLOAD_CHARS`).
3. If OCR path needed, verify Azure Document Intelligence config.

## Rollback procedure
```bash
az containerapp revision list \
  --name <DOCINT_API_CONTAINER_APP> \
  --resource-group <RESOURCE_GROUP>

az containerapp revision activate \
  --name <DOCINT_API_CONTAINER_APP> \
  --resource-group <RESOURCE_GROUP> \
  --revision <PREVIOUS_REVISION_NAME>
```

## Log access
```bash
# Local API logs
docker compose logs -f api

# Azure logs
az containerapp logs show \
  --name <DOCINT_API_CONTAINER_APP> \
  --resource-group <RESOURCE_GROUP> \
  --follow
```

## Contacts / escalation
- Primary owner: [fill in]
- Secondary owner: [fill in]
- Escalation SLA: [fill in]
