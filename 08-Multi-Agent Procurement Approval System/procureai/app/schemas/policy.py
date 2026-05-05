from pydantic import BaseModel, Field
from typing import List, Optional


class PolicyChunk(BaseModel):
    chunk_id: str
    content: str
    source_clause: Optional[str] = None
    score: float = 0.0


class PolicyClause(BaseModel):
    clause_id: str
    title: str
    content: str
    category: str


class PolicyDecision(BaseModel):
    policy_status: str = Field(..., description="compliant, requires_manager_approval, requires_finance_approval, or non_compliant")
    reason: str
    source_clause: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    required_approvers: List[str] = Field(default_factory=list)
