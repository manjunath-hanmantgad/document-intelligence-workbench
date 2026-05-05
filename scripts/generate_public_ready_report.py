from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts"
REPORT_PATH = ARTIFACT_DIR / "public_ready_report.md"


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    result = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output.strip()


def _exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def _provider_summary(path: Path) -> tuple[str, list[str]]:
    if not _exists(path):
        return "missing", []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "invalid", []
    summary = payload.get("summary", {})
    overall = str(summary.get("overall_status", "unknown"))
    failures: list[str] = []
    for scenario in payload.get("scenarios", []):
        scenario_name = str(scenario.get("scenario", "unknown"))
        for check in scenario.get("checks", []):
            if str(check.get("status")) == "fail":
                failures.append(f"{scenario_name}: {check.get('name')} -> {check.get('detail')}")
    return overall, failures


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    pytest_code, pytest_out = _run(["./venv/bin/pytest", "-q"])
    release_code, release_out = _run(
        ["./venv/bin/python", "scripts/prepare_public_release.py", "--destination", "/private/tmp/document-intelligence-workbench-public"]
    )
    provider_code, provider_out = _run(["./venv/bin/python", "scripts/run_provider_live_checks.py"])

    screenshot_files = [
        ROOT / "examples/workbench-dashboard.png",
        ROOT / "examples/workbench-review-table.png",
        ROOT / "examples/workbench-export.png",
    ]
    provider_artifact = ARTIFACT_DIR / "provider_live_check_output.json"
    docker_artifact = ARTIFACT_DIR / "docker_proof_output.txt"
    provider_overall, provider_failures = _provider_summary(provider_artifact)

    lines: list[str] = []
    lines.append("# Public-Ready Report Artifact")
    lines.append("")
    lines.append(f"- generated_at_utc: `{datetime.now(tz=timezone.utc).isoformat()}`")
    lines.append("")
    lines.append("## Validation Summary")
    lines.append(f"- pytest: `{'pass' if pytest_code == 0 else 'fail'}`")
    lines.append(f"- public release packaging: `{'pass' if release_code == 0 else 'fail'}`")
    lines.append(f"- provider live-check artifact: `{'pass' if provider_code == 0 else 'fail'}`")
    lines.append(f"- provider live-check overall status: `{provider_overall}`")
    lines.append("")
    lines.append("## Screenshot Assets")
    for file_path in screenshot_files:
        lines.append(f"- `{file_path.relative_to(ROOT)}`: `{'present' if _exists(file_path) else 'missing'}`")
    lines.append("")
    lines.append("## Artifacts")
    lines.append(f"- provider output: `{provider_artifact.relative_to(ROOT)}` (`{'present' if _exists(provider_artifact) else 'missing'}`)")
    lines.append(f"- docker proof output: `{docker_artifact.relative_to(ROOT)}` (`{'present' if _exists(docker_artifact) else 'missing'}`)")
    if not _exists(docker_artifact):
        lines.append("- docker proof status: `pending` (run `scripts/capture_docker_proof.sh` on a Docker-enabled machine)")
    lines.append("")
    lines.append("## Command Outputs")
    lines.append("### pytest")
    lines.append("```text")
    lines.append(pytest_out or "(no output)")
    lines.append("```")
    lines.append("")
    lines.append("### prepare_public_release")
    lines.append("```text")
    lines.append(release_out or "(no output)")
    lines.append("```")
    lines.append("")
    lines.append("### provider_live_checks")
    lines.append("```text")
    lines.append(provider_out or "(no output)")
    lines.append("```")
    if provider_failures:
        lines.append("")
        lines.append("### provider_live_check_failures")
        for failure in provider_failures:
            lines.append(f"- {failure}")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Public-ready report artifact written: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
