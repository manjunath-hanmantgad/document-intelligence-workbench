# AI Freelance Portfolio — Step-by-Step Build Guide

> **How to use this document:**
> Each project is self-contained. Pick one, follow the steps top to bottom.
> Every step ends with a "verify" check so you know you're on track before moving forward.

---

## GLOBAL SETUP (Do this once before starting any project)

### Step 1 — Install core tools

```bash
# Python (3.11 recommended)
python --version   # should show 3.11.x

# Package manager
pip install uv     # faster than pip, use this for all projects

# Docker
docker --version   # should show 24.x or above
docker compose version

# Git
git --version
```

### Step 2 — Create accounts (free tiers are fine to start)

| Service | Purpose | URL |
|---------|---------|-----|
| OpenAI | LLM API | platform.openai.com |
| Anthropic | Claude API (alternative) | console.anthropic.com |
| Weights & Biases | Experiment tracking | wandb.ai |
| RunPod or Lambda Labs | GPU for fine-tuning | runpod.io |
| Railway or Render | Cloud deployment | railway.app |
| GitHub | Code hosting + portfolio | github.com |

### Step 3 — Set up a shared `.env` template

Create a file `~/ai-portfolio/.env.example`:

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
WANDB_API_KEY=
HUGGINGFACE_TOKEN=
```

Copy this to each project folder and fill in values.

---

---

# PROJECT 1: LLM Evaluation & Monitoring Framework

**What you're building:** A system that watches your LLM in production, measures response quality, catches hallucinations, and alerts you when things go wrong.

**Estimated build time:** 5–7 days
**Folder name:** `llm-observatory`

---

## Phase 1: Project Setup (Day 1 — 1 hour)

### Step 1 — Create the project

```bash
mkdir llm-observatory && cd llm-observatory
git init
uv venv .venv && source .venv/bin/activate
```

### Step 2 — Create folder structure

```bash
mkdir -p gateway eval_engine storage dashboard alerts tests demo
touch README.md docker-compose.yml .env .env.example
```

### Step 3 — Install dependencies

```bash
uv pip install fastapi uvicorn openai anthropic ragas \
               duckdb pandas plotly streamlit \
               slack-sdk python-dotenv pytest httpx
```

Create `requirements.txt`:
```bash
uv pip freeze > requirements.txt
```

**Verify:** `python -c "import fastapi, duckdb, ragas; print('OK')"` — should print OK.

---

## Phase 2: LLM Gateway — Logging Layer (Day 1 — 3 hours)

**Goal:** Every LLM call in your system passes through this gateway. It logs the request, response, latency, and token count automatically.

### Step 4 — Create the gateway

Create `gateway/gateway.py`:

```python
import time
import uuid
from fastapi import FastAPI, Request
from openai import OpenAI
import duckdb
from datetime import datetime

app = FastAPI()
client = OpenAI()

# Connect to DuckDB
con = duckdb.connect("storage/metrics.db")

# Create logs table on startup
con.execute("""
    CREATE TABLE IF NOT EXISTS llm_logs (
        id VARCHAR,
        timestamp TIMESTAMP,
        prompt TEXT,
        response TEXT,
        model VARCHAR,
        latency_ms FLOAT,
        prompt_tokens INT,
        completion_tokens INT,
        total_cost_usd FLOAT,
        endpoint VARCHAR
    )
""")

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    # GPT-4o pricing (update as needed)
    rates = {
        "gpt-4o": {"input": 0.000005, "output": 0.000015},
        "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
    }
    rate = rates.get(model, {"input": 0.000005, "output": 0.000015})
    return (prompt_tokens * rate["input"]) + (completion_tokens * rate["output"])

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    model = body.get("model", "gpt-4o-mini")
    messages = body.get("messages", [])
    endpoint = body.get("endpoint", "default")  # which feature triggered this call

    start = time.time()
    response = client.chat.completions.create(model=model, messages=messages)
    latency = (time.time() - start) * 1000

    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    # Log to DuckDB
    con.execute("""
        INSERT INTO llm_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        str(uuid.uuid4()),
        datetime.now(),
        str(messages),
        response.choices[0].message.content,
        model,
        latency,
        prompt_tokens,
        completion_tokens,
        cost,
        endpoint
    ])

    return {
        "response": response.choices[0].message.content,
        "latency_ms": round(latency, 2),
        "cost_usd": round(cost, 6)
    }
```

### Step 5 — Run the gateway and test it

```bash
uvicorn gateway.gateway:app --reload --port 8001
```

In another terminal:
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is 2+2?"}], "endpoint": "test"}'
```

**Verify:** You should get a JSON response with `response`, `latency_ms`, and `cost_usd`.

---

## Phase 3: Evaluation Engine (Day 2 — 4 hours)

**Goal:** Automatically score every response for quality, groundedness, and hallucination.

### Step 6 — Create the eval engine

Create `eval_engine/evaluator.py`:

```python
from openai import OpenAI
import duckdb

client = OpenAI()
con = duckdb.connect("storage/metrics.db")

# Create eval results table
con.execute("""
    CREATE TABLE IF NOT EXISTS eval_results (
        log_id VARCHAR,
        timestamp TIMESTAMP,
        faithfulness_score FLOAT,
        relevancy_score FLOAT,
        hallucination_flag BOOLEAN,
        judge_reasoning TEXT
    )
""")

JUDGE_PROMPT = """
You are an expert AI evaluator. Score the following LLM response.

Question: {question}
Response: {response}

Rate on a scale of 0.0 to 1.0:
1. Faithfulness: Is the response factually accurate and not hallucinated?
2. Relevancy: Does the response actually answer the question?

Also set hallucination_flag to true if you detect any made-up facts.

Respond ONLY in this JSON format:
{{
  "faithfulness": 0.0-1.0,
  "relevancy": 0.0-1.0,
  "hallucination_flag": true/false,
  "reasoning": "brief explanation"
}}
"""

def evaluate_response(log_id: str, question: str, response: str):
    prompt = JUDGE_PROMPT.format(question=question, response=response)

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    import json
    from datetime import datetime
    scores = json.loads(result.choices[0].message.content)

    con.execute("""
        INSERT INTO eval_results VALUES (?, ?, ?, ?, ?, ?)
    """, [
        log_id,
        datetime.now(),
        scores["faithfulness"],
        scores["relevancy"],
        scores["hallucination_flag"],
        scores["reasoning"]
    ])

    return scores
```

### Step 7 — Create a batch eval runner

Create `eval_engine/run_evals.py`:

```python
import duckdb
from evaluator import evaluate_response
import json

con = duckdb.connect("storage/metrics.db")

# Get recent logs that haven't been evaluated yet
logs = con.execute("""
    SELECT l.id, l.prompt, l.response
    FROM llm_logs l
    LEFT JOIN eval_results e ON l.id = e.log_id
    WHERE e.log_id IS NULL
    LIMIT 20
""").fetchall()

for log_id, prompt_str, response in logs:
    # Extract the actual user question from the logged messages string
    # (simplification — in production, store structured)
    question = prompt_str[:200]
    result = evaluate_response(log_id, question, response)
    print(f"Evaluated {log_id}: faithfulness={result['faithfulness']}, hallucination={result['hallucination_flag']}")

print("Batch eval complete.")
```

**Verify:** Run `python eval_engine/run_evals.py` — should print eval scores for each logged call.

---

## Phase 4: Dashboard (Day 3 — 3 hours)

### Step 8 — Create the Streamlit dashboard

Create `dashboard/app.py`:

```python
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

con = duckdb.connect("storage/metrics.db", read_only=True)

st.set_page_config(page_title="LLM Observatory", layout="wide")
st.title("LLM Observatory — Production Monitoring")

# --- Metrics Row ---
col1, col2, col3, col4 = st.columns(4)

total_calls = con.execute("SELECT COUNT(*) FROM llm_logs").fetchone()[0]
total_cost = con.execute("SELECT ROUND(SUM(total_cost_usd), 4) FROM llm_logs").fetchone()[0]
avg_latency = con.execute("SELECT ROUND(AVG(latency_ms), 1) FROM llm_logs").fetchone()[0]
hallucination_rate = con.execute("""
    SELECT ROUND(100.0 * SUM(CASE WHEN hallucination_flag THEN 1 ELSE 0 END) / COUNT(*), 1)
    FROM eval_results
""").fetchone()[0]

col1.metric("Total Calls", total_calls)
col2.metric("Total Cost", f"${total_cost}")
col3.metric("Avg Latency", f"{avg_latency}ms")
col4.metric("Hallucination Rate", f"{hallucination_rate}%")

# --- Latency Over Time ---
st.subheader("Latency Over Time")
latency_df = con.execute("""
    SELECT DATE_TRUNC('hour', timestamp) as hour, AVG(latency_ms) as avg_latency
    FROM llm_logs GROUP BY 1 ORDER BY 1
""").df()
st.plotly_chart(px.line(latency_df, x="hour", y="avg_latency", title="Avg Latency (ms)"))

# --- Hallucination Trend ---
st.subheader("Hallucination Rate Trend")
hall_df = con.execute("""
    SELECT DATE_TRUNC('hour', timestamp) as hour,
           ROUND(100.0 * SUM(CASE WHEN hallucination_flag THEN 1 ELSE 0 END) / COUNT(*), 1) as rate
    FROM eval_results GROUP BY 1 ORDER BY 1
""").df()
st.plotly_chart(px.line(hall_df, x="hour", y="rate", title="Hallucination Rate (%)"))

# --- Cost by Endpoint ---
st.subheader("Cost by Endpoint")
cost_df = con.execute("""
    SELECT endpoint, ROUND(SUM(total_cost_usd), 4) as total_cost
    FROM llm_logs GROUP BY endpoint ORDER BY total_cost DESC
""").df()
st.plotly_chart(px.bar(cost_df, x="endpoint", y="total_cost", title="Cost by Endpoint ($)"))

# --- Recent Logs Table ---
st.subheader("Recent Logs")
logs_df = con.execute("""
    SELECT l.timestamp, l.model, l.endpoint, l.latency_ms,
           l.total_cost_usd, e.faithfulness_score, e.hallucination_flag
    FROM llm_logs l
    LEFT JOIN eval_results e ON l.id = e.log_id
    ORDER BY l.timestamp DESC LIMIT 20
""").df()
st.dataframe(logs_df)
```

### Step 9 — Run the dashboard

```bash
streamlit run dashboard/app.py
```

**Verify:** Open `http://localhost:8501` in your browser. You should see all 4 metric cards and charts.

---

## Phase 5: Slack Alerts (Day 3 — 1 hour)

### Step 10 — Add alert logic

Create `alerts/slack_alert.py`:

```python
import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_alert(message: str, severity: str = "warning"):
    emoji = {"warning": ":warning:", "critical": ":red_circle:", "info": ":information_source:"}
    payload = {"text": f"{emoji.get(severity, '')} *LLM Observatory Alert*\n{message}"}
    requests.post(SLACK_WEBHOOK_URL, json=payload)

def check_and_alert():
    import duckdb
    con = duckdb.connect("storage/metrics.db", read_only=True)

    # Alert if hallucination rate > 20% in last hour
    rate = con.execute("""
        SELECT ROUND(100.0 * SUM(CASE WHEN hallucination_flag THEN 1 ELSE 0 END) / COUNT(*), 1)
        FROM eval_results
        WHERE timestamp > NOW() - INTERVAL 1 HOUR
    """).fetchone()[0]

    if rate and rate > 20:
        send_alert(f"Hallucination rate is {rate}% in the last hour — above 20% threshold.", "critical")

    # Alert if avg latency > 5000ms
    latency = con.execute("""
        SELECT AVG(latency_ms) FROM llm_logs
        WHERE timestamp > NOW() - INTERVAL 1 HOUR
    """).fetchone()[0]

    if latency and latency > 5000:
        send_alert(f"Avg latency is {round(latency)}ms — above 5000ms threshold.", "warning")

if __name__ == "__main__":
    check_and_alert()
```

---

## Phase 6: Docker + README (Day 3 — 1 hour)

### Step 11 — Create docker-compose.yml

```yaml
version: "3.9"
services:
  gateway:
    build: .
    command: uvicorn gateway.gateway:app --host 0.0.0.0 --port 8001
    ports:
      - "8001:8001"
    env_file: .env
    volumes:
      - ./storage:/app/storage

  dashboard:
    build: .
    command: streamlit run dashboard/app.py --server.port 8502
    ports:
      - "8502:8502"
    volumes:
      - ./storage:/app/storage
```

### Step 12 — Final check

```bash
docker compose up --build
# Gateway at http://localhost:8001
# Dashboard at http://localhost:8502
```

**Verify:** Send a test request to gateway, open dashboard — data shows up.

---

---

# PROJECT 2: Multi-Agent Business Process Automation

**What you're building:** A system where multiple AI agents work together to automate a multi-step business workflow (research → write → notify → log).

**Estimated build time:** 6–8 days
**Folder name:** `multi-agent-bpa`

---

## Phase 1: Setup (Day 1 — 1 hour)

### Step 1 — Create project

```bash
mkdir multi-agent-bpa && cd multi-agent-bpa
git init
uv venv .venv && source .venv/bin/activate
mkdir -p agents tools workflows api storage tests demo
touch README.md docker-compose.yml .env
```

### Step 2 — Install dependencies

```bash
uv pip install langgraph langchain langchain-openai \
               fastapi uvicorn python-dotenv \
               psycopg2-binary redis sqlalchemy \
               google-api-python-client slack-sdk
```

**Verify:** `python -c "import langgraph; print(langgraph.__version__)"` — prints version.

---

## Phase 2: Define the Workflow (Day 1 — 2 hours)

**The demo workflow:** New lead email arrives → Agent researches the company → Agent drafts a personalized reply → Logs to CRM → Notifies Slack.

### Step 3 — Define the workflow state

Create `workflows/state.py`:

```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class WorkflowState(TypedDict):
    # Input
    lead_email: str
    lead_name: str
    lead_company: str

    # Intermediate results
    company_research: str
    drafted_reply: str
    crm_entry_id: str

    # Control
    messages: Annotated[list, add_messages]
    current_step: str
    requires_approval: bool
    approved: bool
    audit_log: List[dict]
```

---

## Phase 3: Build Each Agent (Day 2 — 4 hours)

### Step 4 — Research Agent

Create `agents/research_agent.py`:

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from datetime import datetime

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def research_agent(state: dict) -> dict:
    company = state["lead_company"]
    name = state["lead_name"]

    prompt = f"""
    Research this company and person for a sales outreach:
    - Company: {company}
    - Contact: {name}

    Provide:
    1. What the company does (2 sentences)
    2. Their likely pain points related to AI/automation
    3. A personalization hook for outreach

    Be concise and factual.
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    research = response.content

    # Add to audit log
    log = state.get("audit_log", [])
    log.append({
        "step": "research",
        "timestamp": datetime.now().isoformat(),
        "output_preview": research[:100]
    })

    return {
        "company_research": research,
        "current_step": "research_complete",
        "audit_log": log
    }
```

### Step 5 — Writer Agent

Create `agents/writer_agent.py`:

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from datetime import datetime

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

def writer_agent(state: dict) -> dict:
    research = state["company_research"]
    name = state["lead_name"]
    original_email = state["lead_email"]

    prompt = f"""
    Write a professional, personalized email reply to this lead.

    Original email: {original_email}
    Contact name: {name}
    Research about their company: {research}

    Rules:
    - Keep it under 150 words
    - Reference something specific from the research
    - Clear call to action (book a 20-minute call)
    - Friendly but professional tone
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    draft = response.content

    log = state.get("audit_log", [])
    log.append({
        "step": "draft_email",
        "timestamp": datetime.now().isoformat(),
        "output_preview": draft[:100]
    })

    return {
        "drafted_reply": draft,
        "current_step": "draft_complete",
        "requires_approval": True,
        "audit_log": log
    }
```

### Step 6 — CRM Agent (simulated)

Create `agents/crm_agent.py`:

```python
import uuid
from datetime import datetime

def crm_agent(state: dict) -> dict:
    # In production: call HubSpot / Salesforce API
    # For demo: simulate a CRM entry
    entry_id = str(uuid.uuid4())[:8]

    print(f"[CRM] Creating lead entry for {state['lead_name']} at {state['lead_company']}")
    print(f"[CRM] Entry ID: {entry_id}")

    log = state.get("audit_log", [])
    log.append({
        "step": "crm_log",
        "timestamp": datetime.now().isoformat(),
        "entry_id": entry_id
    })

    return {
        "crm_entry_id": entry_id,
        "current_step": "crm_complete",
        "audit_log": log
    }
```

### Step 7 — Notification Agent

Create `agents/notification_agent.py`:

```python
import os
from datetime import datetime

def notification_agent(state: dict) -> dict:
    # In production: send to Slack via webhook
    # For demo: print to console
    message = f"""
    New Lead Processed:
    - Name: {state['lead_name']}
    - Company: {state['lead_company']}
    - CRM Entry: {state['crm_entry_id']}
    - Draft ready for review
    """
    print(f"[SLACK NOTIFICATION]\n{message}")

    log = state.get("audit_log", [])
    log.append({
        "step": "notification_sent",
        "timestamp": datetime.now().isoformat()
    })

    return {
        "current_step": "complete",
        "audit_log": log
    }
```

---

## Phase 4: Wire the Workflow with LangGraph (Day 3 — 3 hours)

### Step 8 — Build the graph

Create `workflows/lead_workflow.py`:

```python
from langgraph.graph import StateGraph, END
from agents.research_agent import research_agent
from agents.writer_agent import writer_agent
from agents.crm_agent import crm_agent
from agents.notification_agent import notification_agent
from workflows.state import WorkflowState

def should_continue_after_draft(state: dict) -> str:
    # If requires_approval is True and not yet approved, pause here
    if state.get("requires_approval") and not state.get("approved"):
        return "wait_for_approval"
    return "crm"

def build_workflow():
    graph = StateGraph(WorkflowState)

    # Add nodes (each node = one agent)
    graph.add_node("research", research_agent)
    graph.add_node("write", writer_agent)
    graph.add_node("crm", crm_agent)
    graph.add_node("notify", notification_agent)

    # Add edges (flow between agents)
    graph.set_entry_point("research")
    graph.add_edge("research", "write")
    graph.add_conditional_edges(
        "write",
        should_continue_after_draft,
        {
            "wait_for_approval": END,  # pause and wait for human
            "crm": "crm"
        }
    )
    graph.add_edge("crm", "notify")
    graph.add_edge("notify", END)

    return graph.compile()
```

### Step 9 — Test the workflow end-to-end

Create `test_workflow.py` in root:

```python
from workflows.lead_workflow import build_workflow

workflow = build_workflow()

# Simulate incoming lead
initial_state = {
    "lead_email": "Hi, I saw your post about AI automation. We're a 50-person logistics company struggling with manual data entry. Can we chat?",
    "lead_name": "Sarah Chen",
    "lead_company": "FastFreight Logistics",
    "approved": True,  # set to False to test the approval gate
    "audit_log": []
}

result = workflow.invoke(initial_state)

print("\n=== WORKFLOW COMPLETE ===")
print(f"Research: {result['company_research'][:200]}...")
print(f"\nDrafted Reply:\n{result['drafted_reply']}")
print(f"\nCRM Entry ID: {result['crm_entry_id']}")
print(f"\nAudit Log:")
for entry in result['audit_log']:
    print(f"  - {entry['step']} at {entry['timestamp']}")
```

```bash
python test_workflow.py
```

**Verify:** You should see research output, a personalized email draft, CRM ID, and audit log printed in sequence.

---

## Phase 5: FastAPI Trigger Endpoint (Day 4 — 2 hours)

### Step 10 — Create the API

Create `api/main.py`:

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from workflows.lead_workflow import build_workflow
import json

app = FastAPI(title="Multi-Agent BPA")
workflow = build_workflow()

class LeadInput(BaseModel):
    lead_email: str
    lead_name: str
    lead_company: str
    auto_approve: bool = False

@app.post("/process-lead")
async def process_lead(lead: LeadInput, background_tasks: BackgroundTasks):
    initial_state = {
        "lead_email": lead.lead_email,
        "lead_name": lead.lead_name,
        "lead_company": lead.lead_company,
        "approved": lead.auto_approve,
        "audit_log": []
    }

    result = workflow.invoke(initial_state)

    return {
        "status": "complete" if result["current_step"] == "complete" else "awaiting_approval",
        "draft": result.get("drafted_reply"),
        "crm_entry_id": result.get("crm_entry_id"),
        "audit_log": result["audit_log"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}
```

```bash
uvicorn api.main:app --reload --port 8002
```

**Verify:** `curl http://localhost:8002/health` returns `{"status":"ok"}`.

---

## Phase 6: Docker + README (Day 4 — 1 hour)

### Step 11 — Create docker-compose.yml

```yaml
version: "3.9"
services:
  api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8002
    ports:
      - "8002:8002"
    env_file: .env
```

---

---

# PROJECT 3: LLM Fine-Tuning Pipeline (QLoRA + DPO)

**What you're building:** A pipeline to take a base open-source LLM and train it to be an expert in a specific domain (e.g., legal, medical, customer support).

**Estimated build time:** 5–7 days
**Folder name:** `llm-finetune-pipeline`

---

## Phase 1: Setup (Day 1 — 1 hour)

### Step 1 — Create project

```bash
mkdir llm-finetune-pipeline && cd llm-finetune-pipeline
git init
uv venv .venv && source .venv/bin/activate
mkdir -p data_prep training alignment evaluation serving configs experiments
touch README.md .env
```

### Step 2 — Install dependencies

```bash
# Core training stack
uv pip install torch transformers peft trl datasets \
               accelerate bitsandbytes wandb \
               sentencepiece protobuf

# For data prep
uv pip install pandas jsonlines tqdm
```

> **Note on GPU:** Fine-tuning requires a GPU. For local Mac (Apple Silicon): PyTorch MPS works but is slow. For serious training, use RunPod ($0.39/hr for RTX 3090) or Google Colab Pro.

**Verify:** `python -c "import torch; print(torch.cuda.is_available())"` — True on GPU, False on CPU (OK for now).

---

## Phase 2: Data Preparation Pipeline (Day 1 — 3 hours)

**Goal:** Take raw text data (PDFs, CSVs, text files) and convert them into the format needed for fine-tuning.

### Step 3 — Understand the target format

For instruction fine-tuning, every example must look like this:

```json
{
  "instruction": "What are the key obligations in a non-disclosure agreement?",
  "input": "",
  "output": "An NDA typically requires the receiving party to: 1) maintain confidentiality..."
}
```

### Step 4 — Create the data prep script

Create `data_prep/prepare_data.py`:

```python
import json
import re
from pathlib import Path
from datasets import Dataset
import random

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # remove non-ASCII
    return text

def load_raw_data(file_path: str) -> list:
    """Load from JSONL file (one JSON object per line)"""
    data = []
    with open(file_path) as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

def format_for_training(examples: list) -> list:
    """Convert to Alpaca format for instruction tuning"""
    formatted = []
    for ex in examples:
        if not ex.get("instruction") or not ex.get("output"):
            continue
        if len(ex["output"]) < 20:  # skip very short outputs
            continue
        formatted.append({
            "instruction": clean_text(ex["instruction"]),
            "input": clean_text(ex.get("input", "")),
            "output": clean_text(ex["output"])
        })
    return formatted

def create_prompt(example: dict) -> str:
    """Create the full training prompt string"""
    if example["input"]:
        return f"""### Instruction:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Response:\n{example['output']}"""
    return f"""### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"""

def split_and_save(data: list, output_dir: str, train_ratio: float = 0.9):
    random.shuffle(data)
    split = int(len(data) * train_ratio)
    train_data = data[:split]
    val_data = data[split:]

    Path(output_dir).mkdir(exist_ok=True)

    # Save as JSONL
    for name, split_data in [("train", train_data), ("val", val_data)]:
        with open(f"{output_dir}/{name}.jsonl", "w") as f:
            for item in split_data:
                item["text"] = create_prompt(item)
                f.write(json.dumps(item) + "\n")

    print(f"Saved {len(train_data)} train, {len(val_data)} val examples")

if __name__ == "__main__":
    # Create sample data for testing the pipeline
    sample_data = [
        {
            "instruction": "What is a force majeure clause?",
            "input": "",
            "output": "A force majeure clause excuses a party from performing contractual obligations when extraordinary events beyond their control occur, such as natural disasters, wars, or pandemics."
        },
        {
            "instruction": "Explain the difference between void and voidable contracts.",
            "input": "",
            "output": "A void contract has no legal effect from inception, as if it never existed. A voidable contract is valid but can be cancelled by one party due to defects like misrepresentation or undue influence."
        },
        # Add more examples here — aim for 500-1000 for meaningful fine-tuning
    ]

    formatted = format_for_training(sample_data)
    split_and_save(formatted, "data_prep/processed")
    print("Data preparation complete.")
```

```bash
python data_prep/prepare_data.py
```

**Verify:** Check `data_prep/processed/train.jsonl` exists and contains properly formatted JSON lines.

---

## Phase 3: Fine-Tuning with QLoRA (Days 2–3)

### Step 5 — Create the training config

Create `configs/qlora_config.yaml`:

```yaml
# Base model — start with a small one for testing
base_model: "microsoft/phi-2"       # good small model for testing (2.7B)
# base_model: "meta-llama/Llama-2-7b-hf"  # switch to this for production

# LoRA settings
lora_r: 16              # rank — higher = more parameters = better quality but slower
lora_alpha: 32          # scaling factor
lora_dropout: 0.05
lora_target_modules:    # which layers to fine-tune
  - q_proj
  - v_proj

# Training settings
num_epochs: 3
per_device_train_batch_size: 4
gradient_accumulation_steps: 4    # effective batch size = 4 * 4 = 16
learning_rate: 2.0e-4
lr_scheduler_type: "cosine"
warmup_ratio: 0.03

# Quantization (enables training on consumer GPUs)
load_in_4bit: true
bnb_4bit_compute_dtype: "float16"

# Data
dataset_path: "data_prep/processed"
max_seq_length: 512

# Output
output_dir: "training/checkpoints"
logging_steps: 10
save_steps: 100
```

### Step 6 — Create the training script

Create `training/train.py`:

```python
import yaml
import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
from datasets import load_dataset
import wandb
import os

def load_config(path="configs/qlora_config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

def train():
    config = load_config()

    # Initialize W&B tracking
    wandb.init(project="llm-finetune", name=f"qlora-{config['base_model'].split('/')[-1]}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config["base_model"])
    tokenizer.pad_token = tokenizer.eos_token

    # Load model with 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        quantization_config=bnb_config,
        device_map="auto"
    )

    # Apply LoRA adapters
    lora_config = LoraConfig(
        r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        target_modules=config["lora_target_modules"],
        task_type=TaskType.CAUSAL_LM
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()  # shows % of params being trained

    # Load dataset
    dataset = load_dataset("json", data_files={
        "train": f"{config['dataset_path']}/train.jsonl",
        "validation": f"{config['dataset_path']}/val.jsonl"
    })

    # Training arguments
    training_args = TrainingArguments(
        output_dir=config["output_dir"],
        num_train_epochs=config["num_epochs"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        logging_steps=config["logging_steps"],
        save_steps=config["save_steps"],
        eval_strategy="steps",
        eval_steps=100,
        report_to="wandb",
        fp16=True
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=config["max_seq_length"]
    )

    trainer.train()
    trainer.save_model(f"{config['output_dir']}/final")
    print("Training complete. Model saved.")

if __name__ == "__main__":
    train()
```

```bash
# Run training (on GPU)
python training/train.py
```

**Verify:** W&B dashboard opens showing loss curve. Training loss should decrease over epochs.

---

## Phase 4: Evaluation (Day 4 — 2 hours)

### Step 7 — Create before/after comparison

Create `evaluation/compare.py`:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from peft import PeftModel
import torch

BASE_MODEL = "microsoft/phi-2"
FINETUNED_PATH = "training/checkpoints/final"

TEST_QUESTIONS = [
    "What is a force majeure clause?",
    "What makes a contract legally binding?",
    "Explain liquidated damages."
]

def load_base_model():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16)
    return pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)

def load_finetuned_model():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16)
    model = PeftModel.from_pretrained(model, FINETUNED_PATH)
    return pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200)

def run_comparison():
    print("Loading models...")
    base = load_base_model()
    finetuned = load_finetuned_model()

    for question in TEST_QUESTIONS:
        prompt = f"### Instruction:\n{question}\n\n### Response:\n"
        print(f"\n{'='*60}")
        print(f"QUESTION: {question}")
        print(f"\n--- BASE MODEL ---")
        print(base(prompt)[0]["generated_text"][len(prompt):])
        print(f"\n--- FINE-TUNED MODEL ---")
        print(finetuned(prompt)[0]["generated_text"][len(prompt):])

if __name__ == "__main__":
    run_comparison()
```

**Verify:** Fine-tuned model should give more precise, domain-appropriate answers than the base model.

---

## Phase 5: Export for Serving (Day 5 — 2 hours)

### Step 8 — Export merged model for deployment

Create `serving/export.py`:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

BASE_MODEL = "microsoft/phi-2"
ADAPTER_PATH = "training/checkpoints/final"
OUTPUT_PATH = "serving/merged_model"

print("Loading base model...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16)

print("Merging LoRA adapters...")
model = PeftModel.from_pretrained(model, ADAPTER_PATH)
model = model.merge_and_unload()  # merge LoRA weights into base model

print(f"Saving merged model to {OUTPUT_PATH}...")
model.save_pretrained(OUTPUT_PATH)
tokenizer.save_pretrained(OUTPUT_PATH)

print("Export complete. Ready for vLLM or llama.cpp serving.")
```

---

---

# PROJECT 4: Domain-Specific AI Copilot

**What you're building:** An AI assistant that answers questions from your private documents with citations. Works offline for privacy-sensitive clients.

**Estimated build time:** 5–7 days
**Folder name:** `domain-copilot`

---

## Phase 1: Setup (Day 1 — 1 hour)

### Step 1 — Create project

```bash
mkdir domain-copilot && cd domain-copilot
git init
uv venv .venv && source .venv/bin/activate
mkdir -p ingestion retrieval memory llm api ui local_mode config demo_data
touch README.md .env docker-compose.yml
```

### Step 2 — Install dependencies

```bash
uv pip install fastapi uvicorn openai qdrant-client \
               unstructured[pdf] rank-bm25 sentence-transformers \
               langchain langchain-openai psycopg2-binary \
               streamlit python-dotenv
```

**Verify:** `python -c "from qdrant_client import QdrantClient; print('OK')"` — prints OK.

---

## Phase 2: Document Ingestion (Day 1 — 3 hours)

### Step 3 — Start Qdrant (vector database)

```bash
docker run -d -p 6333:6333 qdrant/qdrant
```

**Verify:** Open `http://localhost:6333/dashboard` in browser — Qdrant UI should appear.

### Step 4 — Create the ingestion pipeline

Create `ingestion/ingest.py`:

```python
import os
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from unstructured.partition.pdf import partition_pdf
import json

openai_client = OpenAI()
qdrant = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "domain_copilot"
EMBED_MODEL = "text-embedding-3-small"
VECTOR_SIZE = 1536  # for text-embedding-3-small

def setup_collection():
    """Create collection if it doesn't exist"""
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in collections:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"Created collection: {COLLECTION_NAME}")

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk.strip()) > 50:  # skip tiny chunks
            chunks.append(chunk)
    return chunks

def embed(texts: list) -> list:
    """Get embeddings from OpenAI"""
    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]

def ingest_pdf(pdf_path: str, metadata: dict = None):
    """Parse PDF, chunk, embed, and store in Qdrant"""
    print(f"Ingesting: {pdf_path}")

    # Parse PDF
    elements = partition_pdf(filename=pdf_path)
    text = "\n".join([str(e) for e in elements if str(e).strip()])

    # Chunk
    chunks = chunk_text(text)
    print(f"  Created {len(chunks)} chunks")

    # Embed in batches of 100
    all_points = []
    for i in range(0, len(chunks), 100):
        batch = chunks[i:i+100]
        embeddings = embed(batch)

        for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
            chunk_id = int(hashlib.md5(f"{pdf_path}-{i+j}".encode()).hexdigest(), 16) % (10**9)
            all_points.append(PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "text": chunk,
                    "source": Path(pdf_path).name,
                    "chunk_index": i + j,
                    **(metadata or {})
                }
            ))

    # Upsert to Qdrant
    qdrant.upsert(collection_name=COLLECTION_NAME, points=all_points)
    print(f"  Stored {len(all_points)} vectors in Qdrant")

if __name__ == "__main__":
    setup_collection()

    # Put test PDFs in demo_data/
    for pdf in Path("demo_data").glob("*.pdf"):
        ingest_pdf(str(pdf), metadata={"department": "legal"})

    print("Ingestion complete.")
```

```bash
# Add some PDFs to demo_data/ folder first
python ingestion/ingest.py
```

**Verify:** Open Qdrant dashboard → your collection should show vectors count > 0.

---

## Phase 3: Retrieval (Day 2 — 3 hours)

### Step 5 — Create hybrid search (vector + keyword)

Create `retrieval/search.py`:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
from rank_bm25 import BM25Okapi
import numpy as np

qdrant = QdrantClient(host="localhost", port=6333)
openai_client = OpenAI()
COLLECTION_NAME = "domain_copilot"
EMBED_MODEL = "text-embedding-3-small"

def embed_query(query: str) -> list:
    response = openai_client.embeddings.create(model=EMBED_MODEL, input=[query])
    return response.data[0].embedding

def vector_search(query: str, top_k: int = 10, filters: dict = None) -> list:
    """Dense vector search"""
    query_vector = embed_query(query)

    qdrant_filter = None
    if filters:
        conditions = [FieldCondition(key=k, match=MatchValue(value=v))
                      for k, v in filters.items()]
        qdrant_filter = Filter(must=conditions)

    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        query_filter=qdrant_filter,
        with_payload=True
    )
    return results

def hybrid_search(query: str, top_k: int = 5, filters: dict = None) -> list:
    """
    Hybrid search: combine dense vector search with BM25 keyword scoring.
    Returns top_k most relevant chunks with metadata.
    """
    # 1. Dense search (get more candidates)
    dense_results = vector_search(query, top_k=20, filters=filters)

    if not dense_results:
        return []

    # 2. BM25 reranking on the dense candidates
    texts = [r.payload["text"] for r in dense_results]
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())

    # 3. Combine scores (RRF - Reciprocal Rank Fusion)
    combined = []
    for i, (result, bm25_score) in enumerate(zip(dense_results, bm25_scores)):
        dense_rank = i + 1
        dense_score = 1 / (dense_rank + 60)   # RRF formula
        bm25_rank = int(np.argsort(-bm25_scores).tolist().index(i)) + 1
        bm25_fusion = 1 / (bm25_rank + 60)
        combined_score = dense_score + bm25_fusion

        combined.append({
            "text": result.payload["text"],
            "source": result.payload.get("source", "unknown"),
            "chunk_index": result.payload.get("chunk_index", 0),
            "score": combined_score
        })

    # 4. Sort and return top_k
    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[:top_k]
```

---

## Phase 4: LLM Generation with Citations (Day 3 — 2 hours)

### Step 6 — Create the answer generator

Create `llm/generate.py`:

```python
from openai import OpenAI
from retrieval.search import hybrid_search

client = OpenAI()

SYSTEM_PROMPT = """You are a precise, expert assistant. 
Answer questions ONLY based on the provided context.
Always cite which document you got the information from using [Source: filename].
If the context doesn't contain enough information, say so clearly — do not guess."""

def answer_with_citations(question: str, filters: dict = None) -> dict:
    # Retrieve relevant chunks
    chunks = hybrid_search(question, top_k=5, filters=filters)

    if not chunks:
        return {
            "answer": "I couldn't find relevant information in the knowledge base.",
            "sources": [],
            "chunks_used": 0
        }

    # Build context string
    context = "\n\n".join([
        f"[Source: {c['source']}, Chunk {c['chunk_index']}]\n{c['text']}"
        for c in chunks
    ])

    # Generate answer
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ],
        temperature=0
    )

    answer = response.choices[0].message.content
    sources = list(set([c["source"] for c in chunks]))

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks),
        "context_preview": [c["text"][:100] for c in chunks[:3]]
    }
```

---

## Phase 5: Streamlit UI (Day 4 — 2 hours)

### Step 7 — Create the chat interface

Create `ui/app.py`:

```python
import streamlit as st
from llm.generate import answer_with_citations

st.set_page_config(page_title="Domain Copilot", layout="wide")
st.title("Domain AI Copilot")
st.caption("Ask questions from your private knowledge base — answers cite their sources.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption(f"Sources: {', '.join(msg['sources'])}")

# Chat input
if question := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            result = answer_with_citations(question)

        st.markdown(result["answer"])
        if result["sources"]:
            st.caption(f"Sources: {', '.join(result['sources'])}")
            with st.expander("View retrieved context"):
                for preview in result["context_preview"]:
                    st.text(preview + "...")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })
```

```bash
streamlit run ui/app.py
```

**Verify:** Open browser, upload PDFs, ask questions — answers should reference specific source files.

---

---

# PROJECT 5: Code Review & Generation Agent

**What you're building:** A GitHub bot that automatically reviews pull requests, flags bugs, and generates missing tests/docs.

**Estimated build time:** 4–5 days
**Folder name:** `code-review-agent`

---

## Phase 1: Setup (Day 1 — 1 hour)

### Step 1 — Create project

```bash
mkdir code-review-agent && cd code-review-agent
git init
uv venv .venv && source .venv/bin/activate
mkdir -p agents parsers github output tests .github/workflows
touch README.md .env
```

### Step 2 — Install dependencies

```bash
uv pip install fastapi uvicorn openai PyGithub \
               tree-sitter python-dotenv httpx
```

### Step 3 — Create a GitHub App (or Personal Access Token for demo)

For demo purposes, use a Personal Access Token (PAT):
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Create token with `repo` scope
3. Add to `.env`: `GITHUB_TOKEN=your_token`

---

## Phase 2: Code Parser (Day 1 — 2 hours)

### Step 4 — Create the diff parser

Create `parsers/diff_parser.py`:

```python
import re
from dataclasses import dataclass

@dataclass
class CodeChunk:
    filename: str
    language: str
    added_lines: str
    full_diff: str
    start_line: int

def detect_language(filename: str) -> str:
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".go": "go", ".java": "java", ".rb": "ruby", ".rs": "rust"
    }
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang
    return "unknown"

def parse_pr_diff(pr_files: list) -> list[CodeChunk]:
    """Parse GitHub PR file objects into code chunks"""
    chunks = []
    for file in pr_files:
        if not file.patch:
            continue

        # Extract only added lines (lines starting with +)
        added = []
        for line in file.patch.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                added.append(line[1:])  # remove the + prefix

        if not added:
            continue

        chunks.append(CodeChunk(
            filename=file.filename,
            language=detect_language(file.filename),
            added_lines="\n".join(added),
            full_diff=file.patch[:3000],  # limit to 3000 chars per file
            start_line=0
        ))

    return chunks
```

---

## Phase 3: Review Agents (Day 2 — 4 hours)

### Step 5 — Security Agent

Create `agents/security_agent.py`:

```python
from openai import OpenAI
import json

client = OpenAI()

SECURITY_PROMPT = """You are a security code reviewer specializing in OWASP Top 10 vulnerabilities.

Review this code diff for security issues:

File: {filename}
Language: {language}
Code:
{code}

Check for:
- SQL injection
- XSS vulnerabilities  
- Hardcoded secrets or API keys
- Insecure deserialization
- Path traversal
- Command injection
- Insecure direct object references

Respond in JSON:
{{
  "issues": [
    {{
      "severity": "critical|high|medium|low",
      "type": "vulnerability type",
      "line_hint": "approximate code snippet",
      "description": "what the issue is",
      "fix": "how to fix it"
    }}
  ],
  "overall_risk": "critical|high|medium|low|clean"
}}

If no issues found, return {{"issues": [], "overall_risk": "clean"}}"""

def security_review(filename: str, language: str, code: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": SECURITY_PROMPT.format(
                filename=filename, language=language, code=code[:2000]
            )
        }],
        response_format={"type": "json_object"},
        temperature=0
    )
    return json.loads(response.choices[0].message.content)
```

### Step 6 — Logic Review Agent

Create `agents/logic_agent.py`:

```python
from openai import OpenAI
import json

client = OpenAI()

LOGIC_PROMPT = """You are an expert code reviewer focused on logic correctness.

Review this code for logic errors, bugs, and bad practices:

File: {filename}
Language: {language}  
Code:
{code}

Check for:
- Off-by-one errors
- Null/None pointer dereferences
- Unhandled edge cases
- Incorrect conditional logic
- Resource leaks (unclosed files, connections)
- Race conditions

Respond in JSON:
{{
  "issues": [
    {{
      "severity": "high|medium|low",
      "type": "bug type",
      "line_hint": "approximate code snippet",
      "description": "what the issue is",
      "fix": "suggested fix"
    }}
  ],
  "code_quality": "good|fair|poor"
}}"""

def logic_review(filename: str, language: str, code: str) -> dict:
    client_openai = OpenAI()
    response = client_openai.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": LOGIC_PROMPT.format(
                filename=filename, language=language, code=code[:2000]
            )
        }],
        response_format={"type": "json_object"},
        temperature=0
    )
    return json.loads(response.choices[0].message.content)
```

---

## Phase 4: GitHub Integration (Day 3 — 3 hours)

### Step 7 — Create the webhook handler

Create `github/webhook.py`:

```python
from fastapi import FastAPI, Request, BackgroundTasks
from github import Github
from parsers.diff_parser import parse_pr_diff
from agents.security_agent import security_review
from agents.logic_agent import logic_review
from output.formatter import format_review_comment
import os

app = FastAPI()
g = Github(os.getenv("GITHUB_TOKEN"))

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    if event == "pull_request" and payload["action"] in ["opened", "synchronize"]:
        pr_number = payload["pull_request"]["number"]
        repo_name = payload["repository"]["full_name"]
        background_tasks.add_task(review_pull_request, repo_name, pr_number)
        return {"status": "review queued"}

    return {"status": "ignored"}

async def review_pull_request(repo_name: str, pr_number: int):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    files = list(pr.get_files())

    chunks = parse_pr_diff(files)

    all_security_issues = []
    all_logic_issues = []

    for chunk in chunks[:5]:  # limit to 5 files per review
        if chunk.language == "unknown":
            continue

        sec = security_review(chunk.filename, chunk.language, chunk.added_lines)
        log = logic_review(chunk.filename, chunk.language, chunk.added_lines)

        for issue in sec.get("issues", []):
            issue["file"] = chunk.filename
            issue["agent"] = "security"
            all_security_issues.append(issue)

        for issue in log.get("issues", []):
            issue["file"] = chunk.filename
            issue["agent"] = "logic"
            all_logic_issues.append(issue)

    comment = format_review_comment(all_security_issues, all_logic_issues)
    pr.create_issue_comment(comment)
```

### Step 8 — Format the PR comment

Create `output/formatter.py`:

```python
def format_review_comment(security_issues: list, logic_issues: list) -> str:
    lines = ["## AI Code Review Report\n"]

    # Security section
    lines.append("### Security Analysis")
    if not security_issues:
        lines.append("No security issues found.")
    else:
        for issue in security_issues:
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(issue["severity"], "⚪")
            lines.append(f"\n{emoji} **{issue['severity'].upper()}** — {issue['type']} (`{issue['file']}`)")
            lines.append(f"> {issue['description']}")
            lines.append(f"**Fix:** {issue['fix']}")

    # Logic section
    lines.append("\n### Logic & Bug Analysis")
    if not logic_issues:
        lines.append("No logic issues found.")
    else:
        for issue in logic_issues:
            emoji = {"high": "🟠", "medium": "🟡", "low": "🔵"}.get(issue["severity"], "⚪")
            lines.append(f"\n{emoji} **{issue['severity'].upper()}** — {issue['type']} (`{issue['file']}`)")
            lines.append(f"> {issue['description']}")
            lines.append(f"**Fix:** {issue['fix']}")

    total = len(security_issues) + len(logic_issues)
    lines.append(f"\n---\n*{total} issue(s) found. Reviewed by AI Code Agent.*")

    return "\n".join(lines)
```

```bash
uvicorn github.webhook:app --reload --port 8003
```

**Verify:** Use `ngrok http 8003` to expose locally, add webhook URL to a test GitHub repo, open a PR with intentional bugs → check PR comments.

---

---

# PROJECT 6: AI Analytics Copilot (Text-to-SQL)

**What you're building:** A natural language interface over your database. Type a question in English, get a chart and an insight back.

**Estimated build time:** 4–6 days
**Folder name:** `data-copilot`

---

## Phase 1: Setup (Day 1 — 1 hour)

### Step 1 — Create project

```bash
mkdir data-copilot && cd data-copilot
git init
uv venv .venv && source .venv/bin/activate
mkdir -p schema sql_engine charts insights api ui cache demo_data
touch README.md .env docker-compose.yml
```

### Step 2 — Install dependencies

```bash
uv pip install fastapi uvicorn openai duckdb \
               plotly pandas streamlit sqlalchemy \
               redis python-dotenv
```

### Step 3 — Create demo database

Create `demo_data/seed.py`:

```python
import duckdb

con = duckdb.connect("demo_data/sales.db")

con.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER,
        customer_id INTEGER,
        product VARCHAR,
        category VARCHAR,
        revenue FLOAT,
        quantity INTEGER,
        order_date DATE,
        region VARCHAR,
        customer_tier VARCHAR
    )
""")

# Insert sample data
import random
from datetime import date, timedelta

products = [("Laptop", "Electronics"), ("Phone", "Electronics"), ("Desk", "Furniture"),
            ("Chair", "Furniture"), ("Monitor", "Electronics"), ("Keyboard", "Accessories")]
regions = ["North", "South", "East", "West"]
tiers = ["Enterprise", "SMB", "Startup"]

for i in range(500):
    product, category = random.choice(products)
    con.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        i+1, random.randint(1, 50), product, category,
        round(random.uniform(100, 5000), 2), random.randint(1, 10),
        date(2025, 1, 1) + timedelta(days=random.randint(0, 120)),
        random.choice(regions), random.choice(tiers)
    ])

con.close()
print("Demo database created with 500 orders.")
```

```bash
python demo_data/seed.py
```

**Verify:** `python -c "import duckdb; c=duckdb.connect('demo_data/sales.db'); print(c.execute('SELECT COUNT(*) FROM orders').fetchone())"` — prints `(500,)`.

---

## Phase 2: Schema Inspector (Day 1 — 2 hours)

### Step 4 — Auto-build schema context

Create `schema/inspector.py`:

```python
import duckdb
import json

def get_schema_context(db_path: str) -> str:
    """Extract schema and sample data to feed to LLM as context"""
    con = duckdb.connect(db_path, read_only=True)

    tables = con.execute("SHOW TABLES").fetchall()
    schema_parts = []

    for (table_name,) in tables:
        # Get column info
        columns = con.execute(f"DESCRIBE {table_name}").fetchall()
        col_descriptions = [f"{col[0]} ({col[1]})" for col in columns]

        # Get sample data (3 rows)
        sample = con.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()

        schema_parts.append(f"""
Table: {table_name}
Columns: {', '.join(col_descriptions)}
Sample rows:
{chr(10).join([str(row) for row in sample])}
""")

    return "\n".join(schema_parts)

if __name__ == "__main__":
    context = get_schema_context("demo_data/sales.db")
    print(context)
```

---

## Phase 3: SQL Generator + Validator (Day 2 — 4 hours)

### Step 5 — Create SQL generator

Create `sql_engine/generator.py`:

```python
from openai import OpenAI
import json

client = OpenAI()

def generate_sql(question: str, schema_context: str) -> dict:
    prompt = f"""You are an expert SQL analyst. Generate a SQL query to answer the user's question.

Database Schema:
{schema_context}

User Question: {question}

Rules:
- Use only SELECT statements (no INSERT, UPDATE, DELETE, DROP, CREATE)
- Use proper SQL syntax for DuckDB
- Include appropriate aggregations, GROUP BY, ORDER BY as needed
- Limit results to 100 rows maximum

Return ONLY valid JSON in this format:
{{
  "sql": "SELECT ...",
  "explanation": "This query does X by Y"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
```

### Step 6 — Create SQL validator (safety layer)

Create `sql_engine/validator.py`:

```python
import re

FORBIDDEN_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
                       "ALTER", "TRUNCATE", "EXEC", "EXECUTE"]

def validate_sql(sql: str) -> dict:
    """
    Validate SQL for safety before execution.
    Returns {"valid": True/False, "reason": "..."}
    """
    sql_upper = sql.upper().strip()

    # Must start with SELECT
    if not sql_upper.startswith("SELECT"):
        return {"valid": False, "reason": "Query must start with SELECT"}

    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return {"valid": False, "reason": f"Forbidden keyword: {keyword}"}

    # Check for comments (could be used to inject)
    if "--" in sql or "/*" in sql:
        return {"valid": False, "reason": "SQL comments not allowed"}

    return {"valid": True, "reason": "OK"}
```

### Step 7 — Create executor

Create `sql_engine/executor.py`:

```python
import duckdb
import pandas as pd
from sql_engine.validator import validate_sql

DB_PATH = "demo_data/sales.db"

def execute_query(sql: str) -> dict:
    # Validate first
    validation = validate_sql(sql)
    if not validation["valid"]:
        return {
            "success": False,
            "error": f"SQL validation failed: {validation['reason']}",
            "data": None
        }

    try:
        con = duckdb.connect(DB_PATH, read_only=True)
        df = con.execute(sql).df()
        return {
            "success": True,
            "data": df,
            "rows": len(df),
            "columns": list(df.columns)
        }
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}
```

---

## Phase 4: Chart + Insight Generator (Day 3 — 3 hours)

### Step 8 — Auto-select chart type and render

Create `charts/renderer.py`:

```python
import plotly.express as px
import pandas as pd

def select_chart_type(df: pd.DataFrame, question: str) -> str:
    """Decide best chart type based on data shape and question"""
    question_lower = question.lower()
    cols = df.columns.tolist()
    num_cols = df.select_dtypes(include='number').columns.tolist()

    if any(w in question_lower for w in ["trend", "over time", "by month", "by week"]):
        return "line"
    if len(df) <= 10 and len(num_cols) >= 1:
        return "bar"
    if "distribution" in question_lower or "breakdown" in question_lower:
        return "pie"
    if len(df) > 20:
        return "bar"
    return "table"

def render_chart(df: pd.DataFrame, question: str, explanation: str):
    """Return a Plotly figure"""
    chart_type = select_chart_type(df, question)
    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(exclude='number').columns.tolist()

    if not num_cols:
        return None

    y_col = num_cols[0]
    x_col = cat_cols[0] if cat_cols else df.columns[0]

    if chart_type == "line":
        fig = px.line(df, x=x_col, y=y_col, title=explanation)
    elif chart_type == "pie":
        fig = px.pie(df, names=x_col, values=y_col, title=explanation)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=explanation)

    return fig
```

### Step 9 — Create the Streamlit UI

Create `ui/app.py`:

```python
import streamlit as st
import sys
sys.path.insert(0, ".")

from schema.inspector import get_schema_context
from sql_engine.generator import generate_sql
from sql_engine.executor import execute_query
from charts.renderer import render_chart

st.set_page_config(page_title="Data Copilot", layout="wide")
st.title("Data Copilot — Ask Your Database Anything")

# Load schema once
schema_context = get_schema_context("demo_data/sales.db")

with st.expander("Database Schema"):
    st.code(schema_context)

question = st.text_input(
    "Ask a question:",
    placeholder="e.g. What are the top 5 products by revenue this quarter?"
)

if question:
    with st.spinner("Generating SQL..."):
        result = generate_sql(question, schema_context)

    st.subheader("Generated SQL")
    st.code(result["sql"], language="sql")
    st.caption(f"Explanation: {result['explanation']}")

    with st.spinner("Executing query..."):
        query_result = execute_query(result["sql"])

    if not query_result["success"]:
        st.error(f"Query failed: {query_result['error']}")
    else:
        df = query_result["data"]
        st.success(f"Returned {query_result['rows']} rows")

        # Show chart
        fig = render_chart(df, question, result["explanation"])
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        # Show table
        st.dataframe(df)
```

```bash
streamlit run ui/app.py
```

**Verify:** Ask "What are the top 5 products by total revenue?" — you should see SQL, a bar chart, and a data table.

---

---

# PROJECT 7: Enterprise RAG System

**What you're building:** A production-grade knowledge base QA system with role-based access control, multi-source ingestion, and multi-tenant isolation.

**Estimated build time:** 6–8 days
**Folder name:** `enterprise-rag`

---

## Phase 1: Setup (Day 1 — 1 hour)

### Step 1 — Create project

```bash
mkdir enterprise-rag && cd enterprise-rag
git init
uv venv .venv && source .venv/bin/activate
mkdir -p ingestion embedding storage retrieval access_control api ui workers
touch README.md .env docker-compose.yml
```

### Step 2 — Install dependencies

```bash
uv pip install fastapi uvicorn openai qdrant-client \
               unstructured[pdf] celery redis \
               psycopg2-binary python-jose \
               python-multipart streamlit
```

### Step 3 — Start services

```bash
# Start Qdrant + Redis + Postgres with Docker
cat > docker-compose.yml << 'EOF'
version: "3.9"
services:
  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]

  redis:
    image: redis:alpine
    ports: ["6379:6379"]

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: enterprise_rag
    ports: ["5432:5432"]
EOF

docker compose up -d
```

**Verify:** `docker compose ps` — all 3 services should show "running".

---

## Phase 2: Database Schema for Users + Tenants (Day 1 — 2 hours)

### Step 4 — Create user/tenant management

Create `storage/db_setup.py`:

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="enterprise_rag", user="postgres", password="password"
)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        id SERIAL PRIMARY KEY,
        name VARCHAR UNIQUE NOT NULL,
        collection_name VARCHAR UNIQUE NOT NULL
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR UNIQUE NOT NULL,
        tenant_id INTEGER REFERENCES tenants(id),
        role VARCHAR DEFAULT 'viewer',
        departments TEXT[]  -- departments this user can access
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        filename VARCHAR,
        tenant_id INTEGER REFERENCES tenants(id),
        department VARCHAR,
        ingested_at TIMESTAMP DEFAULT NOW(),
        chunk_count INTEGER
    )
""")

# Insert demo data
cur.execute("INSERT INTO tenants (name, collection_name) VALUES ('acme_corp', 'acme_corp') ON CONFLICT DO NOTHING")
cur.execute("""
    INSERT INTO users (email, tenant_id, role, departments)
    SELECT 'admin@acme.com', id, 'admin', ARRAY['hr','engineering','sales']
    FROM tenants WHERE name='acme_corp'
    ON CONFLICT DO NOTHING
""")
cur.execute("""
    INSERT INTO users (email, tenant_id, role, departments)
    SELECT 'engineer@acme.com', id, 'viewer', ARRAY['engineering']
    FROM tenants WHERE name='acme_corp'
    ON CONFLICT DO NOTHING
""")

conn.commit()
cur.close()
conn.close()
print("Database setup complete.")
```

```bash
python storage/db_setup.py
```

---

## Phase 3: RBAC-Aware Ingestion (Day 2 — 3 hours)

### Step 5 — Create ingestion with access metadata

Create `ingestion/ingest_document.py`:

```python
import hashlib
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from unstructured.partition.pdf import partition_pdf
import psycopg2

qdrant = QdrantClient(host="localhost", port=6333)
openai_client = OpenAI()

def get_or_create_collection(collection_name: str):
    collections = [c.name for c in qdrant.get_collections().collections]
    if collection_name not in collections:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )

def embed_texts(texts: list) -> list:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small", input=texts
    )
    return [item.embedding for item in response.data]

def chunk_text(text: str, size: int = 400, overlap: int = 50) -> list:
    words = text.split()
    return [
        " ".join(words[i:i+size])
        for i in range(0, len(words), size - overlap)
        if len(" ".join(words[i:i+size]).strip()) > 50
    ]

def ingest_document(
    pdf_path: str,
    tenant_id: int,
    collection_name: str,
    department: str
):
    """Ingest a document with tenant + department metadata for RBAC"""
    get_or_create_collection(collection_name)

    elements = partition_pdf(filename=pdf_path)
    text = "\n".join([str(e) for e in elements if str(e).strip()])
    chunks = chunk_text(text)

    print(f"Ingesting {len(chunks)} chunks for dept={department}")

    points = []
    for i in range(0, len(chunks), 100):
        batch = chunks[i:i+100]
        embeddings = embed_texts(batch)
        for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
            chunk_id = int(hashlib.md5(f"{pdf_path}-{i+j}".encode()).hexdigest(), 16) % (10**9)
            points.append(PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "text": chunk,
                    "source": Path(pdf_path).name,
                    "tenant_id": tenant_id,
                    "department": department,  # RBAC tag
                    "chunk_index": i + j
                }
            ))

    qdrant.upsert(collection_name=collection_name, points=points)

    # Log in PostgreSQL
    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="enterprise_rag", user="postgres", password="password"
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (filename, tenant_id, department, chunk_count) VALUES (%s, %s, %s, %s)",
        [Path(pdf_path).name, tenant_id, department, len(chunks)]
    )
    conn.commit()
    conn.close()

    print(f"Ingested {len(points)} vectors.")
```

---

## Phase 4: RBAC Search (Day 3 — 2 hours)

### Step 6 — Search with access control filter

Create `retrieval/rbac_search.py`:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue
from openai import OpenAI

qdrant = QdrantClient(host="localhost", port=6333)
openai_client = OpenAI()

def search_with_rbac(
    query: str,
    collection_name: str,
    allowed_departments: list,
    top_k: int = 5
) -> list:
    """Search only returns results from departments the user is allowed to access"""

    # Embed query
    embedding = openai_client.embeddings.create(
        model="text-embedding-3-small", input=[query]
    ).data[0].embedding

    # Build RBAC filter — user can only see their allowed departments
    rbac_filter = Filter(
        must=[
            FieldCondition(
                key="department",
                match=MatchAny(any=allowed_departments)
            )
        ]
    )

    results = qdrant.search(
        collection_name=collection_name,
        query_vector=embedding,
        query_filter=rbac_filter,
        limit=top_k,
        with_payload=True
    )

    return [{
        "text": r.payload["text"],
        "source": r.payload["source"],
        "department": r.payload["department"],
        "score": r.score
    } for r in results]
```

---

## Phase 5: FastAPI with User Auth (Day 4 — 3 hours)

### Step 7 — Create the API with simple token auth

Create `api/main.py`:

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
import psycopg2
from retrieval.rbac_search import search_with_rbac
from openai import OpenAI

app = FastAPI(title="Enterprise RAG")
openai_client = OpenAI()

def get_user_from_token(authorization: str = Header(...)):
    """Simple token auth — in production use JWT"""
    # Token format: "Bearer email@company.com"
    email = authorization.replace("Bearer ", "").strip()

    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="enterprise_rag", user="postgres", password="password"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT u.email, u.departments, t.collection_name
        FROM users u
        JOIN tenants t ON u.tenant_id = t.id
        WHERE u.email = %s
    """, [email])
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    return {"email": row[0], "departments": row[1], "collection": row[2]}

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(request: QueryRequest, user=Depends(get_user_from_token)):
    # Search with RBAC — user only sees their allowed departments
    results = search_with_rbac(
        query=request.question,
        collection_name=user["collection"],
        allowed_departments=user["departments"]
    )

    if not results:
        return {"answer": "No relevant documents found for your access level.", "sources": []}

    context = "\n\n".join([f"[{r['source']} / {r['department']}]\n{r['text']}" for r in results])

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Answer based on context only. Cite sources."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"}
        ],
        temperature=0
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": list(set([r["source"] for r in results])),
        "departments_accessed": list(set([r["department"] for r in results]))
    }

@app.get("/my-access")
def my_access(user=Depends(get_user_from_token)):
    return {"email": user["email"], "can_access_departments": user["departments"]}
```

```bash
uvicorn api.main:app --reload --port 8004
```

**Verify — test RBAC:**
```bash
# Engineering user — can only access engineering docs
curl -X POST http://localhost:8004/query \
  -H "Authorization: Bearer engineer@acme.com" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the HR vacation policy?"}'

# Should return empty or "No relevant documents found"
# because engineer@acme.com cannot access HR department
```

---

---

## FINAL CHECKLIST — Before Publishing Each Project

For each of the 7 projects, before pushing to GitHub:

| Task | Why |
|------|-----|
| `README.md` has architecture diagram (Mermaid or image) | Clients judge in 30 seconds |
| `README.md` has a metrics table (latency / cost / accuracy) | Proof of outcomes, not just code |
| `docker-compose up` works with one command | Reduces friction for evaluation |
| `.env.example` committed (not `.env`) | Security + client onboarding |
| Demo GIF or screenshot in `demo/` folder | Embedded in README for visual impact |
| All secrets in `.env`, not hardcoded | Basic security hygiene |
| `requirements.txt` or `pyproject.toml` present | Reproducibility |
| At least 5 meaningful commits in git history | Shows professional development process |

---

## QUICK REFERENCE — Ports

| Project | Service | Port |
|---------|---------|------|
| LLM Observatory | Gateway API | 8001 |
| LLM Observatory | Dashboard | 8501 |
| Multi-Agent BPA | Trigger API | 8002 |
| Code Review Agent | Webhook | 8003 |
| Enterprise RAG | Query API | 8004 |
| Data Copilot | Streamlit | 8502 |
| Domain Copilot | Streamlit | 8503 |
| Qdrant | Dashboard | 6333 |

---

*Document version: 1.0 — May 2026*
