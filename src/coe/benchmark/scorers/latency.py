"""Comprobación de presupuesto t_coe."""

from __future__ import annotations


def latency_ok(t_coe_ms: float, budget_ms: float | None) -> bool:
    if budget_ms is None:
        return True
    return t_coe_ms <= budget_ms
