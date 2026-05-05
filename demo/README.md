# Demo Workflow

## Scenario

Finance operations receives a monthly vendor invoice and legal operations receives a procurement services contract. The team needs structured extraction with confidence scoring, deterministic validation, and clean export.

## Steps

1. Start API and dashboard from the README quick start.
2. Run `python demo/seed_data.py` to load reference invoice and contract examples.
3. Open dashboard and inspect review-required indicators.
4. Upload a new invoice file through `/documents/upload` with an intentional total mismatch to trigger validation failure.
5. Apply a manual review correction through the review endpoint.
6. Export the corrected document as JSON and CSV.
7. Run `/evaluation/run` to validate extraction profile accuracy.

## Assets

- Reference text sample: `demo/reference_documents.md`
- Evaluation set: `demo/evaluation_set.json`
- Captured screenshots:
  - `demo/workbench-dashboard.png`
  - `demo/workbench-review-table.png`
  - `demo/workbench-export.png`
