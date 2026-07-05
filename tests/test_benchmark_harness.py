"""Tests del harness de benchmarks (sin LLM ni red)."""

from pathlib import Path

from coe.benchmark.arms import render_arm_a_context
from coe.benchmark.dataset import load_case
from coe.benchmark.profile import load_profile
from coe.benchmark.report import compare_reports
from coe.benchmark.runner import run_suite_from_ids
from coe.benchmark.scorers.artifacts import detect_artifact_leak
from coe.benchmark.scorers.factual import factual_recall

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "data" / "benchmarks"


class TestScorers:
    def test_factual_recall(self):
        assert factual_recall("Juan approved the budget", ["Juan", "budget"]) == 1.0
        assert factual_recall("Pedro did it", ["Juan"]) == 0.0

    def test_artifact_leak(self):
        assert detect_artifact_leak("Juan works at ACME.") is False
        assert detect_artifact_leak("entity:Juan company=ACME") is True


class TestHarnessSmoke:
    def test_arm_a_raw(self):
        case = load_case(BENCH / "cases" / "core" / "acme_budget_v1.json")
        raw = render_arm_a_context(case)
        assert "[A]" in raw
        assert "ACME" in raw
        assert "Empresa=ACME" not in raw

    def test_run_n1_smoke(self):
        report = run_suite_from_ids(
            profile_id="n1",
            tier="smoke",
            benchmark_root=BENCH,
        )
        assert report.cases_run >= 2
        assert report.gate_passed
        assert report.summary["artifact_leak_rate"] == 0.0

    def test_compare_no_regression(self):
        report = run_suite_from_ids(profile_id="n1", tier="smoke", benchmark_root=BENCH)
        data = report.to_dict()
        assert compare_reports(data, data) == []


class TestProfile:
    def test_load_n1_profile(self):
        profile = load_profile(BENCH / "profiles" / "n1.yaml")
        assert profile.id == "n1"
        assert profile.levels == [1]
        assert profile.gate.t_coe_p95_ms == 80
