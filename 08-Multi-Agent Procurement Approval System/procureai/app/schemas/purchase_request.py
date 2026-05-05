from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PurchaseRequest(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    department: str = Field(..., description="Department making the request")
    requester: str = Field(..., description="Name of the requester")
    vendor: str = Field(..., description="Vendor name")
    category: str = Field(..., description="Purchase category")
    amount: float = Field(..., gt=0, description="Purchase amount")
    justification: str = Field(..., description="Business justification")
    urgency: str = Field(default="normal", description="Urgency level: low, normal, high")
    timestamp: Optional[datetime] = None


class PurchaseRequestResponse(BaseModel):
    request_id: str
    status: str
    message: str
