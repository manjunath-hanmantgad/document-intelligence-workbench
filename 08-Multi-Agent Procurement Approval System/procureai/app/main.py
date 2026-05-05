from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.database import init_db
from app.config import HOST, PORT, CORS_ORIGINS
from app.orchestrator import OrchestratorAgent
from app.schemas.purchase_request import PurchaseRequest, PurchaseRequestResponse
from app.mcp_server.server import MCPServer
from app.a2a.agent_card import A2AServer
from app.a2a.client import A2AClient
from app.a2a.task_message import TaskMessage

orchestrator = OrchestratorAgent()
mcp_server = MCPServer()
a2a_server = A2AServer()
a2a_client = A2AClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ProcureAI - Multi-Agent Procurement Approval System",
    version="1.0.0",
    description="A multi-agent procurement approval system with MCP and A2A communication",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(",") if CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "ProcureAI",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# ---- Purchase Request Endpoints ----

@app.post("/purchase-requests/analyze", response_model=dict)
def analyze_purchase_request(request: PurchaseRequest):
    packet = orchestrator.process_request(request)
    return packet.model_dump()


@app.get("/purchase-requests/{request_id}")
def get_purchase_request(request_id: str):
    status = orchestrator.get_request_status(request_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status


@app.get("/audit/{request_id}")
def get_audit_log(request_id: str):
    status = orchestrator.get_request_status(request_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return {"audit_logs": status.get("audit_logs", [])}


# ---- A2A Endpoints ----

@app.get("/agents")
def list_agents():
    return {"agents": a2a_server.list_agents()}


@app.get("/agents/{agent_name}/card")
def get_agent_card(agent_name: str):
    try:
        return a2a_server.get_agent_card(agent_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/agents/{agent_name}/tasks")
def send_agent_task(agent_name: str, task: TaskMessage):
    if task.to_agent != agent_name:
        raise HTTPException(status_code=400, detail="Agent name mismatch")
    return a2a_client.send_task(task)


# ---- MCP Endpoints ----

@app.get("/mcp/tools")
def list_mcp_tools():
    return {"tools": mcp_server.list_tools()}


@app.post("/mcp/tools/{tool_name}")
def call_mcp_tool(tool_name: str, arguments: dict):
    try:
        result = mcp_server.call_tool(tool_name, arguments)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/mcp/resources")
def list_mcp_resources():
    return mcp_server.list_resources()


@app.get("/mcp/prompts")
def list_mcp_prompts():
    return mcp_server.list_prompts()


@app.get("/mcp/prompts/{prompt_name}")
def get_mcp_prompt(prompt_name: str):
    try:
        return mcp_server.get_prompt(prompt_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
