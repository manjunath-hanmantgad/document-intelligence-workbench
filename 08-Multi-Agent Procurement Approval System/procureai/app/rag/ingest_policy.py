import hashlib
import os
from typing import List

from app.schemas.policy import PolicyChunk


POLICY_PATH = os.environ.get("PROCUREAI_POLICY_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "data", "procurement_policy.md"))

CHUNK_SEPARATORS = [
    "## Approval Thresholds",
    "## Vendor Policy",
    "## Category Policy",
    "## Duplicate Policy",
    "## Compliance",
]


def chunk_policy_document(text: str) -> List[dict]:
    chunks = []
    lines = text.split("\n")
    current_section = "general"
    current_clause = None
    current_lines = []

    for line in lines:
        if line.startswith("## "):
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    chunk_id = hashlib.md5(content.encode()).hexdigest()[:12]
                    chunks.append({
                        "chunk_id": f"POL-{chunk_id}",
                        "content": content,
                        "source_clause": current_clause,
                    })
            current_section = line.strip("# ")
            current_clause = f"PROC-{current_section.upper().replace(' ', '_')}"
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            chunk_id = hashlib.md5(content.encode()).hexdigest()[:12]
            chunks.append({
                "chunk_id": f"POL-{chunk_id}",
                "content": content,
                "source_clause": current_clause,
            })

    return chunks


def ingest_policy_document():
    from app.db.database import get_connection

    if not os.path.exists(POLICY_PATH):
        raise FileNotFoundError(f"Policy document not found at {POLICY_PATH}")

    with open(POLICY_PATH) as f:
        text = f.read()

    chunks = chunk_policy_document(text)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS policy_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            source_clause TEXT,
            embedding BLOB
        )
    """)
    for chunk in chunks:
        conn.execute(
            "INSERT OR REPLACE INTO policy_embeddings (chunk_id, content, source_clause) VALUES (?, ?, ?)",
            (chunk["chunk_id"], chunk["content"], chunk["source_clause"]),
        )
    conn.commit()
    conn.close()
    print(f"Ingested {len(chunks)} policy chunks.")
    return chunks


if __name__ == "__main__":
    ingest_policy_document()
