"""Chunker interface and registry for chunking strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
import logging

from ..models.chunk import Chunk

logger = logging.getLogger(__name__)

CHUNKER_REGISTRY: List["Chunker"] = []


def register_chunker(chunker_cls):
    """Class decorator to register a Chunker implementation."""

    instance = chunker_cls()
    CHUNKER_REGISTRY.append(instance)
    logger.debug("Registered chunker: %s", chunker_cls.__name__)
    return chunker_cls


class Chunker(ABC):
    """Abstract chunker interface.

    Implementations must provide `can_handle()` and `chunk()` methods.
    `chunk()` returns a list of `Chunk` objects.
    """

    @abstractmethod
    def can_handle(self, modality: str, source: Optional[str] = None) -> bool:
        """Return True if this chunker can handle the given modality/source."""

    @abstractmethod
    def chunk(self, payload: Any, source_file: Optional[str] = None, page_number: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """Break payload into chunks and return list of `Chunk` objects."""
*** End Patch