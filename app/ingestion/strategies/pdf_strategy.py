"""PDF parser strategy using Docling (placeholder).

This strategy demonstrates the Strategy Pattern. The actual Docling
integration is optional at runtime; if `docling` is not installed the
strategy will raise `NotImplementedError` when used.
"""
from __future__ import annotations

import os
from typing import List

from .base import ParserStrategy, register_strategy
from ...models.document import Document


@register_strategy
class PDFStrategy(ParserStrategy):
    EXTENSIONS = {".pdf"}

    def can_handle(self, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in self.EXTENSIONS

    def parse(self, file_path: str) -> List[Document]:
        try:
            import docling
        except Exception as exc:
            raise NotImplementedError("Docling is required for PDF parsing. Install docling.") from exc

        # Placeholder: real Docling integration should parse text, tables and images.
        # For now, present a minimal contract-compliant Document.
        doc = Document(
            id=file_path,
            content=f"(parsed PDF placeholder) {file_path}",
            metadata={"source": file_path, "type": "pdf"},
        )
        return [doc]
