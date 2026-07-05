"""Tests Model Adapter — registro, adaptadores y Gateway."""

from __future__ import annotations

from coe import optimize_context
from coe.model_adapter import adapt_for_model, resolve_adapter_id
from coe.model_adapter.adapters import MistralAdapter, OpenAIAdapter
from coe.models import ContextBlock


SAMPLE_TEXT = "--- session state ---\nJuan works at ACME.\n\n--- context ---\nBudget: 50k.\n"

BLOCKS = [
    ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
    ContextBlock(id="B", content="Empresa: ACME\nPresupuesto: 50k"),
    ContextBlock(id="C", content="Empresa: ACME\nCliente: Globex"),
]


class TestModelAdapterRegistry:
    def test_resolve_mistral_and_openai(self):
        assert resolve_adapter_id("mistral-large") == "mistral"
        assert resolve_adapter_id("gpt-4o") == "openai"
        assert resolve_adapter_id(None) is None

    def test_mistral_and_openai_outputs_differ(self):
        mistral, mid = adapt_for_model(SAMPLE_TEXT, "mistral-large")
        openai, oid = adapt_for_model(SAMPLE_TEXT, "gpt-4o")

        assert mid == "mistral"
        assert oid == "openai"
        assert mistral != openai
        assert "[AVAILABLE CONTEXT]" in mistral
        assert "<optimized_context>" in openai
        assert "## Session State" in openai
        assert "[session state]" in mistral.lower() or "[Session State]" in mistral

    def test_adapters_preserve_semantic_content(self):
        mistral = MistralAdapter().adapt(SAMPLE_TEXT, "mistral")
        openai = OpenAIAdapter().adapt(SAMPLE_TEXT, "gpt-4")

        assert "ACME" in mistral
        assert "50k" in mistral
        assert "ACME" in openai
        assert "50k" in openai


class TestGatewayModelAdapter:
    def test_no_target_model_skips_adapter(self):
        out = optimize_context(BLOCKS, levels=[1], locale="en")
        assert out.metrics.model_adapter is None
        assert out.metrics.target_model is None
        assert "<optimized_context>" not in out.text

    def test_mistral_target_model_in_metrics_and_text(self):
        out = optimize_context(
            BLOCKS,
            levels=[1, 5],
            locale="en",
            session_id="ma-mistral",
            include_pending_turn=True,
            target_model="mistral-large",
        )
        assert out.metrics.target_model == "mistral-large"
        assert out.metrics.model_adapter == "mistral"
        assert "[AVAILABLE CONTEXT]" in out.text
        assert "model_adapter" in out.metrics.latency_ms_by_level
        assert any("model_adapter:mistral" in t.detail for t in out.trace)

    def test_openai_target_model_differs_from_mistral(self):
        base = optimize_context(BLOCKS, levels=[1], locale="en", target_model="mistral")
        openai = optimize_context(BLOCKS, levels=[1], locale="en", target_model="gpt-4o")

        assert base.text != openai.text
        assert openai.metrics.model_adapter == "openai"
        assert "<optimized_context>" in openai.text
