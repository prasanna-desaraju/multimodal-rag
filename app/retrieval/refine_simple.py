"""Simple refiner that trims or reorders retrieved documents.

This placeholder returns the top N documents unchanged but demonstrates
how refiners can be plugged in.
"""
from __future__ import annotations

from typing import List, Optional

from .refiner_interface import Refiner, register_refiner
from ..models.document import Document


@register_refiner("simple")
class SimpleRefiner(Refiner):
    def __init__(self, max_docs: int = 5):
        self.max_docs = max_docs

    def refine(self, original_query: str, documents: List[Document]) -> List[Document]:
        return documents[: self.max_docs]
