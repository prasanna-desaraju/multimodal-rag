"""Image parser strategy (placeholder).

Extracts image references and optional OCR via Docling if available.
"""
from __future__ import annotations

import os
from typing import List

from .base import ParserStrategy, register_strategy
from ...models.document import Document


@register_strategy
class ImageStrategy(ParserStrategy):
    EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}

    def can_handle(self, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in self.EXTENSIONS

    def parse(self, file_path: str) -> List[Document]:
        try:
            import docling
        except Exception as exc:
            raise NotImplementedError("Docling (or an OCR library) is required for image parsing.") from exc

        doc = Document(
            id=file_path,
            content="",
            metadata={"source": file_path, "type": "image"},
        )
        return [doc]
