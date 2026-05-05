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
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_processing_jobs_status_created
ON processing_jobs(status, created_at);
