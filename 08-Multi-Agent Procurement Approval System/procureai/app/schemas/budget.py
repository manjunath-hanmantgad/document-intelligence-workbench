from pydantic import BaseModel, Field
from typing import Optional


class BudgetRecord(BaseModel):
    department: str
    total_budget: float
    spent_budget: float
    remaining_budget: float = 0.0


class BudgetDecision(BaseModel):
    budget_status: str = Field(..., description="available, insufficient, or depleted")
    remaining_budget_after_purchase: float
    current_remaining: float = 0.0
    reason: Optional[str] = None
