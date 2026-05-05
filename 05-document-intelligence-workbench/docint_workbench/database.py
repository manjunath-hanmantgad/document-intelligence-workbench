from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional dependency for postgres mode
    psycopg = None
    dict_row = None


def _dict_factory(cursor: sqlite3.Cursor, row: tuple[object, ...]) -> dict[str, object]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def _to_driver_query(backend: str, query: str) -> str:
    if backend == "postgres":
        return query.replace("?", "%s")
    return query


class ManagedConnection:
    def __init__(self, backend: str, conn: sqlite3.Connection | object) -> None:
        self.backend = backend
        self._conn = conn

    def execute(self, query: str, params: tuple[object, ...] = ()) -> object:
        return self._conn.execute(_to_driver_query(self.backend, query), params)

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


@contextmanager
def connect(
    database_path: Path,
    database_backend: str = "sqlite",
    database_url: str = "",
) -> Iterator[ManagedConnection]:
    backend = database_backend.strip().lower()
    if backend not in {"sqlite", "postgres"}:
        raise ValueError(f"Unsupported DOCINT_DATABASE_BACKEND '{database_backend}'")

    if backend == "postgres":
        if psycopg is None or dict_row is None:
            raise ValueError("psycopg is required for DOCINT_DATABASE_BACKEND=postgres")
        if not database_url:
            raise ValueError("DOCINT_DATABASE_URL must be configured for DOCINT_DATABASE_BACKEND=postgres")
        conn = psycopg.connect(database_url, row_factory=dict_row)
        managed = ManagedConnection(backend=backend, conn=conn)
    else:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(database_path)
        conn.row_factory = _dict_factory
        managed = ManagedConnection(backend=backend, conn=conn)

    try:
        yield managed
    finally:
        managed.close()


def init_db(conn: ManagedConnection) -> None:
    if conn.backend == "postgres":
        statements = (
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                document_type TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence_average DOUBLE PRECISION NOT NULL,
                requires_review BOOLEAN NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS extracted_fields (
                id BIGSERIAL PRIMARY KEY,
                document_id TEXT NOT NULL,
                field_key TEXT NOT NULL,
                field_value TEXT NOT NULL,
                confidence DOUBLE PRECISION NOT NULL,
                requires_review BOOLEAN NOT NULL,
                validator_status TEXT NOT NULL,
                validator_message TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS validations (
                id BIGSERIAL PRIMARY KEY,
                document_id TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id BIGSERIAL PRIMARY KEY,
                document_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS processing_jobs (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                document_type TEXT NOT NULL,
                status TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                worker_id TEXT,
                attempt_count INTEGER NOT NULL,
                document_id TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                next_run_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """,
        )
        for statement in statements:
            conn.execute(statement)
    else:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                document_type TEXT NOT NULL,
                status TEXT NOT NULL,
                confidence_average REAL NOT NULL,
                requires_review INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS extracted_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                field_key TEXT NOT NULL,
                field_value TEXT NOT NULL,
                confidence REAL NOT NULL,
                requires_review INTEGER NOT NULL,
                validator_status TEXT NOT NULL,
                validator_message TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processing_jobs (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                content TEXT NOT NULL,
                document_type TEXT NOT NULL,
                status TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                worker_id TEXT,
                attempt_count INTEGER NOT NULL,
                document_id TEXT,
                last_error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                next_run_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )
    conn.commit()
