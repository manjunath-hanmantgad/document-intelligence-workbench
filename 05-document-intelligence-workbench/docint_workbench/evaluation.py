from __future__ import annotations

import json
from pathlib import Path

from docint_workbench.extraction import detect_document_type, extract_fields
from docint_workbench.schemas import EvaluationCase, EvaluationResult


def run_evaluation(evaluation_path: Path) -> EvaluationResult:
    cases_json = json.loads(evaluation_path.read_text(encoding="utf-8"))
    cases = [EvaluationCase.model_validate(case) for case in cases_json]

    passed = 0
    match_rates: list[float] = []
    for case in cases:
        doc_type = detect_document_type(case.content, case.document_type)
        field_map = {field.key: field.value for field in extract_fields(case.content, doc_type)}
        expected = case.expected_fields
        match_count = sum(1 for key, value in expected.items() if field_map.get(key, "") == value)
        rate = match_count / max(len(expected), 1)
        match_rates.append(rate)
        if rate == 1.0:
            passed += 1

    average_match_rate = sum(match_rates) / max(len(match_rates), 1)
    pass_rate = passed / max(len(cases), 1)
    return EvaluationResult(
        total_cases=len(cases),
        passed_cases=passed,
        pass_rate=round(pass_rate, 3),
        average_field_match_rate=round(average_match_rate, 3),
    )
