"""Tests H4 — evaluadores Ollama, arms, readability."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from coe.benchmark.arms import build_answer_messages, render_arm_a_context
from coe.benchmark.dataset import load_case
from coe.benchmark.evaluators.base import Message, parse_evaluator_spec
from coe.benchmark.evaluators.factory import create_evaluator
from coe.benchmark.evaluators.ollama import OllamaEvaluator
from coe.benchmark.scorers.language import user_language_match
from coe.benchmark.scorers.readability import judge_readability, parse_readability_score

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "data" / "benchmarks"


class TestEvaluatorSpec:
    def test_parse_mock(self):
        assert parse_evaluator_spec("mock") == ("mock", None)

    def test_parse_ollama_model(self):
        assert parse_evaluator_spec("ollama:llama3") == ("ollama", "llama3")

    def test_create_mock(self):
        evaluator, eid = create_evaluator("mock")
        assert evaluator is None
        assert eid == "mock"


class TestArmsMessages:
    def test_build_messages_same_system(self):
        case = load_case(BENCH / "cases" / "core" / "acme_budget_v1.json")
        raw = render_arm_a_context(case)
        msgs_a = build_answer_messages(case, raw)
        msgs_b = build_answer_messages(case, "optimized context")
        assert msgs_a[0].content == msgs_b[0].content
        assert "Who approved" in msgs_a[1].content
        assert "[A]" in msgs_a[1].content
        assert "optimized context" in msgs_b[1].content


class TestOllamaEvaluator:
    def test_complete_parses_response(self, monkeypatch):
        payload = {"message": {"content": "Juan approved the budget."}}

        def fake_urlopen(request, timeout=0):
            response = MagicMock()
            response.read.return_value = json.dumps(payload).encode("utf-8")
            response.__enter__ = lambda s: s
            response.__exit__ = MagicMock(return_value=False)
            return response

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        evaluator = OllamaEvaluator(model="test-model", host="http://127.0.0.1:11434")
        result = evaluator.complete([Message("user", "hi")])
        assert result.text == "Juan approved the budget."
        assert result.model == "test-model"


class TestReadabilityJudge:
    def test_parse_score(self):
        assert parse_readability_score("SCORE: 4.5") == 4.5
        assert parse_readability_score("The score is 3") == 3.0
        assert parse_readability_score("no score here") is None

    def test_judge_readability_with_fake_evaluator(self):
        case = load_case(BENCH / "cases" / "core" / "acme_budget_v1.json")

        class FakeEval:
            def complete(self, messages, *, temperature=0.0):
                from coe.benchmark.evaluators.base import LLMResult

                return LLMResult(text="SCORE: 4")

        score = judge_readability(FakeEval(), case, "Juan approved the budget.")
        assert score == 4.0


class TestLanguageScorer:
    def test_english_fallback(self):
        assert user_language_match("Juan approved the budget.", "en") is True
