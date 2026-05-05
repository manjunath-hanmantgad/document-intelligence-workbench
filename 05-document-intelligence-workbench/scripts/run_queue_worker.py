from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docint_workbench.config import get_settings
from docint_workbench.service import DocumentWorkbenchService


def default_worker_id() -> str:
    return f"{socket.gethostname()}-queue-worker"


def build_service() -> DocumentWorkbenchService:
    settings = get_settings()
    return DocumentWorkbenchService(
        database_path=settings.database_path,
        low_confidence_threshold=settings.low_confidence_threshold,
        evaluation_set_path=Path("examples/evaluation_set.json"),
        database_backend=settings.database_backend,
        database_url=settings.database_url,
        llm_provider=settings.llm_provider,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_key=settings.azure_openai_key,
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        queue_max_attempts=settings.queue_max_attempts,
        queue_retry_base_seconds=settings.queue_retry_base_seconds,
        queue_retry_max_seconds=settings.queue_retry_max_seconds,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run document processing queue worker.")
    parser.add_argument("--worker-id", default=default_worker_id(), help="Worker identifier stored on processed jobs.")
    parser.add_argument("--max-jobs", type=int, default=1, help="Maximum jobs to process before exit.")
    parser.add_argument("--poll-seconds", type=float, default=2.0, help="Poll interval when no jobs are available.")
    parser.add_argument("--continuous", action="store_true", help="Run continuously until interrupted.")
    args = parser.parse_args()

    service = build_service()
    processed = 0
    while True:
        job = service.process_next_job(worker_id=args.worker_id)
        if job is None:
            if not args.continuous:
                break
            time.sleep(max(0.1, args.poll_seconds))
            continue

        processed += 1
        print(f"processed job={job.job_id} status={job.status} document_id={job.document_id}")
        if not args.continuous and processed >= max(1, args.max_jobs):
            break

    print(f"worker complete processed={processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
