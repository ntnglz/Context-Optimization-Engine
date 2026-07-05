"""Nivel 1 — deduplicación determinista de líneas repetidas entre bloques."""

from __future__ import annotations

from collections import defaultdict

from ..models import ContextBlock, DeduplicationResult, SharedFact, estimate_tokens
from .normalize import normalize_line, split_lines
from .render import render_deduplication


def deduplicate_context(
    blocks: list[ContextBlock],
    *,
    min_occurrences: int = 2,
) -> DeduplicationResult:
    """
    Extrae líneas repetidas (tras normalización) a hechos compartidos.

    Una línea se considera redundante si aparece en al menos `min_occurrences`
    bloques distintos. El contenido único permanece en cada bloque.
    """
    if min_occurrences < 2:
        raise ValueError("min_occurrences debe ser >= 2")

    original_text = _concat_original(blocks)
    original_tokens = estimate_tokens(original_text)

    # normalized_key -> { canonical_line, set(block_ids) }
    occurrences: dict[str, dict[str, set[str] | str]] = defaultdict(
        lambda: {"canonical": "", "blocks": set()}
    )

    # block_id -> list of (normalized_key, canonical_line) in order
    block_lines: dict[str, list[tuple[str, str]]] = {}

    for block in blocks:
        block_lines[block.id] = []
        for line in split_lines(block.content):
            key = normalize_line(line)
            entry = occurrences[key]
            if not entry["canonical"]:
                entry["canonical"] = line.strip()
            entry["blocks"].add(block.id)
            block_lines[block.id].append((key, line.strip()))

    shared_keys = {
        key
        for key, entry in occurrences.items()
        if len(entry["blocks"]) >= min_occurrences
    }

    shared_facts: list[SharedFact] = []
    for key in sorted(shared_keys, key=lambda k: occurrences[k]["canonical"]):
        entry = occurrences[key]
        shared_facts.append(
            SharedFact(
                canonical_line=str(entry["canonical"]),
                normalized_key=key,
                source_ids=sorted(entry["blocks"]),
            )
        )

    unique_blocks: list[ContextBlock] = []
    for block in blocks:
        remaining: list[str] = []
        for key, canonical in block_lines[block.id]:
            if key not in shared_keys:
                remaining.append(canonical)
        unique_blocks.append(
            ContextBlock(
                id=block.id,
                content="\n".join(remaining),
                source_type=block.source_type,
                detected_lang=block.detected_lang,
                token_estimate=block.token_estimate,
                metadata=dict(block.metadata),
            )
        )

    if shared_facts:
        optimized_text = render_deduplication(
            DeduplicationResult(
                shared_facts=shared_facts,
                unique_blocks=unique_blocks,
                original_tokens=0,
                optimized_tokens=0,
            )
        )
        optimized_tokens = estimate_tokens(optimized_text)
    else:
        optimized_text = original_text
        optimized_tokens = original_tokens

    return DeduplicationResult(
        shared_facts=shared_facts,
        unique_blocks=unique_blocks,
        original_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
    )


def _concat_original(blocks: list[ContextBlock]) -> str:
    parts = []
    for block in blocks:
        parts.append(f"[{block.id}]\n{block.content}")
    return "\n\n".join(parts)
