# Security Considerations

- `.env.example` contains placeholders only.
- Local runtime stores metadata in SQLite under `storage/`.
- Secrets must be injected at runtime through environment variables.
- Reviewer operations are protected by `AUTH_MODE=api_key` (`X-API-Key`) or `AUTH_MODE=oidc` (`Authorization: Bearer`).
- `REVIEWER_ROLE_MAP` assigns reviewer keys to `ops`, `finance`, `legal`, or `admin` roles.
- `REVIEWER_SCOPE_MAP` limits each reviewer key to allowed document domains.
- `OIDC_ROLE_SCOPE_MAP` enforces document-domain scopes based on token roles.
- Evaluation execution is protected with `X-Admin-Token` in API-key mode or admin-scoped OIDC bearer token in OIDC mode.
- Reviewer actions (process, review, export) are persisted in `audit_events`.
- Dashboard secret fields are not prefilled by default; enable only with `DASHBOARD_ALLOW_SECRET_PREFILL=true` in controlled local environments.
- Azure mode must enforce managed secret storage via Key Vault.
- PII controls and retention policy should be defined before production workloads.
