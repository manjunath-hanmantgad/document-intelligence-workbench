import uuid
from datetime import datetime, timedelta
from typing import List

from app.db.database import get_connection
from app.schemas.purchase_request import PurchaseRequest
from app.schemas.risk import DuplicateCheck, RiskDecision


HIGH_RISK_CATEGORIES = {
    "data_services": "Data services may involve sensitive information handling.",
    "legal_services": "Legal services require compliance oversight.",
    "consulting": "Consulting engagements above 50,000 INR require board notification.",
    "security_services": "Security services require vendor security audit.",
}


class RiskAgent:

    def __init__(self):
        self.name = "RiskAgent"
        self.description = "Flags suspicious or compliance-heavy requests"

    def detect_duplicate_request(self, request: PurchaseRequest) -> DuplicateCheck:
        conn = get_connection()
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        cursor = conn.execute(
            """SELECT request_id FROM purchase_requests
               WHERE vendor = ? AND amount = ? AND created_at >= ?
               AND request_id != ?""",
            (request.vendor, request.amount, thirty_days_ago, request.request_id),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return DuplicateCheck(
                is_duplicate=True,
                original_request_id=row["request_id"],
                reason=f"Similar request to {request.vendor} for {request.amount} found within 30 days.",
            )
        return DuplicateCheck(is_duplicate=False)

    def check_high_risk_category(self, category: str) -> RiskDecision:
        flags: List[str] = []
        risk_level = "low"

        if category in HIGH_RISK_CATEGORIES:
            flags.append(f"{category}_requires_compliance_review")
            risk_level = "medium"
            if category in ("consulting", "data_services"):
                risk_level = "high"

        if "software" in category.lower():
            flags.append("software_subscription_requires_security_review")
            if risk_level == "low":
                risk_level = "medium"

        return RiskDecision(risk_level=risk_level, flags=flags)

    def mask_pii(self, text: str) -> str:
        import re
        text = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME_REDACTED]', text)
        text = re.sub(r'\b\d{10}\b', '[PHONE_REDACTED]', text)
        text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL_REDACTED]', text)
        return text
