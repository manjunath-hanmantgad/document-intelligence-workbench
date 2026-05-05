import json
from datetime import datetime
from typing import Dict, Any

from app.db.database import get_connection
from app.schemas.purchase_request import PurchaseRequest
from app.schemas.approval import FinalApprovalPacket
from app.agents.policy_agent import PolicyAgent
from app.agents.vendor_agent import VendorAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.risk_agent import RiskAgent
from app.agents.approval_agent import ApprovalAgent


class OrchestratorAgent:

    def __init__(self):
        self.name = "OrchestratorAgent"
        self.description = "Controls the procurement approval workflow"
        self.policy_agent = PolicyAgent()
        self.vendor_agent = VendorAgent()
        self.budget_agent = BudgetAgent()
        self.risk_agent = RiskAgent()
        self.approval_agent = ApprovalAgent()

    def process_request(self, request: PurchaseRequest) -> FinalApprovalPacket:
        request.timestamp = datetime.utcnow()

        self._log_action(request.request_id, "orchestrator", "Workflow started")

        self._log_action(request.request_id, "policy_agent", "Policy check initiated")
        policy_result = self.policy_agent.validate_policy_compliance(request)
        self._log_action(request.request_id, "policy_agent",
                         f"Policy check completed: {policy_result.policy_status}")

        self._log_action(request.request_id, "vendor_agent", "Vendor check initiated")
        vendor_result = self.vendor_agent.check_vendor_status(request.vendor)
        self._log_action(request.request_id, "vendor_agent",
                         f"Vendor check completed: {vendor_result.vendor_status}")

        self._log_action(request.request_id, "budget_agent", "Budget check initiated")
        budget_result = self.budget_agent.check_budget_availability(request.department, request.amount)
        self._log_action(request.request_id, "budget_agent",
                         f"Budget check completed: {budget_result.budget_status}")

        self._log_action(request.request_id, "risk_agent", "Risk check initiated")
        risk_result = self.risk_agent.detect_duplicate_request(request)
        risk_category = self.risk_agent.check_high_risk_category(request.category)
        self._log_action(request.request_id, "risk_agent",
                         f"Risk check completed: {risk_category.risk_level}")

        self._store_request(request)

        self._log_action(request.request_id, "approval_agent", "Approval packet generation initiated")
        packet = self.approval_agent.create_approval_packet(
            request=request,
            policy_finding=policy_result.model_dump(),
            vendor_finding=vendor_result.model_dump(),
            budget_finding=budget_result.model_dump(),
            risk_finding={
                **risk_category.model_dump(),
                "duplicate_check": risk_result.model_dump(),
            },
        )
        self._log_action(request.request_id, "orchestrator",
                         f"Workflow completed. Decision: {packet.decision}")
        return packet

    def _store_request(self, request: PurchaseRequest):
        conn = get_connection()
        conn.execute(
            """INSERT OR IGNORE INTO purchase_requests
               (request_id, department, requester, vendor, category, amount, justification, urgency)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (request.request_id, request.department, request.requester,
             request.vendor, request.category, request.amount,
             request.justification, request.urgency),
        )
        conn.commit()
        conn.close()

    def _log_action(self, request_id: str, agent_name: str, action: str):
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_logs (request_id, action, agent_name) VALUES (?, ?, ?)",
            (request_id, action, agent_name),
        )
        conn.commit()
        conn.close()

    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT * FROM purchase_requests WHERE request_id = ?",
            (request_id,),
        )
        req = cursor.fetchone()
        if not req:
            conn.close()
            return {"error": "Request not found"}

        cursor = conn.execute(
            "SELECT * FROM approval_decisions WHERE request_id = ?",
            (request_id,),
        )
        decision = cursor.fetchone()
        cursor = conn.execute(
            "SELECT * FROM audit_logs WHERE request_id = ? ORDER BY created_at",
            (request_id,),
        )
        logs = cursor.fetchall()
        conn.close()

        return {
            "request": dict(req),
            "decision": dict(decision) if decision else None,
            "audit_logs": [dict(log) for log in logs],
        }
