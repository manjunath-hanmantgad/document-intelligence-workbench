# Demo Script — Document Intelligence Workbench

**Duration:** 15–20 minutes  
**Audience:** Operations, finance, legal, and platform stakeholders  
**What you need open:** `http://localhost:8005/docs`, `http://localhost:8512`, terminal

## Pre-demo setup (do this 10 minutes before)
- [ ] Run: `make up`
- [ ] Seed data: `make seed`
- [ ] Verify API: `curl http://localhost:8005/health`
- [ ] Open dashboard: `http://localhost:8512`

## The problem you're solving (2 minutes)
> Say: "Manual document extraction is inconsistent and hard to audit. This workbench automates extraction, validates output quality, and routes uncertain records into a controlled human review queue."

## The solution overview (3 minutes)
> Show `docs/architecture.md` and summarize synchronous processing, async queue, validation, and reviewer controls.

## Live demo walkthrough (10 minutes)

### Step 1 — Process a document synchronously
Call `POST /documents/process` with invoice text.

Expected output: extracted fields plus confidence scores and validation results.

### Step 2 — Enqueue async processing
Call `POST /documents/process-async`.

Expected output: job id and queued status.

### Step 3 — Review queue visibility
Open `GET /documents/review-queue` and `GET /documents/review-queue/partitions`.

Expected output: partitioned queue counts by document type.

### Step 4 — Submit human correction
Call `POST /documents/{document_id}/review` with field updates.

Expected output: corrected document payload and updated status.

### Step 5 — Export result
Call `GET /documents/{document_id}/export?export_format=csv`.

Expected output: export artifact path/metadata.

### Step 6 — Show evaluation metrics
Call `POST /evaluation/run` and `GET /metrics/summary`.

Expected output: pass-rate style evaluation summary and operational counters.

## Business value close (2 minutes)
> Say: "Teams get faster processing, reviewer focus on exceptions only, and an audit trail of corrections and quality trends."

## Fallback plan
If API is unstable:
- Walk through `docs/walkthrough.md` and screenshot assets.
- Use `examples/evaluation_set.json` and `evals/golden_dataset.json` as deterministic proof artifacts.

## Common demo gotchas
- API auth mode mismatch (`api_key` vs `oidc`) causing authorization errors.
- Worker not running when showing async queue progression.
- Using dashboard port `8501` instead of Compose port `8512`.
