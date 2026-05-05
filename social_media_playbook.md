# Social Media Playbook for the AI Engineering Portfolio

This playbook helps the user post continuously while building the seven projects. The goal is to create public proof of work, communicate technical depth, and make each project understandable to non-technical stakeholders.

## Posting Principles

- Post progress before the project is perfect.
- Show business value, not only code.
- Use screenshots, short clips, diagrams, and before/after examples.
- Explain what problem the project solves in plain language.
- End posts with a practical lesson or a soft invitation to discuss similar problems.
- Avoid presenting projects as tutorials. Present them as solution demos.

## Weekly Posting Rhythm

For each project, post 5 to 7 times:

1. Problem post: what business pain the project solves.
2. Architecture post: simple diagram and system explanation.
3. Build post: one technical challenge and how it was solved.
4. Demo post: screenshot or short video.
5. Metrics post: latency, cost, accuracy, time saved, or error reduction.
6. Deployment post: local-first now, Azure-ready later.
7. Retrospective post: what a real client would customize.

## Reusable Post Template

```text
I am building [project name] to solve [business problem].

The core workflow:
1. [Step]
2. [Step]
3. [Step]

What makes this useful for businesses:
- [Outcome]
- [Outcome]
- [Outcome]

Current status: [what works now]
Next: [what you are building next]
```

## Project 1: LLM Observatory

Positioning: production monitoring for LLM quality, hallucinations, latency, and cost.

Post ideas:

- "Most teams track app uptime, but not LLM answer quality. That is risky."
- "I built a gateway that logs every LLM call with latency, tokens, cost, and endpoint."
- "LLM observability is not just logs. You need quality scoring and regression detection."
- "Demo: bad prompt in, hallucination alert out."
- "Cost per endpoint is one of the most useful metrics for AI products."
- "Local-first now: FastAPI, DuckDB, Streamlit. Azure-ready later: Container Apps, Key Vault, App Insights."

Suggested assets:

- Dashboard screenshot
- Architecture diagram
- Short alert demo
- Cost breakdown chart

Soft CTA:

```text
If your product uses LLMs in production, this is the type of monitoring layer I would want before scaling usage.
```

## Project 2: Enterprise RAG

Positioning: secure internal document search with citations and access control.

Post ideas:

- "RAG demos are easy. Enterprise RAG is hard because permissions matter."
- "A useful document AI system should say where the answer came from."
- "I am building RBAC-aware retrieval so users only see documents they are allowed to access."
- "Demo: same question, different users, different accessible answers."
- "Evaluation matters: retrieval quality should be measured, not guessed."

Suggested assets:

- Citation-backed answer screenshot
- Permission test screenshot
- Ingestion pipeline diagram
- Retrieval evaluation table

Soft CTA:

```text
This is the pattern I would use for teams that want AI search over internal docs without leaking restricted information.
```

## Project 3: AI Analytics Copilot

Positioning: business users ask questions and get safe SQL, charts, and insights.

Post ideas:

- "Text-to-SQL is useful only if it is safe."
- "I added a validator that blocks destructive SQL before execution."
- "The copilot should not just return SQL. It should return charts and business interpretation."
- "Demo: ask a sales question, get SQL, chart, and insight."
- "A good analytics copilot explains assumptions and limitations."

Suggested assets:

- Streamlit UI screenshot
- Generated chart
- Blocked unsafe query screenshot
- SQL validation flow diagram

Soft CTA:

```text
This is useful for businesses where analysts are overloaded with repeated reporting questions.
```

## Project 4: Multi-Agent BPA

Positioning: automate a concrete business workflow with auditability and human approval.

Post ideas:

- "The best agent demos are not about agents. They are about workflow."
- "I am building an automation that handles lead intake, research, email drafting, CRM update, and approval."
- "Human approval is not a weakness. It is what makes automation usable in real businesses."
- "Demo: one lead enters, researched email draft and CRM update come out."
- "Audit logs make agent workflows easier to trust."

Suggested assets:

- Workflow state diagram
- Lead processing demo
- Approval screen
- Audit log screenshot

Soft CTA:

```text
This is the type of workflow automation that can save hours every week without requiring a full internal engineering team.
```

## Project 5: Document Intelligence Workbench

Positioning: extract structured data from invoices, contracts, forms, and scanned documents.

Post ideas:

- "Document AI is valuable because manual data entry is still everywhere."
- "I am building a workbench that extracts fields, confidence scores, and validation errors."
- "The important feature is not extraction alone. It is human review for low-confidence fields."
- "Demo: upload invoices and contracts, export clean CSV/JSON."
- "Validation rules catch extraction mistakes before they enter business systems."

Suggested assets:

- Upload/review UI screenshot
- Extracted JSON sample
- CSV export screenshot
- Validation error example

Soft CTA:

```text
This maps well to invoice processing, contract review, claims intake, KYC, and back-office automation.
```

## Project 6: Domain-Specific Copilot

Positioning: niche AI assistant grounded in domain documents and workflows.

Post ideas:

- "Generic chatbots are weak technical demos. Domain-specific copilots are more convincing."
- "I am choosing one domain and building around its real vocabulary and workflow."
- "A copilot should cite sources, refuse unsupported answers, and expose uncertainty."
- "Demo: domain question in, cited answer out."
- "The same RAG pattern becomes more valuable when it is adapted to a specific business function."

Suggested assets:

- Domain-specific UI screenshot
- Cited answer
- Refusal example
- Domain workflow diagram

Soft CTA:

```text
The value is not the chatbot. The value is adapting AI to a specific workflow, document set, and risk profile.
```

## Project 7: Fine-Tuning and Evaluation Pipeline

Positioning: dataset preparation, quality checks, before/after evaluation, and optional fine-tuning.

Post ideas:

- "Most fine-tuning projects should start with evaluation, not training."
- "I am building a pipeline that checks dataset quality before any GPU spend."
- "Fine-tuning without a baseline is just guessing."
- "Demo: compare base model vs improved behavior using an evaluation set."
- "A professional fine-tuning workflow includes data checks, versioning, evals, and cost awareness."

Suggested assets:

- Dataset quality report
- Before/after comparison table
- JSONL validation screenshot
- Evaluation score chart

Soft CTA:

```text
This is the process I would use before recommending fine-tuning to a client.
```

## Monthly Content Arc

Month 1:

- Build and post LLM Observatory.
- Start Enterprise RAG.
- Publish one long-form portfolio update.

Month 2:

- Finish Enterprise RAG.
- Build AI Analytics Copilot.
- Post short demos weekly.

Month 3:

- Build Document Intelligence Workbench.
- Polish the strongest three projects.
- Start outreach using the demos.

## Outreach Use

Every project should produce:

- One LinkedIn post announcing the problem.
- One technical post showing architecture.
- One short demo video.
- One GitHub README.
- One concise implementation summary.
- One portfolio page summary.

The user should reuse these assets across LinkedIn, X, GitHub, a personal website, and direct outreach.
