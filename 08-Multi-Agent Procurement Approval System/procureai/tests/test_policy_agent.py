import pytest
from app.agents.policy_agent import PolicyAgent
from app.schemas.purchase_request import PurchaseRequest


class TestPolicyAgent:

    def setup_method(self):
        self.agent = PolicyAgent()

    def test_low_amount_passes(self):
        req = PurchaseRequest(
            request_id="TEST-001",
            department="IT",
            requester="Test",
            vendor="Adobe",
            category="software",
            amount=10000,
            justification="Test",
        )
        result = self.agent.validate_policy_compliance(req)
        assert result.policy_status == "compliant"

    def test_medium_amount_requires_manager(self):
        req = PurchaseRequest(
            request_id="TEST-002",
            department="IT",
            requester="Test",
            vendor="Adobe",
            category="software",
            amount=50000,
            justification="Test",
        )
        result = self.agent.validate_policy_compliance(req)
        assert result.policy_status == "requires_manager_approval"
        assert "department_manager" in result.required_approvers

    def test_high_amount_requires_finance(self):
        req = PurchaseRequest(
            request_id="TEST-003",
            department="IT",
            requester="Test",
            vendor="Dell",
            category="hardware",
            amount=150000,
            justification="Test",
        )
        result = self.agent.validate_policy_compliance(req)
        assert result.policy_status == "requires_manager_approval"
        assert "finance_controller" in result.required_approvers

    def test_software_adds_security(self):
        req = PurchaseRequest(
            request_id="TEST-004",
            department="IT",
            requester="Test",
            vendor="Adobe",
            category="software_subscription",
            amount=30000,
            justification="Test",
        )
        result = self.agent.validate_policy_compliance(req)
        assert "security_team" in result.required_approvers

    def test_director_approval_over_500k(self):
        req = PurchaseRequest(
            request_id="TEST-005",
            department="IT",
            requester="Test",
            vendor="Dell",
            category="hardware",
            amount=600000,
            justification="Test",
        )
        result = self.agent.validate_policy_compliance(req)
        assert "director" in result.required_approvers
