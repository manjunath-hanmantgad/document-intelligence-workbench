from pydantic import BaseModel, Field
from typing import List, Optional


class VendorRecord(BaseModel):
    vendor_id: str
    vendor_name: str
    status: str = Field(..., description="approved, pending, blacklisted")
    risk_level: str = Field(..., description="low, medium, high")
    categories: List[str] = Field(default_factory=list)


class VendorStatus(BaseModel):
    vendor_status: str
    vendor_id: str
    risk_flags: List[str] = Field(default_factory=list)
    risk_level: str = "low"
