"""TableChunker implementation placeholder.

Accepts a table-like payload (e.g., pandas.DataFrame or list-of-rows)
and returns chunk(s) representing table content. Real table chunking
may produce multiple chunks per table (per row, per region).
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from .chunker_interface import Chunker, register_chunker
from ..models.chunk import Chunk


@register_chunker
class TableChunker(Chunker):
    MODALITY = "table"

    def can_handle(self, modality: str, source: Optional[str] = None) -> bool:
        return modality == self.MODALITY

    def chunk(self, payload: Any, source_file: Optional[str] = None, page_number: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        # Accept common table payload types: pandas.DataFrame, list of dicts, list of lists
        try:
            import pandas as pd
        except Exception:
            pd = None

        text_repr = ""
        if pd is not None and isinstance(payload, pd.DataFrame):
            text_repr = payload.to_csv(index=False)
        elif isinstance(payload, (list, tuple)):
            # naive conversion
            text_repr = "\n".join([str(r) for r in payload])
        else:
            text_repr = str(payload)

        chunk = Chunk.create(content=text_repr, modality=self.MODALITY, source_file=source_file, page_number=page_number, metadata=metadata)
        return [chunk]
