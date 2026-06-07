"""Table extraction strategy placeholder.

Some files (e.g., CSV, Excel, HTML) may carry tables. Strategies can
be added later without modifying the loader.
"""
from __future__ import annotations

import os
from typing import List

from .base import ParserStrategy, register_strategy
from ...models.document import Document


@register_strategy
class TableStrategy(ParserStrategy):
    EXTENSIONS = {".csv", ".xls", ".xlsx", ".html"}

    def can_handle(self, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in self.EXTENSIONS

    def parse(self, file_path: str) -> List[Document]:
        # For now, return a placeholder Document indicating table presence.
        doc = Document(
            id=file_path,
            content="",
            metadata={"source": file_path, "type": "table"},
        )
        return [doc]
