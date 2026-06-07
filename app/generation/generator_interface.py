"""Generator interface and registry to abstract LLM providers.

Implementations (Grok, OpenAI, Claude, etc.) should register via
the `register_generator` decorator so callers can obtain providers by name.

The `generate` method accepts a `query` and `inserted_context` (list of
`Document`) and returns a dictionary with at least a `text` key.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type, Optional
import logging

from ..models.document import Document

logger = logging.getLogger(__name__)


class Generator(ABC):
    @abstractmethod
    def generate(self, query: str, inserted_context: List[Document], timeout: Optional[float] = None, retries: int = 3, **kwargs) -> Dict[str, Any]:
        """Generate a grounded answer.

        Returns a dict with at least `text` (str). Implementations may add
        provider-specific fields under other keys.
        """


GENERATOR_REGISTRY: Dict[str, Type[Generator]] = {}


def register_generator(name: str):
    def _decorator(cls: Type[Generator]) -> Type[Generator]:
        GENERATOR_REGISTRY[name] = cls
        logger.debug("Registered generator: %s -> %s", name, cls)
        return cls

    return _decorator


def get_generator(name: Optional[str], **kwargs) -> Generator:
    if not name:
        raise ValueError("Generator name must be provided")
    cls = GENERATOR_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Generator not found: {name}")
    return cls(**kwargs)
