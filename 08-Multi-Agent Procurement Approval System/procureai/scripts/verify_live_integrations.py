import os
import sys
import httpx


def verify_health():
    base_url = os.environ.get("PROCUREAI_URL", "http://127.0.0.1:8004")
    checks = []

    print(f"Verifying ProcureAI at {base_url}")
    print("=" * 60)

    with httpx.Client(base_url=base_url, timeout=10) as client:

        checks.append(("Health check", client.get("/health")))
        checks.append(("List MCP tools", client.get("/mcp/tools")))
        checks.append(("List MCP resources", client.get("/mcp/resources")))
        checks.append(("List MCP prompts", client.get("/mcp/prompts")))
        checks.append(("List A2A agents", client.get("/agents")))

        for agent in ["orchestrator", "policy", "vendor", "budget", "risk", "approval"]:
            checks.append((f"A2A card: {agent}", client.get(f"/agents/{agent}/card")))

        request_payload = {
            "request_id": "REQ-INT-2024-001",
            "department": "IT",
            "requester": "Integration Runner",
            "vendor": "Adobe",
            "category": "software_subscription",
            "amount": 85000,
            "justification": "Adobe Creative Cloud licenses for design team — integration validation",
            "urgency": "normal",
        }
        checks.append(("Analyze purchase request", client.post("/purchase-requests/analyze", json=request_payload)))

        checks.append(("Get request status", client.get("/purchase-requests/REQ-INT-2024-001")))
        checks.append(("Get audit log", client.get("/audit/REQ-INT-2024-001")))

    all_pass = True
    for name, response in checks:
        status = response.status_code
        ok = 200 <= status < 300
        symbol = "PASS" if ok else "FAIL"
        print(f"  [{symbol}] {name} -> {status}")
        if not ok:
            all_pass = False
            print(f"         Body: {response.text[:200]}")

    print("=" * 60)
    if all_pass:
        print("All checks passed.")
        return 0
    else:
        print("Some checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(verify_health())
