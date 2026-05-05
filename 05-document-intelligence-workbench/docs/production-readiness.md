# Production Readiness

Current status: production-grade implementation complete for extraction, validation workflow, role-scoped review queues, async processing queue foundation, and exports.

## Completed

- FastAPI API and Streamlit review dashboard.
- Deterministic extraction and validation baseline.
- Binary upload parsing for txt/pdf/docx and optional OCR path for images.
- Mode-aware reviewer/admin authorization (`api_key` or OIDC bearer token with role-based gating).
- Dual reviewer authentication modes (`api_key` and OIDC bearer token) with role-scoped access control.
- Scoped reviewer permissions by role/domain with dedicated review-queue and queue-partition endpoints.
- Persistent reviewer audit trail.
- Async queue endpoints and worker entrypoint for background processing.
- SQLite and PostgreSQL backend configuration with migration scaffold.
- Structured JSON request logging with request-id propagation and Prometheus-compatible metrics endpoint.
- Operational SLO and alerting baseline documentation.
- Reference evaluation workflow.
- Test suite and CI workflow.
- Docker runtime files.
- Azure-ready environment placeholders.

## External Environment Validation

Use `scripts/verify_live_integrations.py` to verify provider and cloud configuration readiness. Unconfigured checks return `skip` without blocking local operation.

## Execution Tracker

Use `docs/execution-checklist.md` as the source of truth for production hardening and public release completion tracking.

## Remaining For Public Release Hardening

- Validate Docker runtime in a Docker-enabled environment.
- Run provider checks with real staging credentials and archive outputs in `artifacts/`.
