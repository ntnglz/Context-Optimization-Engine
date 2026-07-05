"""N5 — merge turn-by-turn y materialización de StateView."""

from __future__ import annotations

from ..models import ContextBlock, estimate_tokens
from .materialize import blocks_to_context_graph, render_state_view
from .merge import merge_context_graphs, _clone_graph
from .state import Commit, SemanticState, StateView, UpdateResult
from .store import InMemoryStateStore, StateStore


def update_semantic_state(
    blocks: list[ContextBlock],
    *,
    session_id: str,
    store: StateStore | None = None,
    locale: str | None = "en",
    levels: list[int] | None = None,
    query_context: str | None = None,
) -> UpdateResult:
    """
    Integra el grafo del turno en el State Store y materializa ``StateView``.

    v2: merge incremental de ``ContextGraph`` (N4) entre turnos.
    """
    if not blocks:
        raise ValueError("blocks must not be empty")

    loc = locale or "en"
    sub_levels = sorted(set(levels or [1]))
    if 5 in sub_levels:
        sub_levels = [n for n in sub_levels if n != 5] or [1]

    state_store = store or InMemoryStateStore()
    state = state_store.load(session_id) or SemanticState(session_id=session_id)
    previous_graph = _clone_graph(state.graph) if state.graph is not None else None

    _merge_blocks(state, blocks)

    turn_graph = blocks_to_context_graph(blocks, locale=loc, levels=sub_levels)
    if query_context:
        from ..level4.slice import apply_query_slice

        turn_graph = apply_query_slice(
            turn_graph,
            query_context=query_context,
            max_hops=turn_graph.max_hops,
        )

    state.graph = merge_context_graphs(state.graph, turn_graph)
    if state.graph is not None:
        prose_body = state.graph.render_prose(locale=loc)
        state.graph.optimized_tokens = estimate_tokens(prose_body)

    state.commit_count += 1
    commit_id = f"{session_id}-c{state.commit_count}"

    view = render_state_view(
        state.graph,
        previous=previous_graph,
        locale=loc,
    ) if state.graph is not None else StateView(prose="")

    state.history.append(Commit(commit_id=commit_id, graph=_clone_graph(state.graph)))
    state.head_commit_id = commit_id
    state_store.save(state)

    return UpdateResult(
        view=view,
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
        state.blocks.append(
            ContextBlock(
                id=block_id,
                content=block.content,
                source_type=block.source_type,
                detected_lang=block.detected_lang,
                token_estimate=block.token_estimate,
                metadata=dict(block.metadata),
            )
        )
