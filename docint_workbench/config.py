from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROLE_SCOPE_DEFAULTS: dict[str, tuple[str, ...]] = {
    "ops": ("invoice", "contract", "unknown"),
    "finance": ("invoice",),
    "legal": ("contract",),
    "admin": ("*",),
}


def _parse_reviewer_scope_map(value: str) -> dict[str, tuple[str, ...]]:
    scope_map: dict[str, tuple[str, ...]] = {}
    if not value.strip():
        return scope_map
    for item in value.split(";"):
        token_part, _, scope_part = item.strip().partition(":")
        token = token_part.strip()
        if not token:
            continue
        raw_scopes = [scope.strip() for scope in scope_part.split(",") if scope.strip()]
        if not raw_scopes:
            raw_scopes = ["invoice", "contract", "unknown"]
        scope_map[token] = tuple(raw_scopes)
    return scope_map


def _parse_reviewer_role_map(value: str) -> dict[str, str]:
    role_map: dict[str, str] = {}
    if not value.strip():
        return role_map
    for item in value.split(";"):
        token_part, _, role_part = item.strip().partition(":")
        token = token_part.strip()
        role = role_part.strip().lower() or "ops"
        if token:
            role_map[token] = role
    return role_map


def _parse_role_scope_map(value: str) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, tuple[str, ...]] = {}
    if not value.strip():
        return mapping
    for item in value.split(";"):
        role_part, _, scope_part = item.strip().partition(":")
        role = role_part.strip().lower()
        if not role:
            continue
        raw_scopes = [scope.strip() for scope in scope_part.split(",") if scope.strip()]
        if not raw_scopes:
            raw_scopes = list(ROLE_SCOPE_DEFAULTS.get(role, ("invoice", "contract", "unknown")))
        mapping[role] = tuple(raw_scopes)
    return mapping


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    log_level: str
    database_path: Path
    database_backend: str
    database_url: str
    low_confidence_threshold: float
    max_upload_chars: int
    max_upload_bytes: int
    queue_max_attempts: int
    queue_retry_base_seconds: int
    queue_retry_max_seconds: int
    enable_local_ocr: bool
    auth_enabled: bool
    auth_mode: str
    reviewer_api_keys: tuple[str, ...]
    reviewer_scope_map: dict[str, tuple[str, ...]]
    reviewer_role_map: dict[str, str]
    oidc_issuer: str
    oidc_audience: str
    oidc_algorithms: tuple[str, ...]
    oidc_jwks_url: str
    oidc_hs256_shared_secret: str
    oidc_role_claim: str
    oidc_subject_claim: str
    oidc_role_scope_map: dict[str, tuple[str, ...]]
    admin_token: str
    llm_provider: str
    openai_api_key: str
    openai_model: str
    azure_openai_endpoint: str
    azure_openai_key: str
    azure_openai_chat_deployment: str
    azure_document_intelligence_endpoint: str
    azure_document_intelligence_key: str

    def require_openai_credentials(self) -> None:
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set when LLM_PROVIDER=openai")
        if self.llm_provider == "azure":
            missing = [
                name
                for name, value in {
                    "AZURE_OPENAI_ENDPOINT": self.azure_openai_endpoint,
                    "AZURE_OPENAI_KEY": self.azure_openai_key,
                    "AZURE_OPENAI_CHAT_DEPLOYMENT": self.azure_openai_chat_deployment,
                }.items()
                if not value
            ]
            if missing:
                raise ValueError("Missing Azure OpenAI configuration: " + ", ".join(missing))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    reviewer_keys = tuple(
        key.strip() for key in os.getenv("REVIEWER_API_KEYS", "local-reviewer-key").split(",") if key.strip()
    )
    reviewer_role_map = _parse_reviewer_role_map(os.getenv("REVIEWER_ROLE_MAP", ""))
    if not reviewer_role_map:
        reviewer_role_map = {key: "ops" for key in reviewer_keys}

    reviewer_scope_map = _parse_reviewer_scope_map(os.getenv("REVIEWER_SCOPE_MAP", ""))
    if not reviewer_scope_map:
        reviewer_scope_map = {
            key: ROLE_SCOPE_DEFAULTS.get(reviewer_role_map.get(key, "ops"), ("invoice", "contract", "unknown"))
            for key in reviewer_keys
        }
    oidc_role_scope_map = _parse_role_scope_map(os.getenv("OIDC_ROLE_SCOPE_MAP", ""))
    if not oidc_role_scope_map:
        oidc_role_scope_map = ROLE_SCOPE_DEFAULTS
    oidc_algorithms = tuple(
        algorithm.strip() for algorithm in os.getenv("OIDC_ALGORITHMS", "RS256").split(",") if algorithm.strip()
    )

    return Settings(
        app_name=os.getenv("APP_NAME", "Document Intelligence Workbench"),
        app_env=os.getenv("APP_ENV", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        database_path=Path(os.getenv("DOCINT_DATABASE_PATH", "storage/docint_workbench.db")),
        database_backend=os.getenv("DOCINT_DATABASE_BACKEND", "sqlite").strip().lower() or "sqlite",
        database_url=os.getenv("DOCINT_DATABASE_URL", "").strip(),
        low_confidence_threshold=float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.85")),
        max_upload_chars=int(os.getenv("MAX_UPLOAD_CHARS", "120000")),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", "8000000")),
        queue_max_attempts=int(os.getenv("QUEUE_MAX_ATTEMPTS", "3")),
        queue_retry_base_seconds=int(os.getenv("QUEUE_RETRY_BASE_SECONDS", "5")),
        queue_retry_max_seconds=int(os.getenv("QUEUE_RETRY_MAX_SECONDS", "300")),
        enable_local_ocr=os.getenv("ENABLE_LOCAL_OCR", "false").lower() == "true",
        auth_enabled=os.getenv("AUTH_ENABLED", "true").lower() == "true",
        auth_mode=os.getenv("AUTH_MODE", "api_key").strip().lower() or "api_key",
        reviewer_api_keys=reviewer_keys,
        reviewer_scope_map=reviewer_scope_map,
        reviewer_role_map=reviewer_role_map,
        oidc_issuer=os.getenv("OIDC_ISSUER", ""),
        oidc_audience=os.getenv("OIDC_AUDIENCE", ""),
        oidc_algorithms=oidc_algorithms or ("RS256",),
        oidc_jwks_url=os.getenv("OIDC_JWKS_URL", ""),
        oidc_hs256_shared_secret=os.getenv("OIDC_HS256_SHARED_SECRET", ""),
        oidc_role_claim=os.getenv("OIDC_ROLE_CLAIM", "roles"),
        oidc_subject_claim=os.getenv("OIDC_SUBJECT_CLAIM", "sub"),
        oidc_role_scope_map=oidc_role_scope_map,
        admin_token=os.getenv("ADMIN_TOKEN", "local-admin-token"),
        llm_provider=os.getenv("LLM_PROVIDER", "deterministic"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_openai_key=os.getenv("AZURE_OPENAI_KEY", ""),
        azure_openai_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", ""),
        azure_document_intelligence_endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", ""),
        azure_document_intelligence_key=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY", ""),
    )
