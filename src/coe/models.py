"""Modelos de datos compartidos de COE."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


def estimate_tokens(text: str) -> int:
    """Estimación rápida de tokens (~4 chars/token en texto mixto)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class ContextBlock:
    """Fragmento de contexto con identificador estable."""

    id: str
    content: str

    def token_count(self) -> int:
        return estimate_tokens(self.content)


@dataclass
class SharedFact:
    """Hecho repetido extraído a representación compartida."""

    canonical_line: str
    normalized_key: str
    source_ids: list[str] = field(default_factory=list)

    def to_compact(self) -> str:
        """Formato clave=valor si la línea usa ':', si no la línea literal."""
        if ":" in self.canonical_line:
            key, _, value = self.canonical_line.partition(":")
            return f"{key.strip()}={value.strip()}"
        return self.canonical_line.strip()


@dataclass
class DeduplicationResult:
    """Resultado del optimizador Nivel 1."""

    shared_facts: list[SharedFact]
    unique_blocks: list[ContextBlock]
    original_tokens: int
    optimized_tokens: int

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.optimized_tokens / self.original_tokens)

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.optimized_tokens

    def render(self) -> str:
        from .level1.render import render_deduplication

        if not self.shared_facts and not any(b.content.strip() for b in self.unique_blocks):
            return ""
        if not self.shared_facts:
            return "\n\n".join(
                f"[{block.id}]\n{block.content}" for block in self.unique_blocks if block.content.strip()
            ) + "\n"
        return render_deduplication(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shared_facts": [
                {
                    "compact": fact.to_compact(),
                    "canonical_line": fact.canonical_line,
                    "source_ids": fact.source_ids,
                }
                for fact in self.shared_facts
            ],
            "unique_blocks": [
                {"id": block.id, "content": block.content} for block in self.unique_blocks
            ],
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "compression_ratio": round(self.compression_ratio, 4),
            "tokens_saved": self.tokens_saved,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
