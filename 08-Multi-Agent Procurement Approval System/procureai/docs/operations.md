# Operations Guide

## Health Checks

```bash
curl http://127.0.0.1:8004/health
# {"status": "healthy"}
```

The `/health` endpoint can be used by load balancers, orchestrators, and monitoring systems. It returns HTTP 200 when the server is running. Database connectivity can be verified by checking the MCP tool registry:

```bash
curl http://127.0.0.1:8004/mcp/tools
```

A successful response with registered tools confirms the database is accessible.

## Starting the Service

### Local (development)

```bash
cd procureai
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8004 --reload
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8004 --workers 4
```

### Optional: Streamlit Dashboard

```bash
streamlit run dashboard/app.py --server.port 8501 --server.headless true
```

## Data Initialization

Run these commands once before first use:

```bash
# Initialize tables and seed vendors, budgets, sample requests
python -c "from app.db.seed import seed_all; seed_all()"

# Ingest procurement policy into the RAG index
python -c "from app.rag.ingest_policy import ingest_policy_document; ingest_policy_document()"
```

These commands are idempotent — safe to re-run.

## Demo Reset

To reset the database to its initial seeded state:

```bash
rm -f data/procureai.db data/procureai.db-shm data/procureai.db-wal
python -c "from app.db.seed import seed_all; seed_all()"
python -c "from app.rag.ingest_policy import ingest_policy_document; ingest_policy_document()"
```

## Updating Reference Data

### Add or update vendors

Edit `data/vendor_master.csv` and re-run:

```bash
python -c "from app.db.seed import seed_vendors; seed_vendors()"
```

### Update department budgets

Edit `data/department_budget.csv` and re-run:

```bash
python -c "from app.db.seed import seed_budgets; seed_budgets()"
```

### Update procurement policy

Edit `data/procurement_policy.md` and re-ingest:

```bash
python -c "from app.rag.ingest_policy import ingest_policy_document; ingest_policy_document()"
```

## Logging

Structured logging is controlled by two environment variables:

| Variable | Values | Effect |
|----------|--------|--------|
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Log verbosity |
| `JSON_LOGS` | `true` / `false` | JSON vs. plain text output |

Set `JSON_LOGS=true` and direct stdout to a log aggregator (Datadog, Application Insights) in production.

## Audit Trail

Every purchase request generates an audit log. Retrieve it:

```bash
curl http://127.0.0.1:8004/audit/{request_id}
```

Each audit entry records: request ID, agent name, action description, and timestamp. The audit log is append-only and is not modified after creation.

## Integration Verification

Before any deployment, run the live integration check:

```bash
python scripts/verify_live_integrations.py
```

This script verifies: health, MCP tools/resources/prompts, A2A agent cards for all six agents, purchase request analysis, request status, and audit log retrieval.

Expected output: `All checks passed.`

## Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `no such table: vendors` | Data not seeded | Run `seed_all()` |
| `no such table: policy_embeddings` | Policy not ingested | Run `ingest_policy_document()` |
| `FOREIGN KEY constraint failed` | Approval written before request stored | Fixed in orchestrator v1.0.1+ |
| `database is locked` | Concurrent writes on WAL mode | Restart server; use WAL journal mode (default) |
| `Cannot connect to API` | Server not running | Run uvicorn command |

## Database Backup

For local use, the SQLite database is at `data/procureai.db`. Back it up with:

```bash
cp data/procureai.db data/procureai.db.backup.$(date +%Y%m%d)
```

For production, migrate to PostgreSQL and use managed database backup.

## Environment Variable Reference

See `.env.example` for the full list. Key operational variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROCUREAI_DB_PATH` | `data/procureai.db` | SQLite database path |
| `PROCUREAI_POLICY_PATH` | `data/procurement_policy.md` | Policy document |
| `APPROVAL_MATRIX_PATH` | `data/approval_matrix.yaml` | Approval rules |
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `8004` | Listen port |
| `CORS_ORIGINS` | `*` | Restrict in production |
| `LLM_PROVIDER` | `mock` | `mock`, `openai`, or `azure` |
