import os
import sys
import shutil


def prepare_public_release(destination: str):
    """Prepare a clean public release artifact."""
    source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if os.path.exists(destination):
        shutil.rmtree(destination)

    exclude = {
        ".venv", "__pycache__", "*.pyc", "*.db",
        ".env", ".pytest_cache", ".ruff_cache",
    }

    def should_exclude(name: str) -> bool:
        for pattern in exclude:
            if pattern.startswith("*"):
                if name.endswith(pattern[1:]):
                    return True
            elif name == pattern:
                return True
        return False

    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        if rel_path.startswith("."):
            continue
        if should_exclude(os.path.basename(root)):
            continue

        dest_dir = os.path.join(destination, rel_path)
        os.makedirs(dest_dir, exist_ok=True)

        for file in files:
            if should_exclude(file):
                continue
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_dir, file)
            shutil.copy2(src_file, dst_file)

    print(f"Public release prepared at: {destination}")
    print("Files copied:")
    for root, dirs, files in os.walk(destination):
        for file in files:
            rel = os.path.relpath(os.path.join(root, file), destination)
            print(f"  {rel}")


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "../procureai-public"
    prepare_public_release(os.path.abspath(dest))
