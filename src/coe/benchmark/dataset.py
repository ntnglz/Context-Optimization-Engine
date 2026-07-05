"""Carga y filtrado de casos de benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from .schema import BenchmarkCase
from .validate import validate_case_dict


def load_case(path: Path) -> BenchmarkCase:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_case_dict(data)
    return BenchmarkCase.from_dict(data)


def load_cases(
    cases_dir: Path,
    *,
    tags: set[str] | None = None,
) -> list[BenchmarkCase]:
    paths = sorted(cases_dir.rglob("*.json"))
    cases: list[BenchmarkCase] = []
    for path in paths:
        if path.name.startswith("."):
            continue
        case = load_case(path)
        if tags and not tags.intersection(case.tags):
            continue
        cases.append(case)
    return cases
