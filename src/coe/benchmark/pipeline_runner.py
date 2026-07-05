"""Ejecución del pipeline COE vía Gateway para benchmarks."""

from __future__ import annotations

from dataclasses import dataclass

from coe.gateway import OptimizeResult, optimize_context
from coe.models import estimate_tokens
from coe.renderer import render_raw_context

from .case_utils import context_blocks
from .schema import BenchmarkCase, PipelineProfile

_GATEWAY_LEVELS = frozenset({1, 2, 5})


@dataclass
class PipelineRunResult:
    optimized_text: str
    t_coe_ms: float
    original_tokens: int
    optimized_tokens: int
    optimize_result: OptimizeResult | None = None


def _resolve_levels(profile: PipelineProfile) -> list[int]:
    """Mapea perfil YAML a niveles soportados por el Gateway."""
    levels = list(profile.levels) or [1]
    level_set = set(levels)

    if level_set <= {1, 2}:
        return sorted(level_set)
    if level_set <= {1, 5} or level_set == {5}:
        return [1]
    unsupported = sorted(n for n in level_set if n not in _GATEWAY_LEVELS)
    raise NotImplementedError(
        f"Benchmark profile levels {unsupported} not implemented (gateway: N1, N2; N5 passthrough)"
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
