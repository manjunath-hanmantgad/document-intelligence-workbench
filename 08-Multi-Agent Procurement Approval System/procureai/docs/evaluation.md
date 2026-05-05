# Metrics and Evaluation

## Workflow Metrics

ProcureAI tracks operational metrics across the full approval workflow. These metrics are observable through the audit log API and dashboard.

| Metric | Description | Where Visible |
|--------|-------------|---------------|
| Workflow completion time | Time from request submission to final decision | Audit log timestamps |
| Decision distribution | Approved / conditional / rejected breakdown | `/purchase-requests/{id}` |
| Policy compliance rate | Percentage of requests that pass all policy checks without additional approvers | Audit log `policy_agent` entries |
| Vendor approval rate | Percentage of requests where vendor is approved vs. pending/blacklisted | Vendor agent findings |
| Budget utilization rate | Remaining budget per department after approvals | Budget agent findings |
| Risk flag frequency | How often each risk category is triggered | Risk agent findings |
| Duplicate detection rate | Requests flagged as duplicates within 30 days | Risk agent duplicate check |
| Audit log completeness | Number of audit entries per request (expected: ~10 per workflow) | `/audit/{request_id}` |

## Agent-Level Metrics

### Policy Agent

- `policy_status` distribution: `compliant` / `requires_manager_approval`
- `confidence` score per decision (0.92–0.98 range in current implementation)
- `source_clause` coverage: which policy clauses are most frequently cited

### Vendor Agent

- `vendor_status` distribution: `approved` / `pending` / `blacklisted` / `unknown`
- `risk_level` distribution: `low` / `medium` / `high`

### Budget Agent

- `budget_status` distribution: `available` / `insufficient` / `unknown`
- Average `remaining_budget_after_purchase` per department

### Risk Agent

- `risk_level` distribution per category
- Most frequent `flags` triggered (e.g., `software_subscription_requires_security_review`)
- Duplicate detection true positive rate (requires historical data)

### Approval Agent

- `decision` distribution: `approved` / `conditional_approval` / `rejected`
- Average number of required approvers per decision
- Evidence count per approval packet

## Evaluation Approach

### Correctness Validation

Run the full test suite to verify agent decision logic:

```bash
python -m pytest tests/ -v
```

All 30 tests cover:
- Policy threshold logic at 25k, 100k, 500k INR
- Category-based approver routing
- Vendor status handling including blacklisted and unknown vendors
- Budget availability and overflow detection
- Duplicate detection within 30-day window
- MCP tool contract conformance
- A2A task message and response contracts

### Live Workflow Validation

```bash
# Start the server
uvicorn app.main:app --port 8004

# Run integration verification
python scripts/verify_live_integrations.py
```

Expected output: 14 checks, all `[PASS]`.

### Policy Coverage Validation

After ingestion, verify the policy RAG index covers expected clauses:

```bash
curl http://127.0.0.1:8004/mcp/tools/validate_policy_compliance \
  -H "Content-Type: application/json" \
  -d '{"request": {"department":"IT","vendor":"Adobe","amount":85000,"category":"software_subscription"}}'
```

Expected: `requires_manager_approval` with `source_clause` populated.

## Metrics Roadmap

For production deployment, these additional metrics are recommended:

- **Latency P50/P95**: End-to-end request analysis latency
- **LLM token usage**: Per-request token counts when using OpenAI/Azure OpenAI
- **LLM cost**: Estimated cost per workflow run
- **RAG retrieval quality**: Chunk relevance scores (requires embedding-based retrieval)
- **Audit log query latency**: Time to retrieve full audit trail per request
- **SLA compliance**: Percentage of requests completed within defined SLA windows

These metrics can be instrumented using Prometheus (`/metrics` endpoint) or Azure Application Insights once the production configuration is active.
