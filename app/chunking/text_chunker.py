def chunk_text(text: str, chunk_size: int = 512, overlap:int = 64):
"""TextChunker implementation.

Splits text into character-based chunks as a placeholder. Real
implementations may use tokenizers for better quality.
"""
from __future__ import annotations

from typing import List, Optional, Dict

from .chunker_interface import Chunker, register_chunker
from ..models.chunk import Chunk


@register_chunker
class TextChunker(Chunker):
    MODALITY = "text"

    def can_handle(self, modality: str, source: Optional[str] = None) -> bool:
        return modality == self.MODALITY

    def chunk(self, payload: str, source_file: Optional[str] = None, page_number: Optional[int] = None, metadata: Optional[Dict[str, any]] = None, chunk_size: int = 512, overlap: int = 64) -> List[Chunk]:
        if not isinstance(payload, str):
            raise TypeError("TextChunker expects a string payload")

        text = payload
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")

        chunks: List[Chunk] = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            piece = text[start:end]
            chunk = Chunk.create(content=piece, modality=self.MODALITY, source_file=source_file, page_number=page_number, metadata=metadata)
            chunks.append(chunk)
            if end == text_len:
                break
            start = max(end - overlap, end)
        return chunks
