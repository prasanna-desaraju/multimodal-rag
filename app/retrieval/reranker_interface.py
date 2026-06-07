"""Reranker interface and registry.

Rerankers score and reorder retrieved documents/chunks. New
implementations should register via the `register_reranker` decorator
so they can be discovered by name without modifying existing code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional
import logging

from ..models.document import Document

logger = logging.getLogger(__name__)


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, documents: List[Document], top_k: Optional[int] = None) -> List[Document]:
        """Return a re-ordered (and possibly truncated) list of Documents."""


RERANKER_REGISTRY: Dict[str, Type[Reranker]] = {}


def register_reranker(name: str):
    def _decorator(cls: Type[Reranker]) -> Type[Reranker]:
        RERANKER_REGISTRY[name] = cls
        logger.debug("Registered reranker: %s -> %s", name, cls)
        return cls

    return _decorator


def get_reranker(name: Optional[str], **kwargs) -> Reranker:
    if not name:
        raise ValueError("Reranker name must be provided")
    cls = RERANKER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Reranker not found: {name}")
    return cls(**kwargs)
