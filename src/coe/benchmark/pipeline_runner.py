"""Ejecución parcial del pipeline COE para benchmarks (H1: N1)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from coe.level1 import deduplicate_context
from coe.models import ContextBlock, estimate_tokens

from .schema import BenchmarkCase, PipelineProfile


@dataclass
class PipelineRunResult:
    optimized_text: str
    t_coe_ms: float
    original_tokens: int
    optimized_tokens: int


def run_pipeline_on_case(
    case: BenchmarkCase,
    profile: PipelineProfile,
) -> PipelineRunResult:
    blocks = [
        ContextBlock(id=b.id, content=b.content) for b in case.blocks
    ]
    original_tokens = sum(estimate_tokens(b.content) for b in blocks)

    t0 = time.perf_counter()
    text = _render_raw_blocks(blocks)

    if 1 in profile.levels:
        result = deduplicate_context(blocks)
        text = result.render()
        optimized_tokens = result.optimized_tokens
    else:
        optimized_tokens = original_tokens

    t_coe_ms = (time.perf_counter() - t0) * 1000.0

    if profile.levels != [1] and max(profile.levels) > 1:
        # N2+ no implementado — passthrough N1 o raw hasta H2
        pass

    return PipelineRunResult(
        optimized_text=text,
        t_coe_ms=t_coe_ms,
        original_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
    )


def _render_raw_blocks(blocks: list[ContextBlock]) -> str:
    parts: list[str] = []
    for block in blocks:
        parts.append(f"[{block.id}]\n{block.content.strip()}")
    return "\n\n".join(parts) + "\n"
