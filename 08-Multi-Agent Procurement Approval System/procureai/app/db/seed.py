import json
import csv
import os
from app.db.database import get_connection


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def seed_vendors():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id TEXT PRIMARY KEY,
            vendor_name TEXT NOT NULL,
            status TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            categories TEXT NOT NULL
        )
    """)
    with open(os.path.join(DATA_DIR, "vendor_master.csv")) as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                "INSERT OR REPLACE INTO vendors (vendor_id, vendor_name, status, risk_level, categories) VALUES (?, ?, ?, ?, ?)",
                (row["vendor_id"], row["vendor_name"], row["status"], row["risk_level"], row["categories"]),
            )
    conn.commit()
    print(f"Seeded vendors from {DATA_DIR}/vendor_master.csv")


def seed_budgets():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS department_budgets (
            department TEXT PRIMARY KEY,
            total_budget REAL NOT NULL,
            spent_budget REAL NOT NULL
        )
    """)
    with open(os.path.join(DATA_DIR, "department_budget.csv")) as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                "INSERT OR REPLACE INTO department_budgets (department, total_budget, spent_budget) VALUES (?, ?, ?)",
                (row["department"], float(row["total_budget"]), float(row["spent_budget"])),
            )
    conn.commit()
    print(f"Seeded budgets from {DATA_DIR}/department_budget.csv")


def seed_sample_requests():
    conn = get_connection()
    from app.db.database import init_db
    init_db()
    with open(os.path.join(DATA_DIR, "sample_requests.json")) as f:
        requests = json.load(f)
        for req in requests:
            conn.execute(
                "INSERT OR IGNORE INTO purchase_requests (request_id, department, requester, vendor, category, amount, justification, urgency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (req["request_id"], req["department"], req["requester"], req["vendor"], req["category"], req["amount"], req["justification"], req["urgency"]),
            )
    conn.commit()
    print(f"Seeded {len(requests)} sample requests from {DATA_DIR}/sample_requests.json")


def seed_all():
    seed_vendors()
    seed_budgets()
    seed_sample_requests()
    print("All data seeded successfully.")


if __name__ == "__main__":
    seed_all()
