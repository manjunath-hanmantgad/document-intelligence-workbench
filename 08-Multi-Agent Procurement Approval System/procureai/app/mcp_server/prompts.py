PROMPTS = {
    "procurement_policy_check_prompt": {
        "name": "procurement_policy_check_prompt",
        "description": "Prompt template for checking purchase requests against procurement policy",
        "template": (
            "You are a procurement policy compliance officer. Review the following purchase request "
            "against company procurement policy rules.\n\n"
            "Purchase Request:\n"
            "- Department: {department}\n"
            "- Vendor: {vendor}\n"
            "- Category: {category}\n"
            "- Amount: {amount} INR\n"
            "- Justification: {justification}\n\n"
            "Policy Rules:\n"
            "- Purchases above 25,000 INR require department manager approval.\n"
            "- Purchases above 100,000 INR require finance controller approval.\n"
            "- Software subscriptions require security review.\n"
            "- Vendors must be approved before purchase orders.\n\n"
            "Provide a structured decision with policy status, reason, and required approvers."
        ),
    },
    "vendor_risk_review_prompt": {
        "name": "vendor_risk_review_prompt",
        "description": "Prompt template for reviewing vendor risk status",
        "template": (
            "You are a vendor risk analyst. Review the vendor details and provide a risk assessment.\n\n"
            "Vendor: {vendor_name}\n"
            "Status: {vendor_status}\n"
            "Risk Level: {risk_level}\n"
            "Categories: {categories}\n\n"
            "Provide a risk assessment with flags and recommended actions."
        ),
    },
    "approval_summary_prompt": {
        "name": "approval_summary_prompt",
        "description": "Prompt template for generating final approval summary",
        "template": (
            "You are an approval officer. Summarize the following procurement findings into a final decision.\n\n"
            "Policy Finding: {policy_finding}\n"
            "Vendor Finding: {vendor_finding}\n"
            "Budget Finding: {budget_finding}\n"
            "Risk Finding: {risk_finding}\n\n"
            "Generate a final decision, required approvers, and summary."
        ),
    },
}


def list_prompts() -> dict:
    return {
        "prompts": [
            {
                "name": v["name"],
                "description": v["description"],
            }
            for v in PROMPTS.values()
        ]
    }


def get_prompt(name: str) -> dict:
    prompt = PROMPTS.get(name)
    if not prompt:
        raise ValueError(f"Prompt '{name}' not found")
    return prompt
