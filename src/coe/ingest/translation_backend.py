"""Backends de traducción inyectables para L0."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .translate import translate_text as _benchmark_translate


@runtime_checkable
class TranslationBackend(Protocol):
    """Contrato mínimo para motores MT en L0."""

    name: str

    def translate(self, text: str, *, source_lang: str, target_lang: str) -> str:
        """Traduce ``text`` entre idiomas ISO639-1."""


class BenchmarkStubBackend:
    """Traducción determinista ES→EN para CI y casos benchmark (sin red)."""

    name = "benchmark_stub"

    def translate(self, text: str, *, source_lang: str, target_lang: str) -> str:
        return _benchmark_translate(
            text,
            source_lang=source_lang,
            target_lang=target_lang,
        )


class DeepTranslatorBackend:
    """MT vía ``deep-translator`` (Google Translate público; requiere red)."""

    name = "deep_translator"

    def translate(self, text: str, *, source_lang: str, target_lang: str) -> str:
        from deep_translator import GoogleTranslator

        src = source_lang.split("-")[0].lower()
        tgt = target_lang.split("-")[0].lower()
        if src == tgt:
            return text
        return GoogleTranslator(source=src, target=tgt).translate(text)


def get_default_translation_backend() -> TranslationBackend:
    """Stub offline por defecto; ``deep-translator`` solo si se inyecta explícitamente."""
    return BenchmarkStubBackend()
