# Operations

## Health And Checks

- `GET /health` for liveness.
- `GET /metrics/summary` for extraction workload and confidence posture.
- `GET /metrics/queue` for job backlog and worker throughput posture.
- `GET /metrics/prometheus` for counters and latency aggregates.
- `GET /documents/review-queue` for prioritized reviewer workload.
- `GET /documents/review-queue/partitions` for domain-level queue balancing by reviewer scope.
- `GET /jobs` for queue depth and processing status visibility.
- `GET /audit/events` for reviewer action history.
- `POST /evaluation/run` for reference-data quality checks.
- Validate auth posture: `AUTH_MODE=api_key` for local validation or `AUTH_MODE=oidc` for enterprise identity integration.

## Runbook

- If extraction confidence drops, inspect source document formatting.
- If uploaded image parsing fails, verify `ENABLE_LOCAL_OCR=true` and local Tesseract availability.
- If validation failures spike, review invoice totals and contract date parsing rules.
- If async jobs fail, inspect `GET /jobs` for retry scheduling (`pending` with `next_run_at`) versus terminal failures (`dead_letter`).
- Periodically rerun evaluation against known-good references.
- For managed DB rollout, execute `scripts/migrate_database.py` before starting API instances.
- Run queue worker for async processing: `scripts/run_queue_worker.py --continuous`.
- Tune queue reliability with `QUEUE_MAX_ATTEMPTS`, `QUEUE_RETRY_BASE_SECONDS`, and `QUEUE_RETRY_MAX_SECONDS`.
- Use `docs/alerting.md` and `docs/slo-runbook.md` as operational incident references.
