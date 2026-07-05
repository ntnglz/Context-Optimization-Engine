"""Truncado post-Renderer por prioridad documentada en ingest.md."""

from __future__ import annotations

from ..models import estimate_tokens
from ..renderer.assembly import assemble_gateway_output
from ..renderer.templates import get_templates

_TRUNCATION_MARKER = "... [truncated]\n"


def _section_overhead_tokens(
    *,
    locale: str | None,
    section_delimiters: bool,
    include_state: bool,
    include_turn: bool,
) -> int:
    if not section_delimiters:
        return 0
    tpl = get_templates(locale)
    overhead = ""
    if include_state:
        overhead += tpl["section_session_state"] + "\n\n"
    if include_turn:
        overhead += tpl["section_context"] + "\n\n"
    return estimate_tokens(overhead) if overhead else 0


def truncate_text_to_tokens(
    text: str,
    max_tokens: int,
    *,
    keep_end: bool = True,
) -> str:
    """Recorta prosa a ``max_tokens`` estimados (≈4 chars/token)."""
    if max_tokens <= 0:
        return _TRUNCATION_MARKER.strip()
    body = text.strip()
    if not body:
        return body
    if estimate_tokens(body) <= max_tokens:
        return text

    max_chars = max(1, max_tokens * 4)
    marker = _TRUNCATION_MARKER
    marker_tokens = estimate_tokens(marker)
    budget_chars = max(1, (max_tokens - marker_tokens) * 4)

    if keep_end:
        clipped = body[-budget_chars:]
        return marker + clipped
    clipped = body[:budget_chars]
    return clipped + "\n" + marker.strip()


def apply_assembled_budget(
    *,
    state_prose: str | None,
    turn_prose: str | None,
    max_tokens: int,
    locale: str | None = "en",
    section_delimiters: bool = True,
) -> tuple[str, bool]:
    """
    Aplica tope soft a salida N5 ensamblada.

    Prioridad de recorte (ingest.md): conservar turno reciente y slice de consulta;
    recortar primero la vista de estado expandida, luego el inicio del turno.
    """
    full = assemble_gateway_output(
        state_prose=state_prose,
        turn_prose=turn_prose,
        locale=locale,
        section_delimiters=section_delimiters,
    )
    if estimate_tokens(full) <= max_tokens:
        return full, False

    turn_body = (turn_prose or "").strip()
    state_body = (state_prose or "").strip()

    if not turn_body and state_body:
        overhead = _section_overhead_tokens(
            locale=locale,
            section_delimiters=section_delimiters,
            include_state=True,
            include_turn=False,
        )
        trimmed_state = truncate_text_to_tokens(
            state_body,
            max(1, max_tokens - overhead),
            keep_end=True,
        )
        return assemble_gateway_output(
            state_prose=trimmed_state,
            turn_prose=None,
            locale=locale,
            section_delimiters=section_delimiters,
        ), True

    if state_body:
        without_state = assemble_gateway_output(
            state_prose=None,
            turn_prose=turn_prose,
            locale=locale,
            section_delimiters=section_delimiters,
        )
        if estimate_tokens(without_state) <= max_tokens:
            return without_state, True

    overhead = assemble_gateway_output(
        state_prose=None,
        turn_prose="",
        locale=locale,
        section_delimiters=section_delimiters,
    )
    overhead_tokens = estimate_tokens(overhead) if section_delimiters else 0
    turn_budget = max(1, max_tokens - overhead_tokens)
    trimmed_turn = truncate_text_to_tokens(turn_body, turn_budget, keep_end=True)
    final = assemble_gateway_output(
        state_prose=None,
        turn_prose=trimmed_turn,
        locale=locale,
        section_delimiters=section_delimiters,
    )
    if estimate_tokens(final) > max_tokens:
        final = truncate_text_to_tokens(final, max_tokens, keep_end=True)
    return final, True
