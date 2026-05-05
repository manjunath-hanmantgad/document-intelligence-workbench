from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PurchaseRequestDB(BaseModel):
    request_id: str
    department: str
    requester: str
    vendor: str
    category: str
    amount: float
    justification: str
    urgency: str = "normal"
    status: str = "pending"
    created_at: Optional[datetime] = None


class ApprovalDecisionDB(BaseModel):
    id: Optional[int] = None
    request_id: str
    decision: str
    required_approvers: str
    summary: str
    agent_findings: str
    audit_id: str
    created_at: Optional[datetime] = None


class AuditLogDB(BaseModel):
    id: Optional[int] = None
    request_id: str
    action: str
    agent_name: str
    details: Optional[str] = None
    created_at: Optional[datetime] = None
