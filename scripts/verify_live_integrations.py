from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docint_workbench.config import get_settings


@dataclass
class Check:
    name: str
    status: str
    detail: str


def check_docker() -> Check:
    if not shutil.which("docker"):
        return Check("docker_compose", "skip", "docker command not found")
    result = subprocess.run(["docker", "compose", "config"], capture_output=True, text=True)
    if result.returncode != 0:
        return Check("docker_compose", "fail", result.stderr.strip() or result.stdout.strip())
    return Check("docker_compose", "pass", "docker compose config is valid")


def check_openai_env() -> Check:
    if os.getenv("LLM_PROVIDER") != "openai":
        return Check("openai_mode", "skip", "set LLM_PROVIDER=openai to validate OpenAI mode")
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        return Check("openai_mode", "fail", "OPENAI_API_KEY is required for openai mode")
    return Check("openai_mode", "pass", "OPENAI_API_KEY configured")


def check_azure_env() -> Check:
    if os.getenv("LLM_PROVIDER") != "azure":
        return Check("azure_mode", "skip", "set LLM_PROVIDER=azure to validate Azure mode")
    settings = get_settings()
    try:
        settings.require_openai_credentials()
    except ValueError as exc:
        return Check("azure_mode", "fail", str(exc))
    return Check("azure_mode", "pass", "Azure OpenAI configuration placeholders are set")


def check_document_intelligence_env() -> Check:
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")
    if not endpoint or not key:
        return Check(
            "azure_document_intelligence",
            "skip",
            "set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY",
        )
    return Check("azure_document_intelligence", "pass", "Azure Document Intelligence configuration is present")


def check_auth_config() -> Check:
    enabled = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    if not enabled:
        return Check("auth_config", "skip", "AUTH_ENABLED=false")
    auth_mode = os.getenv("AUTH_MODE", "api_key").strip().lower() or "api_key"
    if auth_mode == "api_key" and not os.getenv("REVIEWER_API_KEYS", "").strip():
        return Check("auth_config", "fail", "REVIEWER_API_KEYS must be configured for AUTH_MODE=api_key")
    if auth_mode == "oidc":
        has_hs = bool(os.getenv("OIDC_HS256_SHARED_SECRET", "").strip())
        has_jwks = bool(os.getenv("OIDC_JWKS_URL", "").strip())
        if not (has_hs or has_jwks):
            return Check(
                "auth_config",
                "fail",
                "OIDC_HS256_SHARED_SECRET or OIDC_JWKS_URL must be configured for AUTH_MODE=oidc",
            )
        if not os.getenv("OIDC_ALGORITHMS", "").strip():
            return Check("auth_config", "fail", "OIDC_ALGORITHMS must be configured for AUTH_MODE=oidc")
    if auth_mode not in {"api_key", "oidc"}:
        return Check("auth_config", "fail", f"Unsupported AUTH_MODE={auth_mode}")
    if auth_mode == "api_key" and not os.getenv("ADMIN_TOKEN", "").strip():
        return Check("auth_config", "fail", "ADMIN_TOKEN must be configured when auth is enabled")
    return Check("auth_config", "pass", f"Authentication configured for AUTH_MODE={auth_mode}")


def check_database_config() -> Check:
    backend = os.getenv("DOCINT_DATABASE_BACKEND", "sqlite").strip().lower() or "sqlite"
    if backend == "sqlite":
        return Check("database_config", "pass", "SQLite local runtime configured")
    if backend == "postgres":
        if not os.getenv("DOCINT_DATABASE_URL", "").strip():
            return Check("database_config", "fail", "DOCINT_DATABASE_URL is required for postgres backend")
        return Check("database_config", "pass", "Postgres backend configuration is present")
    return Check("database_config", "fail", f"Unsupported DOCINT_DATABASE_BACKEND={backend}")


def main() -> int:
    checks = [
        check_docker(),
        check_openai_env(),
        check_azure_env(),
        check_document_intelligence_env(),
        check_auth_config(),
        check_database_config(),
    ]
    print(json.dumps([check.__dict__ for check in checks], indent=2))
    return 1 if any(check.status == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
