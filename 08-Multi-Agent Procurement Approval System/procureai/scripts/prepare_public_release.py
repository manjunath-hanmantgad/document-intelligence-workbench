"""Prepare a clean public release artifact for ProcureAI.

Usage:
    python scripts/prepare_public_release.py [destination]

Default destination: ../procureai-public
"""

import os
import sys
import shutil


EXCLUDE_DIRS = {
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}

EXCLUDE_FILES = {
    ".env",
    ".DS_Store",
}

EXCLUDE_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".db",
    ".db-shm",
    ".db-wal",
    ".log",
    ".egg-info",
)

# Hidden directories that ARE safe and useful for the public repo
INCLUDE_HIDDEN_DIRS = {".github"}


def _should_exclude_dir(name: str) -> bool:
    if name in EXCLUDE_DIRS:
        return True
    # Skip hidden dirs unless explicitly allowed
    if name.startswith(".") and name not in INCLUDE_HIDDEN_DIRS:
        return True
    return False


def _should_exclude_file(name: str) -> bool:
    if name in EXCLUDE_FILES:
        return True
    if any(name.endswith(suffix) for suffix in EXCLUDE_SUFFIXES):
        return True
    return False


def prepare_public_release(destination: str):
    source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if os.path.exists(destination):
        shutil.rmtree(destination)
    os.makedirs(destination, exist_ok=True)

    copied = []

    for root, dirs, files in os.walk(source_dir):
        # Prune excluded dirs in-place so os.walk doesn't recurse into them
        dirs[:] = [d for d in dirs if not _should_exclude_dir(d)]

        rel_path = os.path.relpath(root, source_dir)
        dest_dir = os.path.join(destination, rel_path)
        os.makedirs(dest_dir, exist_ok=True)

        for file in files:
            if _should_exclude_file(file):
                continue
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_dir, file)
            shutil.copy2(src_file, dst_file)
            rel = os.path.relpath(dst_file, destination)
            copied.append(rel)

    print(f"Public release prepared at: {destination}")
    print(f"Files copied: {len(copied)}")
    for f in sorted(copied):
        print(f"  {f}")

    # Quick sanity checks
    problems = []
    must_exist = [
        "README.md",
        ".env.example",
        ".gitignore",
        ".github/workflows/ci.yml",
        "demo/procureai-dashboard.png",
        "dashboard/app.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "docs/architecture.md",
        "docs/api.md",
        "docs/security.md",
        "docs/deployment.md",
        "docs/evaluation.md",
        "docs/operations.md",
        "docs/production-readiness.md",
    ]
    must_not_exist = [
        ".env",
        "data/procureai.db",
        "data/procureai.db-shm",
        "data/procureai.db-wal",
    ]

    for path in must_exist:
        if not os.path.exists(os.path.join(destination, path)):
            problems.append(f"MISSING: {path}")
    for path in must_not_exist:
        if os.path.exists(os.path.join(destination, path)):
            problems.append(f"SENSITIVE FILE PRESENT: {path}")

    print()
    if problems:
        print("Release validation FAILED:")
        for p in problems:
            print(f"  [FAIL] {p}")
        sys.exit(1)
    else:
        print("Release validation PASSED — artifact is clean.")
        print()
        print("Next steps:")
        print(f"  cd {destination}")
        print("  git init")
        print("  git add .")
        print('  git commit -m "Initial commit: ProcureAI v1.0"')
        print("  git remote add origin <your-github-repo-url>")
        print("  git push -u origin main")


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "procureai-public",
    )
    prepare_public_release(os.path.abspath(dest))
