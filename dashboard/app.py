from __future__ import annotations

import os
from hashlib import sha256

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("DASHBOARD_API_URL", "http://127.0.0.1:8005")
ALLOW_SECRET_PREFILL = os.getenv("DASHBOARD_ALLOW_SECRET_PREFILL", "false").lower() == "true"
DEFAULT_REVIEWER_KEY = os.getenv("DASHBOARD_REVIEWER_API_KEY", "") if ALLOW_SECRET_PREFILL else ""
DEFAULT_ADMIN_TOKEN = os.getenv("DASHBOARD_ADMIN_TOKEN", "") if ALLOW_SECRET_PREFILL else ""
DEFAULT_AUTH_MODE = os.getenv("DASHBOARD_AUTH_MODE", "api_key").strip().lower() or "api_key"
DEFAULT_BEARER_TOKEN = os.getenv("DASHBOARD_BEARER_TOKEN", "") if ALLOW_SECRET_PREFILL else ""

st.set_page_config(page_title="Document Intelligence Workbench", layout="wide")
st.title("Document Intelligence Workbench")
st.caption("Structured extraction, validation workflow, review queue, and audit events.")


def fetch_documents(headers: tuple[tuple[str, str], ...]) -> list[dict]:
    response = requests.get(f"{API_URL}/documents", headers=dict(headers), timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_metrics(headers: tuple[tuple[str, str], ...]) -> dict:
    response = requests.get(f"{API_URL}/metrics/summary", headers=dict(headers), timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_audit_events(headers: tuple[tuple[str, str], ...]) -> list[dict]:
    response = requests.get(f"{API_URL}/audit/events", headers=dict(headers), timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_review_queue(headers: tuple[tuple[str, str], ...], document_type: str | None = None) -> list[dict]:
    params = {"document_type": document_type} if document_type else None
    response = requests.get(f"{API_URL}/documents/review-queue", headers=dict(headers), params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_review_queue_partitions(headers: tuple[tuple[str, str], ...]) -> list[dict]:
    response = requests.get(f"{API_URL}/documents/review-queue/partitions", headers=dict(headers), timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_jobs(headers: tuple[tuple[str, str], ...], status: str | None = None) -> list[dict]:
    params = {"status": status} if status else None
    response = requests.get(f"{API_URL}/jobs", headers=dict(headers), params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def process_document(file_name: str, content: str, document_type: str, headers: dict[str, str]) -> dict:
    response = requests.post(
        f"{API_URL}/documents/process",
        headers=headers,
        json={"file_name": file_name, "content": content, "document_type": document_type},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def enqueue_document(file_name: str, content: str, document_type: str, headers: dict[str, str]) -> dict:
    response = requests.post(
        f"{API_URL}/documents/process-async",
        headers=headers,
        json={"file_name": file_name, "content": content, "document_type": document_type},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def upload_document(file_name: str, payload: bytes, document_type: str, headers: dict[str, str]) -> dict:
    response = requests.post(
        f"{API_URL}/documents/upload?document_type={document_type}",
        headers=headers,
        files={"file": (file_name, payload)},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_reviewer_headers(auth_mode: str, reviewer_key: str, bearer_token: str) -> dict[str, str]:
    if auth_mode == "oidc":
        token = bearer_token.strip()
        return {"Authorization": f"Bearer {token}"} if token else {}
    return {"X-API-Key": reviewer_key}


with st.sidebar:
    st.subheader("Access")
    auth_mode = st.selectbox("Auth mode", options=["api_key", "oidc"], index=0 if DEFAULT_AUTH_MODE == "api_key" else 1)
    reviewer_key = st.text_input("Reviewer API key", value=DEFAULT_REVIEWER_KEY, type="password", disabled=auth_mode == "oidc")
    bearer_token = st.text_input("OIDC bearer token", value=DEFAULT_BEARER_TOKEN, type="password", disabled=auth_mode == "api_key")
    admin_token = st.text_input("Admin token", value=DEFAULT_ADMIN_TOKEN, type="password")
    if not ALLOW_SECRET_PREFILL:
        st.caption("Secret prefill is disabled by default. Set `DASHBOARD_ALLOW_SECRET_PREFILL=true` only for controlled local demos.")
    headers = build_reviewer_headers(auth_mode=auth_mode, reviewer_key=reviewer_key, bearer_token=bearer_token)

    st.divider()
    st.subheader("Process Text")
    file_name = st.text_input("File name", value="invoice-sample.txt")
    doc_type = st.selectbox("Document type", options=["unknown", "invoice", "contract"], index=0)
    content = st.text_area("Document content", height=180)
    if st.button("Run Text Extraction", type="primary"):
        if not content.strip():
            st.error("Document content is required")
        else:
            try:
                result = process_document(file_name=file_name, content=content, document_type=doc_type, headers=headers)
                st.success(f"Processed {result['document_id']}")
                st.cache_data.clear()
            except requests.RequestException as exc:
                st.error(f"Processing failed: {exc}")
    if st.button("Queue Text Extraction"):
        if not content.strip():
            st.error("Document content is required")
        else:
            try:
                result = enqueue_document(file_name=file_name, content=content, document_type=doc_type, headers=headers)
                st.success(f"Queued {result['job_id']}")
                st.cache_data.clear()
            except requests.RequestException as exc:
                st.error(f"Queueing failed: {exc}")

    st.divider()
    st.subheader("Upload File")
    upload_type = st.selectbox("Upload document type", options=["unknown", "invoice", "contract"], index=0)
    upload = st.file_uploader("Upload txt, pdf, docx, png, jpg", type=["txt", "pdf", "docx", "png", "jpg", "jpeg", "tif", "tiff"])
    if st.button("Run Upload Extraction"):
        if upload is None:
            st.error("Select a file first")
        else:
            try:
                result = upload_document(upload.name, upload.getvalue(), upload_type, headers)
                st.success(f"Processed {result['document_id']}")
                st.cache_data.clear()
            except requests.RequestException as exc:
                st.error(f"Upload failed: {exc}")

    st.divider()
    if st.button("Run Evaluation"):
        try:
            eval_headers = (
                {"Authorization": f"Bearer {bearer_token.strip()}"} if auth_mode == "oidc" else {"X-Admin-Token": admin_token}
            )
            response = requests.post(
                f"{API_URL}/evaluation/run",
                headers=eval_headers,
                timeout=20,
            )
            response.raise_for_status()
            st.success(response.json())
        except requests.RequestException as exc:
            st.error(f"Evaluation failed: {exc}")

# Keep auth values out of visible state while still producing deterministic request inputs.
header_tuple = tuple(sorted(headers.items()))
auth_context_hash = sha256(repr(header_tuple).encode("utf-8")).hexdigest()[:12]
st.caption(f"Auth context: `{auth_context_hash}`")

try:
    metrics = fetch_metrics(header_tuple)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total documents", metrics["total_documents"])
    col2.metric("Processed", metrics["processed_documents"])
    col3.metric("Review required", metrics["review_required_documents"])
    col4.metric("Avg confidence", metrics["average_confidence"])
except requests.RequestException as exc:
    st.error(f"Could not reach API at {API_URL}: {exc}")
    st.stop()

st.subheader("Documents")
try:
    docs = fetch_documents(header_tuple)
except requests.RequestException as exc:
    st.error(f"Could not load documents: {exc}")
    st.stop()

if docs:
    rows: list[dict] = []
    field_rows: list[dict] = []
    for doc in docs:
        rows.append(
            {
                "document_id": doc["document_id"],
                "file_name": doc["file_name"],
                "document_type": doc["document_type"],
                "requires_review": doc["requires_review"],
                "confidence_average": doc["confidence_average"],
                "status": doc["status"],
            }
        )
        for field in doc["fields"]:
            field_rows.append(
                {
                    "document_id": doc["document_id"],
                    "field": field["key"],
                    "value": field["value"],
                    "confidence": field["confidence"],
                    "requires_review": field["requires_review"],
                    "validator_status": field["validator_status"],
                    "validator_message": field["validator_message"],
                }
            )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.subheader("Extracted Fields")
    st.dataframe(pd.DataFrame(field_rows), use_container_width=True, hide_index=True)
else:
    st.info("No documents processed yet.")

st.subheader("Review Queue")
try:
    partitions = fetch_review_queue_partitions(header_tuple)
    if partitions:
        partition_rows = [
            {
                "document_type": partition["document_type"],
                "total_documents": partition["total_documents"],
                "average_confidence": partition["average_confidence"],
            }
            for partition in partitions
        ]
        st.dataframe(pd.DataFrame(partition_rows), use_container_width=True, hide_index=True)

        filter_options = ["all"] + [partition["document_type"] for partition in partitions]
        selected_partition = st.selectbox(
            "Queue partition",
            options=filter_options,
            format_func=lambda value: "All domains" if value == "all" else value,
            key="review_queue_partition",
        )
        selected_type = None if selected_partition == "all" else selected_partition
        review_docs = fetch_review_queue(header_tuple, document_type=selected_type)
    else:
        review_docs = fetch_review_queue(header_tuple)
        st.info("No documents currently require review.")

    if review_docs:
        review_rows = [
            {
                "document_id": doc["document_id"],
                "file_name": doc["file_name"],
                "document_type": doc["document_type"],
                "confidence_average": doc["confidence_average"],
                "updated_at": doc["updated_at"],
            }
            for doc in review_docs
        ]
        st.dataframe(pd.DataFrame(review_rows), use_container_width=True, hide_index=True)
except requests.RequestException as exc:
    st.warning(f"Could not load review queue: {exc}")

st.subheader("Audit Events")
try:
    audit_rows = fetch_audit_events(header_tuple)
    if audit_rows:
        st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No audit events yet.")
except requests.RequestException as exc:
    st.warning(f"Could not load audit events: {exc}")

st.subheader("Processing Jobs")
try:
    job_status = st.selectbox(
        "Job status filter",
        options=["all", "pending", "in_progress", "completed", "failed", "dead_letter"],
        key="job_status_filter",
    )
    status_filter = None if job_status == "all" else job_status
    jobs = fetch_jobs(header_tuple, status=status_filter)
    if jobs:
        st.dataframe(pd.DataFrame(jobs), use_container_width=True, hide_index=True)
    else:
        st.info("No processing jobs found for the selected filter.")
except requests.RequestException as exc:
    st.warning(f"Could not load processing jobs: {exc}")
