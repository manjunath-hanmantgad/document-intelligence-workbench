# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Added

- Role-aware reviewer actor context in API audit flows.
- Review queue partition endpoint (`/documents/review-queue/partitions`) and dashboard integration.
- Public-repository governance files (`LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`).
- Production/public release execution checklist (`docs/execution-checklist.md`).
- OIDC bearer-token authentication mode with role-to-scope mapping and admin-gated evaluation authorization.
- Dual database backend configuration (`sqlite`/`postgres`) with migration runner and versioned SQL migration scaffold.
- Async processing queue APIs (`/documents/process-async`, `/jobs`) and queue worker runtime (`scripts/run_queue_worker.py`).
- Structured JSON logging, request tracing headers, queue metrics endpoint, and Prometheus export.
- Provider-backed extraction path for OpenAI/Azure with deterministic fallback and Azure Document Intelligence upload parsing integration.
- Operational alerting and SLO/runbook documentation.

### Changed

- Review queue aggregation now applies stable `updated_at` ordering across scoped document domains.
- Public release validation now expects governance files to be present.
