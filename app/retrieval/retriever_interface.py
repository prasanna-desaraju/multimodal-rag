"""Retriever interface for retrieving Documents given a query.

This abstraction allows swapping retrieval strategies and ranking
algorithms without changing high-level code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional
import logging

from ..models.document import Document

logger = logging.getLogger(__name__)


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        """Return a list of Documents relevant to the query."""


RETRIEVER_REGISTRY: Dict[str, Type[Retriever]] = {}


def register_retriever(name: str):
    def _decorator(cls: Type[Retriever]) -> Type[Retriever]:
        RETRIEVER_REGISTRY[name] = cls
        logger.debug("Registered retriever: %s -> %s", name, cls)
        return cls

    return _decorator


def get_retriever(name: Optional[str], **kwargs) -> Retriever:
    if not name:
        raise ValueError("Retriever name must be provided")
    cls = RETRIEVER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Retriever not found: {name}")
    return cls(**kwargs)
