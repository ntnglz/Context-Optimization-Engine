"""Interfaz Model Adapter — post-renderer, pre-LLM."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ModelAdapter(ABC):
    """Ajusta formato de prosa optimizada al modelo destino (no idioma ni hechos)."""

    id: str

    @abstractmethod
    def adapt(self, text: str, target_model: str) -> str:
        """Devuelve prosa con marcadores/secciones preferidos por el modelo."""
