from typing import List

from app.db.database import get_connection
from app.schemas.vendor import VendorRecord, VendorStatus


class VendorAgent:

    def __init__(self):
        self.name = "VendorAgent"
        self.description = "Checks whether vendor is approved or risky"

    def lookup_vendor(self, vendor_name: str) -> VendorRecord:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT vendor_id, vendor_name, status, risk_level, categories FROM vendors WHERE vendor_name = ?",
            (vendor_name,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return VendorRecord(
                vendor_id=row["vendor_id"],
                vendor_name=row["vendor_name"],
                status=row["status"],
                risk_level=row["risk_level"],
                categories=row["categories"].split(",") if row["categories"] else [],
            )
        return VendorRecord(
            vendor_id="UNKNOWN",
            vendor_name=vendor_name,
            status="unknown",
            risk_level="unknown",
            categories=[],
        )

    def check_vendor_status(self, vendor_name: str) -> VendorStatus:
        vendor = self.lookup_vendor(vendor_name)
        risk_flags: List[str] = []

        if vendor.status == "blacklisted" or vendor.status == "banned":
            risk_flags.append(f"Vendor {vendor_name} is {vendor.status}.")
        elif vendor.status == "pending":
            risk_flags.append(f"Vendor {vendor_name} is pending approval.")
        elif vendor.status == "unknown":
            risk_flags.append(f"Vendor {vendor_name} is not found in vendor master.")

        if vendor.risk_level == "high":
            risk_flags.append("High-risk vendor requires finance and compliance review.")

        return VendorStatus(
            vendor_status=vendor.status,
            vendor_id=vendor.vendor_id,
            risk_flags=risk_flags,
            risk_level=vendor.risk_level,
        )
