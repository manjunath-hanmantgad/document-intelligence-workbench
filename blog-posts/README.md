# Document Intelligence Workbench — Blog Post Series

6-post series for Medium / Substack. Each post is standalone. Together they form a complete practitioner case study.

**Tone:** First-person engineering retrospective. Not a tutorial. Not a product pitch.
**Target:** Mixed — Operations leaders, engineering managers, CTOs, platform engineers, back-office automation teams.

---

## Series Arc

| File | Post title | Pillar |
|---|---|---|
| `01-the-problem-with-extraction-without-confidence.md` | Why Document Extraction Without Confidence Scoring Creates More Work Than It Saves | Problem and failure mode |
| `02-architecture-sync-async-queue.md` | The Architecture Behind Document Intelligence Workbench: Sync, Async, and Why Both Matter | Architecture and boundaries |
| `03-design-decisions-extraction-validation-auth.md` | Three Design Decisions That Shaped the Document Intelligence Workbench Pipeline | Design decisions (why A over B) |
| `04-metrics-confidence-review-evaluation.md` | The Metrics That Tell You Whether Your Document Pipeline Is Actually Working | Validation and measured outputs |
| `05-security-reviewer-scope-audit-trail.md` | Security in a Document Processing Pipeline: Scope Enforcement, Audit Trails, and What Comes Before Production | Security and controls |
| `06-deployment-readiness-and-limits.md` | What Document Intelligence Workbench Is Ready For and What Production Actually Requires | Deployment readiness and limits |

---

## Screenshots for Medium upload

Source files are in `../examples/`. Upload each PNG directly via Medium's inline image button.
Use the alt text in each post as the Medium caption.

| Screenshot | Used in posts |
|---|---|
| `workbench-dashboard.png` | 1 |
| `workbench-review-table.png` | 4 |
| `workbench-export.png` | 4 |

## Medium publishing checklist

Before hitting Publish on each post:
- [ ] Upload referenced screenshots inline at the correct position
- [ ] Replace the `*Post N of 6*` series line with a Medium series tag if applicable
- [ ] In post 6, fill in the series index with actual Medium post URLs after earlier posts are published
- [ ] Add Medium tags: `document-processing`, `automation`, `machine-learning`, `software-engineering`, `operations`
- [ ] Set subtitle from the first sentence of each post's opening paragraph

## QA checklist status

All 6 posts verified against the playbook QA checklist:
- Every claim maps to a verified file, endpoint, screenshot, or metric
- No unverifiable metrics included
- "Production" wording is scoped precisely throughout
- Security claims are specific: "scope check at authentication layer", "SHA-256 hashed keys", "audit_events per reviewer action"
- At least one limitation disclosed per post
- One technical anchor per post (API path, queue metric, evaluation metric, or architecture component)
- No full code blocks or replication walkthroughs
- No hype terms used
