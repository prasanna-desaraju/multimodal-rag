"""Base parser strategy and registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
import logging

from ...models.document import Document


logger = logging.getLogger(__name__)


STRATEGY_REGISTRY: List["ParserStrategy"] = []


def register_strategy(strategy_cls):
    """Class decorator to register a ParserStrategy implementation."""

    instance = strategy_cls()
    STRATEGY_REGISTRY.append(instance)
    logger.debug("Registered parser strategy: %s", strategy_cls.__name__)
    return strategy_cls


class ParserStrategy(ABC):
    """Abstract parser strategy.

    Implementations parse one or more Documents from a file path and
    advertise which file extensions they handle via `can_handle()`.
    """

    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """Return True if this strategy can parse the given file."""

    @abstractmethod
    def parse(self, file_path: str) -> List[Document]:
        """Parse the file and return a list of Document objects."""
        