from typing import Dict, Any, List


AGENT_CARDS = {
    "orchestrator": {
        "name": "OrchestratorAgent",
        "description": "Controls the entire procurement approval workflow",
        "capabilities": ["workflow_orchestration", "request_routing", "audit_logging"],
        "input_schema": "PurchaseRequest",
        "output_schema": "FinalApprovalPacket",
        "endpoint": "/agents/orchestrator/tasks",
    },
    "policy": {
        "name": "PolicyAgent",
        "description": "Checks purchase requests against procurement policy using RAG",
        "capabilities": ["policy_search", "policy_validation"],
        "input_schema": "PurchaseRequest",
        "output_schema": "PolicyDecision",
        "endpoint": "/agents/policy/tasks",
    },
    "vendor": {
        "name": "VendorAgent",
        "description": "Checks whether vendor is approved or risky",
        "capabilities": ["vendor_lookup", "vendor_status_check"],
        "input_schema": "VendorLookup",
        "output_schema": "VendorStatus",
        "endpoint": "/agents/vendor/tasks",
    },
    "budget": {
        "name": "BudgetAgent",
        "description": "Checks department budget availability",
        "capabilities": ["budget_lookup", "budget_availability_check"],
        "input_schema": "BudgetCheck",
        "output_schema": "BudgetDecision",
        "endpoint": "/agents/budget/tasks",
    },
    "risk": {
        "name": "RiskAgent",
        "description": "Flags suspicious or compliance-heavy requests",
        "capabilities": ["duplicate_detection", "risk_category_check", "pii_masking"],
        "input_schema": "RiskCheck",
        "output_schema": "RiskDecision",
        "endpoint": "/agents/risk/tasks",
    },
    "approval": {
        "name": "ApprovalAgent",
        "description": "Combines all agent outputs into final decision",
        "capabilities": ["approval_decision", "approval_packet_creation"],
        "input_schema": "ApprovalInput",
        "output_schema": "FinalApprovalPacket",
        "endpoint": "/agents/approval/tasks",
    },
}


class A2AServer:

    def get_agent_card(self, agent_name: str) -> Dict[str, Any]:
        card = AGENT_CARDS.get(agent_name)
        if not card:
            raise ValueError(f"Agent '{agent_name}' not found")
        return card

    def list_agents(self) -> List[str]:
        return list(AGENT_CARDS.keys())
