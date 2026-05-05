from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docint_workbench.config import get_settings
from docint_workbench.database import connect


MIGRATIONS_ROOT = Path(__file__).resolve().parents[1] / "migrations"


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _split_sql(sql: str) -> list[str]:
    statements = [statement.strip() for statement in re.split(r";\s*(?:\n|$)", sql) if statement.strip()]
    return statements


def _ensure_migrations_table(conn: object) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _applied_versions(conn: object) -> set[str]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {str(row["version"]) for row in rows}


def _migration_files(backend: str) -> list[Path]:
    backend_dir = MIGRATIONS_ROOT / backend
    if not backend_dir.exists():
        return []
    return sorted(path for path in backend_dir.glob("*.sql") if path.is_file())


def main() -> int:
    settings = get_settings()
    backend = settings.database_backend
    migrations = _migration_files(backend)
    if not migrations:
        print(f"No migration files found for backend={backend}")
        return 1

    with connect(
        settings.database_path,
        database_backend=settings.database_backend,
        database_url=settings.database_url,
    ) as conn:
        _ensure_migrations_table(conn)
        applied = _applied_versions(conn)
        applied_count = 0
        for migration_file in migrations:
            version = migration_file.stem
            if version in applied:
                continue
            sql = migration_file.read_text(encoding="utf-8")
            for statement in _split_sql(sql):
                try:
                    conn.execute(statement)
                except Exception as exc:
                    message = str(exc).lower()
                    if "duplicate column name" in message or "already exists" in message:
                        continue
                    raise
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, _utc_now()),
            )
            conn.commit()
            applied_count += 1
            print(f"Applied migration: {backend}/{migration_file.name}")

    print(f"Migration run complete. Newly applied: {applied_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
