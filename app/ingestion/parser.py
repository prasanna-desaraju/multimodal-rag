"""Parser facade that delegates to the DoclingLoader.

Higher-level code should call `parse_path()` to obtain a list of
`Document` objects. The implementation uses registered strategies so
new file types can be added without modifying this module.
"""
from __future__ import annotations

from typing import List

from .docling_loader import DoclingLoader
from ..models.document import Document


def parse_path(path: str) -> List[Document]:
    loader = DoclingLoader()
    return loader.load(path)
