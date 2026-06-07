"""Query Rewriter interface and registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
import logging

logger = logging.getLogger(__name__)


class Rewriter(ABC):
    @abstractmethod
    def rewrite(self, query: str) -> str:
        """Rewrite or augment the user query."""


REWRITER_REGISTRY: Dict[str, Type[Rewriter]] = {}


def register_rewriter(name: str):
    def _decorator(cls: Type[Rewriter]) -> Type[Rewriter]:
        REWRITER_REGISTRY[name] = cls
        logger.debug("Registered rewriter: %s -> %s", name, cls)
        return cls

    return _decorator


def get_rewriter(name: Optional[str], **kwargs) -> Rewriter:
    if not name:
        raise ValueError("Rewriter name must be provided")
    cls = REWRITER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Rewriter not found: {name}")
    return cls(**kwargs)
