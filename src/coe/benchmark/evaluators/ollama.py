"""Evaluador LLM vía API HTTP de Ollama."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from .base import LLMResult, Message


class OllamaEvaluator:
    """Cliente mínimo para ``POST /api/chat`` de Ollama."""

    def __init__(
        self,
        *,
        model: str | None = None,
        host: str | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        self.model = model or os.environ.get("OLLAMA_MODEL", "qwen3:8b")
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip(
            "/"
        )
        self.timeout_s = timeout_s

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
    ) -> LLMResult:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        t0 = time.perf_counter()
        data = self._post_json("/api/chat", payload)
        elapsed = (time.perf_counter() - t0) * 1000.0
        message = data.get("message") or {}
        text = str(message.get("content", "")).strip()
        return LLMResult(text=text, model=self.model, latency_ms=elapsed)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.host}{path}"
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise ConnectionError(
                    f"Ollama model or endpoint not found ({url}): {exc}. "
                    f"Check model name {self.model!r} with `ollama list` or `ollama pull`."
                ) from exc
            raise ConnectionError(
                f"Ollama request failed ({url}): {exc}. "
                "Is Ollama running? Set OLLAMA_HOST if needed."
            ) from exc
        except urllib.error.URLError as exc:
            raise ConnectionError(
                f"Ollama request failed ({url}): {exc}. "
                "Is Ollama running? Set OLLAMA_HOST if needed."
            ) from exc
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected Ollama response: {raw[:200]}")
        return data
