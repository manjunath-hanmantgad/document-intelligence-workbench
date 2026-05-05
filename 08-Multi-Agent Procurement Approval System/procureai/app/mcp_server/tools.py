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


def register_tool(name: str, description: str, input_schema: dict, output_schema: dict, handler: Callable):
    TOOL_REGISTRY[name] = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "output_schema": output_schema,
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
        request_id="MCP-POLICY-CHECK",
        department=department,
        requester="MCP Server",
        vendor=vendor,
        category=category,
        amount=amount,
        justification="MCP tool call — policy compliance check",
    )
    return policy_agent.validate_policy_compliance(req).model_dump()


def _lookup_vendor(vendor_name: str) -> dict:
    return vendor_agent.lookup_vendor(vendor_name).model_dump()


def _check_budget_availability(department: str, amount: float) -> dict:
    return budget_agent.check_budget_availability(department, amount).model_dump()


def _detect_duplicate_request(request_id: str, vendor: str, amount: float) -> dict:
    req = PurchaseRequest(
        request_id=request_id,
        department="Operations",
        requester="MCP Server",
        vendor=vendor,
        category="general",
        amount=amount,
        justification="MCP tool call — duplicate request check",
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
    description="Search procurement policy documents by keyword query and return matching policy chunks with source clause references.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query string"},
            "top_k": {"type": "integer", "description": "Maximum number of results to return", "default": 3},
        },
        "required": ["query"],
    },
    output_schema={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "string"},
                "content": {"type": "string"},
                "source_clause": {"type": "string"},
                "score": {"type": "number"},
            },
        },
    },
    handler=_search_policy_docs,
)

register_tool(
    name="validate_policy_compliance",
    description="Validate a purchase request against procurement policy rules and return approval requirements.",
    input_schema={
        "type": "object",
        "properties": {
            "department": {"type": "string", "description": "Requesting department"},
            "vendor": {"type": "string", "description": "Vendor name"},
            "amount": {"type": "number", "description": "Purchase amount in INR"},
            "category": {"type": "string", "description": "Purchase category"},
        },
        "required": ["department", "vendor", "amount", "category"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "policy_status": {"type": "string", "enum": ["compliant", "requires_manager_approval"]},
            "reason": {"type": "string"},
            "source_clause": {"type": "string"},
            "confidence": {"type": "number"},
            "required_approvers": {"type": "array", "items": {"type": "string"}},
        },
    },
    handler=_validate_policy_compliance,
)

register_tool(
    name="lookup_vendor",
    description="Look up vendor details including approval status and risk level by vendor name.",
    input_schema={
        "type": "object",
        "properties": {
            "vendor_name": {"type": "string", "description": "Vendor name to look up"},
        },
        "required": ["vendor_name"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "vendor_id": {"type": "string"},
            "vendor_name": {"type": "string"},
            "status": {"type": "string", "enum": ["approved", "pending", "blacklisted", "banned", "unknown"]},
            "risk_level": {"type": "string", "enum": ["low", "medium", "high", "unknown"]},
            "categories": {"type": "string"},
        },
    },
    handler=_lookup_vendor,
)

register_tool(
    name="check_budget_availability",
    description="Check whether a department has sufficient budget for a given purchase amount.",
    input_schema={
        "type": "object",
        "properties": {
            "department": {"type": "string", "description": "Department name"},
            "amount": {"type": "number", "description": "Requested purchase amount in INR"},
        },
        "required": ["department", "amount"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "budget_status": {"type": "string", "enum": ["available", "insufficient", "unknown"]},
            "current_remaining": {"type": "number"},
            "remaining_budget_after_purchase": {"type": "number"},
            "reason": {"type": "string"},
        },
    },
    handler=_check_budget_availability,
)

register_tool(
    name="detect_duplicate_request",
    description="Check whether a similar purchase request for the same vendor and amount was submitted within the last 30 days.",
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "description": "Unique request identifier"},
            "vendor": {"type": "string", "description": "Vendor name"},
            "amount": {"type": "number", "description": "Purchase amount"},
        },
        "required": ["request_id", "vendor", "amount"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "is_duplicate": {"type": "boolean"},
            "original_request_id": {"type": "string"},
            "reason": {"type": "string"},
        },
    },
    handler=_detect_duplicate_request,
)

register_tool(
    name="mask_pii",
    description="Mask personally identifiable information such as email addresses, phone numbers, and Aadhaar/PAN numbers in text.",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Input text to mask PII from"},
        },
        "required": ["text"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "masked_text": {"type": "string", "description": "Text with PII replaced by placeholders"},
        },
    },
    handler=_mask_pii,
)

register_tool(
    name="create_approval_packet",
    description="Run the full multi-agent procurement workflow for a purchase request and return a complete approval packet with decision, required approvers, and evidence.",
    input_schema={
        "type": "object",
        "properties": {
            "request_data": {
                "type": "object",
                "description": "Purchase request fields",
                "properties": {
                    "request_id": {"type": "string"},
                    "department": {"type": "string"},
                    "requester": {"type": "string"},
                    "vendor": {"type": "string"},
                    "category": {"type": "string"},
                    "amount": {"type": "number"},
                    "justification": {"type": "string"},
                    "urgency": {"type": "string", "enum": ["low", "normal", "high"]},
                },
                "required": ["request_id", "department", "requester", "vendor", "category", "amount", "justification"],
            },
        },
        "required": ["request_data"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "request_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["approved", "conditional_approval", "rejected"]},
            "required_approvers": {"type": "array", "items": {"type": "string"}},
            "agent_findings": {"type": "object"},
            "summary": {"type": "string"},
            "audit_id": {"type": "string"},
        },
    },
    handler=_create_approval_packet,
)
