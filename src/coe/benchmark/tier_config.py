"""Configuración por tier del harness (tags, evaluador)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TierDefaults:
    tags: frozenset[str] | None
    evaluator: str


TIER_DEFAULTS: dict[str, TierDefaults] = {
    "smoke": TierDefaults(tags=frozenset({"core"}), evaluator="mock"),
    "ci": TierDefaults(tags=frozenset({"core"}), evaluator="mock"),
    "nightly": TierDefaults(tags=frozenset({"single_turn"}), evaluator="ollama"),
    "release": TierDefaults(tags=None, evaluator="ollama"),
}


def default_tags_for_tier(tier: str) -> set[str] | None:
    defaults = TIER_DEFAULTS.get(tier)
    if defaults is None:
        raise ValueError(f"Unknown tier: {tier!r}")
    if defaults.tags is None:
        return None
    return set(defaults.tags)


def default_evaluator_for_tier_config(tier: str) -> str:
    defaults = TIER_DEFAULTS.get(tier)
    if defaults is None:
        raise ValueError(f"Unknown tier: {tier!r}")
    return defaults.evaluator
