# Data Model

## Entities

### purchase_requests

| Column | Type | Description |
|--------|------|-------------|
| request_id | TEXT (PK) | Unique request identifier |
| department | TEXT | Department making the request |
| requester | TEXT | Name of the requester |
| vendor | TEXT | Vendor name |
| category | TEXT | Purchase category |
| amount | REAL | Purchase amount in INR |
| justification | TEXT | Business justification |
| urgency | TEXT | low, normal, or high |
| status | TEXT | pending, approved, conditional_approval, or rejected |
| created_at | TIMESTAMP | Auto-generated timestamp |

### approval_decisions

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| request_id | TEXT (FK) | References purchase_requests |
| decision | TEXT | approved, conditional_approval, rejected |
| required_approvers | TEXT | JSON array of approver roles |
| summary | TEXT | Human-readable summary |
| agent_findings | TEXT | JSON object with all agent outputs |
| audit_id | TEXT (UNIQUE) | Audit trail identifier |
| created_at | TIMESTAMP | Auto-generated timestamp |

### audit_logs

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| request_id | TEXT | References purchase_requests |
| action | TEXT | Description of the action |
| agent_name | TEXT | Which agent performed the action |
| details | TEXT | Optional JSON details |
| created_at | TIMESTAMP | Auto-generated timestamp |

### vendors

| Column | Type | Description |
|--------|------|-------------|
| vendor_id | TEXT (PK) | Vendor identifier |
| vendor_name | TEXT | Vendor display name |
| status | TEXT | approved, pending, blacklisted, banned, unknown |
| risk_level | TEXT | low, medium, high |
| categories | TEXT | Comma-separated categories |

### department_budgets

| Column | Type | Description |
|--------|------|-------------|
| department | TEXT (PK) | Department name |
| total_budget | REAL | Annual budget allocation |
| spent_budget | REAL | Year-to-date spending |

### policy_embeddings

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| chunk_id | TEXT (UNIQUE) | Policy chunk identifier |
| content | TEXT | Policy text content |
| source_clause | TEXT | Source clause reference |
| embedding | BLOB | Stored embedding vector (optional) |

## Relationships

- `approval_decisions.request_id` -> `purchase_requests.request_id`
- `audit_logs.request_id` -> `purchase_requests.request_id`
