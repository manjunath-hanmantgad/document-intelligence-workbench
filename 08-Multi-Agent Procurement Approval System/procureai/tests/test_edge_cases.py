"""Edge-case and boundary tests for API validation and agent robustness."""
import pytest
from pydantic import ValidationError
from app.schemas.purchase_request import PurchaseRequest
from app.agents.policy_agent import PolicyAgent
from app.agents.vendor_agent import VendorAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.risk_agent import RiskAgent


class TestPurchaseRequestValidation:
    """Schema-level validation boundaries."""

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            PurchaseRequest(
                request_id="BAD-001",
                department="IT",
                requester="Test",
                vendor="Adobe",
                category="software_subscription",
                amount=-1000,
                justification="Should fail",
            )

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            PurchaseRequest(
                request_id="BAD-002",
                department="IT",
                requester="Test",
                vendor="Adobe",
                category="software_subscription",
                amount=0,
                justification="Should fail",
            )

    def test_missing_required_fields_rejected(self):
        with pytest.raises(ValidationError):
            PurchaseRequest(
                request_id="BAD-003",
                department="IT",
                # requester is missing
                vendor="Adobe",
                category="software_subscription",
                amount=10000,
                justification="Should fail",
            )

    def test_urgency_defaults_to_normal(self):
        req = PurchaseRequest(
            request_id="OK-001",
            department="IT",
            requester="Alice",
            vendor="Adobe",
            category="software_subscription",
            amount=10000,
            justification="Fine",
        )
        assert req.urgency == "normal"

    def test_very_large_amount_accepted(self):
        req = PurchaseRequest(
            request_id="OK-002",
            department="Engineering",
            requester="Bob",
            vendor="Oracle",
            category="software_subscription",
            amount=9_999_999,
            justification="Enterprise license",
        )
        assert req.amount == 9_999_999


class TestPolicyAgentBoundaries:
    """Policy threshold boundary conditions."""

    def setup_method(self):
        self.agent = PolicyAgent()

    def _req(self, amount: float, category: str = "hardware") -> PurchaseRequest:
        return PurchaseRequest(
            request_id="EDGE-POL",
            department="IT",
            requester="Test",
            vendor="Dell",
            category=category,
            amount=amount,
            justification="Edge case",
        )

    def test_exactly_at_low_threshold_compliant(self):
        result = self.agent.validate_policy_compliance(self._req(25000))
        assert result.policy_status == "compliant"

    def test_one_above_low_threshold_requires_manager(self):
        result = self.agent.validate_policy_compliance(self._req(25001))
        assert result.policy_status == "requires_manager_approval"
        assert "department_manager" in result.required_approvers

    def test_exactly_at_high_threshold(self):
        result = self.agent.validate_policy_compliance(self._req(100000))
        assert "department_manager" in result.required_approvers

    def test_one_above_high_threshold_adds_finance(self):
        result = self.agent.validate_policy_compliance(self._req(100001))
        assert "finance_controller" in result.required_approvers

    def test_exactly_at_director_threshold(self):
        result = self.agent.validate_policy_compliance(self._req(500000))
        assert "finance_controller" in result.required_approvers

    def test_one_above_director_threshold_adds_director(self):
        result = self.agent.validate_policy_compliance(self._req(500001))
        assert "director" in result.required_approvers


class TestVendorAgentEdgeCases:

    def setup_method(self):
        self.agent = VendorAgent()

    def test_empty_vendor_name_returns_unknown(self):
        result = self.agent.check_vendor_status("")
        assert result.vendor_status == "unknown"

    def test_vendor_name_case_insensitive(self):
        lower = self.agent.check_vendor_status("adobe")
        upper = self.agent.check_vendor_status("ADOBE")
        assert lower.vendor_status == upper.vendor_status == "approved"

    def test_whitespace_only_vendor_name(self):
        result = self.agent.check_vendor_status("   ")
        assert result.vendor_status == "unknown"

    def test_banned_vendor_rejected(self):
        result = self.agent.check_vendor_status("ShadyConsult")
        assert result.vendor_status in ("banned", "blacklisted")
        assert len(result.risk_flags) > 0


class TestBudgetAgentEdgeCases:

    def setup_method(self):
        self.agent = BudgetAgent()

    def test_exactly_equal_to_remaining_budget(self):
        # IT: total=500000, spent=320000 → remaining=180000
        result = self.agent.check_budget_availability("IT", 180000)
        assert result.budget_status == "available"
        assert result.remaining_budget_after_purchase == 0

    def test_one_above_remaining_budget(self):
        result = self.agent.check_budget_availability("IT", 180001)
        assert result.budget_status == "insufficient"

    def test_minimum_valid_amount(self):
        result = self.agent.check_budget_availability("HR", 1)
        assert result.budget_status == "available"


class TestRiskAgentEdgeCases:

    def setup_method(self):
        self.agent = RiskAgent()

    def test_pii_email_masked(self):
        text = "Contact john.doe@company.com for details"
        result = self.agent.mask_pii(text)
        assert "@" not in result or "[EMAIL]" in result

    def test_pii_phone_masked(self):
        text = "Call +91-9876543210 to confirm"
        result = self.agent.mask_pii(text)
        assert "9876543210" not in result

    def test_empty_text_pii_masking_safe(self):
        result = self.agent.mask_pii("")
        assert result == ""

    def test_unknown_category_low_risk(self):
        result = self.agent.check_high_risk_category("office_supplies")
        assert result.risk_level in ("low", "medium")
