"""Evaluador mock — respuestas prefijadas en el caso."""

from __future__ import annotations

from ..schema import BenchmarkCase, MockFixture


def mock_responses(case: BenchmarkCase) -> MockFixture:
    if case.mock is None:
        raise ValueError(f"Case {case.id} has no mock fixture (required for tier smoke/ci)")
    return case.mock
