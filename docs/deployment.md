# Deployment Guide

## Local Deployment

1. Create a Python 3.12 virtual environment.
2. Install dependencies from `requirements.txt`.
3. Seed reference data.
4. Start FastAPI and optional Streamlit dashboard.
5. For enterprise auth, set `AUTH_MODE=oidc` with issuer, audience, algorithm, and JWKS configuration.
6. For managed persistence, set `DOCINT_DATABASE_BACKEND=postgres`, configure `DOCINT_DATABASE_URL`, and run `scripts/migrate_database.py`.
7. Run `scripts/run_queue_worker.py --continuous` to process async document jobs.
8. Set `QUEUE_MAX_ATTEMPTS`, `QUEUE_RETRY_BASE_SECONDS`, and `QUEUE_RETRY_MAX_SECONDS` for retry/dead-letter policy.
9. Set `LLM_PROVIDER=openai` or `LLM_PROVIDER=azure` with required provider credentials for live extraction paths.

## Managed Deployment Path (Azure)

1. Containerize API and dashboard for Azure Container Apps.
2. Replace local storage with managed database.
3. Integrate Azure AI Document Intelligence and Azure OpenAI.
4. Store secrets in Azure Key Vault.
5. Wire telemetry to Application Insights.

The project is Azure-ready by configuration but does not require Azure credentials for local validation.
