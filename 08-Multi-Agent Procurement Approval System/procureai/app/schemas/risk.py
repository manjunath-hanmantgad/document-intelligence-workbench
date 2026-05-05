from pydantic import BaseModel, Field
from typing import List, Optional


class DuplicateCheck(BaseModel):
    is_duplicate: bool
    original_request_id: Optional[str] = None
    reason: Optional[str] = None


class RiskDecision(BaseModel):
    risk_level: str = Field(..., description="low, medium, high")
    flags: List[str] = Field(default_factory=list)
    pii_masked: bool = False
