"""Matriz source_type → niveles permitidos."""

from __future__ import annotations

from ..models import ContextBlock

MAX_LEVELS_BY_SOURCE_TYPE: dict[str, frozenset[int]] = {
    "prose": frozenset({1, 2, 3, 4, 5}),
    "history": frozenset({1, 2, 3, 4, 5}),
    "rag": frozenset({1, 2, 3, 4, 5}),
    "tool": frozenset({1, 2, 3, 4, 5}),
    "structured": frozenset({1, 5}),
    "code": frozenset({1}),
    "glossary": frozenset({1, 5}),
    "memory": frozenset({1, 2, 3, 4, 5}),
}

L0_ALLOWED_BY_SOURCE_TYPE: dict[str, bool] = {
    "prose": True,
    "history": True,
    "rag": True,
    "tool": True,
    "structured": True,
    "code": False,
    "glossary": True,
    "memory": True,
}


def max_levels_for_block(block: ContextBlock) -> frozenset[int]:
    override = block.metadata.get("levels_override")
    if override:
        return frozenset(int(level) for level in override)
    return MAX_LEVELS_BY_SOURCE_TYPE.get(block.source_type, MAX_LEVELS_BY_SOURCE_TYPE["prose"])


def resolve_effective_levels(
    requested: list[int],
    blocks: list[ContextBlock],
) -> tuple[list[int], list[str]]:
    """Intersección conservadora: solo niveles permitidos para todos los bloques."""
    if not requested:
        return [], []
    if not blocks:
        return sorted(set(requested)), []

    allowed_sets = [max_levels_for_block(block) for block in blocks]
    intersection = allowed_sets[0]
    for allowed in allowed_sets[1:]:
        intersection = intersection & allowed
    effective = sorted(set(requested) & intersection)

    notes: list[str] = []
    skipped = sorted(set(requested) - set(effective))
    if skipped:
        types = ", ".join(sorted({block.source_type for block in blocks}))
        notes.append(f"levels {skipped} skipped for bundle source_types=[{types}]")
    return effective, notes


def l0_allowed_for_blocks(blocks: list[ContextBlock]) -> tuple[bool, list[str]]:
    notes: list[str] = []
    for block in blocks:
        if not L0_ALLOWED_BY_SOURCE_TYPE.get(block.source_type, True):
            notes.append(
                f"block {block.id}: L0 disabled for source_type={block.source_type}"
            )
    return not notes, notes
