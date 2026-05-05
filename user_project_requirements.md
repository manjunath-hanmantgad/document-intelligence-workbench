# User Project Requirements

This document captures project-level requirements the user has stated while building the AI engineering portfolio. Use it before starting every new project in this workspace.

## Global Intent

The seven projects are intended to demonstrate professional AI engineering capability through realistic, enterprise-oriented systems. Each project should look like a production-shaped reference implementation that can be pushed to GitHub and reviewed by technical or business stakeholders.

## Public Repository Tone

All public-facing documentation should be professional and enterprise-grade.

Avoid words and framing such as:

- freelance
- Upwork
- proposal
- buyer
- lead generation
- toy project
- tutorial project

Use language such as:

- solution overview
- business use case
- architecture
- operational metrics
- deployment guide
- security considerations
- production readiness
- implementation summary

The README files should read like serious engineering documentation, not personal marketing copy.

## Local-First Requirement

The user currently does not have an Azure account. Every project must run locally first.

Required local behavior:

- Project can be cloned and started with placeholder environment variables.
- No real secrets are committed.
- `.env.example` contains safe placeholder values.
- Local mode should be the default where practical.
- If an API key is required for a real provider, the project should document it clearly.
- Where possible, include a no-key mock/demo mode so reviewers can run the project immediately.

## Azure-Ready Requirement

Azure should be treated as the forward production deployment path, not as a blocker for local development.

Azure credentials should be represented with placeholders such as:

```env
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_EVAL_DEPLOYMENT=
AZURE_KEY_VAULT_URL=
APPLICATIONINSIGHTS_CONNECTION_STRING=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
```

When Azure mode is selected and required variables are missing, code should fail with clear configuration errors.

## Required Documentation Per Project

Each project should include:

- Professional README
- Business use case
- Architecture diagrams
- Local quick start
- API usage or UI walkthrough
- Metrics and evaluation section
- Demo scenario
- Forward deployment guide
- Azure placeholder configuration
- Security notes
- Operational considerations
- Professional implementation summary

## Architecture Diagrams

Each project should include diagrams, preferably Mermaid in Markdown.

Expected diagrams:

- Local architecture
- Future Azure deployment architecture
- Workflow/data flow where relevant

## Metrics and Evaluation

Each project should define meaningful metrics, not only features.

Examples:

- latency
- cost
- token usage
- accuracy
- hallucination rate
- extraction confidence
- retrieval quality
- SQL safety violations
- workflow completion time
- failed job count

Metrics should be visible in the UI, dashboard, report, logs, or README.

## Demo Readiness

Each project should include a realistic demo scenario.

Expected assets:

- seed data or sample documents
- demo script or `demo/README.md`
- screenshots or GIFs when UI exists
- local commands to reproduce demo state

The first experience should show a meaningful business outcome quickly.

## Implementation Quality

Projects should be production-shaped even when running locally.

Expected practices:

- keep provider-specific code behind wrappers
- avoid hardcoded secrets
- validate LLM outputs
- handle missing credentials cleanly
- use structured outputs where possible
- add tests for core logic
- include Docker files where practical
- keep local and future cloud paths clearly separated

## Project 1 Specific Requirements Captured

For LLM Observatory, the user explicitly wanted:

- architecture diagrams
- forward deployment guide
- business use case
- metrics evaluation
- placeholders for API keys
- production-style source control hygiene
- public GitHub-safe documentation
- any user should be able to clone the repo and configure their own variables

Use this same standard for the next projects unless the user changes direction.

## Issue Tracking Requirement

While building projects, maintain a bug and issue tracker so previously solved problems are not rediscovered or reworked.

Required behavior:

- Read `issues_tracker.md` before debugging or continuing implementation.
- Read the current project's issue tracker if it exists.
- Record bugs with symptom, root cause, fix, and verification.
- Promote reusable environment or workflow lessons to the global tracker.

## Customer Demo Readiness Requirement

For a project to be shown as a customer-style demo, backend functionality alone is not enough.

Minimum demo-ready requirements:

- enterprise dashboard shell with clear navigation
- login/register or guided local onboarding
- project selector and endpoint selector where relevant
- API key management or at least API key creation flow
- request/trace logs with filters, search, and pagination
- evaluation quality view with scores and reasoning
- alert rules and incidents surface
- demo data that shows meaningful operational outcomes
- Docker Compose path when Docker is available
- documentation that explains the demo workflow

When upgrading a project, build in phases:

1. backend/database/auth
2. ingestion/evals/alerts
3. dashboard/customer demo UX
4. docs/deployment hardening

Before writing code, evaluate the prompt and existing codebase, then implement only the parts that are missing for the current phase.
