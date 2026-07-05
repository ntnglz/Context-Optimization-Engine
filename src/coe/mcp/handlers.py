"""Handlers MCP — lógica pura reutilizable por el servidor y los tests."""

from __future__ import annotations

import json
from typing import Any

from ..gateway import optimize_context
from ..ingest import ingest_context
from ..models import ContextBlock


def _resolve_input(
    blocks: list[dict[str, Any]],
    *,
    locale: str | None = None,
    target_lang: str | None = None,
    query_context: str | None = None,
    response_lang: str | None = None,
    session_id: str | None = None,
    section_delimiters: bool | None = None,
    include_pending_turn: bool | None = None,
    max_commits: int | None = None,
    max_context_tokens: int | None = None,
    target_model: str | None = None,
    session_ttl_hours: float | None = None,
    fuzzy_link_threshold: float | None = None,
    state_store_backend: str | None = None,
    state_store_path: str | None = None,
):
    if not blocks:
        raise ValueError("blocks must not be empty")
    ingest = ingest_context(
        blocks,
        target_lang=target_lang,
        locale=locale,
        query_context=query_context,
        response_lang=response_lang,
        session_id=session_id,
    )
    bundle = ingest.bundle
    if section_delimiters is not None:
        bundle.options.section_delimiters = section_delimiters
    if include_pending_turn is not None:
        bundle.options.include_pending_turn = include_pending_turn
    if max_commits is not None:
        bundle.options.max_commits = max_commits
    if max_context_tokens is not None:
        bundle.options.max_context_tokens = max_context_tokens
    if target_model is not None:
        bundle.options.target_model = target_model
    if session_ttl_hours is not None:
        bundle.options.session_ttl_hours = session_ttl_hours
    if fuzzy_link_threshold is not None:
        bundle.options.fuzzy_link_threshold = fuzzy_link_threshold
    if state_store_backend is not None:
        bundle.options.state_store_backend = state_store_backend
    if state_store_path is not None:
        bundle.options.state_store_path = state_store_path
    return bundle


def handle_optimize_context(
    blocks: list[dict[str, Any]],
    *,
    levels: list[int] | None = None,
    locale: str | None = None,
    target_lang: str | None = None,
    l0: bool = False,
    session_id: str | None = None,
    query_context: str | None = None,
    response_lang: str | None = None,
    section_delimiters: bool | None = None,
    include_pending_turn: bool | None = None,
    max_commits: int | None = None,
    max_context_tokens: int | None = None,
    target_model: str | None = None,
    session_ttl_hours: float | None = None,
    fuzzy_link_threshold: float | None = None,
    state_store_backend: str | None = None,
    state_store_path: str | None = None,
) -> dict[str, Any]:
    """Ejecuta el pipeline COE y devuelve prosa optimizada + métricas."""
    bundle = _resolve_input(
        blocks,
        locale=locale,
        target_lang=target_lang,
        query_context=query_context,
        response_lang=response_lang,
        session_id=session_id,
        section_delimiters=section_delimiters,
        include_pending_turn=include_pending_turn,
        max_commits=max_commits,
        max_context_tokens=max_context_tokens,
        target_model=target_model,
        session_ttl_hours=session_ttl_hours,
        fuzzy_link_threshold=fuzzy_link_threshold,
        state_store_backend=state_store_backend,
        state_store_path=state_store_path,
    )
    result = optimize_context(
        bundle,
        levels=levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
        target_model=target_model,
        session_ttl_hours=session_ttl_hours,
        fuzzy_link_threshold=fuzzy_link_threshold,
        state_store_backend=state_store_backend,
        state_store_path=state_store_path,
    )
    payload = result.to_dict()
    payload["text"] = result.text
    if result.commit_id is not None:
        payload["commit_id"] = result.commit_id
    return payload


def handle_estimate_savings(
    blocks: list[dict[str, Any]],
    *,
    levels: list[int] | None = None,
    locale: str | None = None,
    target_lang: str | None = None,
    l0: bool = False,
    session_id: str | None = None,
    query_context: str | None = None,
    response_lang: str | None = None,
    section_delimiters: bool | None = None,
    include_pending_turn: bool | None = None,
    max_commits: int | None = None,
    max_context_tokens: int | None = None,
    target_model: str | None = None,
    session_ttl_hours: float | None = None,
    fuzzy_link_threshold: float | None = None,
    state_store_backend: str | None = None,
    state_store_path: str | None = None,
) -> dict[str, Any]:
    """Estima tokens ahorrados sin devolver prosa ni invocar evaluador LLM."""
    bundle = _resolve_input(
        blocks,
        locale=locale,
        target_lang=target_lang,
        query_context=query_context,
        response_lang=response_lang,
        session_id=session_id,
        section_delimiters=section_delimiters,
        include_pending_turn=include_pending_turn,
        max_commits=max_commits,
        max_context_tokens=max_context_tokens,
        target_model=target_model,
        session_ttl_hours=session_ttl_hours,
        fuzzy_link_threshold=fuzzy_link_threshold,
        state_store_backend=state_store_backend,
        state_store_path=state_store_path,
    )
    result = optimize_context(
        bundle,
        levels=levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
        target_model=target_model,
        session_ttl_hours=session_ttl_hours,
        fuzzy_link_threshold=fuzzy_link_threshold,
        state_store_backend=state_store_backend,
        state_store_path=state_store_path,
    )
    original = result.metrics.original_tokens
    optimized = result.metrics.optimized_tokens
    payload = {
        "original_tokens": original,
        "optimized_tokens": optimized,
        "tokens_saved": max(0, original - optimized),
        "compression_ratio": round(result.metrics.compression_ratio, 4),
        "latency_ms": round(result.metrics.latency_ms, 2),
        "latency_ms_by_level": {
            k: round(v, 2) for k, v in result.metrics.latency_ms_by_level.items()
        },
        "truncated": result.metrics.truncated,
        "levels": levels or [1],
    }
    if result.metrics.target_model is not None:
        payload["target_model"] = result.metrics.target_model
    if result.metrics.model_adapter is not None:
        payload["model_adapter"] = result.metrics.model_adapter
    if result.metrics.store_metrics is not None:
        payload["store"] = result.metrics.store_metrics
    if result.metrics.pre_truncation_tokens is not None:
        payload["pre_truncation_tokens"] = result.metrics.pre_truncation_tokens
    return payload


def blocks_from_context_block_models(blocks: list[ContextBlock]) -> list[dict[str, Any]]:
    """Serializa ``ContextBlock`` a dicts para la API MCP."""
    return [
        {
            "id": block.id,
            "content": block.content,
            "source_type": block.source_type,
            **({"detected_lang": block.detected_lang} if block.detected_lang else {}),
            **({"metadata": dict(block.metadata)} if block.metadata else {}),
        }
        for block in blocks
    ]


def format_tool_result(data: dict[str, Any]) -> str:
    """JSON compacto para respuestas MCP."""
    return json.dumps(data, ensure_ascii=False, indent=2)
