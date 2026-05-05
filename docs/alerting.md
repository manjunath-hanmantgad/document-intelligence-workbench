# Alerting Baseline

This project exposes operational metrics through `GET /metrics/prometheus` and queue posture through `GET /metrics/queue`.

## Recommended Alerts

1. `HighQueueDepth`
- Trigger when `pending_jobs > 100` for 10 minutes.
- Action: scale worker replicas or investigate upstream ingestion spikes.

2. `QueueFailureRate`
- Trigger when `failed_jobs` increases continuously for 5 minutes.
- Action: inspect worker logs and provider connectivity.

3. `APIErrorRate`
- Trigger when `docint_http_requests_total{status=~"5.."}` exceeds 2% of total requests for 5 minutes.
- Action: check recent deploy, provider outages, and database connectivity.

4. `HighRequestLatency`
- Trigger when `docint_http_request_duration_seconds_max` exceeds 3 seconds for critical endpoints.
- Action: inspect backend saturation and downstream provider latency.

## Alert Routing

- Route P1 (error rate, service unavailable) to on-call pager.
- Route P2 (queue depth, latency degradation) to operations channel.
- Route P3 (single worker failures) to engineering backlog with daily review.
