import uuid
import json
from datetime import datetime
from typing import Dict, Any, List

from app.db.database import get_connection
from app.schemas.approval import ApprovalDecision, ApprovalEvidence, FinalApprovalPacket
from app.schemas.purchase_request import PurchaseRequest


class ApprovalAgent:

    def __init__(self):
        self.name = "ApprovalAgent"
        self.description = "Combines all agent outputs into final decision"

    def _generate_audit_id(self) -> str:
        return f"AUD-{uuid.uuid4().hex[:6].upper()}"

    def create_approval_packet(
        self,
        request: PurchaseRequest,
        policy_finding: Dict[str, Any],
        vendor_finding: Dict[str, Any],
        budget_finding: Dict[str, Any],
        risk_finding: Dict[str, Any],
    ) -> FinalApprovalPacket:
        findings = {
            "policy": policy_finding,
            "vendor": vendor_finding,
            "budget": budget_finding,
            "risk": risk_finding,
        }

        evidence: List[ApprovalEvidence] = []
        required_approvers: List[str] = []
        decision = ""
        summary_parts = []

        vendor_ok = vendor_finding.get("vendor_status") in ("approved",)
        budget_ok = budget_finding.get("budget_status") == "available"
        policy_approvers = policy_finding.get("required_approvers", [])
        risk_flags = risk_finding.get("flags", [])

        evidence.append(ApprovalEvidence(
            source="Vendor Agent",
            finding=f"Vendor status: {vendor_finding.get('vendor_status', 'unknown')}",
        ))
        evidence.append(ApprovalEvidence(
            source="Budget Agent",
            finding=f"Budget status: {budget_finding.get('budget_status', 'unknown')}",
        ))
        evidence.append(ApprovalEvidence(
            source="Policy Agent",
            finding=f"Policy status: {policy_finding.get('policy_status', 'unknown')}",
        ))
        evidence.append(ApprovalEvidence(
            source="Risk Agent",
            finding=f"Risk level: {risk_finding.get('risk_level', 'unknown')}",
        ))

        if not vendor_ok:
            decision = "rejected"
            required_approvers = []
            summary_parts.append(f"Vendor {request.vendor} is not approved.")
        elif not budget_ok:
            decision = "rejected"
            required_approvers = []
            summary_parts.append(f"Insufficient budget for {request.department} department.")
        elif policy_approvers or risk_flags:
            decision = "conditional_approval"
            required_approvers = list(policy_approvers)
            if risk_flags:
                if "security_team" not in required_approvers:
                    for flag in risk_flags:
                        if "security" in flag:
                            required_approvers.append("security_team")

            if "security_team" in required_approvers:
                summary_parts.append("Security review is required.")
            if "finance_controller" in required_approvers:
                summary_parts.append("Finance controller approval is required.")
            if "department_manager" in required_approvers:
                summary_parts.append("Department manager approval is required.")
            if "director" in required_approvers:
                summary_parts.append("Director approval is required.")

            summary_parts.append("The purchase can proceed after required approvals.")
        else:
            decision = "approved"
            required_approvers = ["team_lead"]
            summary_parts.append("Purchase can proceed with team lead approval.")

        if vendor_ok:
            evidence.append(ApprovalEvidence(source="Vendor Agent", finding="Vendor approved"))
        if budget_ok:
            evidence.append(ApprovalEvidence(
                source="Budget Agent",
                finding=f"Budget available, remaining after purchase: {budget_finding.get('remaining_budget_after_purchase', 0)}",
            ))
        if policy_finding.get("policy_status") != "compliant":
            evidence.append(ApprovalEvidence(
                source="Policy Agent",
                finding=f"Policy requires approval: {policy_finding.get('reason', '')}",
            ))
        if risk_flags:
            for flag in risk_flags:
                evidence.append(ApprovalEvidence(
                    source="Risk Agent",
                    finding=flag,
                ))

        audit_id = self._generate_audit_id()
        summary = " ".join(summary_parts)

        packet = FinalApprovalPacket(
            request_id=request.request_id,
            decision=decision,
            required_approvers=list(set(required_approvers)),
            agent_findings=findings,
            summary=summary,
            audit_id=audit_id,
        )

        self._store_decision(request, packet, findings)
        return packet

    def _store_decision(self, request: PurchaseRequest, packet: FinalApprovalPacket, findings: Dict):
        conn = get_connection()
        conn.execute(
            """INSERT INTO approval_decisions
               (request_id, decision, required_approvers, summary, agent_findings, audit_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                request.request_id,
                packet.decision,
                json.dumps(packet.required_approvers),
                packet.summary,
                json.dumps(findings),
                packet.audit_id,
            ),
        )
        conn.execute(
            "UPDATE purchase_requests SET status = ? WHERE request_id = ?",
            (packet.decision, request.request_id),
        )
        conn.commit()
        conn.close()
