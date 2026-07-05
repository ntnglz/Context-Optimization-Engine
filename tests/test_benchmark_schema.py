"""Validación de casos benchmark contra JSON Schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from coe.benchmark.dataset import load_case, load_cases
from coe.benchmark.validate import load_case_schema, validate_case_dict

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "data" / "benchmarks"
CASES = BENCH / "cases"
SCHEMA = BENCH / "schema" / "case.schema.json"


class TestCaseSchema:
    def test_schema_file_exists(self):
        assert SCHEMA.is_file()
        schema = load_case_schema(SCHEMA)
        assert schema["title"] == "COE Benchmark Case"

    @pytest.mark.parametrize(
        "path",
        sorted(CASES.rglob("*.json")),
        ids=lambda p: str(p.relative_to(CASES)),
    )
    def test_existing_cases_validate(self, path: Path):
        load_case(path)

    def test_regression_cases_load(self):
        cases = load_cases(CASES, tags={"regression"})
        assert len(cases) >= 2

    def test_es_cases_load(self):
        cases = load_cases(CASES, tags={"es"})
        assert len(cases) >= 1

    def test_multi_turn_team_case(self):
        case = load_case(CASES / "multi_turn" / "acme_session_team_v1.json")
        assert case.session is not None
        assert len(case.session.turns) == 3

    def test_invalid_case_rejected(self):
        with pytest.raises(Exception):
            validate_case_dict({"id": "broken"})
