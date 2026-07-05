"""Ejecución del pipeline COE vía Gateway para benchmarks."""

from __future__ import annotations

from dataclasses import dataclass

from coe.gateway import OptimizeResult, optimize_context
from coe.models import estimate_tokens
from coe.renderer import render_raw_context

from .arms import blocks_from_case
from .schema import BenchmarkCase, PipelineProfile


@dataclass
class PipelineRunResult:
    optimized_text: str
    t_coe_ms: float
    original_tokens: int
    optimized_tokens: int
    optimize_result: OptimizeResult | None = None


def run_pipeline_on_case(
    case: BenchmarkCase,
    profile: PipelineProfile,
) -> PipelineRunResult:
    blocks = blocks_from_case(case)
    original_text = render_raw_context(blocks)
    original_tokens = estimate_tokens(original_text)

    if profile.l0:
        raise NotImplementedError("L0 not implemented in benchmark pipeline yet")

    unsupported = [n for n in profile.levels if n > 1]
    if unsupported:
        raise NotImplementedError(
            f"Benchmark profile levels {unsupported} not implemented (max ready: N1)"
        )

    result = optimize_context(
        blocks,
        levels=profile.levels,
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
