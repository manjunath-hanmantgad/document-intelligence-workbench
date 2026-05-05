# Security

## Current Implementation

### PII Handling
- Purchase request justifications are passed through PII masking during risk analysis.
- Names, email addresses, and phone numbers are detected and redacted using regex patterns.
- Masked: `[NAME_REDACTED]`, `[EMAIL_REDACTED]`, `[PHONE_REDACTED]`

### Vendor Risk Management
- Vendors are classified as approved, pending, blacklisted, or banned.
- Blacklisted and banned vendors trigger automatic rejection.
- High-risk vendors generate compliance review flags.
- Risk levels (low, medium, high) are tracked and propagated through the approval decision.

### Audit Trail
- Every agent action is logged with timestamp, agent name, and action description.
- Approval decisions include full agent findings as evidence.
- All requests, decisions, and audit logs are persisted in SQLite and queryable via API.

### CORS
- Configurable CORS origins via `CORS_ORIGINS` environment variable.
- Default `*` allows all origins for local development.
- Production deployments should restrict to specific origins.

### Credential Management
- No secrets, tokens, or keys are stored in the codebase.
- All environment variables use `.env.example` with safe placeholder values.
- API keys for external providers are loaded from environment variables.
- Azure credentials are required only when Azure mode is selected.

## Production Considerations

### Authentication and Authorization
- Current implementation is open-access for local development.
- Production deployments should add API key authentication (e.g., `X-API-Key` header).
- Role-based access control can be added for different user roles (requester, approver, admin, auditor).
- Microsoft Entra ID / OIDC integration can be added for enterprise SSO.

### Data Protection
- SQLite is suitable for single-instance local deployments.
- Production deployments should use managed PostgreSQL with encryption at rest.
- PII data in audit logs should be anonymized or stored separately.
- Consider data retention policies for audit logs and request history.

### Compliance
- Approval decisions are evidence-backed with full agent findings.
- All agent actions are traceable through the audit log.
- Policy decisions reference specific policy clauses for verifiability.
- The approval matrix defines clear approval rules by amount and category.
