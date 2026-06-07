"""Document model used across ingestion, storage, and retrieval."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
