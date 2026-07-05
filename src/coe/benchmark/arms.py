"""Construcción de brazos A/B para benchmarks E2E."""

from __future__ import annotations

from coe.models import ContextBlock
from coe.renderer import render_raw_context

from .schema import BenchmarkCase


def blocks_from_case(case: BenchmarkCase) -> list[ContextBlock]:
    return [ContextBlock(id=b.id, content=b.content) for b in case.blocks]


def render_arm_a_context(case: BenchmarkCase) -> str:
    """Contexto original crudo pre-COE (patrón oro brazo A)."""
    return render_raw_context(blocks_from_case(case))
