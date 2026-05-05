import pytest
from app.a2a.agent_card import A2AServer
from app.a2a.client import A2AClient
from app.a2a.task_message import TaskMessage


class TestA2AMessages:

    def setup_method(self):
        self.a2a = A2AServer()
        self.client = A2AClient()

    def test_agent_cards_exist(self):
        agents = self.a2a.list_agents()
        assert len(agents) > 0
        assert "policy" in agents
        assert "vendor" in agents
        assert "budget" in agents
        assert "risk" in agents
        assert "approval" in agents

    def test_agent_card_has_required_fields(self):
        card = self.a2a.get_agent_card("policy")
        assert card["name"] == "PolicyAgent"
        assert "capabilities" in card
        assert "input_schema" in card
        assert "output_schema" in card
        assert "endpoint" in card

    def test_send_task_to_policy_agent(self):
        task = TaskMessage(
            task_id="test-task-001",
            from_agent="orchestrator",
            to_agent="policy",
            task_type="policy_validation",
            payload={
                "request_id": "TEST-001",
                "department": "IT",
                "requester": "Test",
                "vendor": "Adobe",
                "category": "software_subscription",
                "amount": 85000,
                "justification": "Test",
            },
        )
        response = self.client.send_task(task)
        assert response.status == "completed"
        assert response.result is not None

    def test_send_task_to_vendor_agent(self):
        task = TaskMessage(
            task_id="test-task-002",
            from_agent="orchestrator",
            to_agent="vendor",
            task_type="vendor_check",
            payload={"vendor_name": "Adobe"},
        )
        response = self.client.send_task(task)
        assert response.status == "completed"
        assert response.result["vendor_status"] == "approved"
