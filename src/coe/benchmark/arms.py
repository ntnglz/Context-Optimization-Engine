"""Construcción de brazos A/B para benchmarks E2E."""

from __future__ import annotations

from coe.models import ContextBlock
from coe.renderer import render_raw_context

from .evaluators.base import Message
from .evaluators.prompts import load_prompt
from .schema import BenchmarkCase


def blocks_from_case(case: BenchmarkCase) -> list[ContextBlock]:
    return [ContextBlock(id=b.id, content=b.content) for b in case.blocks]


def render_arm_a_context(case: BenchmarkCase) -> str:
    """Contexto original crudo pre-COE (patrón oro brazo A)."""
    return render_raw_context(blocks_from_case(case))


def build_answer_messages(case: BenchmarkCase, context: str) -> list[Message]:
    """Mensajes LLM idénticos salvo el bloque de contexto (invariante A/B)."""
    addendum = case.system_addendum.strip() or "Answer clearly for a non-technical user."
    system = load_prompt("answer_system.txt").format(
        response_lang=case.response_lang,
        system_addendum=addendum,
    )
    user = f"Context:\n{context.strip()}\n\nQuestion: {case.question.strip()}"
    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]
