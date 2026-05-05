RESOURCES = {
    "procurement_policy.pdf": {
        "uri": "file:///data/procurement_policy.md",
        "name": "Procurement Policy Document",
        "description": "Company procurement policy with approval thresholds, vendor rules, and compliance requirements",
        "mime_type": "text/markdown",
    },
    "vendor_master.csv": {
        "uri": "file:///data/vendor_master.csv",
        "name": "Vendor Master List",
        "description": "Approved vendors with status, risk level, and categories",
        "mime_type": "text/csv",
    },
    "department_budget.csv": {
        "uri": "file:///data/department_budget.csv",
        "name": "Department Budget Data",
        "description": "Department budgets with total and spent amounts",
        "mime_type": "text/csv",
    },
    "approval_matrix.yaml": {
        "uri": "file:///data/approval_matrix.yaml",
        "name": "Approval Matrix",
        "description": "Approval rules by amount thresholds and special categories",
        "mime_type": "text/yaml",
    },
    "sample_purchase_requests.json": {
        "uri": "file:///data/sample_requests.json",
        "name": "Sample Purchase Requests",
        "description": "Sample purchase requests for testing the workflow",
        "mime_type": "application/json",
    },
}


def list_resources() -> dict:
    return {
        "resources": [
            {
                "uri": v["uri"],
                "name": v["name"],
                "description": v["description"],
                "mimeType": v["mime_type"],
            }
            for v in RESOURCES.values()
        ]
    }
