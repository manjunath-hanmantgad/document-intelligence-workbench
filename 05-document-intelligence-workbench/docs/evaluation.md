# Evaluation

Evaluation uses `examples/evaluation_set.json` and reports:

- total cases
- passed cases
- pass rate
- average field match rate

Run locally:

```bash
curl -X POST http://127.0.0.1:8005/evaluation/run
```

This deterministic evaluation provides a repeatable baseline before adding live provider-backed extraction.
