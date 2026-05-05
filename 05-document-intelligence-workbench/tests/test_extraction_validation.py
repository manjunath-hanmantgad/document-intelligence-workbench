from docint_workbench.extraction import detect_document_type, extract_fields
from docint_workbench.validation import validate_fields


def test_invoice_extraction_and_validation() -> None:
    content = """Vendor: Apex Office Supplies
Invoice Number: INV-2026-0042
Invoice Date: 2026-04-29
Subtotal: 1250.00
Tax: 125.00
Total: 1375.00
Currency: USD
"""
    doc_type = detect_document_type(content, "unknown")
    assert doc_type == "invoice"

    fields = list(extract_fields(content, doc_type))
    field_map = {field.key: field.value for field in fields}
    assert field_map["invoice_number"] == "INV-2026-0042"
    assert field_map["total"] == "1375.00"

    validations = validate_fields(doc_type, fields)
    assert validations[0][0] == "pass"


def test_contract_validation_fails_when_dates_invalid() -> None:
    content = """Party 1: Northwind Logistics
Party 2: Skyline Procurement Services
Effective Date: 2027-01-01
Expiry Date: 2026-01-01
Payment Terms: Net 30
Auto Renewal: No
"""
    fields = list(extract_fields(content, "contract"))
    validations = validate_fields("contract", fields)
    assert validations[0][0] == "fail"
