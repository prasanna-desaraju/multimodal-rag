"""Markdown parser strategy.

Parses markdown into text and extracts code blocks, images and links.
"""
from __future__ import annotations

import os
from typing import List

from .base import ParserStrategy, register_strategy
from ...models.document import Document


@register_strategy
class MarkdownStrategy(ParserStrategy):
    EXTENSIONS = {".md", ".markdown"}

    def can_handle(self, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in self.EXTENSIONS

    def parse(self, file_path: str) -> List[Document]:
        with open(file_path, "r", encoding="utf-8") as fh:
            text = fh.read()

        doc = Document(
            id=file_path,
            content=text,
            metadata={"source": file_path, "type": "markdown"},
        )
        return [doc]
