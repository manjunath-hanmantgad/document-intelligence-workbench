# Data Model

The service uses a shared relational schema across supported backends:

- `documents`: top-level processing status and confidence summary.
- `extracted_fields`: per-field extraction value, confidence, and review-required flag.
- `validations`: validation outcomes per processed document.
- `audit_events`: reviewer and export activity trail.
- `schema_migrations`: applied migration versions.

## Backend Selection

- `DOCINT_DATABASE_BACKEND=sqlite` (default local mode)
- `DOCINT_DATABASE_BACKEND=postgres` with `DOCINT_DATABASE_URL` for managed runtime

## Migration Workflow

SQL migrations are versioned under:

- `migrations/sqlite/`
- `migrations/postgres/`

Run migrations with:

```bash
./venv/bin/python scripts/migrate_database.py
```

Runtime still initializes tables defensively, but managed deployment should apply migrations explicitly during deployment pipelines.
