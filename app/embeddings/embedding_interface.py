"""Embedder interface and registry to enforce Dependency Inversion.

High-level modules should depend on the `Embedder` interface rather
than concrete implementations. This module also provides a simple
registry and factory so new embedder implementations can be added
without modifying existing code (Open/Closed Principle).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
import logging


logger = logging.getLogger(__name__)


class Embedder(ABC):
    """Abstract embedding model interface."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for a list of texts."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Return an embedding for a single query."""


# Simple registry to allow discovery and factory creation of embedders
EMBEDDER_REGISTRY: Dict[str, Type[Embedder]] = {}


def register_embedder(name: str):
    """Decorator to register an Embedder implementation under `name`.

    Usage:
        @register_embedder("sentence-transformers")
        class SentenceTransformerEmbedder(Embedder):
            ...
    """

    def _decorator(cls: Type[Embedder]) -> Type[Embedder]:
        EMBEDDER_REGISTRY[name] = cls
        logger.debug("Registered embedder: %s -> %s", name, cls)
        return cls

    return _decorator


def get_embedder(name: Optional[str] = None, **kwargs) -> Embedder:
    """Factory to instantiate a registered embedder by name.

    If `name` is None the caller should provide an explicit name to
    avoid surprises. The factory will raise `ValueError` if the named
    embedder is not registered.
    """

    if not name:
        raise ValueError("Embedder name must be provided")

    cls = EMBEDDER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Embedder not found for name: {name}")
    return cls(**kwargs)
