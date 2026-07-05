"""Gateway — punto de entrada unificado del pipeline COE."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .level1 import deduplicate_context
from .level2 import factorize_context
from .models import (
    ContextBlock,
    DeduplicationResult,
    FactorizationResult,
    estimate_tokens,
)
from .renderer import render_raw_context

_SUPPORTED_LEVELS = frozenset({1, 2})


@dataclass
class OptimizeOptions:
    levels: list[int] = field(default_factory=lambda: [1])
    locale: str | None = "en"
    target_lang: str | None = None
    l0: bool = False


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
        return data


def optimize_context(
    blocks: list[ContextBlock],
    *,
    levels: list[int] | None = None,
    locale: str | None = "en",
    target_lang: str | None = None,
    l0: bool = False,
) -> OptimizeResult:
    """
    Ejecuta el pipeline COE sobre un bundle de bloques.

    Niveles soportados: **1** (dedup), **2** (factorización). L0 pendiente.
    """
    opts = OptimizeOptions(
        levels=_normalize_levels(levels or [1]),
        locale=locale,
        target_lang=target_lang,
        l0=l0,
    )
    return _optimize(blocks, opts)


def _normalize_levels(levels: list[int]) -> list[int]:
    if not levels:
        return [1]
    return sorted(set(levels))


def _optimize(blocks: list[ContextBlock], opts: OptimizeOptions) -> OptimizeResult:
    if opts.l0:
        raise NotImplementedError("L0 language normalization not implemented yet")

    unsupported = [n for n in opts.levels if n not in _SUPPORTED_LEVELS]
    if unsupported:
        raise NotImplementedError(f"Levels not implemented: {unsupported}")

    original_text = render_raw_context(blocks)
    original_tokens = estimate_tokens(original_text)

    trace: list[LevelTrace] = []
    latency_by_level: dict[str, float] = {}
    dedup: DeduplicationResult | None = None
    factorized: FactorizationResult | None = None
    text = original_text

    t_total = time.perf_counter()

    run_n1 = 1 in opts.levels
    run_n2 = 2 in opts.levels

    if run_n1:
        t0 = time.perf_counter()
        dedup = deduplicate_context(blocks)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n1"] = elapsed
        trace.append(LevelTrace(level=1, latency_ms=elapsed, detail="deduplicate"))

    if run_n2:
        t0 = time.perf_counter()
        source = dedup if dedup is not None else blocks
        factorized = factorize_context(source, locale=opts.locale)
        text = factorized.render_prose(locale=opts.locale)
        elapsed = (time.perf_counter() - t0) * 1000.0
        latency_by_level["n2"] = elapsed
        trace.append(LevelTrace(level=2, latency_ms=elapsed, detail="factorize+prose"))
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
        trace=trace,
    )
