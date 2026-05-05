# API Reference

## Purchase Request Endpoints

### POST /purchase-requests/analyze

Submit a purchase request for multi-agent analysis.

**Request body:**

```json
{
  "request_id": "REQ-1001",
  "department": "IT",
  "requester": "Amit Sharma",
  "vendor": "Adobe",
  "category": "software_subscription",
  "amount": 85000,
  "justification": "Need Adobe Creative Cloud licenses for design team",
  "urgency": "normal"
}
```

**Response:**

```json
{
  "request_id": "REQ-1001",
  "decision": "conditional_approval",
  "required_approvers": ["department_manager", "security_team"],
  "agent_findings": {
    "policy": { "policy_status": "requires_manager_approval", "source_clause": "PROC-APPROVAL_THRESHOLDS" },
    "vendor": { "vendor_status": "approved", "risk_level": "low" },
    "budget": { "budget_status": "available", "remaining_budget_after_purchase": 95000 },
    "risk": { "risk_level": "medium", "flags": ["software_subscription_requires_security_review"] }
  },
  "summary": "Security review is required. Department manager approval is required. The purchase can proceed after required approvals.",
  "audit_id": "AUD-ABCDEF"
}
```

### GET /purchase-requests/{request_id}

Get full request status including decision and audit logs.

### GET /audit/{request_id}

Get audit trail for a specific request.

## A2A Endpoints

### GET /agents

List available agents.

### GET /agents/{agent_name}/card

Get agent card with capabilities and schema information.

### POST /agents/{agent_name}/tasks

Send a structured task message to an agent.

**Request body:**

```json
{
  "task_id": "task-001",
  "from_agent": "orchestrator",
  "to_agent": "policy",
  "task_type": "policy_validation",
  "payload": {
    "request_id": "REQ-1001",
    "department": "IT",
    "vendor": "Adobe",
    "category": "software_subscription",
    "amount": 85000,
    "justification": "Software licenses",
    "requester": "Amit Sharma",
    "urgency": "normal"
  }
}
```

## MCP Endpoints

### GET /mcp/tools

List all MCP-compatible tools with input schemas.

### POST /mcp/tools/{tool_name}

Execute an MCP tool.

**Example: search_policy_docs**

```json
{
  "query": "approval thresholds",
  "top_k": 3
}
```

### GET /mcp/resources

List available MCP resources.

### GET /mcp/prompts

List available MCP prompt templates.

### GET /mcp/prompts/{prompt_name}

Get prompt template details including template text.
