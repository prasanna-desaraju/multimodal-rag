"""Vector retriever implementation that composes an Embedder and VectorStore."""
from __future__ import annotations

from typing import List, Optional, Dict

from .retriever_interface import Retriever, register_retriever
from ..models.document import Document

from app.embeddings.embedding_interface import get_embedder
from app.vectordb.vectordb_interface import get_vectordb


@register_retriever("vector")
class VectorRetriever(Retriever):
    def __init__(self, embedder_name: str = "sentence-transformers", vectordb_name: str = "chroma", embedder_kwargs: Optional[Dict] = None, vectordb_kwargs: Optional[Dict] = None):
        self.embedder = get_embedder(embedder_name, **(embedder_kwargs or {}))
        self.vectordb = get_vectordb(vectordb_name, **(vectordb_kwargs or {}))

    def retrieve(self, query: str, top_k: int = 5) -> List[Document]:
        emb = self.embedder.embed_query(query)
        results = self.vectordb.query(embedding=emb, top_k=top_k)
        return results
