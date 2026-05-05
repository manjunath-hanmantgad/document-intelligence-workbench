CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    document_type TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence_average DOUBLE PRECISION NOT NULL,
    requires_review BOOLEAN NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS validations (
    id BIGSERIAL PRIMARY KEY,
    document_id TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    document_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);
