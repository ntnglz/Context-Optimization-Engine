"""Tests de scorers H3 (factual F1, embedding, compare)."""

import pytest

from coe.benchmark.report import compare_reports, compare_reports_detailed
from coe.benchmark.scorers.embedding import comprehension_similarity
from coe.benchmark.scorers.factual import (
    comprehension_delta,
    factual_f1,
    factual_recall,
    factual_scores,
)


class TestFactualScorers:
    def test_factual_scores_full_match(self):
        f1, precision, recall = factual_scores(
            "Juan approved the budget",
            ["Juan", "approved", "budget"],
        )
        assert recall == 1.0
        assert precision == 1.0
        assert f1 == 1.0

    def test_factual_f1_partial(self):
        assert factual_recall("Juan approved", ["Juan", "budget"]) == 0.5
        assert factual_f1("Juan approved", ["Juan", "budget"]) > 0.5

    def test_comprehension_delta(self):
        assert comprehension_delta(1.0) == 0.0
        assert comprehension_delta(0.85) == pytest.approx(-0.15)


class TestEmbeddingScorer:
    def test_identical_responses(self):
        text = "Juan approved the budget."
        assert comprehension_similarity(text, text, backend="simple") == 1.0

    def test_different_responses_lower(self):
        sim = comprehension_similarity(
            "Juan approved the budget.",
            "Pedro rejected the proposal.",
            backend="simple",
        )
        assert sim < 0.5

    def test_near_duplicate_high_similarity(self):
        sim = comprehension_similarity(
            "Juan approved the budget",
            "Juan approved the budget.",
            backend="simple",
        )
        assert sim >= 0.9


class TestCompareReports:
    def test_no_regression_when_equal(self):
        summary = {
            "summary": {
                "factual_recall_mean": 1.0,
                "comprehension_similarity_mean": 0.95,
                "comprehension_delta_mean": -0.05,
                "t_coe_p95_ms": 0.04,
                "artifact_leak_rate": 0.0,
            }
        }
        assert compare_reports(summary, summary) == []

    def test_similarity_regression_detected(self):
        current = {"summary": {"comprehension_similarity_mean": 0.80}}
        baseline = {"summary": {"comprehension_similarity_mean": 0.95}}
        detailed = compare_reports_detailed(current, baseline)
        assert len(detailed) == 1
        assert detailed[0]["metric"] == "comprehension_similarity_mean"

    def test_latency_regression_detected(self):
        current = {"summary": {"t_coe_p95_ms": 100.0}}
        baseline = {"summary": {"t_coe_p95_ms": 50.0}}
        assert "t_coe_p95_ms regressed" in compare_reports(current, baseline)[0]
