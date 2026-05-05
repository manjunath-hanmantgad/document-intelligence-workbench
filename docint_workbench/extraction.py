from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

import requests


@dataclass
class ExtractedField:
    key: str
    value: str
    confidence: float


def _find(pattern: str, text: str, key: str, confidence: float = 0.94) -> ExtractedField:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return ExtractedField(key=key, value="", confidence=0.35)
    return ExtractedField(key=key, value=match.group(1).strip(), confidence=confidence)


def detect_document_type(content: str, requested_type: str) -> str:
    if requested_type != "unknown":
        return requested_type
    text = content.lower()
    if "invoice" in text or "subtotal" in text:
        return "invoice"
    if "agreement" in text or "effective date" in text or "party" in text:
        return "contract"
    return "unknown"


def extract_invoice_fields(content: str) -> list[ExtractedField]:
    patterns = [
        (r"(?m)^vendor\s*:\s*(.+)$", "vendor_name"),
        (r"(?m)^invoice\s*(?:number|no)\s*:\s*(.+)$", "invoice_number"),
        (r"(?m)^invoice\s*date\s*:\s*(.+)$", "invoice_date"),
        (r"(?m)^subtotal\s*:\s*([0-9]+(?:\.[0-9]{1,2})?)$", "subtotal"),
        (r"(?m)^tax\s*:\s*([0-9]+(?:\.[0-9]{1,2})?)$", "tax"),
        (r"(?m)^total\s*:\s*([0-9]+(?:\.[0-9]{1,2})?)$", "total"),
        (r"(?m)^currency\s*:\s*([A-Z]{3})$", "currency"),
    ]
    return [_find(pattern, content, key) for pattern, key in patterns]


def extract_contract_fields(content: str) -> list[ExtractedField]:
    patterns = [
        (r"party\s*1\s*:\s*(.+)", "party_one"),
        (r"party\s*2\s*:\s*(.+)", "party_two"),
        (r"effective\s*date\s*:\s*(.+)", "effective_date"),
        (r"expiry\s*date\s*:\s*(.+)", "expiry_date"),
        (r"payment\s*terms\s*:\s*(.+)", "payment_terms"),
        (r"auto\s*renewal\s*:\s*(.+)", "auto_renewal"),
    ]
    return [_find(pattern, content, key) for pattern, key in patterns]


def extract_fields(content: str, document_type: str) -> Iterable[ExtractedField]:
    if document_type == "invoice":
        return extract_invoice_fields(content)
    if document_type == "contract":
        return extract_contract_fields(content)
    return []


def extract_fields_with_provider(
    content: str,
    document_type: str,
    llm_provider: str,
    openai_api_key: str,
    openai_model: str,
    azure_openai_endpoint: str,
    azure_openai_key: str,
    azure_openai_chat_deployment: str,
) -> Iterable[ExtractedField]:
    provider = llm_provider.strip().lower()
    if provider == "deterministic":
        return extract_fields(content, document_type)
    if provider == "openai":
        return _extract_with_openai(content, document_type, openai_api_key, openai_model)
    if provider == "azure":
        return _extract_with_azure(content, document_type, azure_openai_endpoint, azure_openai_key, azure_openai_chat_deployment)
    return extract_fields(content, document_type)


def _expected_keys(document_type: str) -> list[str]:
    if document_type == "invoice":
        return ["vendor_name", "invoice_number", "invoice_date", "subtotal", "tax", "total", "currency"]
    if document_type == "contract":
        return ["party_one", "party_two", "effective_date", "expiry_date", "payment_terms", "auto_renewal"]
    return []


def _json_instruction(document_type: str) -> str:
    keys = _expected_keys(document_type)
    if not keys:
        return '{"fields":[]}'
    keys_text = ", ".join(keys)
    return (
        "Extract fields from the document and return strict JSON with this shape: "
        '{"fields":[{"key":"<field_name>","value":"<string>","confidence":<0_to_1_float>}]} '
        f"Only include keys from: {keys_text}. Use empty string and low confidence when missing."
    )


def _normalize_fields(payload: object, document_type: str) -> list[ExtractedField]:
    expected = set(_expected_keys(document_type))
    fields: list[ExtractedField] = []
    if not isinstance(payload, dict):
        return list(extract_fields("", document_type))
    entries = payload.get("fields", [])
    if not isinstance(entries, list):
        entries = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).strip()
        if key not in expected:
            continue
        value = str(item.get("value", "")).strip()
        raw_conf = item.get("confidence", 0.7)
        try:
            confidence = float(raw_conf)
        except (TypeError, ValueError):
            confidence = 0.7
        confidence = max(0.0, min(confidence, 1.0))
        fields.append(ExtractedField(key=key, value=value, confidence=confidence))
    seen = {field.key for field in fields}
    for key in expected - seen:
        fields.append(ExtractedField(key=key, value="", confidence=0.2))
    return fields


def _extract_with_openai(content: str, document_type: str, api_key: str, model: str) -> list[ExtractedField]:
    if not api_key:
        return list(extract_fields(content, document_type))
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _json_instruction(document_type)},
            {"role": "user", "content": content},
        ],
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    raw = data["choices"][0]["message"]["content"]
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    return _normalize_fields(parsed, document_type)


def _extract_with_azure(
    content: str,
    document_type: str,
    endpoint: str,
    api_key: str,
    deployment: str,
) -> list[ExtractedField]:
    if not endpoint or not api_key or not deployment:
        return list(extract_fields(content, document_type))
    url = (
        f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions"
        "?api-version=2024-06-01"
    )
    payload = {
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _json_instruction(document_type)},
            {"role": "user", "content": content},
        ],
    }
    response = requests.post(
        url,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    raw = data["choices"][0]["message"]["content"]
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    return _normalize_fields(parsed, document_type)
