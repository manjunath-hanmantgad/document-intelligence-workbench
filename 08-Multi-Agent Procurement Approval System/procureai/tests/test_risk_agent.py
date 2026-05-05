import pytest
from app.agents.risk_agent import RiskAgent
from app.schemas.purchase_request import PurchaseRequest


class TestRiskAgent:

    def setup_method(self):
        self.agent = RiskAgent()

    def test_low_risk_category(self):
        result = self.agent.check_high_risk_category("hardware")
        assert result.risk_level == "low"
        assert len(result.flags) == 0

    def test_software_category_flagged(self):
        result = self.agent.check_high_risk_category("software_subscription")
        assert result.risk_level == "medium"
        assert "software_subscription_requires_security_review" in result.flags

    def test_high_risk_category(self):
        result = self.agent.check_high_risk_category("data_services")
        assert result.risk_level == "high"

    def test_pii_masking(self):
        text = "Contact Amit Sharma at amit@company.com or 9876543210"
        masked = self.agent.mask_pii(text)
        assert "[NAME_REDACTED]" in masked
        assert "[EMAIL_REDACTED]" in masked
        assert "[PHONE_REDACTED]" in masked
