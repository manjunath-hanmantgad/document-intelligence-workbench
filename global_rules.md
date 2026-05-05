# Global Rules for All Projects

These rules apply to every project in this workspace. Use this file before starting implementation work on any project.

Also read `user_project_requirements.md` before starting a project. That file captures user requirements stated during prior builds and should be treated as the standing project brief unless superseded by newer instructions.

Before debugging or continuing implementation, read `issues_tracker.md` and the relevant project-specific issue tracker. These files record bugs already found and fixed so the same issue is not reworked.

## Goal

The portfolio is built as a set of professional, enterprise-oriented AI systems rather than tutorial exercises. Each project must prove that the user can solve a real operational problem, package the solution clearly, and make the business value easy to understand.

## Build Philosophy

Build every project as:

- Local-first: it must run without Azure.
- Production-shaped: the architecture should look like something that can be deployed for a client.
- Cloud-ready: Azure integrations should be represented through clean interfaces, environment variables, and placeholders.
- Demo-first: the first user experience should show the business outcome quickly.
- Client-readable: the README should explain the problem, result, architecture, setup, and demo flow.

Do not block progress because the user does not currently have an Azure account. Implement local mode first, then leave Azure configuration placeholders and clear instructions for later.

## Required Local Mode

Every project should work locally with:

- `.env.example` with placeholder values only.
- Docker Compose where practical.
- Seed/demo data.
- A clear README quick start.
- Screenshots or a short demo GIF in `demo/`.
- Local storage fallback such as DuckDB, SQLite, local files, Qdrant, Redis, or Postgres via Docker.
- OpenAI or provider-agnostic LLM support where cloud-specific Azure OpenAI is not available yet.

## Azure Placeholder Policy

Azure support should be designed now, but real credentials are required only later.

Use placeholders such as:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here

# Azure placeholders, required only for Azure mode or deployment
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=
AZURE_OPENAI_MINI_DEPLOYMENT=
AZURE_OPENAI_EMBED_DEPLOYMENT=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_KEY_VAULT_URL=
APPLICATIONINSIGHTS_CONNECTION_STRING=
```

Code should fail with clear messages when Azure mode is selected but required Azure credentials are missing.

## Required README Sections

Each project README should include:

1. Problem statement
2. Client persona
3. Business value
4. Architecture diagram
5. Local quick start
6. Demo walkthrough
7. Screenshots or GIF
8. Environment variables
9. Azure deployment notes
10. Cost and security notes
11. Professional implementation summary

## Required Demo Assets

Each project should include:

- `demo/README.md` explaining the demo scenario.
- Seed data or sample documents where appropriate.
- At least one screenshot after the UI exists.
- A short demo script the user can follow while recording.

## Engineering Standards

- Keep provider-specific code behind small wrappers.
- Never hardcode secrets.
- Keep local and cloud storage behind interfaces where practical.
- Prefer structured outputs for LLM extraction and evaluation.
- Add validation and error handling around LLM outputs.
- Include basic tests for high-risk logic.
- Track cost, latency, and failures wherever LLM calls are made.

## Professional Standards

Each project should answer these questions clearly:

- What expensive manual work does this reduce?
- What operational risk does this reduce?
- What metric proves the result?
- What would a client need to customize?
- What can be deployed locally now?
- What requires Azure later?

The user should not present projects as experiments. Present them as packaged solution demos that can be adapted for production workflows.

## Recommended Build Order

1. LLM Observatory
2. Enterprise RAG
3. AI Analytics Copilot
4. Multi-Agent BPA
5. Document Intelligence Workbench
6. Domain-Specific Copilot
7. Fine-Tuning and Evaluation Pipeline

The first three projects should be polished before all seven are expanded. Three strong, demo-ready systems are more valuable than seven incomplete repositories.
