# Security in a Document Processing Pipeline: Scope Enforcement, Audit Trails, and What Comes Before Production

*Document Intelligence Workbench — A practitioner's build log | Post 5 of 6*

---

A document processing pipeline that handles invoices, contracts, and operational forms occupies a specific security position: it stores sensitive business records, it grants reviewers correction authority over structured data, and it exports validated records to downstream financial and legal systems.

The security model needs to answer three questions: who can access which documents, what actions were taken and by whom, and what controls prevent unauthorized modification before records reach downstream systems. Document Intelligence Workbench addresses each with a distinct mechanism.

---

## Reviewer scope enforcement: document domain access control

The authentication model supports two modes: API key (`AUTH_MODE=api_key`) and OIDC bearer token (`AUTH_MODE=oidc`). In both modes, access is scoped to document domains — not just authenticated versus unauthenticated.

**API key mode.** Each reviewer API key is mapped to one or more document domains at configuration time:

```env
REVIEWER_SCOPE_MAP=finance-key:invoice;legal-key:contract;ops-key:invoice,contract
```

A reviewer authenticated with `finance-key` can access the invoice review queue, process invoice documents, correct invoice fields, and export invoice records. The same key is rejected for contract document endpoints — the scope check happens at the authentication layer before application logic runs.

**OIDC mode.** When `AUTH_MODE=oidc`, bearer token validation checks issuer, audience, expiration, and JWKS signing keys. Role claims from the token are mapped to document domain scopes through `OIDC_ROLE_SCOPE_MAP`. An Entra ID group membership that grants the `invoice-reviewer` role allows access to invoice documents without requiring manual key assignment per user.

The practical implication: a finance reviewer cannot see contract documents. A legal reviewer cannot see invoice details. If a reviewer changes teams, their scope changes at the identity provider or the key configuration — and takes effect on the next request.

---

## The admin boundary: separating reviewer access from management access

Reviewer keys govern document operations: processing, reviewing, correcting, exporting. They do not govern management operations: running evaluation, accessing audit logs at the system level.

The evaluation endpoint (`POST /evaluation/run`) requires `X-Admin-Token` in API key mode, or an admin-scoped OIDC bearer token in OIDC mode. A reviewer key cannot trigger an evaluation run. An admin token cannot substitute for a reviewer key on document correction endpoints. The two credential types have non-overlapping authority.

This separation ensures that a leaked reviewer key does not grant the ability to trigger evaluation runs or access the full audit log — and a leaked admin token does not grant the ability to impersonate a specific reviewer's document access scope.

---

## Audit events: every reviewer action is recorded

Every document operation by a reviewer — processing, correction, export — writes a record to `audit_events`. The audit trail is accessible through `GET /audit/events`.

Each audit event records: the action type, the document ID, the reviewer identity (API key reference or OIDC subject claim), and the timestamp. For reviewer corrections, the audit event captures which fields were changed and what the corrected values were.

This record answers the audit questions that downstream systems will ask: who approved this invoice before it was exported, when was the contract record corrected, which reviewer marked this document as reviewed. Without an audit trail, those questions can only be answered by reviewing application logs — which are not structured for that purpose and may not be retained at the right granularity.

---

## What does not protect itself without operator action

**`ADMIN_TOKEN` must be set.** If `ADMIN_TOKEN` is not configured, the evaluation endpoint and audit log endpoint are unprotected in API key mode. The control is in place. The operator must activate it. Any shared, hosted, or externally accessible deployment must set this value before the service is started.

**`AUTH_ENABLED` must be set to true.** Reviewer API key checks are gated on `AUTH_ENABLED=true`. In the default local development configuration, auth may be disabled for convenience. This must be enabled for any deployment handling real documents.

**Dashboard secret prefill is off by default.** `DASHBOARD_ALLOW_SECRET_PREFILL` is `false` by default. Setting it to `true` in a shared environment would expose credential values in dashboard configuration fields. It should remain `false` in any deployment accessible to more than one person.

These are configuration controls, not missing implementation. The platform ships with the protection mechanisms in place. Operators are responsible for enabling them.

---

## What requires additional implementation for production use

**PII classification and retention policy.** The extracted fields from real invoices and contracts may include vendor names, contract party identities, financial totals, and other sensitive data. Before ingesting real documents, the pipeline should classify content for PII, apply sensitivity labels, and define explicit data retention periods for stored prompts and extracted records.

**Managed secret storage.** In Azure deployment, provider keys, the admin token, and the database URL should be stored in Azure Key Vault and loaded at runtime. Hardcoding or committing these values to environment files in a shared deployment is a credential exposure risk.

**Multi-tenant isolation.** The current implementation is single-organization. A deployment serving multiple business units with strict data separation between them — separate invoice corpora for separate subsidiaries — requires a tenant isolation layer.

**Distributed reviewer session management.** Multi-instance deployments where reviewers connect to different API instances need a shared session or token validation layer. Local in-process auth works correctly for a single-instance deployment.

---

## Current limits

- Scope enforcement is configuration-based. An admin API for managing reviewer keys at runtime without environment changes is a planned extension.
- OIDC end-to-end validation requires a live identity provider. Local and CI testing uses an HS256 shared secret, which is not appropriate for production.
- Audit events record reviewer actions. Background worker actions — automatic processing, retry attempts — are tracked in job records, not in the audit event trail.

---

## Next engineering step

Set `AUTH_ENABLED=true` and `ADMIN_TOKEN` in your local `.env`. Attempt to call `POST /evaluation/run` without the admin token and verify the endpoint returns 401. Then call it with the token, inspect the response, and verify the evaluation run appears in the audit events accessible through `GET /audit/events`.

---

## One question for you

In your document processing system, if a reviewer incorrectly modified an extracted field before export, would you have a record of who made the change, when, and what the original value was? If not, how would a downstream reconciliation error be traced back to its source?

---

*Final post in this series: Deployment readiness — what is operational locally, what the Azure path requires, and an honest accounting of what this system needs before it handles real business documents in production.*
