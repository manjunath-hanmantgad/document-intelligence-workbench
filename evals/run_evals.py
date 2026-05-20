#!/usr/bin/env python3
"""Eval runner for Document Intelligence Workbench."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docint_workbench.extraction import ExtractedField, _find, detect_document_type, extract_fields
from docint_workbench.validation import validate_fields


def run_extraction(case: dict) -> tuple[bool, str]:
    payload = case["input"]
    expected = case["expected"]
    detected = detect_document_type(payload["content"], payload["requested_type"])
    fields = {field.key: field.value for field in extract_fields(payload["content"], detected)}

    expected_fields = expected.get("fields", {})
    matched = all(fields.get(key, "") == value for key, value in expected_fields.items())
    passed = matched and detected == expected["document_type"]
    detail = f"detected={detected} extracted_subset={expected_fields}"
    return passed, detail


def run_validation(case: dict) -> tuple[bool, str]:
    payload = case["input"]
    expected = case["expected"]
    fields = [ExtractedField(key=key, value=value, confidence=1.0) for key, value in payload["fields"].items()]
    outcome = validate_fields(payload["document_type"], fields)
    status, message = outcome[0]

    passed = status == expected["status"] and expected["message_contains"].lower() in message.lower()
    detail = f"status={status} message={message}"
    return passed, detail


def run_confidence(case: dict) -> tuple[bool, str]:
    payload = case["input"]
    expected = case["expected"]

    field = _find(payload["pattern"], payload["text"], payload["key"])
    reliable = field.confidence >= float(payload["threshold"])
    passed = reliable == bool(expected["reliable"]) and abs(field.confidence - float(expected["confidence"])) <= 1e-9
    detail = f"confidence={field.confidence} reliable={reliable}"
    return passed, detail


def main() -> int:
    dataset_path = Path(__file__).with_name("golden_dataset.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    runners = {
        "extraction": run_extraction,
        "validation": run_validation,
        "confidence": run_confidence,
    }

    executed = 0
    passed = 0
    skipped = 0
    failures: list[tuple[str, str]] = []

    for case in dataset["cases"]:
        case_id = case["id"]
        if case.get("requires_live_llm", False):
            skipped += 1
            print(f"[SKIP] {case_id} requires live LLM")
            continue

        runner = runners.get(case["category"])
        if runner is None:
            executed += 1
            failures.append((case_id, f"unsupported category: {case['category']}"))
            print(f"[FAIL] {case_id} unsupported category")
            continue

        ok, detail = runner(case)
        executed += 1
        if ok:
            passed += 1
            print(f"[PASS] {case_id} {detail}")
        else:
            failures.append((case_id, detail))
            print(f"[FAIL] {case_id} {detail}")

    print("\nSummary")
    print(f"Executed: {executed}")
    print(f"Passed:   {passed}")
    print(f"Skipped:  {skipped}")
    print(f"Failed:   {len(failures)}")

    if failures:
        print("\nFailed cases:")
        for case_id, detail in failures:
            print(f"- {case_id}: {detail}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
