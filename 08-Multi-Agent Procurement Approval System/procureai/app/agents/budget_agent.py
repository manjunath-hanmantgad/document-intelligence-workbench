from app.db.database import get_connection
from app.schemas.budget import BudgetRecord, BudgetDecision


class BudgetAgent:

    def __init__(self):
        self.name = "BudgetAgent"
        self.description = "Checks department budget availability"

    def get_department_budget(self, department: str) -> BudgetRecord:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT department, total_budget, spent_budget FROM department_budgets WHERE department = ?",
            (department,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            remaining = row["total_budget"] - row["spent_budget"]
            return BudgetRecord(
                department=row["department"],
                total_budget=row["total_budget"],
                spent_budget=row["spent_budget"],
                remaining_budget=remaining,
            )
        return BudgetRecord(
            department=department,
            total_budget=0,
            spent_budget=0,
            remaining_budget=0,
        )

    def check_budget_availability(self, department: str, amount: float) -> BudgetDecision:
        budget = self.get_department_budget(department)

        remaining = budget.remaining_budget
        after_purchase = remaining - amount

        if after_purchase >= 0:
            return BudgetDecision(
                budget_status="available",
                remaining_budget_after_purchase=after_purchase,
                current_remaining=remaining,
            )
        else:
            return BudgetDecision(
                budget_status="insufficient",
                remaining_budget_after_purchase=after_purchase,
                current_remaining=remaining,
                reason=f"Insufficient budget. Required: {amount}, Available: {remaining}.",
            )
