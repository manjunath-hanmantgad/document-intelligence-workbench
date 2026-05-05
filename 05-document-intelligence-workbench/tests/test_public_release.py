from pathlib import Path

from scripts.prepare_public_release import copy_project, validate


def test_public_release_preparation(tmp_path: Path) -> None:
    destination = tmp_path / "artifact"
    copy_project(destination)
    errors = validate(destination)
    assert not errors

    assert (destination / "README.md").exists()
    assert not (destination / ".env").exists()
