"""Gateway — punto de entrada unificado del pipeline COE."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .ingest import ContextBundle, IngestTrace, l0_allowed_for_blocks, normalize_language, resolve_effective_levels
from .level1 import deduplicate_context
from .level2 import factorize_context
from .level3 import structure_context
from .level4 import build_context_graph
from .level5 import InMemoryStateStore, StateView, update_semantic_state
from .level5.store import StateStore
from .models import (
    ContextBlock,
    DeduplicationResult,
    FactorizationResult,
    StructuredContext,
    ContextGraph,
    estimate_tokens,
)
from .renderer import render_raw_context

_SUPPORTED_LEVELS = frozenset({1, 2, 3, 4, 5})


@dataclass
class OptimizeOptions:
    levels: list[int] = field(default_factory=lambda: [1])
    locale: str | None = "en"
    target_lang: str | None = None
    l0: bool = False
    session_id: str | None = None
    state_store: StateStore | None = None
    query_context: str | None = None


@dataclass
class LevelTrace:
    level: int
    latency_ms: float
    detail: str = ""


@dataclass
class OptimizationMetrics:
    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    latency_ms: float
    latency_ms_by_level: dict[str, float] = field(default_factory=dict)
    latency_budget_ok: bool = True


@dataclass
class OptimizeResult:
    text: str
    metrics: OptimizationMetrics
    deduplication: DeduplicationResult | None = None
    factorization: FactorizationResult | None = None
    structured: StructuredContext | None = None
    context_graph: ContextGraph | None = None
    state_view: StateView | None = None
    commit_id: str | None = None
    ingest_trace: IngestTrace | None = None
    trace: list[LevelTrace] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "text": self.text,
            "metrics": {
                "original_tokens": self.metrics.original_tokens,
                "optimized_tokens": self.metrics.optimized_tokens,
                "compression_ratio": round(self.metrics.compression_ratio, 4),
                "latency_ms": round(self.metrics.latency_ms, 2),
                "latency_ms_by_level": {
                    k: round(v, 2) for k, v in self.metrics.latency_ms_by_level.items()
                },
                "latency_budget_ok": self.metrics.latency_budget_ok,
            },
            "trace": [
                {"level": t.level, "latency_ms": round(t.latency_ms, 2), "detail": t.detail}
                for t in self.trace
            ],
        }
        if self.deduplication is not None:
            data["deduplication"] = self.deduplication.to_dict()
        if self.factorization is not None:
            data["factorization"] = self.factorization.to_dict()
        if self.structured is not None:
            data["structured"] = self.structured.to_dict()
        if self.context_graph is not None:
            data["context_graph"] = self.context_graph.to_dict()
        if self.commit_id is not None:
            data["commit_id"] = self.commit_id
        return data


def optimize_context(
    blocks: list[ContextBlock] | ContextBundle,
    *,
    levels: list[int] | None = None,
    locale: str | None = None,
    target_lang: str | None = None,
    l0: bool = False,
    session_id: str | None = None,
    state_store: StateStore | None = None,
) -> OptimizeResult:
    """
    Ejecuta el pipeline COE sobre bloques o un ``ContextBundle``.

    Niveles soportados: **1** (dedup), **2** (factorización), **3** (estructura), **4** (grafo), **5** (estado).
    L0 opcional con ``l0=True`` y ``target_lang``.
    """
    bundle: ContextBundle | None = None
    if isinstance(blocks, ContextBundle):
        bundle = blocks
        blocks_list = bundle.blocks
        locale = locale if locale is not None else bundle.locale
        target_lang = target_lang if target_lang is not None else bundle.target_lang
        session_id = session_id if session_id is not None else bundle.session_id
    else:
        blocks_list = blocks
        locale = locale if locale is not None else "en"

    requested_levels = _normalize_levels(levels or [1])
    effective_levels, level_notes = resolve_effective_levels(requested_levels, blocks_list)

    opts = OptimizeOptions(
        levels=effective_levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
        state_store=state_store,
        query_context=bundle.query_context if bundle else None,
    )
    return _optimize(blocks_list, opts, ingest_notes=level_notes)


def _normalize_levels(levels: list[int]) -> list[int]:
    if not levels:
        return [1]
    return sorted(set(levels))


def _optimize(
    blocks: list[ContextBlock],
    opts: OptimizeOptions,
    *,
    ingest_notes: list[str] | None = None,
) -> OptimizeResult:
    unsupported = [n for n in opts.levels if n not in _SUPPORTED_LEVELS]
    if unsupported:
        raise NotImplementedError(f"Levels not implemented: {unsupported}")

    original_text = render_raw_context(blocks)
    original_tokens = estimate_tokens(original_text)

    trace: list[LevelTrace] = []
    latency_by_level: dict[str, float] = {}
    ingest_trace: IngestTrace | None = None
    blocks_work = blocks

    if ingest_notes:
        trace.append(
            LevelTrace(
                level=0,
                latency_ms=0.0,
                detail="ingest: " + "; ".join(ingest_notes),
            )
        )

    t_total = time.perf_counter()

    run_l0 = opts.l0
    if run_l0:
        l0_ok, l0_notes = l0_allowed_for_blocks(blocks_work)
        if not l0_ok:
            run_l0 = False
            trace.append(
                LevelTrace(
                    level=0,
                    latency_ms=0.0,
                    detail="ingest: " + "; ".join(l0_notes),
                )
            )

    if run_l0:
        if not opts.target_lang:
            raise ValueError("target_lang is required when l0=True")
        t0 = time.perf_counter()
        l0_result = normalize_language(blocks_work, target_lang=opts.target_lang)
        blocks_work = l0_result.blocks
        ingest_trace = l0_result.ingest_trace
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["l0"] = elapsed
        trace.append(LevelTrace(level=0, latency_ms=elapsed, detail="normalize_language"))

    dedup: DeduplicationResult | None = None
    factorized: FactorizationResult | None = None
    structured: StructuredContext | None = None
    context_graph: ContextGraph | None = None
    state_view: StateView | None = None
    commit_id: str | None = None
    text = original_text

    run_n5 = 5 in opts.levels
    run_n1 = 1 in opts.levels and not run_n5
    run_n2 = 2 in opts.levels or 3 in opts.levels or 4 in opts.levels
    run_n3 = (3 in opts.levels or 4 in opts.levels) and not run_n5
    run_n4 = 4 in opts.levels and not run_n5

    if run_n5:
        sub_levels = [n for n in opts.levels if n != 5] or [1]
        t0 = time.perf_counter()
        n5_result = update_semantic_state(
            blocks_work,
            session_id=opts.session_id or "_ephemeral",
            store=opts.state_store or InMemoryStateStore(),
            locale=opts.locale,
            levels=sub_levels,
            query_context=opts.query_context,
        )
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n5"] = elapsed
        trace.append(LevelTrace(level=5, latency_ms=elapsed, detail="state_view"))
        state_view = n5_result.view
        commit_id = n5_result.commit_id
        text = state_view.render()
    elif run_n1:
        t0 = time.perf_counter()
        dedup = deduplicate_context(blocks_work)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n1"] = elapsed
        trace.append(LevelTrace(level=1, latency_ms=elapsed, detail="deduplicate"))

    if run_n2 and not run_n5:
        t0 = time.perf_counter()
        source = dedup if dedup is not None else blocks_work
        factorized = factorize_context(source, locale=opts.locale)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n2"] = elapsed
        trace.append(LevelTrace(level=2, latency_ms=elapsed, detail="factorize"))

    if run_n3 and not run_n4:
        t0 = time.perf_counter()
        if factorized is None:
            source = dedup if dedup is not None else blocks_work
            factorized = factorize_context(source, locale=opts.locale)
        structured = structure_context(factorized, locale=opts.locale)
        text = structured.render_prose(locale=opts.locale)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n3"] = elapsed
        trace.append(LevelTrace(level=3, latency_ms=elapsed, detail="structure+prose"))
    elif run_n4:
        t0 = time.perf_counter()
        if factorized is None:
            source = dedup if dedup is not None else blocks_work
            factorized = factorize_context(source, locale=opts.locale)
        if structured is None:
            structured = structure_context(factorized, locale=opts.locale)
        context_graph = build_context_graph(structured, locale=opts.locale)
        text = context_graph.render_prose(locale=opts.locale)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n4"] = elapsed
        trace.append(LevelTrace(level=4, latency_ms=elapsed, detail="graph+prose"))
    elif run_n2 and factorized is not None:
        text = factorized.render_prose(locale=opts.locale)
    elif run_n1 and dedup is not None:
        text = dedup.render_prose(locale=opts.locale)

    optimized_tokens = estimate_tokens(text)
    latency_ms = (time.perf_counter() - t_total) * 1000.0

    ratio = 0.0
    if original_tokens:
        ratio = 1.0 - (optimized_tokens / original_tokens)

    metrics = OptimizationMetrics(
        original_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
        compression_ratio=ratio,
        latency_ms=latency_ms,
        latency_ms_by_level=latency_by_level,
    )

    return OptimizeResult(
        text=text,
        metrics=metrics,
        deduplication=dedup,
        factorization=factorized,
        structured=structured,
        context_graph=context_graph,
        state_view=state_view,
        commit_id=commit_id,
        ingest_trace=ingest_trace,
        trace=trace,
    )
