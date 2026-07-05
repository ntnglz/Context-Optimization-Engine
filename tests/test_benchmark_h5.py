"""Tests H5 — multi-turn, multilingual, tier config."""

from pathlib import Path

import pytest

from coe.benchmark.case_utils import (
    context_blocks,
    effective_expected_facts,
    effective_question,
    is_multi_turn,
)
from coe.benchmark.dataset import load_case, load_cases
from coe.benchmark.report import aggregate_reports
from coe.benchmark.runner import run_suite_from_ids
from coe.benchmark.tier_config import default_tags_for_tier

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "data" / "benchmarks"


class TestMultiTurnCase:
    def test_load_session_case(self):
        case = load_case(BENCH / "cases" / "multi_turn" / "acme_session_budget_v1.json")
        assert is_multi_turn(case)
        assert effective_question(case) == "What is the ACME budget now?"
        assert "50k" in effective_expected_facts(case)
        assert len(context_blocks(case)) == 3

    def test_session_pipeline_smoke_mock(self):
        report = run_suite_from_ids(
            profile_id="n5_session",
            tier="smoke",
            tags={"multi_turn"},
            benchmark_root=BENCH,
        )
        assert report.cases_run == 1
        assert report.gate_passed


class TestDevAgentCase:
    def test_load_dev_warnings_session(self):
        case = load_case(BENCH / "cases" / "dev_agent" / "dev_warnings_session_v1.json")
        assert is_multi_turn(case)
        assert "dev_agent" in case.tags
        assert case.response_lang == "es"
        assert effective_question(case) == (
            "Tras compilar para macOS, ¿cuántos warnings quedan y de qué tipo?"
        )
        assert "AppIntents" in effective_expected_facts(case)
        assert len(context_blocks(case)) == 4

    def test_dev_warnings_n5_graph_smoke_mock(self):
        report = run_suite_from_ids(
            profile_id="n5_graph_session",
            tier="smoke",
            tags={"dev_agent"},
            benchmark_root=BENCH,
        )
        assert report.cases_run == 1
        assert report.gate_passed
        assert report.results[0].case_id == "dev_warnings_session_v1"


class TestMultilingualCase:
    def test_load_es_case(self):
        case = load_case(BENCH / "cases" / "multilingual" / "acme_budget_es_v1.json")
        assert "multilingual" in case.tags
        assert case.response_lang == "es"

    def test_n1_es_profile_mock(self):
        report = run_suite_from_ids(
            profile_id="n1_es",
            tier="smoke",
            tags={"multilingual"},
            benchmark_root=BENCH,
        )
        assert report.cases_run == 1
        assert report.summary.get("user_language_match_rate") == 1.0

    def test_n1_n2_es_profile_mock(self):
        report = run_suite_from_ids(
            profile_id="n1_n2_es",
            tier="smoke",
            tags={"multilingual"},
            benchmark_root=BENCH,
        )
        assert report.cases_run == 1
        assert report.gate_passed
        assert "trabaja en ACME" in (report.results[0].optimized_context_preview or "")


class TestTierConfig:
    def test_smoke_tags(self):
        assert default_tags_for_tier("smoke") == {"core"}

    def test_nightly_tags(self):
        assert default_tags_for_tier("nightly") == {"single_turn"}

    def test_release_tags_all(self):
        assert default_tags_for_tier("release") is None

    def test_nightly_case_filter(self):
        cases = load_cases(BENCH / "cases", tags=default_tags_for_tier("nightly"))
        ids = {c.id for c in cases}
        assert "acme_budget_v1" in ids
        assert "acme_session_budget_v1" not in ids


class TestAggregateReports:
    def test_average_summary(self):
        base = run_suite_from_ids(profile_id="n1", tier="smoke", benchmark_root=BENCH)
        merged = aggregate_reports([base, base])
        assert merged.summary["factual_recall_mean"] == base.summary["factual_recall_mean"]
        assert merged.metadata.get("runs") == 2

    def test_runs_cli(self):
        report = run_suite_from_ids(
            profile_id="n1",
            tier="smoke",
            benchmark_root=BENCH,
            runs=2,
        )
        assert report.metadata.get("runs") == 2
