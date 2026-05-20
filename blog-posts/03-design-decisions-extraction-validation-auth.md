# Three Design Decisions That Shaped the Document Intelligence Workbench Pipeline

*Document Intelligence Workbench — A practitioner's build log | Post 3 of 6*

---

Building a document processing pipeline involves a sequence of decisions that look minor in isolation but compound into the overall reliability and operational character of the system. This post documents three of those decisions in Document Intelligence Workbench: the sequencing of extraction and validation, the choice to start with deterministic extraction rather than LLM-first, and the design of reviewer scope mapping as an auth model concern rather than an application concern.

Each decision had a constraint that drove it and a cost that was accepted.

---

## Decision 1: Validation as a separate pipeline stage — not a post-processing check

The pipeline stages are ordered deliberately:

```
Extract → Score confidence → Validate business rules → Set review-required flag → Store
```

Validation does not happen inside extraction. It happens after extraction has completed, in a dedicated stage that applies business rules to the extracted field set as a whole.

**The constraint:** A field can be extracted correctly and still produce an invalid record. An invoice where the subtotal, tax, and total fields are each extracted with high confidence — correct values, unambiguous text — can still fail arithmetic validation if the stated total does not equal subtotal plus tax. The extraction is not wrong. The document itself may contain an error, or the extraction may have missed a discount line. Either way, the record should not be exported until a reviewer has verified it.

Embedding validation inside the extraction step would conflate two distinct failure types: extraction failure (the field value is wrong) and business rule failure (the field value is correct but the record is internally inconsistent). Separating them makes the review queue signal more precise — a reviewer looking at a validation-failed record knows the issue is not a bad extraction but a business rule violation that requires judgment.

**The accepted cost:** Two pipeline stages instead of one means two places where failures can occur and two types of failure to communicate clearly in the review queue. The review-required flag captures both cases. The validation status field distinguishes them. A reviewer can see whether a record was flagged for confidence or for validation — or both — without inspecting the raw field values.

---

## Decision 2: Deterministic extraction before LLM providers — sequencing, not a preference

The default extraction mode is deterministic: structured field parsing from known document patterns, without an LLM API call. OpenAI and Azure OpenAI extraction adapters are available through `LLM_PROVIDER=openai` or `LLM_PROVIDER=azure` — but they are not the default.

**The constraint:** The evaluation set requires repeatable, deterministic outputs. If extraction results vary run to run — because a generative model produces slightly different structured outputs from the same input, because API responses differ across versions, because rate limits affect timing — the evaluation runner cannot function as a regression test. A pass rate of 0.94 one day and 0.89 the next is not useful as a validation baseline.

Deterministic extraction makes the evaluation set a reliable regression test. The same document, run through the same pipeline, produces the same extracted fields and the same confidence scores every time. This is not a limitation of the current implementation — it is a deliberate property that makes local validation credible without provider credentials.

The LLM adapter path exists for production deployments where document variation, layout complexity, or handwritten content exceeds what structured parsing can handle reliably. The `LLM_PROVIDER` environment variable switches between modes without code changes. Deterministic mode remains the default, and the evaluation set is calibrated for it.

**The accepted cost:** Deterministic extraction handles known document structures. Documents that deviate significantly from the expected format — unusual invoice layouts, non-standard contract structures, scanned forms with OCR artifacts — will produce lower confidence scores and higher review queue rates. That is the correct behavior: flag what the system is not confident about rather than guess.

---

## Decision 3: Reviewer scope mapping in the auth model — not application logic

The system supports multiple reviewers with different access scopes. A finance reviewer should see invoice documents. A legal reviewer should see contract documents. A reviewer with both roles should see both. The configuration is explicit:

```env
REVIEWER_SCOPE_MAP=reviewer-finance:invoice;reviewer-legal:contract;reviewer-ops:invoice,contract
```

Each API key is bound to a document domain at configuration time. A finance reviewer key cannot retrieve contract documents from the review queue or export contract records — the scope check happens at the authentication layer, not inside the application logic.

**The constraint:** If domain scoping is enforced inside application logic rather than in the auth model, there are multiple places in the codebase where scope checks need to be added as the API surface grows — the review queue endpoint, the export endpoint, the individual document endpoint, any future batch endpoint. Each new endpoint is a potential gap.

Enforcing scope in the auth model means a single validation point at request time. A request with a finance reviewer key is rejected for contract domain endpoints at the auth layer, before any application logic runs. New endpoints inherit the enforcement automatically.

The same pattern applies to OIDC mode: `OIDC_ROLE_SCOPE_MAP` maps token role claims to document domain scopes, so Entra ID group membership determines what document types a reviewer can access.

**The accepted cost:** Scope configuration is external — in environment variables — rather than managed through an admin API. Adding a new reviewer or changing a scope requires an environment variable change and a service restart. An admin-managed reviewer registry is a natural evolution for a production multi-team deployment, but adds implementation complexity that was not needed for the initial validation scope.

---

## One decision I deliberately deferred

The review queue is currently flat: all flagged records appear in a single queue, filtered by the reviewer's document domain scope. There is no priority ordering within the queue — a high-value invoice with a large total does not surface before a low-value one.

Priority ordering requires a priority field at extraction time and a sorting mechanism in the queue retrieval endpoint. That is achievable, but it requires a definition of "priority" that depends on the specific business context — invoice value, contract expiry proximity, document age — which varies by deployment. Implementing priority without that context would produce a mechanism that operators immediately reconfigure. The flat queue is the correct default until a specific deployment's priority rules are known.

---

## Current limits

- Reviewer scope mapping is environment-variable based. An admin API for managing reviewer keys and scopes at runtime is a planned extension.
- LLM extraction adapters require staging credentials for end-to-end validation. The deterministic mode covers the local and CI validation scope.
- OIDC mode requires a live identity provider for end-to-end token validation. Local testing uses a shared HS256 secret for CI coverage only.
- Document type coverage is limited to invoices and contracts. Additional extraction profile definitions are required for other document types.

---

## Next engineering step

Configure two reviewer keys with different `REVIEWER_SCOPE_MAP` assignments — one for `invoice`, one for `contract` — then process one of each document type and verify that each reviewer key can only access its scoped document type through `GET /documents/review-queue`.

---

## One question for you

In your document processing system, is reviewer access to document types enforced at the auth layer or inside application logic? If application logic, how many endpoints would need to be updated if a reviewer's scope changed?

---

*Next post: The metrics and evaluation that tell you whether the pipeline is operating correctly — confidence distributions, review queue rates, and what the field match rate actually measures.*
