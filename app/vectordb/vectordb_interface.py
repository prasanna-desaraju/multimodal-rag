"""Vector store interface (VectorStore) for Dependency Inversion.

High-level modules should depend on this interface so stores can be
swapped (Chroma, FAISS, Weaviate, Pinecone, etc.). This module also
provides a simple registry and factory so new providers can be added
without modifying existing code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
import logging

from ..models.document import Document

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract VectorStore interface."""

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add or upsert documents into the store."""

    @abstractmethod
    def query(self, embedding: List[float], top_k: int = 10, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Query the store by embedding and return matching Documents."""

    @abstractmethod
    def persist(self) -> None:
        """Persist any in-memory state to disk/cloud."""

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete documents by id."""


# Registry and factory for VectorStore implementations
VECTORDB_REGISTRY: Dict[str, Type[VectorStore]] = {}


def register_vectordb(name: str):
    def _decorator(cls: Type[VectorStore]) -> Type[VectorStore]:
        VECTORDB_REGISTRY[name] = cls
        logger.debug("Registered vectordb provider: %s -> %s", name, cls)
        return cls

    return _decorator


def get_vectordb(name: str, **kwargs) -> VectorStore:
    cls = VECTORDB_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Vector DB provider not registered: {name}")
    return cls(**kwargs)
