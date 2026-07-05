"""Ejecución del pipeline COE vía Gateway para benchmarks."""

from __future__ import annotations

from dataclasses import dataclass

from coe.gateway import OptimizeResult, optimize_context
from coe.models import estimate_tokens
from coe.renderer import render_raw_context

from .case_utils import context_blocks
from .schema import BenchmarkCase, PipelineProfile


@dataclass
class PipelineRunResult:
    optimized_text: str
    t_coe_ms: float
    original_tokens: int
    optimized_tokens: int
    optimize_result: OptimizeResult | None = None


def _resolve_levels(profile: PipelineProfile) -> list[int]:
    """N5 aún no implementado — perfiles con nivel 5 usan N1 sobre bloques aplanados."""
    levels = list(profile.levels)
    if not levels:
        return [1]
    if all(n == 1 for n in levels):
        return [1]
    if set(levels) <= {1, 5}:
        return [1]
    unsupported = [n for n in levels if n > 1]
    raise NotImplementedError(
        f"Benchmark profile levels {unsupported} not implemented (max ready: N1, N5 passthrough)"
    )


def run_pipeline_on_case(
    case: BenchmarkCase,
    profile: PipelineProfile,
) -> PipelineRunResult:
    blocks = context_blocks(case)
    original_text = render_raw_context(blocks)
    original_tokens = estimate_tokens(original_text)

    if profile.l0:
        raise NotImplementedError("L0 not implemented in benchmark pipeline yet")

    result = optimize_context(
        blocks,
        levels=_resolve_levels(profile),
        locale=profile.locale or "en",
        target_lang=profile.target_lang,
        l0=profile.l0,
    )

    return PipelineRunResult(
        optimized_text=result.text,
        t_coe_ms=result.metrics.latency_ms,
        original_tokens=original_tokens,
        optimized_tokens=result.metrics.optimized_tokens,
        optimize_result=result,
    )
