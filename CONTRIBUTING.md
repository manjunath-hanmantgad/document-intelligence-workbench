# Contributing

Thank you for contributing to Document Intelligence Workbench.

## Development Setup

1. Create a virtual environment and install dependencies:
   - `python3.12 -m venv .venv`
   - `.venv/bin/pip install -r requirements.txt`
2. Copy environment template:
   - `cp .env.example .env`
3. Run tests:
   - `.venv/bin/pytest -q`

## Pull Request Expectations

1. Keep changes scoped and production-focused.
2. Update docs for any API, dashboard, security, or deployment behavior changes.
3. Include or update tests for backend logic changes.
4. Ensure public release guardrails pass:
   - `.venv/bin/python scripts/prepare_public_release.py --destination /private/tmp/document-intelligence-workbench-public`

## Coding Standards

1. Python 3.12 compatible.
2. Prefer explicit typing and deterministic behavior.
3. Avoid committing secrets, local databases, or temporary runtime artifacts.
