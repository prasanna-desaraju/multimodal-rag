"""Chart extraction strategy placeholder.

Charts are typically images embedded in documents; this strategy can
be extended to recognize chart image types or vector formats.
"""
from __future__ import annotations

import os
from typing import List

from .base import ParserStrategy, register_strategy
from ...models.document import Document


@register_strategy
class ChartStrategy(ParserStrategy):
    EXTENSIONS = {".svg"}

    def can_handle(self, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in self.EXTENSIONS

    def parse(self, file_path: str) -> List[Document]:
        doc = Document(
            id=file_path,
            content="",
            metadata={"source": file_path, "type": "chart"},
        )
        return [doc]
