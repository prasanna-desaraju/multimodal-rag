"""A small local/dummy generator for offline testing and demos.

This generator is deterministic and returns a simple answer built from
the provided context. Registering it under the name `dummy` lets the
UI run without network access or API keys.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import logging

from .generator_interface import Generator, register_generator
from ..models.document import Document

logger = logging.getLogger(__name__)


@register_generator("dummy")
class DummyGenerator(Generator):
    def __init__(self, **kwargs):
        pass

    def generate(self, query: str, inserted_context: List[Document], timeout: Optional[float] = None, retries: int = 1, **kwargs) -> Dict[str, Any]:
        # Very small local heuristic: include up to 3 context snippets and echo the query
        snippets = [d.content for d in inserted_context][:3]
        context_block = "\n---\n".join(snippets) if snippets else "(no context)"
        text = f"DUMMY ANSWER\nContext used:\n{context_block}\n\nQuery:\n{query}\n\nAnswer:\nThis is a deterministic dummy response for offline testing."
        return {"text": text, "raw": {"provider": "dummy"}}
