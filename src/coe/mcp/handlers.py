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
    )
    result = optimize_context(
        bundle,
        levels=levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
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
    )
    result = optimize_context(
        bundle,
        levels=levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
    )
    original = result.metrics.original_tokens
    optimized = result.metrics.optimized_tokens
    return {
        "original_tokens": original,
        "optimized_tokens": optimized,
        "tokens_saved": max(0, original - optimized),
        "compression_ratio": round(result.metrics.compression_ratio, 4),
        "latency_ms": round(result.metrics.latency_ms, 2),
        "latency_ms_by_level": {
            k: round(v, 2) for k, v in result.metrics.latency_ms_by_level.items()
        },
        "levels": levels or [1],
    }


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
