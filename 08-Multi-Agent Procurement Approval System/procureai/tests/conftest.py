import os
import tempfile
import pytest

from app.db.seed import seed_vendors, seed_budgets
from app.db.database import init_db
from app.rag.ingest_policy import ingest_policy_document


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(tmp_path_factory):
    """Initialize an isolated test database with seeded data and ingested policy."""
    tmp = tmp_path_factory.mktemp("procureai_test")
    db_path = str(tmp / "procureai_test.db")
    policy_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "procurement_policy.md"
    )

    os.environ["PROCUREAI_DB_PATH"] = db_path
    os.environ["PROCUREAI_POLICY_PATH"] = policy_path

    init_db()
    seed_vendors()
    seed_budgets()
    ingest_policy_document()

    yield

    os.environ.pop("PROCUREAI_DB_PATH", None)
    os.environ.pop("PROCUREAI_POLICY_PATH", None)
