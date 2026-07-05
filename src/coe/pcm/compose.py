"""Composición PCM + COE — instrucción comprimida + contexto optimizado."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..budget import allocate_coe_budget
from ..gateway import OptimizeResult, optimize_context
from ..ingest import ContextBundle
from ..models import ContextBlock, estimate_tokens
from .backends import InstructionCompressionResult, InstructionCompressor, get_instruction_compressor


@dataclass
class WindowMetrics:
    max_window_tokens: int
    response_reserve: int
    instruction_tokens: int
    coe_budget_tokens: int
    context_tokens: int
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_window_tokens": self.max_window_tokens,
            "response_reserve": self.response_reserve,
            "instruction_tokens": self.instruction_tokens,
            "coe_budget_tokens": self.coe_budget_tokens,
            "context_tokens": self.context_tokens,
            "truncated": self.truncated,
        }


@dataclass
class OptimizeWithPCMResult:
    instruction: InstructionCompressionResult
    context: OptimizeResult
    window: WindowMetrics
    messages: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instruction": {
                "original": self.instruction.original,
                "compressed": self.instruction.compressed,
                "original_tokens": self.instruction.original_tokens,
                "compressed_tokens": self.instruction.compressed_tokens,
                "compression_ratio": round(self.instruction.compression_ratio, 4),
                "backend": self.instruction.backend,
                "skipped": self.instruction.skipped,
            },
            "context": self.context.to_dict(),
            "window": self.window.to_dict(),
            "messages": self.messages,
        }


def build_pcm_messages(
    *,
    compressed_instruction: str,
    optimized_context: str,
    user_question: str,
    response_lang: str,
    output_style: str = "normal",
    system_addendum: str = "",
    pcm_interpretation_hint: str = "",
) -> list[dict[str, str]]:
    """Monta messages[] según renderer.md — PCM en system, contexto separado del user."""
    try:
        from pcm.message_assembly import build_system_prompt

        system = build_system_prompt(
            compressed_instruction=compressed_instruction,
            response_lang=response_lang,
            output_style=output_style,  # type: ignore[arg-type]
            pcm_interpretation_hint=pcm_interpretation_hint or system_addendum,
        )
    except ImportError:
        addendum = system_addendum.strip() or (
            f"Answer in {response_lang}. Answer clearly using only the provided context."
        )
        system = f"{compressed_instruction.strip()}\n\n{addendum}"
    user = (
        f"Context:\n{optimized_context.strip()}\n\n"
        f"Question: {user_question.strip()}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def optimize_with_pcm(
    blocks: list[ContextBlock] | ContextBundle,
    *,
    user_instruction: str,
    levels: list[int] | None = None,
    locale: str | None = None,
    target_lang: str | None = None,
    l0: bool = False,
    max_window_tokens: int | None = None,
    response_reserve: int = 512,
    response_lang: str = "en",
    output_style: str = "normal",
    system_addendum: str = "",
    pcm_backend: str = "stub",
    pcm_compressor: InstructionCompressor | None = None,
    session_id: str | None = None,
    query_context: str | None = None,
    **optimize_kwargs: Any,
) -> OptimizeWithPCMResult:
    """
    Pipeline compuesto: comprime instrucción (PCM) + optimiza contexto (COE).

    Si ``max_window_tokens`` está definido, reparte ventana:
    instrucción PCM + contexto COE (``max_context_tokens``) + ``response_reserve``.
    """
    compressor = pcm_compressor or get_instruction_compressor(pcm_backend)
    instruction = compressor.compress(user_instruction)

    max_context_tokens = optimize_kwargs.pop("max_context_tokens", None)
    window_meta: WindowMetrics | None = None

    if max_window_tokens is not None:
        allocation = allocate_coe_budget(
            max_window_tokens=max_window_tokens,
            instruction_tokens=instruction.compressed_tokens,
            response_reserve=response_reserve,
        )
        max_context_tokens = allocation.coe_budget_tokens
        window_meta = WindowMetrics(
            max_window_tokens=max_window_tokens,
            response_reserve=response_reserve,
            instruction_tokens=instruction.compressed_tokens,
            coe_budget_tokens=allocation.coe_budget_tokens,
            context_tokens=0,
        )

    context = optimize_context(
        blocks,
        levels=levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
        max_context_tokens=max_context_tokens,
        **optimize_kwargs,
    )

    if window_meta is None:
        window_meta = WindowMetrics(
            max_window_tokens=max_window_tokens or 0,
            response_reserve=response_reserve,
            instruction_tokens=instruction.compressed_tokens,
            coe_budget_tokens=max_context_tokens or context.metrics.optimized_tokens,
            context_tokens=context.metrics.optimized_tokens,
            truncated=context.metrics.truncated,
        )
    else:
        window_meta.context_tokens = context.metrics.optimized_tokens
        window_meta.truncated = context.metrics.truncated

    messages = build_pcm_messages(
        compressed_instruction=instruction.compressed,
        optimized_context=context.text,
        user_question=user_instruction,
        response_lang=response_lang,
        output_style=output_style,
        system_addendum=system_addendum,
    )

    return OptimizeWithPCMResult(
        instruction=instruction,
        context=context,
        window=window_meta,
        messages=messages,
    )
