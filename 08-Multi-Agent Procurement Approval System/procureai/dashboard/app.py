"""ProcureAI – Streamlit dashboard."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import time
import streamlit as st
import requests

API_BASE = os.environ.get("PROCUREAI_API_URL", "http://127.0.0.1:8004")

st.set_page_config(
    page_title="ProcureAI – Procurement Approval System",
    page_icon="🏢",
    layout="wide",
)


def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach ProcureAI API. Start the server: `uvicorn app.main:app --port 8004`"
    except Exception as e:
        return None, str(e)


def api_post(path: str, payload: dict):
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach ProcureAI API. Start the server: `uvicorn app.main:app --port 8004`"
    except Exception as e:
        return None, str(e)


# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.image(
    "https://img.icons8.com/color/96/000000/purchase-order.png",
    width=64,
)
st.sidebar.title("ProcureAI")
st.sidebar.caption("Multi-Agent Procurement Approval System")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["Submit Request", "Request Status", "Audit Trail", "MCP Tools", "Agent Cards"],
)

health, err = api_get("/health")
if health and health.get("status") == "healthy":
    st.sidebar.success("API: Connected")
else:
    st.sidebar.error("API: Offline")

st.sidebar.divider()
st.sidebar.caption("Local API: http://127.0.0.1:8004")
st.sidebar.caption("Docs: http://127.0.0.1:8004/docs")

# ── Decision badge helper ─────────────────────────────────────────────────────

DECISION_COLOR = {
    "approved": "green",
    "conditional_approval": "orange",
    "rejected": "red",
}


def decision_badge(decision: str) -> str:
    color = DECISION_COLOR.get(decision, "gray")
    label = decision.replace("_", " ").title()
    return f":{color}[**{label}**]"


# ── Pages ─────────────────────────────────────────────────────────────────────

if page == "Submit Request":
    st.title("Submit Purchase Request")
    st.caption("Fill in the form below and click **Analyze** to run the multi-agent workflow.")

    with st.form("purchase_form"):
        col1, col2 = st.columns(2)
        with col1:
            request_id = st.text_input("Request ID", value="REQ-2001")
            requester = st.text_input("Requester", value="Amit Sharma")
            department = st.selectbox("Department", ["IT", "HR", "Finance", "Engineering", "Marketing", "Operations"])
        with col2:
            vendor = st.text_input("Vendor", value="Adobe")
            category = st.selectbox("Category", [
                "software_subscription", "hardware", "cloud_infrastructure",
                "legal_services", "consulting", "data_services",
            ])
            amount = st.number_input("Amount (INR)", min_value=1000, max_value=10_000_000, value=85000, step=1000)
        justification = st.text_area("Business Justification", value="Adobe Creative Cloud licenses for the design team.")
        urgency = st.selectbox("Urgency", ["normal", "low", "high"])
        submitted = st.form_submit_button("Analyze", type="primary", use_container_width=True)

    if submitted:
        payload = {
            "request_id": request_id,
            "department": department,
            "requester": requester,
            "vendor": vendor,
            "category": category,
            "amount": amount,
            "justification": justification,
            "urgency": urgency,
        }
        with st.spinner("Running multi-agent workflow…"):
            result, err = api_post("/purchase-requests/analyze", payload)

        if err:
            st.error(err)
        else:
            decision = result.get("decision", "unknown")
            st.markdown(f"### Decision: {decision_badge(decision)}")
            st.caption(f"Audit ID: `{result.get('audit_id', 'N/A')}`")

            st.subheader("Summary")
            st.info(result.get("summary", ""))

            col_app, col_ev = st.columns(2)
            with col_app:
                st.subheader("Required Approvers")
                approvers = result.get("required_approvers", [])
                if approvers:
                    for a in approvers:
                        st.markdown(f"- `{a}`")
                else:
                    st.markdown("_None required_")

            with col_ev:
                st.subheader("Evidence")
                findings = result.get("agent_findings", {})
                for agent_key, finding in findings.items():
                    with st.expander(agent_key.replace("_", " ").title(), expanded=False):
                        st.json(finding)

            with st.expander("Full API Response"):
                st.json(result)


elif page == "Request Status":
    st.title("Request Status")
    request_id = st.text_input("Enter Request ID", value="REQ-2001")
    if st.button("Fetch Status", type="primary"):
        data, err = api_get(f"/purchase-requests/{request_id}")
        if err:
            st.error(err)
        elif data:
            req = data.get("request", {})
            decision_data = data.get("decision")

            col1, col2, col3 = st.columns(3)
            col1.metric("Department", req.get("department", "-"))
            col2.metric("Amount (INR)", f"₹{req.get('amount', 0):,.0f}")
            col3.metric("Vendor", req.get("vendor", "-"))

            if decision_data:
                decision = decision_data.get("decision", "unknown")
                st.markdown(f"**Decision:** {decision_badge(decision)}")
                st.write(f"**Summary:** {decision_data.get('summary', '')}")
                approvers = json.loads(decision_data.get("required_approvers", "[]"))
                if approvers:
                    st.write("**Required Approvers:** " + ", ".join(f"`{a}`" for a in approvers))

            st.subheader("Request Details")
            st.json(req)
        else:
            st.warning(f"Request `{request_id}` not found.")


elif page == "Audit Trail":
    st.title("Audit Trail")
    request_id = st.text_input("Enter Request ID", value="REQ-2001")
    if st.button("Fetch Audit Log", type="primary"):
        data, err = api_get(f"/audit/{request_id}")
        if err:
            st.error(err)
        else:
            logs = data.get("audit_logs", [])
            if logs:
                st.success(f"{len(logs)} audit entries found")
                for log in logs:
                    icon = "✅" if "completed" in log.get("action", "") else "🔄"
                    with st.expander(f"{icon} [{log.get('agent_name','?')}] {log.get('action','')}", expanded=False):
                        st.write(f"**Timestamp:** {log.get('created_at','')}")
                        if log.get("details"):
                            st.write(f"**Details:** {log.get('details')}")
            else:
                st.info("No audit logs found for this request ID.")


elif page == "MCP Tools":
    st.title("MCP Tool Registry")
    st.caption("MCP-compatible tools exposed by ProcureAI for agent clients.")

    data, err = api_get("/mcp/tools")
    if err:
        st.error(err)
    else:
        tools = data.get("tools", [])
        st.metric("Registered Tools", len(tools))
        for tool in tools:
            with st.expander(f"🔧 {tool.get('name', '')}", expanded=False):
                st.write(f"**Description:** {tool.get('description', '')}")
                st.write("**Input Schema:**")
                st.json(tool.get("input_schema", {}))
                st.write("**Output Schema:**")
                st.json(tool.get("output_schema", {}))

    st.divider()
    st.subheader("MCP Resources")
    res_data, _ = api_get("/mcp/resources")
    if res_data:
        for r in res_data.get("resources", []):
            st.markdown(f"- `{r.get('name')}` — {r.get('description', '')}")

    st.divider()
    st.subheader("MCP Prompts")
    prompt_data, _ = api_get("/mcp/prompts")
    if prompt_data:
        for p in prompt_data.get("prompts", []):
            st.markdown(f"- `{p.get('name')}` — {p.get('description', '')}")


elif page == "Agent Cards":
    st.title("A2A Agent Cards")
    st.caption("Each specialist agent exposes a card describing its capabilities, schemas, and endpoint.")

    agents_data, err = api_get("/agents")
    if err:
        st.error(err)
    else:
        agent_names = agents_data.get("agents", [])
        cols = st.columns(min(len(agent_names), 3))
        for i, name in enumerate(agent_names):
            card_data, _ = api_get(f"/agents/{name}/card")
            if card_data:
                with cols[i % 3]:
                    with st.container(border=True):
                        st.subheader(card_data.get("name", name))
                        st.caption(card_data.get("description", ""))
                        st.write("**Capabilities:**")
                        for cap in card_data.get("capabilities", []):
                            st.markdown(f"- `{cap}`")
                        st.write(f"**Input:** `{card_data.get('input_schema','')}`")
                        st.write(f"**Output:** `{card_data.get('output_schema','')}`")
                        st.code(card_data.get("endpoint", ""), language="text")
