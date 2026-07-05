"""Recorte cooperativo N4 antes de superar ``max_context_tokens``."""

from __future__ import annotations

from ..level4.builder import build_context_graph
from ..models import ContextBlock, ContextGraph, StructuredContext, estimate_tokens
from .truncate import truncate_text_to_tokens


def build_context_graph_within_budget(
    structured: StructuredContext,
    *,
    source_blocks: list[ContextBlock] | None = None,
    query_context: str | None = None,
    max_tokens: int,
    locale: str | None = "en",
    max_hops: int = 2,
    include_orphans: bool = True,
) -> tuple[ContextGraph, str, bool]:
    """
    Materializa grafo N4 reduciendo ``max_hops`` / huérfanos hasta caber en presupuesto.

    Devuelve ``(graph, prose, truncated)``.
    """
    loc = locale or "en"
    best_graph: ContextGraph | None = None
    best_prose = ""

    hop_candidates = list(range(max_hops, -1, -1))
    orphan_candidates = (True, False) if include_orphans else (False,)

    for hops in hop_candidates:
        for orphans in orphan_candidates:
            graph = build_context_graph(
                structured,
                source_blocks=source_blocks,
                query_context=query_context,
                max_hops=hops,
                include_orphans=orphans,
                locale=loc,
            )
            prose = graph.render_prose(locale=loc)
            tokens = estimate_tokens(prose)
            best_graph = graph
            best_prose = prose
            if tokens <= max_tokens:
                return graph, prose, False

    assert best_graph is not None
    trimmed = truncate_text_to_tokens(best_prose, max_tokens, keep_end=True)
    best_graph.optimized_tokens = estimate_tokens(trimmed)
    return best_graph, trimmed, True
