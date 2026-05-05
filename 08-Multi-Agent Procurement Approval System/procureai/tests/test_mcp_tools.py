import pytest
from app.mcp_server.tools import TOOL_REGISTRY, execute_tool


class TestMCPTools:

    def test_tool_registry_has_required_tools(self):
        required = [
            "search_policy_docs",
            "validate_policy_compliance",
            "lookup_vendor",
            "check_budget_availability",
            "detect_duplicate_request",
            "mask_pii",
            "create_approval_packet",
        ]
        for tool in required:
            assert tool in TOOL_REGISTRY, f"Missing tool: {tool}"

    def test_search_policy_docs(self):
        result = execute_tool("search_policy_docs", {"query": "approval thresholds"})
        assert len(result) > 0
        assert "content" in result[0]

    def test_lookup_vendor(self):
        result = execute_tool("lookup_vendor", {"vendor_name": "Adobe"})
        assert result["vendor_name"] == "Adobe"
        assert result["vendor_id"] == "VND-001"

    def test_check_budget_availability(self):
        result = execute_tool("check_budget_availability", {"department": "IT", "amount": 50000})
        assert "budget_status" in result

    def test_mask_pii(self):
        result = execute_tool("mask_pii", {"text": "Test User at test@email.com"})
        assert "[EMAIL_REDACTED]" in result["masked_text"]

    def test_unknown_tool_raises_error(self):
        with pytest.raises(ValueError):
            execute_tool("nonexistent_tool", {})
