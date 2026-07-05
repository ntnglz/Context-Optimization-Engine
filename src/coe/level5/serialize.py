"""Serialización JSON de SemanticState para el State Store N5."""

from __future__ import annotations

from typing import Any

from ..models import ContextBlock, ContextGraph
from ..cir import envelope_from_context_graph, context_graph_from_envelope
from .state import Commit, RetractRecord, SemanticState

STATE_SCHEMA_VERSION = "0.1"


def context_block_to_dict(block: ContextBlock) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": block.id,
        "content": block.content,
        "source_type": block.source_type,
        "metadata": dict(block.metadata),
    }
    if block.detected_lang is not None:
        data["detected_lang"] = block.detected_lang
    if block.token_estimate is not None:
        data["token_estimate"] = block.token_estimate
    return data


def context_block_from_dict(data: dict[str, Any]) -> ContextBlock:
    return ContextBlock(
        id=data["id"],
        content=data["content"],
        source_type=data.get("source_type", "prose"),
        detected_lang=data.get("detected_lang"),
        token_estimate=data.get("token_estimate"),
        metadata=dict(data.get("metadata") or {}),
    )


def commit_to_dict(commit: Commit) -> dict[str, Any]:
    return {
        "commit_id": commit.commit_id,
        "graph": envelope_from_context_graph(commit.graph)
        if commit.graph is not None
        else None,
    }


def commit_from_dict(data: dict[str, Any]) -> Commit:
    graph_data = data.get("graph")
    return Commit(
        commit_id=data["commit_id"],
        graph=context_graph_from_envelope(graph_data) if graph_data else None,
    )


def retract_record_to_dict(record: RetractRecord) -> dict[str, Any]:
    return {
        "commit_id": record.commit_id,
        "previous": record.previous,
        "corrects": record.corrects,
        "source_id": record.source_id,
    }


def retract_record_from_dict(data: dict[str, Any]) -> RetractRecord:
    return RetractRecord(
        commit_id=data["commit_id"],
        previous=str(data.get("previous") or ""),
        corrects=data["corrects"],
        source_id=data["source_id"],
    )


def semantic_state_to_dict(state: SemanticState) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "session_id": state.session_id,
        "blocks": [context_block_to_dict(block) for block in state.blocks],
        "graph": envelope_from_context_graph(state.graph)
        if state.graph is not None
        else None,
        "head_commit_id": state.head_commit_id,
        "history": [commit_to_dict(commit) for commit in state.history],
        "commit_count": state.commit_count,
        "max_commits": state.max_commits,
        "retract_log": [retract_record_to_dict(record) for record in state.retract_log],
        "updated_at": state.updated_at,
        "history_pruned_total": state.history_pruned_total,
    }


def semantic_state_from_dict(data: dict[str, Any]) -> SemanticState:
    graph_data = data.get("graph")
    return SemanticState(
        session_id=data["session_id"],
        blocks=[context_block_from_dict(item) for item in data.get("blocks") or []],
        graph=context_graph_from_envelope(graph_data) if graph_data else None,
        head_commit_id=data.get("head_commit_id"),
        history=[commit_from_dict(item) for item in data.get("history") or []],
        commit_count=int(data.get("commit_count") or 0),
        max_commits=int(data.get("max_commits") or 100),
        retract_log=[
            retract_record_from_dict(item) for item in data.get("retract_log") or []
        ],
        updated_at=float(data["updated_at"]) if data.get("updated_at") is not None else None,
        history_pruned_total=int(data.get("history_pruned_total") or 0),
    )
