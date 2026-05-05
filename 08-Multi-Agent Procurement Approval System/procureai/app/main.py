from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from app.db.database import init_db, get_connection
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

@app.get("/purchase-requests")
def list_purchase_requests(
    department: Optional[str] = Query(None, description="Filter by department"),
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, conditional_approval, rejected)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    conn = get_connection()
    query = "SELECT * FROM purchase_requests WHERE 1=1"
    params = []
    if department:
        query += " AND department = ?"
        params.append(department)
    if vendor:
        query += " AND vendor LIKE ?"
        params.append(f"%{vendor}%")
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    count_cursor = conn.execute(
        "SELECT COUNT(*) FROM purchase_requests WHERE 1=1"
        + (" AND department=?" if department else "")
        + (" AND vendor LIKE ?" if vendor else "")
        + (" AND status=?" if status else ""),
        [p for p in params[:-2]],
    )
    total = count_cursor.fetchone()[0]
    conn.close()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [dict(r) for r in rows],
    }


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
