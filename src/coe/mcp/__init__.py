"""MCP — integración COE para agentes."""

from .handlers import (
    blocks_from_context_block_models,
    format_tool_result,
    handle_estimate_savings,
    handle_optimize_context,
)
from .server import mcp

__all__ = [
    "blocks_from_context_block_models",
    "format_tool_result",
    "handle_estimate_savings",
    "handle_optimize_context",
    "mcp",
]
