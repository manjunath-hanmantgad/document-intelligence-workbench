# The Metrics That Tell You Whether Your Document Pipeline Is Actually Working

*Document Intelligence Workbench — A practitioner's build log | Post 4 of 6*

---

A document processing pipeline that exports records without operational visibility is a pipeline you cannot trust at scale. You need to know: what fraction of documents required human review, what the average extraction confidence is across the current corpus, how the queue is draining, and whether a configuration change improved or degraded extraction quality.

Document Intelligence Workbench exposes these signals at three levels — document-level aggregates, queue state, and a structured evaluation runner — rather than treating observability as an afterthought added after the core pipeline was built.

---

## Three metric layers and what each answers

**Summary metrics (`GET /metrics/summary`)** answer the operational health question: how is the pipeline performing across all processed documents?

- Total processed documents
- Documents requiring human review
- Average extraction confidence across all fields and all documents
- Evaluation pass rate (when evaluation has been run)
- Average field match rate on reference data

The review-required count is the most operationally significant metric here. A stable pipeline with consistent document inputs should produce a stable review queue rate. A spike in review-required documents indicates either a change in document quality — new templates, formatting changes, upstream system changes — or a configuration issue in the extraction profile.

**Queue metrics (`GET /metrics/queue`)** answer the throughput question: what is the current processing state?

- Pending job count
- Processing job count
- Completed job count
- Failed job count
- Dead-letter job count

A growing pending count with a stalled processing count indicates the background worker is not running or has stalled. A growing dead-letter count indicates systematic processing failures that need investigation. These two metrics together give an operator enough signal to distinguish between a backlog (queue is draining slowly but correctly) and a failure (queue is accumulating because the worker is not making progress).

**Prometheus metrics (`GET /metrics/prometheus`)** expose the same operational data in a format compatible with Prometheus scraping and Grafana dashboards. For teams that already have a metrics infrastructure in place, this endpoint makes document processing pipeline health visible alongside other service metrics without additional instrumentation.

![Document Intelligence Workbench review table — flagged records with confidence scores and validation status](workbench-review-table.png)

---

## The evaluation runner and what it measures

The evaluation runner (`POST /evaluation/run`) validates extraction quality against a reference set (`examples/evaluation_set.json`). Each case in the reference set defines an input document and the expected extracted field values. The runner processes each case through the full pipeline and compares extracted values against expected values.

Reported metrics per run:

- **Total cases** — number of evaluation cases executed
- **Passed cases** — cases where all extracted fields matched expected values
- **Pass rate** — passed cases as a fraction of total cases
- **Average field match rate** — average fraction of fields matching expected values across all cases, including partial matches

The pass rate measures end-to-end extraction correctness. The field match rate adds granularity — a case that extracts 7 of 8 fields correctly scores 0.875 on field match rate but 0 on pass rate. Together, they tell you whether failures are systematic (multiple fields wrong across many cases) or marginal (one field off in otherwise correct extractions).

Because the evaluation runner uses the deterministic extraction profile by default, results are fully reproducible. The same reference set produces the same metrics on every run, which makes the evaluation runner a reliable regression baseline before deploying a configuration change.

---

## Confidence scoring as a per-field signal

Confidence scoring assigns a value to each extracted field individually, not to the document as a whole. An invoice where the vendor name is clearly present in the header scores high on `vendor_name` confidence. The same invoice where the tax line is absent or ambiguous scores lower on `tax` confidence — and that field alone can trigger the review-required flag if it falls below `LOW_CONFIDENCE_THRESHOLD`.

This field-level granularity is operationally useful: a reviewer looking at a flagged record can see immediately which field triggered the flag rather than inspecting the entire extracted record. A review queue where every flagged record has a highlighted low-confidence field is faster to triage than one where the reviewer must diagnose the issue from scratch.

![Document Intelligence Workbench export view — clean validated records ready for downstream system delivery](workbench-export.png)

The export endpoint (`GET /documents/{id}/export?export_format=json` or `csv`) is only meaningful when paired with the review workflow. Exporting before review defeats the purpose of confidence scoring. The pipeline enforces this by design — the review status of a record is visible in the export output, making it straightforward to filter for only approved records in any downstream processing step.

---

## What the metrics do not yet cover

**Trend analysis.** The current metrics endpoints return point-in-time state. There is no time-series view showing how review queue rate or average confidence has changed over the past week. Trend data would make it possible to detect gradual quality degradation — an increasing review rate that develops slowly rather than spiking suddenly.

**Extraction error classification.** Failed extractions are counted in the queue metrics but are not classified by failure type — malformed document, missing required field, validation failure, provider error. Classification would make it faster to identify whether failures are document-quality issues or pipeline configuration issues.

**CI integration with threshold gating.** The evaluation runner is callable from CI (`curl -X POST .../evaluation/run` with the admin token). There is no built-in threshold check that fails the CI run if pass rate drops below a configured value. Adding that check is a one-line CI step, not a platform change.

---

## Current limits

- Metrics are point-in-time. Historical trend data requires a time-series store or an external metrics platform.
- The evaluation set is small and calibrated for deterministic local validation. Extending it with real document samples and human-labeled expected values is necessary before using pass rate as a production quality signal.
- Prometheus metrics export provides the data for external dashboards but does not include a pre-built Grafana dashboard configuration.

---

## Next engineering step

Run `POST /evaluation/run` after processing the seeded reference documents. Record the pass rate and average field match rate as a baseline. Then modify one extraction profile parameter — the confidence threshold — and re-run the evaluation. Observe whether the change improves or degrades the metrics, and whether the review queue rate shifts accordingly.

---

## One question for you

Do you track the review-required rate in your document processing pipeline over time? If that rate doubled over a month, how quickly would you detect it — and what would you investigate first?

---

*Next post: Security controls in the workbench — reviewer scope enforcement, audit events, and what needs to be in place before this handles real finance and legal documents.*
