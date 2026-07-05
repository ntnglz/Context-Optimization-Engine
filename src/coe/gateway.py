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
from .level5 import StateView, update_semantic_state
from .level5.store import StateStore, resolve_state_store
from .level5.operations import collect_store_metrics
from .models import (
    ContextBlock,
    DeduplicationResult,
    FactorizationResult,
    StructuredContext,
    ContextGraph,
    estimate_tokens,
)
from .model_adapter import adapt_for_model
from .renderer import render_raw_context
from .renderer.assembly import assemble_gateway_output, render_turn_prose
from .budget import apply_assembled_budget, truncate_text_to_tokens

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
    section_delimiters: bool = True
    include_pending_turn: bool = False
    max_commits: int | None = None
    max_context_tokens: int | None = None
    target_model: str | None = None
    session_ttl_hours: float | None = None
    fuzzy_link_threshold: float | None = None
    state_store_backend: str | None = None
    state_store_path: str | None = None


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
    truncated: bool = False
    pre_truncation_tokens: int | None = None
    target_model: str | None = None
    model_adapter: str | None = None
    store_metrics: dict[str, int] | None = None


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
                "truncated": self.metrics.truncated,
            },
            "trace": [
                {"level": t.level, "latency_ms": round(t.latency_ms, 2), "detail": t.detail}
                for t in self.trace
            ],
        }
        if self.metrics.target_model is not None:
            data["metrics"]["target_model"] = self.metrics.target_model
        if self.metrics.model_adapter is not None:
            data["metrics"]["model_adapter"] = self.metrics.model_adapter
        if self.metrics.store_metrics is not None:
            data["metrics"]["store"] = self.metrics.store_metrics
        if self.metrics.pre_truncation_tokens is not None:
            data["metrics"]["pre_truncation_tokens"] = self.metrics.pre_truncation_tokens
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
    section_delimiters: bool | None = None,
    include_pending_turn: bool | None = None,
    max_commits: int | None = None,
    max_context_tokens: int | None = None,
    target_model: str | None = None,
    session_ttl_hours: float | None = None,
    fuzzy_link_threshold: float | None = None,
    state_store_backend: str | None = None,
    state_store_path: str | None = None,
) -> OptimizeResult:
    """
    Ejecuta el pipeline COE sobre bloques o un ``ContextBundle``.

    Niveles soportados: **1** (dedup), **2** (factorización), **3** (estructura), **4** (grafo), **5** (estado).
    L0 opcional con ``l0=True`` y ``target_lang``.
    """
    bundle: ContextBundle | None = None
    bundle_section_delimiters = True
    bundle_include_pending_turn = False
    bundle_max_commits: int | None = None
    bundle_max_context_tokens: int | None = None
    bundle_target_model: str | None = None
    bundle_session_ttl_hours: float | None = None
    bundle_fuzzy_link_threshold: float | None = None
    bundle_state_store_backend: str | None = None
    bundle_state_store_path: str | None = None
    if isinstance(blocks, ContextBundle):
        bundle = blocks
        blocks_list = bundle.blocks
        locale = locale if locale is not None else bundle.locale
        target_lang = target_lang if target_lang is not None else bundle.target_lang
        session_id = session_id if session_id is not None else bundle.session_id
        bundle_section_delimiters = bundle.options.section_delimiters
        bundle_include_pending_turn = bundle.options.include_pending_turn
        bundle_max_commits = bundle.options.max_commits
        bundle_max_context_tokens = bundle.options.max_context_tokens
        bundle_target_model = bundle.options.target_model
        bundle_session_ttl_hours = bundle.options.session_ttl_hours
        bundle_fuzzy_link_threshold = bundle.options.fuzzy_link_threshold
        bundle_state_store_backend = bundle.options.state_store_backend
        bundle_state_store_path = bundle.options.state_store_path
    else:
        blocks_list = blocks
        locale = locale if locale is not None else "en"

    resolved_section_delimiters = (
        section_delimiters
        if section_delimiters is not None
        else bundle_section_delimiters
    )
    resolved_include_pending_turn = (
        include_pending_turn
        if include_pending_turn is not None
        else bundle_include_pending_turn
    )

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
        section_delimiters=resolved_section_delimiters,
        include_pending_turn=resolved_include_pending_turn,
        max_commits=max_commits if max_commits is not None else bundle_max_commits,
        max_context_tokens=(
            max_context_tokens
            if max_context_tokens is not None
            else bundle_max_context_tokens
        ),
        target_model=target_model if target_model is not None else bundle_target_model,
        session_ttl_hours=(
            session_ttl_hours
            if session_ttl_hours is not None
            else bundle_session_ttl_hours
        ),
        fuzzy_link_threshold=(
            fuzzy_link_threshold
            if fuzzy_link_threshold is not None
            else bundle_fuzzy_link_threshold
        ),
        state_store_backend=(
            state_store_backend
            if state_store_backend is not None
            else bundle_state_store_backend
        ),
        state_store_path=(
            state_store_path
            if state_store_path is not None
            else bundle_state_store_path
        ),
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
    n5_state_prose: str | None = None
    n5_turn_prose: str | None = None

    run_n5 = 5 in opts.levels
    run_n1 = 1 in opts.levels and not run_n5
    run_n2 = 2 in opts.levels or 3 in opts.levels or 4 in opts.levels
    run_n3 = (3 in opts.levels or 4 in opts.levels) and not run_n5
    run_n4 = 4 in opts.levels and not run_n5

    store_metrics_snapshot: dict[str, int] | None = None

    if run_n5:
        sub_levels = [n for n in opts.levels if n != 5] or [1]
        n5_store = opts.state_store or resolve_state_store(
            opts.session_id,
            None,
            session_ttl_hours=opts.session_ttl_hours,
            backend=opts.state_store_backend,
            store_path=opts.state_store_path,
        )
        t0 = time.perf_counter()
        n5_result = update_semantic_state(
            blocks_work,
            session_id=opts.session_id or "_ephemeral",
            store=n5_store,
            locale=opts.locale,
            levels=sub_levels,
            query_context=opts.query_context,
            max_commits=opts.max_commits,
            session_ttl_hours=opts.session_ttl_hours,
            fuzzy_link_threshold=opts.fuzzy_link_threshold,
        )
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n5"] = elapsed
        trace.append(LevelTrace(level=5, latency_ms=elapsed, detail="state_view"))
        state_view = n5_result.view
        commit_id = n5_result.commit_id
        turn_prose = None
        if opts.include_pending_turn:
            turn_prose = render_turn_prose(
                blocks_work,
                levels=opts.levels,
                locale=opts.locale,
                query_context=opts.query_context,
                max_context_tokens=opts.max_context_tokens,
            )
        n5_state_prose = state_view.render()
        n5_turn_prose = turn_prose
        text = assemble_gateway_output(
            state_prose=n5_state_prose,
            turn_prose=n5_turn_prose,
            locale=opts.locale,
            section_delimiters=opts.section_delimiters,
        )
        snapshot = collect_store_metrics(n5_store)
        store_metrics_snapshot = {
            "active_sessions": snapshot.active_sessions,
            "total_bytes": snapshot.total_bytes,
            "archive_bytes": snapshot.archive_bytes,
            "history_pruned_total": snapshot.history_pruned_total,
        }
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

    if not run_n5:
        if run_n3 and not run_n4:
            t0 = time.perf_counter()
            if factorized is None:
                source = dedup if dedup is not None else blocks_work
                factorized = factorize_context(source, locale=opts.locale)
            structured = structure_context(factorized, locale=opts.locale)
            elapsed = (time.perf_counter() - t0) * 1000.0
            latency_by_level["n3"] = elapsed
            trace.append(LevelTrace(level=3, latency_ms=elapsed, detail="structure+prose"))
        elif run_n4:
            t0 = time.perf_counter()
            if factorized is None:
                source = dedup if dedup is not None else blocks_work
                factorized = factorize_context(source, locale=opts.locale)
            structured = structure_context(factorized, locale=opts.locale)
            context_graph = build_context_graph(
                structured,
                source_blocks=blocks_work,
                query_context=opts.query_context,
                locale=opts.locale,
            )
            elapsed = (time.perf_counter() - t0) * 1000.0
            latency_by_level["n4"] = elapsed
            trace.append(LevelTrace(level=4, latency_ms=elapsed, detail="graph+prose"))

        text = render_turn_prose(
            blocks_work,
            levels=opts.levels,
            locale=opts.locale,
            query_context=opts.query_context,
            max_context_tokens=opts.max_context_tokens if 4 in opts.levels else None,
        )

    pre_truncation_tokens = estimate_tokens(text)
    truncated = False
    if opts.max_context_tokens is not None and pre_truncation_tokens > opts.max_context_tokens:
        if run_n5:
            text, truncated = apply_assembled_budget(
                state_prose=n5_state_prose,
                turn_prose=n5_turn_prose,
                max_tokens=opts.max_context_tokens,
                locale=opts.locale,
                section_delimiters=opts.section_delimiters,
            )
        else:
            text = truncate_text_to_tokens(
                text,
                opts.max_context_tokens,
                keep_end=True,
            )
            truncated = True

    model_adapter_id: str | None = None
    if opts.target_model:
        t0 = time.perf_counter()
        text, model_adapter_id = adapt_for_model(text, opts.target_model)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["model_adapter"] = elapsed
        trace.append(
            LevelTrace(
                level=0,
                latency_ms=elapsed,
                detail=f"model_adapter:{model_adapter_id}",
            )
        )

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
        truncated=truncated,
        pre_truncation_tokens=pre_truncation_tokens if truncated else None,
        target_model=opts.target_model,
        model_adapter=model_adapter_id,
        store_metrics=store_metrics_snapshot,
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
