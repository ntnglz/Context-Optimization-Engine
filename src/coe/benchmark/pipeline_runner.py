"""Ejecución del pipeline COE vía Gateway para benchmarks."""

from __future__ import annotations

import time
from dataclasses import dataclass

from coe.gateway import LevelTrace, OptimizationMetrics, OptimizeResult, optimize_context
from coe.level5 import InMemoryStateStore, update_semantic_state
from coe.models import ContextBlock, estimate_tokens
from coe.renderer import render_raw_context

from .case_utils import context_blocks, is_multi_turn
from .schema import BenchmarkCase, PipelineProfile

_GATEWAY_LEVELS = frozenset({1, 2, 3, 5})


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

    if level_set <= _GATEWAY_LEVELS:
        return sorted(level_set)
    unsupported = sorted(n for n in level_set if n not in _GATEWAY_LEVELS)
    raise NotImplementedError(
        f"Benchmark profile levels {unsupported} not implemented (gateway: N1, N2, N3, N5)"
    )


def run_pipeline_on_case(
    case: BenchmarkCase,
    profile: PipelineProfile,
) -> PipelineRunResult:
    blocks = context_blocks(case)
    original_text = render_raw_context(blocks)
    original_tokens = estimate_tokens(original_text)

    if profile.l0 and not profile.target_lang:
        raise ValueError(f"Profile {profile.id!r} has l0=true but target_lang is missing")

    levels = _resolve_levels(profile)
    if 5 in levels and is_multi_turn(case):
        return _run_n5_multi_turn(case, profile, levels, original_tokens)

    result = optimize_context(
        blocks,
        levels=levels,
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


def _run_n5_multi_turn(
    case: BenchmarkCase,
    profile: PipelineProfile,
    levels: list[int],
    original_tokens: int,
) -> PipelineRunResult:
    assert case.session is not None
    sub_levels = [n for n in levels if n != 5] or [1]
    store = InMemoryStateStore()
    session_id = case.session.session_id or case.id
    locale = profile.locale or "en"

    t0 = time.perf_counter()
    last = None
    for turn in case.session.turns:
        turn_blocks = [
            ContextBlock(id=block.id, content=block.content) for block in turn.blocks
        ]
        last = update_semantic_state(
            turn_blocks,
            session_id=session_id,
            store=store,
            locale=locale,
            levels=sub_levels,
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert last is not None
    text = last.view.render()
    optimized_tokens = estimate_tokens(text)

    ratio = 0.0
    if original_tokens:
        ratio = 1.0 - (optimized_tokens / original_tokens)

    optimize_result = OptimizeResult(
        text=text,
        metrics=OptimizationMetrics(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            compression_ratio=ratio,
            latency_ms=elapsed_ms,
            latency_ms_by_level={"n5": elapsed_ms},
        ),
        state_view=last.view,
        commit_id=last.commit_id,
        trace=[LevelTrace(level=5, latency_ms=elapsed_ms, detail="multi_turn_state_view")],
    )

    return PipelineRunResult(
        optimized_text=text,
        t_coe_ms=elapsed_ms,
        original_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
        optimize_result=optimize_result,
    )
