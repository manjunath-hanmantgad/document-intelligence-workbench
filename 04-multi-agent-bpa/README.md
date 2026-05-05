# Multi-Agent Business Process Automation

Workflow automation for lead intake, research, email drafting, CRM update, and human approval.

## Solution Overview

Businesses pay for automation when it removes repeated manual work. This project should focus on one concrete workflow rather than a generic multi-agent demo.

## Local-First Build

Planned local components:

- FastAPI trigger endpoint
- Workflow orchestrator
- Mock CRM
- Research step
- Draft generation step
- Human approval step
- Audit log

## Azure Later

Requires Azure credentials only when deploying cloud mode:

- Azure Service Bus
- Azure Functions or Container Apps
- Entra ID
- Key Vault
- Application Insights

## Demo Goal

Submit one lead and show the automated workflow producing research notes, an email draft, a CRM update, and approval history.
