"""Construcción de brazos A/B para benchmarks E2E."""

from __future__ import annotations

from coe.models import ContextBlock
from coe.renderer import render_raw_context

from .case_utils import context_blocks, effective_question, is_multi_turn
from .evaluators.base import Message
from .evaluators.prompts import load_prompt
from .schema import BenchmarkCase


def render_arm_a_context(case: BenchmarkCase) -> str:
    """Contexto original crudo pre-COE (patrón oro brazo A)."""
    if is_multi_turn(case):
        return render_multi_turn_arm_a(case)
    return render_raw_context(context_blocks(case))


def render_multi_turn_arm_a(case: BenchmarkCase) -> str:
    """Historial multi-turno crudo concatenado (pre-COE)."""
    assert case.session is not None
    sections: list[str] = []
    for turn_idx, turn in enumerate(case.session.turns, start=1):
        turn_blocks = [
            ContextBlock(id=b.id, content=b.content, source_type=b.source_type)
            for b in turn.blocks
        ]
        body = render_raw_context(turn_blocks).strip()
        sections.append(f"--- Turn {turn_idx} ---\nQ: {turn.question}\n{body}")
    return "\n\n".join(sections) + "\n"


def build_answer_messages(case: BenchmarkCase, context: str) -> list[Message]:
    """Mensajes LLM idénticos salvo el bloque de contexto (invariante A/B)."""
    addendum = case.system_addendum.strip() or "Answer clearly for a non-technical user."
    system = load_prompt("answer_system.txt").format(
        response_lang=case.response_lang,
        system_addendum=addendum,
    )
    question = effective_question(case)
    user = f"Context:\n{context.strip()}\n\nQuestion: {question.strip()}"
    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]
