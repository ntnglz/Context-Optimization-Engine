"""Backends de compresión de instrucción (PCM real o stub determinista)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from ..models import estimate_tokens
from .loader import get_prompt_compressor_class


@dataclass
class InstructionCompressionResult:
    original: str
    compressed: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    skipped: bool = False
    backend: str = "stub"
    processing_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class InstructionCompressor(Protocol):
    name: str

    def compress(self, instruction: str) -> InstructionCompressionResult:
        """Comprime la instrucción del usuario a formato PCM."""


class StubInstructionCompressor:
    """Compresión determinista para CI — sin Ollama."""

    name = "stub"

    def compress(self, instruction: str) -> InstructionCompressionResult:
        original = instruction.strip()
        original_tokens = estimate_tokens(original)
        lower = original.lower()

        if "who works" in lower and "acme" in lower:
            compressed = "TASK=query TEAM@ACME REL=works_at"
            forced = True
        elif "budget" in lower or "presupuesto" in lower:
            compressed = "TASK=query TOPIC=budget ENTITY=ACME"
            forced = True
        elif "warning" in lower:
            compressed = "TASK=analyze DOMAIN=swift TYPE=warnings"
            forced = True
        else:
            slug = re.sub(r"[^a-z0-9]+", "_", lower).strip("_")[:48]
            compressed = f"TASK={slug or 'query'}"
            forced = False

        compressed_tokens = estimate_tokens(compressed)
        skipped = not forced and compressed_tokens >= original_tokens
        if skipped:
            compressed = original
            compressed_tokens = original_tokens

        ratio = 0.0
        if original_tokens:
            ratio = 1.0 - (compressed_tokens / original_tokens)

        return InstructionCompressionResult(
            original=original,
            compressed=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=ratio,
            skipped=skipped,
            backend=self.name,
            metadata={"deterministic": True},
        )


class OllamaInstructionCompressor:
    """Wrapper sobre ``pcm.PromptCompressor`` (Ollama local)."""

    name = "ollama"

    def __init__(self, *, model: str = "granite4.1:3b") -> None:
        compressor_cls = get_prompt_compressor_class()
        if compressor_cls is None:
            raise RuntimeError(
                "PCM not importable. Set PCM_ROOT to "
                "'../Prompt Compression Middleware' or install pcm."
            )
        from pcm.compressor import CompressorConfig

        self._compressor = compressor_cls(CompressorConfig(model=model))

    def compress(self, instruction: str) -> InstructionCompressionResult:
        result = self._compressor.compress(instruction)
        skipped = bool(result.metadata.get("skipped"))
        return InstructionCompressionResult(
            original=result.original_prompt,
            compressed=result.compressed_prompt,
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            compression_ratio=result.compression_ratio,
            skipped=skipped,
            backend=self.name,
            processing_time_ms=result.processing_time_ms,
            metadata=dict(result.metadata),
        )


def get_instruction_compressor(backend: str = "stub") -> InstructionCompressor:
    key = backend.strip().lower()
    if key in {"stub", "mock", "deterministic"}:
        return StubInstructionCompressor()
    if key in {"ollama", "pcm", "runtime"}:
        return OllamaInstructionCompressor()
    raise ValueError(f"Unknown PCM backend: {backend!r}")
