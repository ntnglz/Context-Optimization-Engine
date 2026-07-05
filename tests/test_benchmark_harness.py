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

    def test_run_n1_n2_en_smoke(self):
        report = run_suite_from_ids(
            profile_id="n1_n2_en",
            tier="smoke",
            benchmark_root=BENCH,
        )
        assert report.cases_run >= 2
        assert report.gate_passed
        assert report.summary["comprehension_similarity_mean"] >= 0.9
        assert "entity:" not in (report.results[0].optimized_context_preview or "")

    def test_n1_n2_en_baseline_compare(self):
        import json

        report = run_suite_from_ids(
            profile_id="n1_n2_en",
            tier="smoke",
            benchmark_root=BENCH,
        )
        baseline = json.loads(
            (BENCH / "baselines" / "n1_n2_en_smoke.json").read_text(encoding="utf-8")
        )
        assert compare_reports(report.to_dict(), baseline) == []


class TestProfile:
    def test_load_n1_profile(self):
        profile = load_profile(BENCH / "profiles" / "n1.yaml")
        assert profile.id == "n1"
        assert profile.levels == [1]
        assert profile.gate.t_coe_p95_ms == 80

    def test_load_n1_n2_en_profile(self):
        profile = load_profile(BENCH / "profiles" / "n1_n2_en.yaml")
        assert profile.id == "n1_n2_en"
        assert profile.levels == [1, 2]
        assert profile.gate.comprehension_similarity == 0.90

    def test_load_n1_n2_es_profile(self):
        profile = load_profile(BENCH / "profiles" / "n1_n2_es.yaml")
        assert profile.id == "n1_n2_es"
        assert profile.levels == [1, 2]
        assert profile.locale == "es"


class TestHarnessMultilingualN2:
    def test_run_n1_n2_es_smoke(self):
        report = run_suite_from_ids(
            profile_id="n1_n2_es",
            tier="smoke",
            tags={"multilingual"},
            benchmark_root=BENCH,
        )
        assert report.cases_run == 1
        assert report.gate_passed
        assert report.summary["comprehension_similarity_mean"] >= 0.9
        assert "entity:" not in (report.results[0].optimized_context_preview or "")

    def test_n1_n2_es_baseline_compare(self):
        import json

        report = run_suite_from_ids(
            profile_id="n1_n2_es",
            tier="smoke",
            tags={"multilingual"},
            benchmark_root=BENCH,
        )
        baseline = json.loads(
            (BENCH / "baselines" / "n1_n2_es_smoke.json").read_text(encoding="utf-8")
        )
        assert compare_reports(report.to_dict(), baseline) == []


class TestHarnessN5Session:
    def test_run_n5_session_smoke(self):
        report = run_suite_from_ids(
            profile_id="n5_session",
            tier="smoke",
            tags={"multi_turn"},
            benchmark_root=BENCH,
        )
        assert report.cases_run == 1
        assert report.gate_passed
        assert "Accumulated session state:" in (
            report.results[0].optimized_context_preview or ""
        )
        assert "entity:" not in (report.results[0].optimized_context_preview or "")

    def test_n5_session_baseline_compare(self):
        import json

        report = run_suite_from_ids(
            profile_id="n5_session",
            tier="smoke",
            tags={"multi_turn"},
            benchmark_root=BENCH,
        )
        baseline = json.loads(
            (BENCH / "baselines" / "n5_session_smoke.json").read_text(encoding="utf-8")
        )
        assert compare_reports(report.to_dict(), baseline) == []


class TestHarnessL0:
    def test_run_l0_n1_en_multilingual(self):
        report = run_suite_from_ids(
            profile_id="l0_n1_en",
            tier="smoke",
            tags={"multilingual"},
            benchmark_root=BENCH,
        )
        assert report.cases_run == 1
        assert report.gate_passed
        preview = report.results[0].optimized_context_preview or ""
        assert "works at ACME" in preview
        assert "trabaja" not in preview

    def test_l0_n1_en_baseline_compare(self):
        import json

        report = run_suite_from_ids(
            profile_id="l0_n1_en",
            tier="smoke",
            tags={"multilingual"},
            benchmark_root=BENCH,
        )
        baseline = json.loads(
            (BENCH / "baselines" / "l0_n1_en_smoke.json").read_text(encoding="utf-8")
        )
        assert compare_reports(report.to_dict(), baseline) == []


class TestHarnessN3:
    def test_run_n1_n2_n3_en_smoke(self):
        report = run_suite_from_ids(
            profile_id="n1_n2_n3_en",
            tier="smoke",
            benchmark_root=BENCH,
        )
        assert report.cases_run >= 2
        assert report.gate_passed
        assert "entity:" not in (report.results[0].optimized_context_preview or "")

    def test_n1_n2_n3_en_baseline_compare(self):
        import json

        report = run_suite_from_ids(
            profile_id="n1_n2_n3_en",
            tier="smoke",
            benchmark_root=BENCH,
        )
        baseline = json.loads(
            (BENCH / "baselines" / "n1_n2_n3_en_smoke.json").read_text(encoding="utf-8")
        )
        assert compare_reports(report.to_dict(), baseline) == []


class TestHarnessN4:
    def test_run_n1_n2_n3_n4_en_smoke(self):
        report = run_suite_from_ids(
            profile_id="n1_n2_n3_n4_en",
            tier="smoke",
            benchmark_root=BENCH,
        )
        assert report.cases_run >= 2
        assert report.gate_passed
        assert "node:" not in (report.results[0].optimized_context_preview or "")

    def test_n1_n2_n3_n4_en_baseline_compare(self):
        import json

        report = run_suite_from_ids(
            profile_id="n1_n2_n3_n4_en",
            tier="smoke",
            benchmark_root=BENCH,
        )
        baseline = json.loads(
            (BENCH / "baselines" / "n1_n2_n3_n4_en_smoke.json").read_text(encoding="utf-8")
        )
        assert compare_reports(report.to_dict(), baseline) == []
