import pytest
from app.orchestrator import OrchestratorAgent
from app.schemas.purchase_request import PurchaseRequest
from app.db.database import init_db


class TestApprovalWorkflow:

    def setup_method(self):
        init_db()
        self.orchestrator = OrchestratorAgent()

    def test_approved_workflow(self):
        req = PurchaseRequest(
            request_id="WF-TEST-001",
            department="IT",
            requester="Test User",
            vendor="Adobe",
            category="software",
            amount=10000,
            justification="Test purchase",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.request_id == "WF-TEST-001"
        assert packet.decision in ("approved", "conditional_approval")
        assert packet.audit_id.startswith("AUD-")

    def test_rejected_workflow_blacklisted_vendor(self):
        req = PurchaseRequest(
            request_id="WF-TEST-002",
            department="IT",
            requester="Test User",
            vendor="DataLeak Inc",
            category="software",
            amount=10000,
            justification="Test",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.decision == "rejected"

    def test_rejected_workflow_budget_exceeded(self):
        req = PurchaseRequest(
            request_id="WF-TEST-003",
            department="IT",
            requester="Test User",
            vendor="Adobe",
            category="software",
            amount=9999999,
            justification="Test",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.decision == "rejected"

    def test_conditional_approval_workflow(self):
        req = PurchaseRequest(
            request_id="WF-TEST-004",
            department="IT",
            requester="Test User",
            vendor="Adobe",
            category="software_subscription",
            amount=85000,
            justification="Software licenses",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.decision == "conditional_approval"
        assert len(packet.required_approvers) > 0
