"""Integración PCM+COE — compresión de instrucción + contexto optimizado."""

from .backends import (
    InstructionCompressionResult,
    InstructionCompressor,
    OllamaInstructionCompressor,
    StubInstructionCompressor,
    get_instruction_compressor,
)
from .compose import OptimizeWithPCMResult, WindowMetrics, build_pcm_messages, optimize_with_pcm
from .loader import default_pcm_src_path, ensure_pcm_importable

__all__ = [
    "InstructionCompressionResult",
    "InstructionCompressor",
    "OllamaInstructionCompressor",
    "OptimizeWithPCMResult",
    "StubInstructionCompressor",
    "WindowMetrics",
    "build_pcm_messages",
    "default_pcm_src_path",
    "ensure_pcm_importable",
    "get_instruction_compressor",
    "optimize_with_pcm",
]
