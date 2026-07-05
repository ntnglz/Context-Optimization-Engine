"""Servidor MCP COE — herramientas para agentes."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .handlers import format_tool_result, handle_estimate_savings, handle_optimize_context

mcp = FastMCP(
    "coe",
    instructions=(
        "Context Optimization Engine (COE). "
        "Use optimize_context to compress RAG/history/tool context for LLMs. "
        "Use estimate_savings for token metrics without returning optimized prose."
    ),
)


@mcp.tool(
    name="optimize_context",
    description=(
        "Optimize context blocks through the COE pipeline (L0, N1–N5). "
        "Returns optimized prose for the LLM plus compression metrics."
    ),
)
def optimize_context_tool(
    blocks: list[dict[str, Any]],
    levels: list[int] | None = None,
    locale: str | None = "en",
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
) -> str:
    """
    Run COE on raw context blocks.

    Args:
        blocks: List of dicts with at least ``content`` (or ``text``) and optional ``id``, ``source_type``.
        levels: Pipeline levels to apply (default [1]). Use [1,5] for session state (N5).
        locale: Locale pack for N2+ rendering (default en).
        target_lang: Target language for L0 normalization when l0=True.
        l0: Enable L0 language normalization before optimization.
        session_id: Session id for N5 state store (auto-persists when set).
        query_context: Optional query for N4 graph slicing.
        response_lang: Response language hint stored on the bundle.
        section_delimiters: Include section headers in gateway output.
        include_pending_turn: With N5, also render pending turn prose.
        max_commits: N5 history retention limit.
        max_context_tokens: Hard cap on optimized context tokens (post-render budget).
        target_model: Optional model id (e.g. mistral-large, gpt-4o) for post-render format adaptation.
    """
    result = handle_optimize_context(
        blocks,
        levels=levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
        query_context=query_context,
        response_lang=response_lang,
        section_delimiters=section_delimiters,
        include_pending_turn=include_pending_turn,
        max_commits=max_commits,
        max_context_tokens=max_context_tokens,
        target_model=target_model,
    )
    return format_tool_result(result)


@mcp.tool(
    name="estimate_savings",
    description=(
        "Estimate token savings from COE without returning optimized prose "
        "and without running any LLM evaluator."
    ),
)
def estimate_savings_tool(
    blocks: list[dict[str, Any]],
    levels: list[int] | None = None,
    locale: str | None = "en",
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
) -> str:
    """
    Return token savings metrics only (no optimized text).

    Same options as optimize_context; useful for ROI checks before sending context to an LLM.
    """
    result = handle_estimate_savings(
        blocks,
        levels=levels,
        locale=locale,
        target_lang=target_lang,
        l0=l0,
        session_id=session_id,
        query_context=query_context,
        response_lang=response_lang,
        section_delimiters=section_delimiters,
        include_pending_turn=include_pending_turn,
        max_commits=max_commits,
        max_context_tokens=max_context_tokens,
        target_model=target_model,
    )
    return format_tool_result(result)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
