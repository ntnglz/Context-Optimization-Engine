"""Utilidades sobre casos single-turn y multi-turn."""

from __future__ import annotations

from coe.models import ContextBlock

from .schema import BenchmarkCase, CaseBlock


def is_multi_turn(case: BenchmarkCase) -> bool:
    return case.session is not None and len(case.session.turns) > 0


def effective_blocks(case: BenchmarkCase) -> list[CaseBlock]:
    if not is_multi_turn(case):
        return list(case.blocks)
    blocks: list[CaseBlock] = []
    assert case.session is not None
    for turn_idx, turn in enumerate(case.session.turns, start=1):
        for block in turn.blocks:
            blocks.append(
                CaseBlock(
                    id=f"T{turn_idx}-{block.id}",
                    content=block.content,
                    source_type=block.source_type,
                )
            )
    return blocks


def effective_question(case: BenchmarkCase) -> str:
    if is_multi_turn(case):
        assert case.session is not None
        return case.session.turns[-1].question
    return case.question


def effective_expected_facts(case: BenchmarkCase) -> list[str]:
    if is_multi_turn(case):
        assert case.session is not None
        return list(case.session.turns[-1].expected_facts)
    return list(case.expected_facts)


def context_blocks(case: BenchmarkCase) -> list[ContextBlock]:
    return [
        ContextBlock(id=b.id, content=b.content)
        for b in effective_blocks(case)
    ]
