"""SentenceTransformer embedder implementation using local models.

This implementation uses the `sentence_transformers` package when
available. It implements the `Embedder` interface and registers
itself under the name "sentence-transformers" so it can be selected
via the embedder factory.
"""
from __future__ import annotations

from typing import List, Optional
import numpy as np

from .embedding_interface import Embedder, register_embedder


@register_embedder("sentence-transformers")
class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        # lazy import to avoid heavy imports at module import time
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            raise NotImplementedError("Install sentence-transformers to use SentenceTransformerEmbedder") from exc

        self.model_name = model_name or "all-MiniLM-L6-v2"
        self.device = device
        self._model = SentenceTransformer(self.model_name, device=self.device) if device else SentenceTransformer(self.model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        embeddings = self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [list(e) for e in embeddings]

    def embed_query(self, text: str) -> List[float]:
        emb = self._model.encode([text], show_progress_bar=False, convert_to_numpy=True)
        if isinstance(emb, np.ndarray):
            return emb[0].tolist()
        return list(emb[0])
