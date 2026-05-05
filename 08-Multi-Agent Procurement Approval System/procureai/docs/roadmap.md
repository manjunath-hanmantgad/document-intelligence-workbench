# Roadmap

## Implemented (v1.0.0)

- Core workflow: purchase request analysis through 5 specialist agents
- Orchestrator Agent controlling the multi-agent workflow
- Policy Agent with keyword-based RAG over procurement policy
- Vendor Agent with lookup and status checking
- Budget Agent with department budget verification
- Risk Agent with duplicate detection, category risk analysis, and PII masking
- Approval Agent with evidence-backed decision generation
- MCP-compatible tool registry with 7 typed tools
- A2A-style agent cards and structured task messages
- SQLite database with audit logging
- Typed Pydantic schemas for all inputs and outputs
- Reference data: policy, vendors, budgets, approval matrix, sample requests
- Comprehensive test suite
- Docker and Docker Compose support
- GitHub Actions CI/CD
- `.env.example` with placeholders
- API, architecture, database, security, deployment, and production-readiness docs

## Short-term (v1.1.0)

- [ ] Embedding-based semantic search for policy RAG
- [ ] API key authentication
- [ ] Prometheus metrics endpoint
- [ ] Request caching for repeated queries

## Medium-term (v1.2.0)

- [ ] PostgreSQL storage backend
- [ ] Role-based access control
- [ ] Streamlit dashboard for human approval review
- [ ] Email notification on approval required

## Long-term (v2.0.0)

- [ ] Azure Container Apps deployment guide with Terraform
- [ ] Application Insights integration
- [ ] Entra ID / OIDC authentication
- [ ] Multi-tenant support
- [ ] Real-time WebSocket status updates
