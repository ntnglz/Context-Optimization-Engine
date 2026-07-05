"""Ensamblaje final de prosa hacia el LLM (Gateway)."""

from __future__ import annotations

from ..level1 import deduplicate_context
from ..level2 import factorize_context
from ..level3 import structure_context
from ..level4 import build_context_graph
from ..models import ContextBlock
from .templates import get_templates


def assemble_gateway_output(
    *,
    state_prose: str | None = None,
    turn_prose: str | None = None,
    locale: str | None = "en",
    section_delimiters: bool = True,
) -> str:
    """
    Concatena secciones según ``renderer.md``:

    1. StateView (N5) opcional
    2. Prosa del turno opcional
    3. Delimitadores configurables entre secciones
    """
    tpl = get_templates(locale)
    sections: list[str] = []

    state_body = (state_prose or "").strip()
    turn_body = (turn_prose or "").strip()

    if state_body:
        if section_delimiters:
            sections.append(tpl["section_session_state"])
        sections.append(state_body)

    if turn_body:
        if section_delimiters:
            sections.append(tpl["section_context"])
        sections.append(turn_body)

    if not sections:
        return ""
    return "\n\n".join(sections) + "\n"


def render_turn_prose(
    blocks: list[ContextBlock],
    *,
    levels: list[int],
    locale: str | None = "en",
) -> str:
    """Proyecta bloques del turno a prosa (N1–N4, sin N5)."""
    loc = locale or "en"
    pipeline_levels = sorted(n for n in levels if n != 5) or [1]

    run_n1 = 1 in pipeline_levels
    run_n2 = 2 in pipeline_levels or 3 in pipeline_levels or 4 in pipeline_levels
    run_n3 = 3 in pipeline_levels or 4 in pipeline_levels
    run_n4 = 4 in pipeline_levels

    dedup = deduplicate_context(blocks) if run_n1 else None
    factorized = None
    structured = None
    context_graph = None

    if run_n2:
        source = dedup if dedup is not None else blocks
        factorized = factorize_context(source, locale=loc)

    if run_n4:
        if factorized is None:
            source = dedup if dedup is not None else blocks
            factorized = factorize_context(source, locale=loc)
        structured = structure_context(factorized, locale=loc)
        context_graph = build_context_graph(structured, locale=loc)
        return context_graph.render_prose(locale=loc)

    if run_n3:
        if factorized is None:
            source = dedup if dedup is not None else blocks
            factorized = factorize_context(source, locale=loc)
        structured = structure_context(factorized, locale=loc)
        return structured.render_prose(locale=loc)

    if run_n2 and factorized is not None:
        return factorized.render_prose(locale=loc)

    if run_n1 and dedup is not None:
        return dedup.render_prose(locale=loc)

    from . import render_raw_context

    return render_raw_context(blocks)
