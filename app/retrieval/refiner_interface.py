"""Context Refiner interface and registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional
import logging

from ..models.document import Document

logger = logging.getLogger(__name__)


class Refiner(ABC):
    @abstractmethod
    def refine(self, original_query: str, documents: List[Document]) -> List[Document]:
        """Refine or filter retrieved documents given the original query."""


REFINER_REGISTRY: Dict[str, Type[Refiner]] = {}


def register_refiner(name: str):
    def _decorator(cls: Type[Refiner]) -> Type[Refiner]:
        REFINER_REGISTRY[name] = cls
        logger.debug("Registered refiner: %s -> %s", name, cls)
        return cls

    return _decorator


def get_refiner(name: Optional[str], **kwargs) -> Refiner:
    if not name:
        raise ValueError("Refiner name must be provided")
    cls = REFINER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Refiner not found: {name}")
    return cls(**kwargs)
