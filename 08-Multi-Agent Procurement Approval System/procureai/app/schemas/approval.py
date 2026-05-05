from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ApprovalEvidence(BaseModel):
    source: str
    finding: str


class ApprovalDecision(BaseModel):
    decision: str = Field(..., description="approved, conditional_approval, rejected, or needs_review")
    required_approvers: List[str] = Field(default_factory=list)
    summary: str
    evidence: List[ApprovalEvidence] = Field(default_factory=list)


class FinalApprovalPacket(BaseModel):
    request_id: str
    decision: str
    required_approvers: List[str]
    agent_findings: Dict[str, Any]
    summary: str
    audit_id: str
