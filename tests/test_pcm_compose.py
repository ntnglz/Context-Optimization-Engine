"""Tests composición PCM+COE (Fase 11)."""

from unittest.mock import patch

import pytest

from coe import optimize_with_pcm
from coe.budget import allocate_coe_budget
from coe.models import ContextBlock
from coe.pcm import StubInstructionCompressor, ensure_pcm_importable, get_instruction_compressor
from coe.pcm.loader import default_pcm_src_path


class TestWindowBudget:
    def test_allocate_coe_budget(self):
        alloc = allocate_coe_budget(
            max_window_tokens=8192,
            instruction_tokens=24,
            response_reserve=512,
        )
        assert alloc.coe_budget_tokens == 8192 - 24 - 512
        assert alloc.instruction_tokens == 24


class TestPCMBackends:
    def test_stub_compresses_acme_question(self):
        result = StubInstructionCompressor().compress("Who works at ACME?")
        assert result.compressed.startswith("TASK=")
        assert result.skipped is False
        assert result.backend == "stub"

    def test_pcm_loader_finds_sibling_repo(self):
        path = default_pcm_src_path()
        assert path.is_dir()
        assert (path / "pcm" / "compressor.py").is_file()


class TestOptimizeWithPCM:
    def test_compose_returns_messages_and_window(self):
        blocks = [
            ContextBlock(id="A", content="Empresa: ACME\nJuan works at ACME."),
            ContextBlock(id="B", content="Empresa: ACME\nPedro works at ACME."),
        ]
        out = optimize_with_pcm(
            blocks,
            user_instruction="Who works at ACME?",
            levels=[1],
            locale="en",
            max_window_tokens=4096,
            response_reserve=256,
            pcm_backend="stub",
        )

        assert out.instruction.compressed.startswith("TASK=")
        assert "Juan" in out.context.text
        assert out.window.coe_budget_tokens == 4096 - out.instruction.compressed_tokens - 256
        assert len(out.messages) == 2
        assert out.messages[0]["role"] == "system"
        assert "TASK=" in out.messages[0]["content"]
        assert "Context:" in out.messages[1]["content"]

    def test_window_truncates_large_context(self):
        blocks = [
            ContextBlock(
                id=f"b{i}",
                content=f"Empresa: ACME — bloque {i} con relleno repetido.",
            )
            for i in range(40)
        ]
        out = optimize_with_pcm(
            blocks,
            user_instruction="Who works at ACME?",
            levels=[1],
            locale="en",
            max_window_tokens=200,
            response_reserve=32,
            pcm_backend="stub",
        )
        assert out.context.metrics.truncated is True
        assert out.window.truncated is True
        assert out.context.metrics.optimized_tokens <= out.window.coe_budget_tokens + 2


def test_build_pcm_messages_includes_response_block_when_pcm_installed():
    from coe.pcm.compose import build_pcm_messages

    pytest.importorskip("pcm")
    messages = build_pcm_messages(
        compressed_instruction="TASK=review INPUT=python",
        optimized_context="ctx",
        user_question="Review this",
        response_lang="en",
        output_style="concise",
    )
    assert "RESPONSE:" in messages[0]["content"]
    assert "Answer only what was asked" in messages[0]["content"]


def test_build_pcm_messages_import_error_fallback():
    from coe.pcm.compose import build_pcm_messages

    with patch.dict("sys.modules", {"pcm.message_assembly": None}):
        messages = build_pcm_messages(
            compressed_instruction="TASK=review INPUT=python",
            optimized_context="ctx",
            user_question="Review this",
            response_lang="en",
        )
    assert messages[0]["content"] == (
        "TASK=review INPUT=python\n\n"
        "Answer in en. Answer clearly using only the provided context."
    )
    assert messages[1]["content"] == "Context:\nctx\n\nQuestion: Review this"
