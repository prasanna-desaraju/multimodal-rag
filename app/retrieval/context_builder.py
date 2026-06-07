"""Context building utilities: interface and default implementation.

Responsibilities:
- Accept a query and a list of reranked chunks and produce a prompt-ready
  context string and a list of included chunks with preserved metadata.
- Provide deduplication, ordering, token budgeting, and metadata preservation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional
import logging

from ..models.chunk import Chunk

logger = logging.getLogger(__name__)


def default_token_counter(text: str) -> int:
    """Very small token estimator used when a real tokenizer is not available.

    Counts whitespace-separated tokens as an approximation.
    """
    if not text:
        return 0
    return len(text.split())


def normalize_text_for_dedup(text: str) -> str:
    """Normalize text for use in simple deduplication checks."""
    return " ".join(text.lower().split())


@dataclass
class ContextEntry:
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    tokens: int


class ContextBuilder(ABC):
    """Interface for building prompt-ready context from reranked chunks.

    Future strategies should implement this interface and be pluggable.
    """

    @abstractmethod
    def build_context(self, query: str, reranked_chunks: Iterable[Any], token_budget: int) -> Dict[str, Any]:
        """Return a dictionary with at least the keys:

        - `context`: combined string suitable for insertion into a prompt
        - `entries`: List[ContextEntry] preserving metadata and original ids
        - `used_tokens`: int total tokens used
        """


class DefaultContextBuilder(ContextBuilder):
    """Default implementation providing deduplication, ordering and budgeting.

    Parameters
    - token_counter: callable(text) -> int estimating tokens
    - deduplicate: whether to remove duplicate chunks (by normalized content)
    - joiner: string inserted between concatenated chunks
    - ordering_fn: optional function to sort reranked_chunks (defaults to score desc)
    """

    def __init__(
        self,
        token_counter: Callable[[str], int] = default_token_counter,
        deduplicate: bool = True,
        joiner: str = "\n\n",
        ordering_fn: Optional[Callable[[Any], float]] = None,
    ) -> None:
        self.token_counter = token_counter
        self.deduplicate = deduplicate
        self.joiner = joiner
        # ordering_fn(item) -> score (higher means more relevant)
        self.ordering_fn = ordering_fn or (lambda item: getattr(item, "score", 0) or item.get("score", 0) if isinstance(item, dict) else 0)

    def build_context(self, query: str, reranked_chunks: Iterable[Any], token_budget: int) -> Dict[str, Any]:
        chunks = list(reranked_chunks)

        # Order chunks by ordering_fn (descending)
        try:
            chunks.sort(key=self.ordering_fn, reverse=True)
        except Exception:
            logger.exception("Failed to sort reranked_chunks with ordering_fn; proceeding with original order")

        seen = set()
        entries: List[ContextEntry] = []
        parts: List[str] = []
        used_tokens = 0

        for item in chunks:
            # Accept dict-like or Chunk object
            if isinstance(item, dict):
                content = item.get("content") or item.get("text") or ""
                chunk_id = item.get("chunk_id") or item.get("id") or item.get("id_str") or ""
                metadata = dict(item.get("metadata") or {})
            elif isinstance(item, Chunk):
                content = item.content
                chunk_id = item.chunk_id
                metadata = dict(item.metadata or {})
            else:
                # Try attribute access as fallback
                content = getattr(item, "content", "")
                chunk_id = getattr(item, "chunk_id", getattr(item, "id", ""))
                metadata = dict(getattr(item, "metadata", {}) or {})

            if not content:
                continue

            norm = normalize_text_for_dedup(content) if self.deduplicate else None
            if self.deduplicate and norm in seen:
                continue

            tokens = self.token_counter(content)
            remaining = token_budget - used_tokens
            if remaining <= 0:
                break

            if tokens <= remaining:
                included_content = content
                included_tokens = tokens
            else:
                # Truncate conservatively by words to fit remaining budget.
                words = content.split()
                if not words:
                    continue
                # Heuristic: average tokens per word ~= 1, so take first `remaining` words
                take = max(1, remaining)
                included_content = " ".join(words[:take])
                included_tokens = self.token_counter(included_content)

            if included_tokens <= 0:
                continue

            # record
            entries.append(ContextEntry(chunk_id=str(chunk_id), content=included_content, metadata=metadata, tokens=included_tokens))
            parts.append(included_content)
            used_tokens += included_tokens
            if self.deduplicate and norm is not None:
                seen.add(norm)

        context_text = self.joiner.join(parts)

        return {
            "context": context_text,
            "entries": entries,
            "used_tokens": used_tokens,
            "token_budget": token_budget,
        }
