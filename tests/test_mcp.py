"""Tests MCP COE — handlers y registro de herramientas."""

from __future__ import annotations

import asyncio
import json

import pytest

pytest.importorskip("mcp")

from coe.mcp.handlers import handle_estimate_savings, handle_optimize_context
from coe.mcp.server import mcp


SAMPLE_BLOCKS = [
    {"id": "A", "content": "Empresa: ACME\nCliente: Globex"},
    {"id": "B", "content": "Empresa: ACME\nPresupuesto: 50k"},
    {"id": "C", "content": "Empresa: ACME\nCliente: Globex"},
]


class TestMcpHandlers:
    def test_optimize_context_returns_prose_and_metrics(self):
        result = handle_optimize_context(SAMPLE_BLOCKS, levels=[1], locale="en")

        assert "text" in result
        assert "metrics" in result
        assert result["metrics"]["original_tokens"] > 0
        assert "multiple sources" in result["text"] or "ACME" in result["text"]

    def test_estimate_savings_returns_tokens_without_text(self):
        result = handle_estimate_savings(SAMPLE_BLOCKS, levels=[1], locale="en")

        assert "text" not in result
        assert result["original_tokens"] > 0
        assert result["optimized_tokens"] >= 0
        assert result["tokens_saved"] >= 0
        assert "compression_ratio" in result
        assert result["levels"] == [1]

    def test_estimate_savings_n1_n2(self):
        blocks = [
            {"id": "A", "content": "Juan works at ACME."},
            {"id": "B", "content": "Juan approved the budget."},
        ]
        result = handle_estimate_savings(blocks, levels=[1, 2], locale="en")

        assert result["tokens_saved"] >= 0
        assert "n1" in result["latency_ms_by_level"] or "n2" in result["latency_ms_by_level"]

    def test_optimize_context_empty_blocks_raises(self):
        with pytest.raises(ValueError, match="blocks must not be empty"):
            handle_optimize_context([])


class TestMcpServer:
    def test_server_exposes_tools(self):
        async def _run():
            return await mcp.list_tools()

        tools = asyncio.run(_run())
        names = {tool.name for tool in tools}
        assert names == {"optimize_context", "estimate_savings"}

    def test_call_optimize_context_tool(self):
        async def _run():
            return await mcp.call_tool(
                "optimize_context",
                {
                    "blocks": SAMPLE_BLOCKS,
                    "levels": [1],
                    "locale": "en",
                },
            )

        content, _meta = asyncio.run(_run())
        assert content
        payload = json.loads(content[0].text)
        assert "text" in payload
        assert "metrics" in payload

    def test_call_estimate_savings_tool(self):
        async def _run():
            return await mcp.call_tool(
                "estimate_savings",
                {
                    "blocks": SAMPLE_BLOCKS,
                    "levels": [1],
                    "locale": "en",
                },
            )

        content, _meta = asyncio.run(_run())
        payload = json.loads(content[0].text)
        assert "tokens_saved" in payload
        assert "text" not in payload
