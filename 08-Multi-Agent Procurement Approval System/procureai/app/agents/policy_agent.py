from app.schemas.purchase_request import PurchaseRequest
from app.schemas.policy import PolicyDecision
from app.rag.retriever import search_policy_docs


class PolicyAgent:

    def __init__(self):
        self.name = "PolicyAgent"
        self.description = "Checks purchase requests against procurement policy"

    def validate_policy_compliance(self, request: PurchaseRequest) -> PolicyDecision:
        query = f"{request.category} {request.vendor} {request.amount}"
        chunks = search_policy_docs(query)

        combined_text = " ".join(c.content for c in chunks)
        amount = request.amount
        category = request.category.lower()

        approvers = []
        status = "compliant"
        reason = "No policy violations found."
        source_clause = "N/A"
        confidence = 0.95

        if amount > 500000:
            status = "requires_manager_approval"
            reason = f"Purchase amount {amount} INR exceeds 500,000 INR, director approval required."
            source_clause = "PROC-APPROVAL_THRESHOLDS"
            approvers.extend(["department_manager", "finance_controller", "director"])
            confidence = 0.98
        elif amount > 100000:
            status = "requires_manager_approval"
            reason = f"Purchase amount {amount} INR exceeds 100,000 INR, finance controller approval required."
            source_clause = "PROC-APPROVAL_THRESHOLDS"
            approvers.extend(["department_manager", "finance_controller"])
            confidence = 0.97
        elif amount > 25000:
            status = "requires_manager_approval"
            reason = f"Purchase amount {amount} INR exceeds 25,000 INR, department manager approval required."
            source_clause = "PROC-APPROVAL_THRESHOLDS"
            approvers.append("department_manager")
            confidence = 0.96

        if "software" in category or category == "software_subscription":
            if "security_team" not in approvers:
                approvers.append("security_team")
            reason += " Software subscriptions require security review."
            source_clause = "PROC-CATEGORY_POLICY"
            confidence = max(confidence, 0.92)

        if "legal" in category or category == "legal_services":
            if "legal_team" not in approvers:
                approvers.append("legal_team")
            reason += " Legal services require legal team approval."
            source_clause = "PROC-CATEGORY_POLICY"
            confidence = max(confidence, 0.92)

        return PolicyDecision(
            policy_status=status,
            reason=reason,
            source_clause=source_clause,
            confidence=confidence,
            required_approvers=approvers,
        )
