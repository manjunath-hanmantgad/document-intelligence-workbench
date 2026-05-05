# Alerting and Incidents

The platform supports configurable alert rules and incident creation.

## Alert Rule Metrics

Supported metrics:

- `hallucination_rate`
- `latency_p95_ms`
- `error_rate`
- `cost_spike`

## Flow

1. Create an alert rule with `POST /api/v1/alert-rules`.
2. Evaluate rules with `POST /api/v1/alert-rules/evaluate`.
3. Or run the worker entrypoint:

```bash
python workers/alert_worker.py
```

4. Incidents are available from `GET /api/v1/incidents`.

## Suppression

Each rule has `suppression_minutes`. If a matching open incident exists inside the suppression window, the alert engine does not create another incident.

## Channels

Current implemented channel type:

- `console`

The schema supports channel configuration for Slack, email, and webhooks in later phases.
