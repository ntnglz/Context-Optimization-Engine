"""Aplicación FastAPI — paridad HTTP con herramientas MCP."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from ..mcp.handlers import handle_estimate_savings, handle_optimize_context
from .schemas import ContextBlocksRequest

app = FastAPI(
    title="Context Optimization Engine",
    description="HTTP API for COE — same surface as MCP optimize_context / estimate_savings.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "coe"}


@app.post("/optimize")
def optimize(body: ContextBlocksRequest) -> dict:
    """Optimiza bloques de contexto; devuelve prosa + métricas (como MCP ``optimize_context``)."""
    try:
        return handle_optimize_context(**body.handler_kwargs())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


@app.post("/estimate")
def estimate(body: ContextBlocksRequest) -> dict:
    """Estima ahorro de tokens sin devolver prosa (como MCP ``estimate_savings``)."""
    try:
        return handle_estimate_savings(**body.handler_kwargs())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
