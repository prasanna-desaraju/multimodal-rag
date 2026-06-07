"""Cross-encoder based reranker implementation.

Uses `sentence_transformers.CrossEncoder` if available. Falls back to a
lightweight heuristic scorer when the package is not installed so the
module remains importable during early development.
"""
from __future__ import annotations

from typing import List, Optional, Dict
import logging

from .reranker_interface import Reranker, register_reranker
from ..models.document import Document

logger = logging.getLogger(__name__)


@register_reranker("cross-encoder")
class CrossEncoderReranker(Reranker):
    def __init__(self, model_name: str = "cross-encoder/stsb-roberta-large", device: Optional[str] = None):
        self.model_name = model_name
        self.device = device
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device=self.device) if device else CrossEncoder(self.model_name)
        except Exception as exc:
            logger.warning("CrossEncoder not available; falling back to heuristic scorer: %s", exc)
            self._model = None

    def _heuristic_score(self, query: str, doc: Document) -> float:
        # Simple heuristic: count overlapping tokens (space-separated)
        q_tokens = set(query.lower().split())
        d_tokens = set(doc.content.lower().split())
        return float(len(q_tokens & d_tokens))

    def rerank(self, query: str, documents: List[Document], top_k: Optional[int] = None) -> List[Document]:
        if not documents:
            return []

        if self._model is not None:
            # Prepare pairs (query, doc_text)
            pairs = [[query, d.content if d.content is not None else ""] for d in documents]
            scores = self._model.predict(pairs)
            scored = list(zip(documents, scores))
            scored.sort(key=lambda x: x[1], reverse=True)
            docs_sorted = [d for d, s in scored]
        else:
            scored = [(d, self._heuristic_score(query, d)) for d in documents]
            scored.sort(key=lambda x: x[1], reverse=True)
            docs_sorted = [d for d, s in scored]

        if top_k is not None:
            return docs_sorted[:top_k]
        return docs_sorted
