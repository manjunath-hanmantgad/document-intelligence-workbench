from __future__ import annotations

from pathlib import Path

from docint_workbench.config import get_settings
from docint_workbench.service import DocumentWorkbenchService


INVOICE_CONTENT = """Vendor: Apex Office Supplies
Invoice Number: INV-2026-0042
Invoice Date: 2026-04-29
Subtotal: 1250.00
Tax: 125.00
Total: 1375.00
Currency: USD
"""

CONTRACT_CONTENT = """Party 1: Northwind Logistics
Party 2: Skyline Procurement Services
Effective Date: 2026-01-01
Expiry Date: 2027-01-01
Payment Terms: Net 30
Auto Renewal: No
"""


def main() -> int:
    settings = get_settings()
    service = DocumentWorkbenchService(
        database_path=settings.database_path,
        low_confidence_threshold=settings.low_confidence_threshold,
        evaluation_set_path=Path("examples/evaluation_set.json"),
    )
    service.process_document("invoice-record.txt", INVOICE_CONTENT, "invoice")
    service.process_document("contract-record.txt", CONTRACT_CONTENT, "contract")
    print("Seed data ingested into", settings.database_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
