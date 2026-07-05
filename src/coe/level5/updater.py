"""N5 — merge turn-by-turn y materialización de StateView."""

from __future__ import annotations

from ..level1 import deduplicate_context
from ..level2 import factorize_context
from ..level3 import structure_context
from ..models import ContextBlock
from .state import SemanticState, StateView, UpdateResult
from .store import InMemoryStateStore, StateStore

_VIEW_INTRO = {
    "en": "Accumulated session state:",
    "es": "Estado acumulado de la sesión:",
}


def update_semantic_state(
    blocks: list[ContextBlock],
    *,
    session_id: str,
    store: StateStore | None = None,
    locale: str | None = "en",
    levels: list[int] | None = None,
) -> UpdateResult:
    """
    Integra bloques del turno en el store y materializa ``StateView``.

    v1: acumula bloques y proyecta vía N1/N2 (sin grafo N4).
    """
    if not blocks:
        raise ValueError("blocks must not be empty")

    loc = locale or "en"
    sub_levels = sorted(set(levels or [1]))
    if 5 in sub_levels:
        sub_levels = [n for n in sub_levels if n != 5] or [1]

    state_store = store or InMemoryStateStore()
    state = state_store.load(session_id) or SemanticState(session_id=session_id)

    _merge_blocks(state, blocks)
    prose = _materialize_prose(state.blocks, locale=loc, levels=sub_levels)

    state.commit_count += 1
    commit_id = f"{session_id}-c{state.commit_count}"
    state_store.save(state)

    return UpdateResult(
        view=StateView(prose=prose),
        state=state,
        commit_id=commit_id,
    )


def _merge_blocks(state: SemanticState, new_blocks: list[ContextBlock]) -> None:
    seen_ids = {block.id for block in state.blocks}
    for block in new_blocks:
        block_id = block.id
        if block_id in seen_ids:
            block_id = f"c{state.commit_count + 1}-{block.id}"
        seen_ids.add(block_id)
        state.blocks.append(ContextBlock(id=block_id, content=block.content))


def _materialize_prose(
    blocks: list[ContextBlock],
    *,
    locale: str,
    levels: list[int],
) -> str:
    dedup = deduplicate_context(blocks)
    if 3 in levels:
        factorized = factorize_context(dedup, locale=locale)
        structured = structure_context(factorized, locale=locale)
        body = structured.render_prose(locale=locale)
    elif 2 in levels:
        factorized = factorize_context(dedup, locale=locale)
        body = factorized.render_prose(locale=locale)
    else:
        body = dedup.render_prose(locale=locale)

    intro_key = locale.split("-")[0].lower()
    intro = _VIEW_INTRO.get(intro_key, _VIEW_INTRO["en"])
    return f"{intro}\n\n{body.strip()}\n"
