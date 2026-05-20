# What Document Intelligence Workbench Is Ready For and What Production Actually Requires

*Document Intelligence Workbench — A practitioner's build log | Post 6 of 6*

---

This series has built the case for a specific pipeline design: confidence scoring that distinguishes reliable extractions from uncertain ones, validation that catches business rule failures independently of extraction quality, review routing that gates export on human approval for flagged records, and an audit trail that makes every reviewer action traceable.

This final post answers the question a team evaluating this as a foundation would actually ask: what runs today, what the Azure path looks like, and what specific hardening is required before this system handles real finance and legal documents in production.

---

## What is fully operational today

Every capability below runs locally without external provider credentials.

**Document processing pipeline:**
- Synchronous document processing with inline result (`POST /documents/process`)
- Asynchronous queue submission with job tracking (`POST /documents/process-async`)
- Binary file upload for txt, pdf, and docx formats (`POST /documents/upload`)
- Optional OCR path for image formats (png, jpg, tiff) via Tesseract when enabled
- Deterministic invoice extraction: vendor, invoice number, date, subtotal, tax, total, currency
- Deterministic contract extraction: party names, effective date, expiry date, contract value
- Per-field confidence scoring with configurable low-confidence threshold
- Business rule validation: invoice arithmetic consistency, contract date ordering, required field presence
- Review-required flag set when any field falls below confidence threshold or any validation fails

**Review workflow:**
- Role-scoped review queue (`GET /documents/review-queue`)
- Queue partition endpoint for domain-specific reviewer views
- Reviewer field correction and approval (`POST /documents/{id}/review`)
- JSON and CSV export for approved records (`GET /documents/{id}/export`)
- Persistent audit event trail for all reviewer actions (`GET /audit/events`)

**Queue operations:**
- Background worker with configurable poll interval (`scripts/run_queue_worker.py`)
- Exponential backoff retry policy with configurable base, cap, and maximum attempts
- Dead-letter terminal state for exhausted retries — visible in `GET /jobs?status=dead_letter`

**Observability:**
- Document-level summary metrics (`GET /metrics/summary`)
- Queue state metrics (`GET /metrics/queue`)
- Prometheus-compatible metrics export (`GET /metrics/prometheus`)
- Structured JSON request logging with request-ID propagation

**Authentication and security:**
- API key reviewer authentication with document domain scope mapping
- OIDC bearer token authentication with role-to-scope mapping
- Admin token protection for evaluation and privileged operations
- Dual-mode auth configurable through `AUTH_MODE`

**Evaluation and infrastructure:**
- Reference evaluation runner (`POST /evaluation/run`) with pass rate and field match rate
- SQLite and PostgreSQL backend with migration scaffold
- Streamlit review dashboard backed by FastAPI (no direct database access from UI)
- Docker runtime files for containerized validation
- GitHub Actions CI workflow
- Azure-ready environment placeholders for all cloud service integrations

---

## The Azure deployment path

```
Reviewer → Azure Container Apps: API + Dashboard
               ↓
       Background worker replica (Container Apps)
               ↓
       Azure AI Document Intelligence (layout extraction + OCR)
       Azure OpenAI (structured extraction prompts)
       Azure Blob Storage (source document storage)
       Azure PostgreSQL (metadata + audit trail)
               ↓
       Azure Key Vault (secrets)
       Application Insights (logs + metrics)
       Microsoft Entra ID (OIDC reviewer auth)
```

The local-to-Azure switch is environment configuration. `DOCINT_DATABASE_BACKEND=postgres` with `DOCINT_DATABASE_URL` switches storage. `LLM_PROVIDER=azure` activates the Azure OpenAI extraction adapter. `ENABLE_LOCAL_OCR=false` with Azure AI Document Intelligence configured replaces local Tesseract. `AUTH_MODE=oidc` with Entra ID settings activates federated identity. None of these changes require modifying application code.

---

## What production deployment requires beyond the current implementation

**Azure AI Document Intelligence for real document layouts.** The deterministic extraction profile handles known structured formats. Real invoice and contract document diversity — varied templates, scanned originals, handwritten annotations, multi-page layouts — requires layout-aware extraction. Azure AI Document Intelligence is the production path for that capability.

**Staging credential validation for LLM and cloud providers.** The LLM extraction adapters are implemented but have not been validated against live staging credentials. The `scripts/verify_live_integrations.py` script is the intended validation mechanism. It returns `skip` for unconfigured providers and should be run with real credentials before a production deployment.

**Docker runtime validation on a Docker-enabled machine.** Docker files are included. End-to-end container testing has not been confirmed in a Docker-enabled environment and is listed as a remaining public release item.

**PII classification and data retention policy.** Real invoices and contracts contain vendor identities, contract party names, financial figures, and potentially employee information. The ingestion pipeline should classify content for sensitivity, apply labels, and define explicit retention periods for extracted records and stored document text before handling live business documents.

**Event-driven worker for production throughput.** The background worker polls for jobs at a configured interval. An event-driven worker triggered by a queue message (Azure Service Bus, Redis) reduces processing latency and eliminates unnecessary poll cycles in low-volume windows.

**Multi-tenant isolation for multi-business-unit deployments.** The current implementation is single-organization. Serving multiple subsidiaries or business units with strict data separation requires a tenant layer at the data model and API level.

**Admin management API for reviewer key lifecycle.** Reviewer keys and scope assignments are currently managed through environment variables. An admin API that allows creating, rotating, and revoking reviewer keys at runtime — without restarting the service — is the appropriate production model for a multi-reviewer deployment.

---

## An honest assessment

Document Intelligence Workbench delivers the pipeline design that matters for back-office document processing: confidence-gated review routing, validation before export, per-reviewer domain scoping, and a complete audit trail. That design is correct regardless of whether extraction is deterministic, LLM-backed, or OCR-powered. The extraction mechanism plugs in; the pipeline structure does not change.

The gap to production is real and specific. Azure AI Document Intelligence for real document layouts, event-driven workers, PII handling, and multi-tenant isolation are the substantive hardening items. None of them require changing the pipeline design.

For a team building an internal document processing system: adopt the pipeline structure. The confidence-scoring and review-routing design is the part that takes the longest to get right. That work is done.

---

## What I would implement next

The highest-impact single step for a team moving this toward production is validating the Azure AI Document Intelligence adapter against real invoice and contract samples. The deterministic profile works for known structured formats. The moment the document corpus includes real vendor invoices with varied templates, extraction quality will depend on layout-aware parsing — and that gap should be measured before it surfaces in the review queue at scale.

The concrete step: configure `LLM_PROVIDER=azure` with Azure AI Document Intelligence credentials, process 20 real invoice samples, and compare the review-required rate against the deterministic baseline. That comparison tells you exactly how much of the pipeline's value depends on the extraction layer versus the validation and routing design.

---

## One question for you

For the document types your team processes most frequently, do you have a measure of what percentage of extractions require human correction before they can be trusted by a downstream system? If that number is not tracked, it is probably higher than you expect.

---

*This concludes the Document Intelligence Workbench build log series.*

---

## Full series index

1. Why Document Extraction Without Confidence Scoring Creates More Work Than It Saves
2. The Architecture Behind Document Intelligence Workbench: Sync, Async, and Why Both Matter
3. Three Design Decisions That Shaped the Document Intelligence Workbench Pipeline
4. The Metrics That Tell You Whether Your Document Pipeline Is Actually Working
5. Security in a Document Processing Pipeline: Scope Enforcement, Audit Trails, and What Comes Before Production
6. What Document Intelligence Workbench Is Ready For and What Production Actually Requires *(this post)*

*Add Medium post URLs to each title above after publishing.*
