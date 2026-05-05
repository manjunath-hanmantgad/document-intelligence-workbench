# SLO And Runbook

## Service Level Objectives (Initial Targets)

1. API availability: 99.5% monthly for authenticated endpoints.
2. P95 synchronous processing latency (`/documents/process`): under 2.5 seconds.
3. Queue processing freshness: 95% of queued jobs completed within 5 minutes.
4. Queue failure ratio: under 1% failed jobs per rolling 1-hour window.

## Key Signals

- `/health`
- `/metrics/summary`
- `/metrics/queue`
- `/metrics/prometheus`
- Structured JSON logs from API and worker processes

## Incident Triage

1. Confirm incident scope (`api`, `queue`, `provider`, or `database`).
2. Check queue posture:
   - rising `pending_jobs` with flat `completed_jobs` indicates worker starvation.
   - rising `failed_jobs` indicates parsing/provider/data regressions.
3. Check HTTP status distribution for 5xx spikes.
4. Verify provider-specific credentials and endpoint reachability.
5. Roll back recent changes or switch `LLM_PROVIDER=mock` as emergency fallback if provider path is unstable.

## Recovery Playbook

1. Restart worker process if stuck.
2. Scale worker replicas for backlog drain.
3. Requeue failed jobs after root-cause fix (future automation target).
4. Validate with `/metrics/queue` and a controlled canary job.
