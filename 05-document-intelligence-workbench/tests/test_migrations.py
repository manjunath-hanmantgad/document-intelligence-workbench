from __future__ import annotations

import os
from pathlib import Path

from scripts import migrate_database
from docint_workbench.config import get_settings
from docint_workbench.database import connect


def test_sqlite_migrations_are_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "migrated.db"
    original_env = {
        "DOCINT_DATABASE_BACKEND": os.getenv("DOCINT_DATABASE_BACKEND"),
        "DOCINT_DATABASE_PATH": os.getenv("DOCINT_DATABASE_PATH"),
        "DOCINT_DATABASE_URL": os.getenv("DOCINT_DATABASE_URL"),
    }
    try:
        os.environ["DOCINT_DATABASE_BACKEND"] = "sqlite"
        os.environ["DOCINT_DATABASE_PATH"] = str(db_path)
        os.environ.pop("DOCINT_DATABASE_URL", None)
        get_settings.cache_clear()

        assert migrate_database.main() == 0
        assert migrate_database.main() == 0

        with connect(db_path, database_backend="sqlite", database_url="") as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM schema_migrations").fetchone()
            assert int(row["count"]) >= 1
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()
