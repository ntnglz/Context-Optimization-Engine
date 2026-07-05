"""Reparto de ventana modelo entre PCM, COE y reserva de respuesta."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WindowAllocation:
    max_window_tokens: int
    instruction_tokens: int
    response_reserve: int
    coe_budget_tokens: int

    @property
    def used_tokens(self) -> int:
        return self.instruction_tokens + self.coe_budget_tokens + self.response_reserve


def allocate_coe_budget(
    *,
    max_window_tokens: int,
    instruction_tokens: int,
    response_reserve: int = 512,
) -> WindowAllocation:
    """
    Calcula ``max_context_tokens`` para COE tras reservar instrucción PCM y respuesta.

    ``coe_budget = max_window - instruction - response_reserve`` (mínimo 0).
    """
    if max_window_tokens <= 0:
        raise ValueError("max_window_tokens must be positive")
    if response_reserve < 0:
        raise ValueError("response_reserve must be >= 0")

    available = max(0, max_window_tokens - instruction_tokens - response_reserve)
    return WindowAllocation(
        max_window_tokens=max_window_tokens,
        instruction_tokens=instruction_tokens,
        response_reserve=response_reserve,
        coe_budget_tokens=available,
    )
