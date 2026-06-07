"""DOCX parser strategy (placeholder).

Uses Docling when available; otherwise raises NotImplementedError at parse time.
"""
from __future__ import annotations

import os
from typing import List

from .base import ParserStrategy, register_strategy
from ...models.document import Document


@register_strategy
class DocxStrategy(ParserStrategy):
    EXTENSIONS = {".docx", ".doc"}

    def can_handle(self, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in self.EXTENSIONS

    def parse(self, file_path: str) -> List[Document]:
        try:
            import docling
        except Exception as exc:
            raise NotImplementedError("Docling is required for DOCX parsing. Install docling.") from exc

        # Placeholder return
        doc = Document(
            id=file_path,
            content=f"(parsed DOCX placeholder) {file_path}",
            metadata={"source": file_path, "type": "docx"},
        )
        return [doc]
