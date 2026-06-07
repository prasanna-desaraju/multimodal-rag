"""Docling-based loader that applies parser strategies.

This loader implements the Strategy Pattern: new parsers are registered
under `app.ingestion.strategies` and discovered at runtime without
modifying this loader code (Open/Closed Principle).
"""
from __future__ import annotations

import logging
import os
from typing import List

from .strategies import STRATEGY_REGISTRY  # registers strategies on import
from ..models.document import Document


logger = logging.getLogger(__name__)


class DoclingLoader:
    """Walks a file or directory and produces `Document` objects.

    The loader selects an appropriate `ParserStrategy` for each file.
    """

    def __init__(self):
        # strategies are instances registered via the decorator
        self._strategies = STRATEGY_REGISTRY

    def _find_strategy(self, path: str):
        for strategy in self._strategies:
            try:
                if strategy.can_handle(path):
                    return strategy
            except Exception:
                # swallow strategy-level errors during capability check
                continue
        return None

    def load(self, source: str) -> List[Document]:
        """Load documents from `source` (file or directory).

        Returns a flat list of `Document` objects.
        """
        docs: List[Document] = []

        if os.path.isdir(source):
            for root, _, files in os.walk(source):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    docs.extend(self._load_file(fpath))
        elif os.path.isfile(source):
            docs.extend(self._load_file(source))
        else:
            raise FileNotFoundError(source)

        return docs

    def _load_file(self, path: str) -> List[Document]:
        strategy = self._find_strategy(path)
        if not strategy:
            logger.warning("No parser strategy found for file: %s", path)
            return []

        try:
            parsed = strategy.parse(path)
            return parsed or []
        except NotImplementedError:
            # bubble up for missing runtime dependencies
            raise
        except Exception:
            logger.exception("Failed to parse file: %s", path)
            return []

