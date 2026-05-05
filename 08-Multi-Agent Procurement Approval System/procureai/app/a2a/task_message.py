from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class TaskMessage(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    from_agent: str = Field(..., description="Source agent name")
    to_agent: str = Field(..., description="Target agent name")
    task_type: str = Field(..., description="Type of task")
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="pending", description="pending, in_progress, completed, failed")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    task_id: str
    from_agent: str
    to_agent: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
