from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docint_workbench.config import get_settings
from scripts.verify_live_integrations import (
    check_auth_config,
    check_azure_env,
    check_database_config,
    check_document_intelligence_env,
    check_openai_env,
)


ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def _run_scenario(name: str, env_overrides: dict[str, str]) -> dict[str, object]:
    snapshot = {key: os.environ.get(key) for key in env_overrides}
    try:
        for key, value in env_overrides.items():
            os.environ[key] = value
        get_settings.cache_clear()
        checks = [
            check_openai_env(),
            check_azure_env(),
            check_document_intelligence_env(),
            check_auth_config(),
            check_database_config(),
        ]
        return {
            "scenario": name,
            "checks": [check.__dict__ for check in checks],
        }
    finally:
        for key, previous in snapshot.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous
        get_settings.cache_clear()


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = [
        _run_scenario(
            "openai_mode",
            {
                "AUTH_ENABLED": "true",
                "AUTH_MODE": "api_key",
                "REVIEWER_API_KEYS": "local-reviewer-key",
                "ADMIN_TOKEN": "local-admin-token",
                "DOCINT_DATABASE_BACKEND": "sqlite",
                "DOCINT_DATABASE_PATH": "storage/docint_workbench.db",
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            },
        ),
        _run_scenario(
            "azure_mode",
            {
                "AUTH_ENABLED": "true",
                "AUTH_MODE": "oidc",
                "OIDC_ALGORITHMS": "HS256",
                "OIDC_HS256_SHARED_SECRET": "local-test-secret",
                "DOCINT_DATABASE_BACKEND": "postgres",
                "DOCINT_DATABASE_URL": "postgresql://appuser:appuser@localhost:5432/docint",
                "LLM_PROVIDER": "azure",
                "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "AZURE_OPENAI_KEY": os.getenv("AZURE_OPENAI_KEY", ""),
                "AZURE_OPENAI_CHAT_DEPLOYMENT": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", ""),
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", ""),
                "AZURE_DOCUMENT_INTELLIGENCE_KEY": os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", ""),
            },
        ),
    ]
    all_checks = [check for scenario in scenarios for check in scenario["checks"]]
    fail_count = sum(1 for check in all_checks if check["status"] == "fail")
    pass_count = sum(1 for check in all_checks if check["status"] == "pass")
    skip_count = sum(1 for check in all_checks if check["status"] == "skip")

    payload = {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "summary": {
            "pass": pass_count,
            "fail": fail_count,
            "skip": skip_count,
            "overall_status": "fail" if fail_count else "pass",
        },
        "scenarios": scenarios,
    }
    output_path = ARTIFACT_DIR / "provider_live_check_output.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Provider live-check artifact written: {output_path}")
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
