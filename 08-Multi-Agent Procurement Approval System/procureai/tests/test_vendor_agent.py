import pytest
from app.agents.vendor_agent import VendorAgent


class TestVendorAgent:

    def setup_method(self):
        self.agent = VendorAgent()

    def test_approved_vendor(self):
        result = self.agent.check_vendor_status("Adobe")
        assert result.vendor_status == "approved"
        assert len(result.risk_flags) == 0

    def test_blacklisted_vendor(self):
        result = self.agent.check_vendor_status("DataLeak Inc")
        assert result.vendor_status == "blacklisted"
        assert len(result.risk_flags) > 0

    def test_pending_vendor(self):
        result = self.agent.check_vendor_status("UnknownSoft")
        assert result.vendor_status == "pending"
        assert len(result.risk_flags) > 0

    def test_unknown_vendor(self):
        result = self.agent.check_vendor_status("NonExistentCorp")
        assert result.vendor_status == "unknown"
        assert len(result.risk_flags) > 0
