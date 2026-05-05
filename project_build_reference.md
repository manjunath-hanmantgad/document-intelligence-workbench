# Project Build Reference

Use this document as the working reference before starting any project in this workspace.

## Professional Positioning

These seven projects are designed to demonstrate production-oriented AI engineering capability. The goal is not to show isolated coding ability. The goal is to show that the user can turn a business or operational problem into a running AI system with clear metrics, demos, deployment path, and stakeholder-ready documentation.

The user currently does not have an Azure account. Therefore every project should be implemented local-first and Azure-ready. Azure credentials, deployment, Key Vault, App Insights, Azure OpenAI, Cosmos DB, Azure AI Search, and Container Apps should be documented as production options, not required for local development.

## Shared Implementation Pattern

Every project should follow this pattern:

1. Build a local working version.
2. Add realistic demo data.
3. Add a small UI, API, dashboard, or report that makes value visible.
4. Add `.env.example` with placeholders.
5. Add Docker Compose if the project has services.
6. Add README with architecture, screenshots, and demo instructions.
7. Add Azure integration notes and placeholder config.
8. Add a professional implementation summary.

## Project 1: LLM Observatory

Purpose: monitor production LLM calls for hallucination, latency, cost, endpoint usage, and quality drift.

Local stack:

- FastAPI gateway
- DuckDB metrics store
- Streamlit dashboard
- OpenAI-compatible LLM client
- Slack webhook placeholder

Azure-ready later:

- Azure OpenAI
- Cosmos DB or Azure PostgreSQL
- Azure Container Apps
- Azure Key Vault
- Application Insights

Business value: companies deploying LLMs often have no visibility into quality, hallucination rate, latency, or cost. This project demonstrates operational maturity.

Extra effort required from user:

- Record a demo where a bad response triggers an alert.
- Prepare a dashboard screenshot showing cost, latency, and hallucination rate.
- Write a short case-study style README.

## Project 2: Enterprise RAG

Purpose: secure company knowledge search with citations, ingestion, access control, and retrieval evaluation.

Local stack:

- FastAPI query API
- Qdrant or Chroma
- Local documents
- Postgres or SQLite metadata
- Streamlit or simple web UI

Azure-ready later:

- Azure AI Search
- Azure Blob Storage
- Azure OpenAI embeddings
- Entra ID
- AKS or Container Apps

Business value: this maps directly to common enterprise requirements around internal document search, knowledge base QA, citations, and access control.

Extra effort required from user:

- Create a realistic fake company document set.
- Show citation-backed answers.
- Demonstrate that restricted documents are not returned to unauthorized users.

## Project 3: AI Analytics Copilot

Purpose: allow business users to ask questions over data and receive safe SQL, charts, and explanations.

Local stack:

- SQLite or Postgres
- SQL validator
- LLM SQL generator
- Plotly charts
- Streamlit interface

Azure-ready later:

- Azure PostgreSQL
- Azure Cache for Redis
- Azure OpenAI
- App Insights

Business value: business teams want self-serve analytics without waiting for analysts. This project is easy to demo with operational metrics.

Extra effort required from user:

- Use a realistic business dataset such as sales, subscriptions, inventory, or finance.
- Show blocked unsafe SQL.
- Include charts and plain-English insights.

## Project 4: Multi-Agent BPA

Purpose: automate a cross-system business workflow such as lead intake, research, email drafting, CRM update, and approval.

Local stack:

- LangGraph or lightweight workflow orchestration
- FastAPI trigger endpoint
- Mock CRM
- Email draft generator
- Human approval step

Azure-ready later:

- Azure Service Bus
- Azure Functions or Container Apps
- Entra ID
- Key Vault

Business value: workflow automation is valuable when it removes repetitive staff work and creates measurable time savings.

Extra effort required from user:

- Pick one credible workflow and avoid generic "agent team" demos.
- Show state transitions and audit logs.
- Include before/after time savings.

## Project 5: Document Intelligence Workbench

Purpose: extract structured data from invoices, contracts, forms, statements, and scanned documents.

Local stack:

- FastAPI backend
- Streamlit or React review UI
- Local file storage
- SQLite or DuckDB metadata
- PDF/docx parsing
- OCR placeholder or local OCR option
- LLM structured extraction

Azure-ready later:

- Azure AI Document Intelligence
- Azure Blob Storage
- Azure Cosmos DB or PostgreSQL
- Azure Container Apps
- Key Vault

Business value: document extraction directly replaces manual data entry and is understandable to non-technical stakeholders.

Extra effort required from user:

- Build invoice and contract demo samples.
- Add confidence scores and human review.
- Export clean CSV/JSON.
- Show validation rules such as invoice totals matching tax and subtotal.

## Project 6: Domain-Specific Copilot

Purpose: build a serious niche copilot for legal operations, finance, compliance, healthcare admin, real estate, construction, procurement, or insurance.

Local stack:

- RAG pipeline
- Domain prompt templates
- Citation-backed answers
- Chat UI
- Evaluation questions

Azure-ready later:

- Azure AI Search
- Azure OpenAI
- Entra ID
- Blob Storage
- App Insights

Business value: domain copilots become more credible when they use the organization’s domain language, source material, and workflow.

Extra effort required from user:

- Pick one domain and stay specific.
- Create fake but realistic domain documents.
- Include refusal behavior and citation requirements.
- Write the README for that domain, not for generic AI chat.

## Project 7: Fine-Tuning and Evaluation Pipeline

Purpose: prepare datasets, run quality checks, create fine-tuning-ready files, compare before/after model behavior, and optionally run cloud/GPU training later.

Local stack:

- Dataset preparation scripts
- JSONL validation
- Evaluation harness
- Before/after comparison reports
- Optional LoRA training stub

Azure-ready later:

- Azure ML
- Blob Storage
- Managed online endpoints
- GPU compute

Business value: many organizations ask for fine-tuning before they are ready. This project should demonstrate the professional process: dataset quality, evaluation, and measurable improvement.

Extra effort required from user:

- Show dataset diagnostics.
- Show model behavior comparison.
- Explain when fine-tuning is not the right solution.
- Include cost and data readiness notes.

## Additional User Effort Across All Projects

The user should invest time in:

- Writing professional README files.
- Recording short demos.
- Posting build progress publicly.
- Creating realistic demo data.
- Tracking measurable outcomes.
- Preparing concise implementation summaries.
- Keeping screenshots current.

This effort matters because technical reviewers and business stakeholders usually evaluate clarity, operational relevance, and risk before they evaluate code depth.
