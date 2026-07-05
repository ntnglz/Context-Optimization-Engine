"""Modelos de petición HTTP — paridad con MCP."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContextBlocksRequest(BaseModel):
    """Cuerpo compartido por ``POST /optimize`` y ``POST /estimate``."""

    blocks: list[dict[str, Any]] = Field(..., min_length=1)
    levels: list[int] | None = None
    locale: str | None = "en"
    target_lang: str | None = None
    l0: bool = False
    session_id: str | None = None
    query_context: str | None = None
    response_lang: str | None = None
    section_delimiters: bool | None = None
    include_pending_turn: bool | None = None
    max_commits: int | None = None
    max_context_tokens: int | None = None
    target_model: str | None = None
    session_ttl_hours: float | None = None
    fuzzy_link_threshold: float | None = None

    def handler_kwargs(self) -> dict[str, Any]:
        return {
            "blocks": self.blocks,
            "levels": self.levels,
            "locale": self.locale,
            "target_lang": self.target_lang,
            "l0": self.l0,
            "session_id": self.session_id,
            "query_context": self.query_context,
            "response_lang": self.response_lang,
            "section_delimiters": self.section_delimiters,
            "include_pending_turn": self.include_pending_turn,
            "max_commits": self.max_commits,
            "max_context_tokens": self.max_context_tokens,
            "target_model": self.target_model,
            "session_ttl_hours": self.session_ttl_hours,
            "fuzzy_link_threshold": self.fuzzy_link_threshold,
        }
