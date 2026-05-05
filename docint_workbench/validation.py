from __future__ import annotations

from datetime import date

from docint_workbench.extraction import ExtractedField


def _to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def validate_invoice(fields: list[ExtractedField]) -> list[tuple[str, str]]:
    data = {field.key: field.value for field in fields}
    subtotal = _to_float(data.get("subtotal", ""))
    tax = _to_float(data.get("tax", ""))
    total = _to_float(data.get("total", ""))
    expected_total = round(subtotal + tax, 2)

    if not subtotal and not tax and not total:
        return [("fail", "Invoice totals not detected")]
    if abs(expected_total - total) > 0.01:
        return [(
            "fail",
            f"Invoice total mismatch: expected {expected_total:.2f} from subtotal + tax but found {total:.2f}",
        )]
    return [("pass", "Invoice total validation passed")]


def validate_contract(fields: list[ExtractedField]) -> list[tuple[str, str]]:
    data = {field.key: field.value for field in fields}
    effective = data.get("effective_date", "")
    expiry = data.get("expiry_date", "")
    if not effective or not expiry:
        return [("fail", "Contract dates are incomplete")]

    try:
        effective_date = date.fromisoformat(effective)
        expiry_date = date.fromisoformat(expiry)
    except ValueError:
        return [("fail", "Contract dates must use ISO format YYYY-MM-DD")]

    if expiry_date <= effective_date:
        return [("fail", "Contract expiry date must be after effective date")]
    return [("pass", "Contract date validation passed")]


def validate_fields(document_type: str, fields: list[ExtractedField]) -> list[tuple[str, str]]:
    if document_type == "invoice":
        return validate_invoice(fields)
    if document_type == "contract":
        return validate_contract(fields)
    return [("fail", "Document type does not have a validation profile")]
