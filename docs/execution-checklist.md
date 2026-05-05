# Production And Public Release Execution Checklist

This checklist defines the implementation plan, ownership, and exit criteria to reach enterprise production readiness and a high-quality public repository release.

## Phase 1: Public Repository Baseline (In Progress)

| Workstream | Owner | Done Criteria | Status |
| --- | --- | --- | --- |
| Governance files | Engineering | `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `CHANGELOG.md` exist at repo root and are internally consistent. | Completed |
| Public artifact guardrails | Engineering | `scripts/prepare_public_release.py` enforces required public files and rejects forbidden artifacts. | Completed |
| CI release gates | Engineering | CI runs tests and public artifact validation on push/PR. | Completed |
| Evidence assets | Product + Engineering | Dashboard screenshots in `examples/` are current and referenced from README and walkthrough docs. | Completed |

## Phase 2: Enterprise Runtime Hardening

| Workstream | Owner | Done Criteria | Status |
| --- | --- | --- | --- |
| AuthN/AuthZ upgrade | Platform Security | Replace static reviewer keys with OIDC/Entra ID auth; enforce RBAC for ops/finance/legal/admin scopes. | In progress |
| Secrets management | Platform Security | Runtime secrets sourced from Key Vault or equivalent; no local-secret dependency in production mode. | Pending |
| Managed persistence | Data Platform | Replace SQLite with managed DB adapter and migration workflow. | In progress |
| Queue + worker | Backend | Document processing supports async queue, retry policy, and dead-letter workflow. | Completed |
| Observability | SRE | Structured logs, request tracing, and operational metrics with dashboard + alerts. | In progress |
| Reliability | SRE + Backend | SLOs defined; failure-mode runbooks for provider outage/degraded mode. | Pending |

## Phase 3: Cloud Production Capability

| Workstream | Owner | Done Criteria | Status |
| --- | --- | --- | --- |
| OpenAI/Azure provider adapters | Backend AI | Feature-complete provider wrappers with clear fallback behavior. | In progress |
| Azure Document Intelligence integration | Backend AI | Layout/OCR extraction path validated with provider abstraction and error handling. | In progress |
| Deployment pipeline | DevOps | Build, deploy, and rollback flow documented for staging/production. | Pending |
| Performance readiness | SRE + Backend | Load and concurrency tests executed with accepted latency/error thresholds. | Pending |

## Phase 4: Public Release Readiness

| Workstream | Owner | Done Criteria | Status |
| --- | --- | --- | --- |
| Documentation review | Engineering | README/docs are complete, consistent, and reflect implemented behavior only. | Pending |
| Security review | Platform Security | Secret scan, dependency review, and release artifact inspection are complete. | Pending |
| Release tag | Engineering | Versioned release tag and release notes published from `CHANGELOG.md`. | Pending |
| Repository publication | Maintainer | Only sanitized standalone project artifact is pushed to public repository. | Pending |

## Immediate Next Sprint (Recommended Order)

1. Implement managed auth and secrets integration for production mode.
2. Validate provider adapters and postgres backend against staging infrastructure.
3. Add alert plumbing and dashboard checks against SLO/runbook definitions.
4. Execute Docker proof capture in a Docker-enabled environment.
