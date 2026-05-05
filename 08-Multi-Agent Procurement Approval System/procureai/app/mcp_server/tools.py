from typing import Dict, Any, List, Callable
from app.schemas.purchase_request import PurchaseRequest
from app.schemas.policy import PolicyChunk, PolicyDecision
from app.schemas.vendor import VendorRecord, VendorStatus
from app.schemas.budget import BudgetDecision
from app.schemas.risk import RiskDecision, DuplicateCheck
from app.schemas.approval import FinalApprovalPacket

from app.rag.retriever import search_policy_docs
from app.agents.policy_agent import PolicyAgent
from app.agents.vendor_agent import VendorAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.risk_agent import RiskAgent
from app.agents.approval_agent import ApprovalAgent

policy_agent = PolicyAgent()
vendor_agent = VendorAgent()
budget_agent = BudgetAgent()
risk_agent = RiskAgent()
approval_agent = ApprovalAgent()

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, input_schema: dict, handler: Callable):
    TOOL_REGISTRY[name] = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "handler": handler,
    }


def execute_tool(name: str, params: dict) -> Any:
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        raise ValueError(f"Tool '{name}' not found. Available: {list(TOOL_REGISTRY.keys())}")
    return tool["handler"](**params)


# ---- Tool Implementations ----

def _search_policy_docs(query: str, top_k: int = 3) -> List[dict]:
    results = search_policy_docs(query, top_k)
    return [r.model_dump() for r in results]


def _validate_policy_compliance(department: str, vendor: str, amount: float, category: str) -> dict:
    req = PurchaseRequest(
        request_id="tool-call",
        department=department,
        requester="system",
        vendor=vendor,
        category=category,
        amount=amount,
        justification="Tool invocation",
    )
    return policy_agent.validate_policy_compliance(req).model_dump()


def _lookup_vendor(vendor_name: str) -> dict:
    return vendor_agent.lookup_vendor(vendor_name).model_dump()


def _check_budget_availability(department: str, amount: float) -> dict:
    return budget_agent.check_budget_availability(department, amount).model_dump()


def _detect_duplicate_request(request_id: str, vendor: str, amount: float) -> dict:
    req = PurchaseRequest(
        request_id=request_id,
        department="unknown",
        requester="system",
        vendor=vendor,
        category="unknown",
        amount=amount,
        justification="Tool invocation",
    )
    return risk_agent.detect_duplicate_request(req).model_dump()


def _mask_pii(text: str) -> dict:
    return {"masked_text": risk_agent.mask_pii(text)}


def _create_approval_packet(request_data: dict) -> dict:
    req = PurchaseRequest(**request_data)
    policy_r = policy_agent.validate_policy_compliance(req)
    vendor_r = vendor_agent.check_vendor_status(req.vendor)
    budget_r = budget_agent.check_budget_availability(req.department, req.amount)
    risk_dr = risk_agent.detect_duplicate_request(req)
    risk_cr = risk_agent.check_high_risk_category(req.category)
    packet = approval_agent.create_approval_packet(
        request=req,
        policy_finding=policy_r.model_dump(),
        vendor_finding=vendor_r.model_dump(),
        budget_finding=budget_r.model_dump(),
        risk_finding={**risk_cr.model_dump(), "duplicate_check": risk_dr.model_dump()},
    )
    return packet.model_dump()


# ---- Register Tools ----

register_tool(
    name="search_policy_docs",
    description="Search procurement policy documents",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "top_k": {"type": "integer", "description": "Number of results"},
        },
        "required": ["query"],
    },
    handler=_search_policy_docs,
)

register_tool(
    name="validate_policy_compliance",
    description="Validate purchase request against procurement policy",
    input_schema={
        "type": "object",
        "properties": {
            "department": {"type": "string"},
            "vendor": {"type": "string"},
            "amount": {"type": "number"},
            "category": {"type": "string"},
        },
        "required": ["department", "vendor", "amount", "category"],
    },
    handler=_validate_policy_compliance,
)

register_tool(
    name="lookup_vendor",
    description="Look up vendor details by name",
    input_schema={
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string"},
        },
        "required": ["vendor_name"],
    },
    handler=_lookup_vendor,
)

register_tool(
    name="check_budget_availability",
    description="Check budget availability for a department",
    input_schema={
        "type": "object",
        "properties": {
            "department": {"type": "string"},
            "amount": {"type": "number"},
        },
        "required": ["department", "amount"],
    },
    handler=_check_budget_availability,
)

register_tool(
    name="detect_duplicate_request",
    description="Detect duplicate purchase requests within 30 days",
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {"type": "string"},
            "vendor": {"type": "string"},
            "amount": {"type": "number"},
        },
        "required": ["request_id", "vendor", "amount"],
    },
    handler=_detect_duplicate_request,
)

register_tool(
    name="mask_pii",
    description="Mask personally identifiable information in text",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
        },
        "required": ["text"],
    },
    handler=_mask_pii,
)

register_tool(
    name="create_approval_packet",
    description="Create a complete approval packet from purchase request data",
    input_schema={
        "type": "object",
        "properties": {
            "request_data": {
                "type": "object",
                "description": "Purchase request fields",
            },
        },
        "required": ["request_data"],
    },
    handler=_create_approval_packet,
)
