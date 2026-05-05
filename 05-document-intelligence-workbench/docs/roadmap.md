# Roadmap

## Implemented

- Local-first API and dashboard
- Deterministic invoice and contract extraction profiles
- Confidence scoring and review-required flags
- Validation workflow and export endpoints
- Reference-data evaluation runner
- Binary upload parsing and OCR-ready path
- Reviewer auth and audit event trail
- Role-scoped review queues with queue partition endpoint
- Async document queue endpoints with background worker entrypoint
- Dual database backend configuration (`sqlite`/`postgres`) with migration scaffold
- Structured logging, request tracing, queue metrics endpoint, and Prometheus-compatible metrics export
- OpenAI/Azure extraction adapter path with deterministic fallback
- Queue retry policy with exponential backoff and dead-letter terminal state

## Next

- Validate provider adapters against staging credentials
- Validate Docker runtime proof on a Docker-enabled machine
