# Issues Tracker

Use this document before debugging or continuing implementation. It records bugs, environment constraints, and fixes already discovered so the same issue is not investigated repeatedly.

## Process

When a bug is found:

1. Add it to this file or the relevant project tracker.
2. Include symptoms, root cause, fix, and verification.
3. If the issue affects future projects, add a reusable note under Global Lessons.

## Global Lessons

### Python Version

- Symptom: Project docs require Python 3.11+, but `python3` on this machine is Python 3.9.6.
- Root cause: System default Python is older than the project runtime target.
- Fix: Use `python3.12` or create venv with Python 3.12.
- Verification: `python3.12 --version` returns Python 3.12.13.

### uv Cache Permissions

- Symptom: `uv python list` failed with an operation-not-permitted error under `/Users/manjunathhanmantgad/.cache/uv`.
- Root cause: sandbox restrictions blocked access to uv's default cache.
- Fix: Request elevated execution for `uv venv` and dependency installation when required.
- Verification: `.venv` was created and dependencies installed successfully.

### Localhost Port Binding

- Symptom: Uvicorn and Streamlit failed with permission errors when binding localhost ports inside the default sandbox.
- Root cause: sandbox blocked local server port binding.
- Fix: Request elevated execution for local dev servers.
- Verification: FastAPI gateway started on `127.0.0.1:8001`; Streamlit started on `127.0.0.1:8510`.

### Docker Availability

- Symptom: `docker --version` returned command not found.
- Root cause: Docker is not installed or not available in shell.
- Fix: Do not block local code implementation. Mark Docker verification pending until Docker is available.
- Verification: Not yet verified.

### Port Conflicts

- Symptom: Streamlit port `8501` was already in use; user also reported `8502` was already used by another service.
- Root cause: existing local services occupy default Streamlit ports.
- Fix: Use `8510` for the LLM Observatory dashboard during this session.
- Verification: Streamlit reported dashboard available at `http://127.0.0.1:8510`.

## Project Trackers

- LLM Observatory: `01-llm-observatory/docs/issues.md`
