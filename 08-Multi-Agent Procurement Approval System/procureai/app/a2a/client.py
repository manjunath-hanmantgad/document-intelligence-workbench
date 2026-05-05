from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from app.a2a.task_message import TaskMessage, TaskResponse
from app.agents.policy_agent import PolicyAgent
from app.agents.vendor_agent import VendorAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.risk_agent import RiskAgent
from app.agents.approval_agent import ApprovalAgent
from app.schemas.purchase_request import PurchaseRequest


class A2AClient:

    def __init__(self):
        self.policy_agent = PolicyAgent()
        self.vendor_agent = VendorAgent()
        self.budget_agent = BudgetAgent()
        self.risk_agent = RiskAgent()
        self.approval_agent = ApprovalAgent()

    def _create_task(self, from_agent: str, to_agent: str, task_type: str, payload: dict) -> TaskMessage:
        return TaskMessage(
            task_id=f"task-{uuid.uuid4().hex[:8]}",
            from_agent=from_agent,
            to_agent=to_agent,
            task_type=task_type,
            payload=payload,
            status="pending",
            created_at=datetime.utcnow(),
        )

    def send_task(self, task: TaskMessage) -> TaskResponse:
        task.status = "in_progress"

        try:
            if task.to_agent == "policy":
                req = PurchaseRequest(**task.payload)
                result = self.policy_agent.validate_policy_compliance(req)
                task.result = result.model_dump()
            elif task.to_agent == "vendor":
                result = self.vendor_agent.check_vendor_status(task.payload.get("vendor_name", ""))
                task.result = result.model_dump()
            elif task.to_agent == "budget":
                result = self.budget_agent.check_budget_availability(
                    task.payload.get("department", ""),
                    task.payload.get("amount", 0),
                )
                task.result = result.model_dump()
            elif task.to_agent == "risk":
                duplicate = self.risk_agent.detect_duplicate_request(PurchaseRequest(**task.payload))
                category = self.risk_agent.check_high_risk_category(task.payload.get("category", ""))
                masked = self.risk_agent.mask_pii(task.payload.get("justification", ""))
                task.result = {
                    **category.model_dump(),
                    "duplicate_check": duplicate.model_dump(),
                    "pii_masked": True,
                }
            elif task.to_agent == "approval":
                task.result = {"status": "completed", "note": "Approval agent requires all findings"}
            else:
                raise ValueError(f"Unknown agent: {task.to_agent}")

            task.status = "completed"
            task.completed_at = datetime.utcnow()

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.utcnow()

        return TaskResponse(
            task_id=task.task_id,
            from_agent=task.from_agent,
            to_agent=task.to_agent,
            status=task.status,
            result=task.result,
            error=task.error,
        )
