from pathlib import Path
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import jwt

from docint_workbench import api
from docint_workbench.service import DocumentWorkbenchService


def test_api_health_and_process(tmp_path: Path) -> None:
    api.service = DocumentWorkbenchService(
        database_path=tmp_path / "api.db",
        low_confidence_threshold=0.85,
        evaluation_set_path=tmp_path / "evaluation.json",
    )
    client = TestClient(api.app)
    reviewer_headers = {"X-API-Key": "local-reviewer-key"}

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    payload = {
        "file_name": "invoice-record.txt",
        "document_type": "invoice",
        "content": "Vendor: Apex Office Supplies\nInvoice Number: INV-1\nInvoice Date: 2026-04-29\nSubtotal: 100\nTax: 10\nTotal: 110\nCurrency: USD",
    }
    response = client.post("/documents/process", json=payload, headers=reviewer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "invoice"
    assert body["file_name"] == "invoice-record.txt"

    async_response = client.post("/documents/process-async", json=payload, headers=reviewer_headers)
    assert async_response.status_code == 200
    async_job = async_response.json()
    assert async_job["status"] == "pending"
    job_id = async_job["job_id"]

    queue_jobs = client.get("/jobs?status=pending", headers=reviewer_headers)
    assert queue_jobs.status_code == 200
    assert any(job["job_id"] == job_id for job in queue_jobs.json())

    queue_metrics = client.get("/metrics/queue", headers=reviewer_headers)
    assert queue_metrics.status_code == 200
    assert "pending_jobs" in queue_metrics.json()

    processed_job = api.service.process_next_job(worker_id="api-test-worker")
    assert processed_job is not None
    assert processed_job.job_id == job_id
    assert processed_job.status == "completed"

    job_detail = client.get(f"/jobs/{job_id}", headers=reviewer_headers)
    assert job_detail.status_code == 200
    assert job_detail.json()["status"] == "completed"

    list_response = client.get("/documents", headers=reviewer_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2

    prometheus_metrics = client.get("/metrics/prometheus", headers=reviewer_headers)
    assert prometheus_metrics.status_code == 200
    assert "docint_http_requests_total" in prometheus_metrics.text

    upload_response = client.post(
        "/documents/upload?document_type=invoice",
        headers=reviewer_headers,
        files={"file": ("invoice.txt", payload["content"], "text/plain")},
    )
    assert upload_response.status_code == 200

    audit_response = client.get("/audit/events", headers=reviewer_headers)
    assert audit_response.status_code == 200
    assert len(audit_response.json()) >= 2
    assert all(
        event["actor"].startswith("reviewer:ops:") or event["actor"].startswith("queue:")
        for event in audit_response.json()
    )

    unauth_response = client.post("/documents/process", json=payload)
    assert unauth_response.status_code == 401


def test_scope_restriction_and_review_queue(tmp_path: Path) -> None:
    api.service = DocumentWorkbenchService(
        database_path=tmp_path / "scoped.db",
        low_confidence_threshold=0.85,
        evaluation_set_path=tmp_path / "evaluation.json",
    )
    original_settings = api.settings
    api.settings = replace(
        api.settings,
        reviewer_api_keys=("invoice-key", "contract-key"),
        reviewer_role_map={
            "invoice-key": "finance",
            "contract-key": "legal",
        },
        reviewer_scope_map={
            "invoice-key": ("invoice",),
            "contract-key": ("contract",),
        },
    )
    try:
        client = TestClient(api.app)

        invoice_payload = {
            "file_name": "invoice-bad.txt",
            "document_type": "invoice",
            "content": "Vendor: A\nInvoice Number: I-1\nInvoice Date: 2026-05-01\nSubtotal: 100\nTax: 10\nTotal: 99\nCurrency: USD",
        }
        contract_payload = {
            "file_name": "contract-bad.txt",
            "document_type": "contract",
            "content": "Party 1: A\nParty 2: B\nEffective Date: 2027-01-01\nExpiry Date: 2026-01-01\nPayment Terms: Net 30\nAuto Renewal: No",
        }

        invoice_resp = client.post("/documents/process", json=invoice_payload, headers={"X-API-Key": "invoice-key"})
        assert invoice_resp.status_code == 200
        contract_resp = client.post("/documents/process", json=contract_payload, headers={"X-API-Key": "contract-key"})
        assert contract_resp.status_code == 200

        async_invoice = client.post("/documents/process-async", json=invoice_payload, headers={"X-API-Key": "invoice-key"})
        assert async_invoice.status_code == 200
        async_invoice_job_id = async_invoice.json()["job_id"]

        forbidden = client.post("/documents/process", json=contract_payload, headers={"X-API-Key": "invoice-key"})
        assert forbidden.status_code == 403

        queue_invoice = client.get("/documents/review-queue", headers={"X-API-Key": "invoice-key"})
        assert queue_invoice.status_code == 200
        assert all(doc["document_type"] == "invoice" for doc in queue_invoice.json())
        invoice_partitions = client.get("/documents/review-queue/partitions", headers={"X-API-Key": "invoice-key"})
        assert invoice_partitions.status_code == 200
        assert [partition["document_type"] for partition in invoice_partitions.json()] == ["invoice"]

        queue_contract = client.get("/documents/review-queue", headers={"X-API-Key": "contract-key"})
        assert queue_contract.status_code == 200
        assert all(doc["document_type"] == "contract" for doc in queue_contract.json())
        contract_partitions = client.get("/documents/review-queue/partitions", headers={"X-API-Key": "contract-key"})
        assert contract_partitions.status_code == 200
        assert [partition["document_type"] for partition in contract_partitions.json()] == ["contract"]

        forbidden_job_read = client.get(f"/jobs/{async_invoice_job_id}", headers={"X-API-Key": "contract-key"})
        assert forbidden_job_read.status_code == 403
    finally:
        api.settings = original_settings


def test_oidc_reviewer_scope_enforcement(tmp_path: Path) -> None:
    api.service = DocumentWorkbenchService(
        database_path=tmp_path / "oidc.db",
        low_confidence_threshold=0.85,
        evaluation_set_path=tmp_path / "evaluation.json",
    )
    original_settings = api.settings
    api.settings = replace(
        api.settings,
        auth_mode="oidc",
        oidc_algorithms=("HS256",),
        oidc_hs256_shared_secret="test-secret",
        oidc_issuer="https://issuer.example.com",
        oidc_audience="docint-api",
        oidc_role_claim="roles",
        oidc_subject_claim="sub",
        oidc_role_scope_map={
            "ops": ("invoice", "contract", "unknown"),
            "finance": ("invoice",),
            "legal": ("contract",),
            "admin": ("*",),
        },
    )
    try:
        client = TestClient(api.app)
        now = datetime.now(tz=timezone.utc)
        claims = {
            "sub": "finance-user-1",
            "roles": ["finance"],
            "aud": "docint-api",
            "iss": "https://issuer.example.com",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=10)).timestamp()),
        }
        token = jwt.encode(claims, "test-secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}

        invoice_payload = {
            "file_name": "invoice-oidc.txt",
            "document_type": "invoice",
            "content": "Vendor: A\nInvoice Number: I-1\nInvoice Date: 2026-05-01\nSubtotal: 100\nTax: 10\nTotal: 110\nCurrency: USD",
        }
        invoice_resp = client.post("/documents/process", json=invoice_payload, headers=headers)
        assert invoice_resp.status_code == 200

        contract_payload = {
            "file_name": "contract-oidc.txt",
            "document_type": "contract",
            "content": "Party 1: A\nParty 2: B\nEffective Date: 2026-01-01\nExpiry Date: 2027-01-01\nPayment Terms: Net 30\nAuto Renewal: No",
        }
        contract_resp = client.post("/documents/process", json=contract_payload, headers=headers)
        assert contract_resp.status_code == 403

        audit_response = client.get("/audit/events", headers=headers)
        assert audit_response.status_code == 200
        assert all(event["actor"].startswith("oidc:finance:") for event in audit_response.json())
    finally:
        api.settings = original_settings


def test_evaluation_run_requires_oidc_admin_role(tmp_path: Path) -> None:
    api.service = DocumentWorkbenchService(
        database_path=tmp_path / "oidc-admin.db",
        low_confidence_threshold=0.85,
        evaluation_set_path=tmp_path / "evaluation.json",
    )
    original_settings = api.settings
    api.settings = replace(
        api.settings,
        auth_mode="oidc",
        oidc_algorithms=("HS256",),
        oidc_hs256_shared_secret="test-secret",
        oidc_issuer="https://issuer.example.com",
        oidc_audience="docint-api",
        oidc_role_claim="roles",
        oidc_subject_claim="sub",
        oidc_role_scope_map={
            "ops": ("invoice", "contract", "unknown"),
            "finance": ("invoice",),
            "legal": ("contract",),
            "admin": ("*",),
        },
    )
    try:
        client = TestClient(api.app)
        now = datetime.now(tz=timezone.utc)

        non_admin_claims = {
            "sub": "finance-user-1",
            "roles": ["finance"],
            "aud": "docint-api",
            "iss": "https://issuer.example.com",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=10)).timestamp()),
        }
        non_admin_token = jwt.encode(non_admin_claims, "test-secret", algorithm="HS256")
        non_admin_response = client.post(
            "/evaluation/run",
            headers={"Authorization": f"Bearer {non_admin_token}"},
        )
        assert non_admin_response.status_code == 403

        admin_claims = {
            "sub": "admin-user-1",
            "roles": ["admin"],
            "aud": "docint-api",
            "iss": "https://issuer.example.com",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=10)).timestamp()),
        }
        admin_token = jwt.encode(admin_claims, "test-secret", algorithm="HS256")
        admin_response = client.post(
            "/evaluation/run",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_response.status_code == 200
        assert "pass_rate" in admin_response.json()
    finally:
        api.settings = original_settings
