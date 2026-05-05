import pytest
from app.agents.budget_agent import BudgetAgent


class TestBudgetAgent:

    def setup_method(self):
        self.agent = BudgetAgent()

    def test_budget_available(self):
        result = self.agent.check_budget_availability("IT", 50000)
        assert result.budget_status == "available"
        assert result.remaining_budget_after_purchase >= 0

    def test_budget_exceeded(self):
        result = self.agent.check_budget_availability("IT", 500000)
        assert result.budget_status == "insufficient"

    def test_unknown_department(self):
        result = self.agent.check_budget_availability("UnknownDept", 1000)
        assert result.budget_status == "insufficient"
