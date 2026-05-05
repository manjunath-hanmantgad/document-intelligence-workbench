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
            request_id="WF-2024-001",
            department="IT",
            requester="Amit Sharma",
            vendor="Adobe",
            category="software",
            amount=10000,
            justification="Adobe Acrobat Pro licenses for document workflows",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.request_id == "WF-2024-001"
        assert packet.decision in ("approved", "conditional_approval")
        assert packet.audit_id.startswith("AUD-")

    def test_rejected_workflow_blacklisted_vendor(self):
        req = PurchaseRequest(
            request_id="WF-2024-002",
            department="Finance",
            requester="Arun Kumar",
            vendor="Veridata Analytics",
            category="data_services",
            amount=50000,
            justification="Financial data enrichment platform",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.decision == "rejected"

    def test_rejected_workflow_budget_exceeded(self):
        req = PurchaseRequest(
            request_id="WF-2024-003",
            department="IT",
            requester="Priya Patel",
            vendor="Oracle",
            category="software",
            amount=9999999,
            justification="Enterprise Oracle DB license — budget limit exceeded",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.decision == "rejected"

    def test_conditional_approval_workflow(self):
        req = PurchaseRequest(
            request_id="WF-2024-004",
            department="IT",
            requester="Amit Sharma",
            vendor="Adobe",
            category="software_subscription",
            amount=85000,
            justification="Adobe Creative Cloud annual licenses for the design team",
            urgency="normal",
        )
        packet = self.orchestrator.process_request(req)
        assert packet.decision == "conditional_approval"
        assert len(packet.required_approvers) > 0
