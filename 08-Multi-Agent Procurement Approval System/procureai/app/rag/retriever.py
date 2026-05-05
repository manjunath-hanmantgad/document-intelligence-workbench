from typing import List, Optional

from app.db.database import get_connection
from app.schemas.policy import PolicyChunk


def search_policy_docs(query: str, top_k: int = 3) -> List[PolicyChunk]:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT chunk_id, content, source_clause FROM policy_embeddings"
    )
    rows = cursor.fetchall()
    conn.close()

    query_lower = query.lower()
    query_terms = query_lower.split()

    scored = []
    for row in rows:
        content_lower = row["content"].lower()
        score = sum(1 for term in query_terms if term in content_lower)
        if score > 0:
            scored.append(PolicyChunk(
                chunk_id=row["chunk_id"],
                content=row["content"],
                source_clause=row["source_clause"],
                score=score / max(len(query_terms), 1),
            ))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]


def get_policy_clause(clause_id: str) -> Optional[PolicyChunk]:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT chunk_id, content, source_clause FROM policy_embeddings WHERE source_clause = ?",
        (clause_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return PolicyChunk(
            chunk_id=row["chunk_id"],
            content=row["content"],
            source_clause=row["source_clause"],
        )
    return None
