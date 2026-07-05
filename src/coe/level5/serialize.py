"""Serialización JSON de SemanticState para el State Store N5."""

from __future__ import annotations

from typing import Any

from ..models import ContextBlock, ContextGraph
from .state import Commit, SemanticState

STATE_SCHEMA_VERSION = "0.1"


def context_block_to_dict(block: ContextBlock) -> dict[str, Any]:
    return {
        "id": block.id,
        "content": block.content,
        "metadata": dict(block.metadata),
    }


def context_block_from_dict(data: dict[str, Any]) -> ContextBlock:
    return ContextBlock(
        id=data["id"],
        content=data["content"],
        metadata=dict(data.get("metadata") or {}),
    )


def commit_to_dict(commit: Commit) -> dict[str, Any]:
    return {
        "commit_id": commit.commit_id,
        "graph": commit.graph.to_dict() if commit.graph is not None else None,
    }


def commit_from_dict(data: dict[str, Any]) -> Commit:
    graph_data = data.get("graph")
    return Commit(
        commit_id=data["commit_id"],
        graph=ContextGraph.from_dict(graph_data) if graph_data else None,
    )


def semantic_state_to_dict(state: SemanticState) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "session_id": state.session_id,
        "blocks": [context_block_to_dict(block) for block in state.blocks],
        "graph": state.graph.to_dict() if state.graph is not None else None,
        "head_commit_id": state.head_commit_id,
        "history": [commit_to_dict(commit) for commit in state.history],
        "commit_count": state.commit_count,
    }


def semantic_state_from_dict(data: dict[str, Any]) -> SemanticState:
    graph_data = data.get("graph")
    return SemanticState(
        session_id=data["session_id"],
        blocks=[context_block_from_dict(item) for item in data.get("blocks") or []],
        graph=ContextGraph.from_dict(graph_data) if graph_data else None,
        head_commit_id=data.get("head_commit_id"),
        history=[commit_from_dict(item) for item in data.get("history") or []],
        commit_count=int(data.get("commit_count") or 0),
    )
