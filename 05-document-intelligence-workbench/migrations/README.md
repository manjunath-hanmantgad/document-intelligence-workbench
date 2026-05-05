# Database Migrations

This directory stores SQL migrations by backend:

- `sqlite/`
- `postgres/`

Migration files must follow `NNNN_description.sql` ordering and remain immutable after release.

Use the migration runner:

```bash
./venv/bin/python scripts/migrate_database.py
```

Configuration is resolved from `.env` / environment variables:

- `DOCINT_DATABASE_BACKEND` (`sqlite` or `postgres`)
- `DOCINT_DATABASE_PATH` (for sqlite)
- `DOCINT_DATABASE_URL` (for postgres)
