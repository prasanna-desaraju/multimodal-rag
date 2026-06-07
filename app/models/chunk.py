"""Chunk data model for different modalities."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid


@dataclass
class Chunk:
    chunk_id: str
    content: str
    modality: str
    source_file: Optional[str] = None
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, content: str, modality: str, source_file: Optional[str] = None, page_number: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> "Chunk":
        return cls(
            chunk_id=str(uuid.uuid4()),
            content=content,
            modality=modality,
            source_file=source_file,
            page_number=page_number,
            metadata=metadata or {},
        )
