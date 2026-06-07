"""ChromaDB provider moved into providers/ for cleaner architecture."""
from __future__ import annotations

from typing import List, Optional, Dict, Any
import os
import logging

from ..vectordb_interface import VectorStore, register_vectordb
from ...models.document import Document

logger = logging.getLogger(__name__)


@register_vectordb("chroma")
class ChromaVectorStore(VectorStore):
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "default"):
        try:
            import chromadb
            from chromadb.config import Settings
        except Exception as exc:
            raise NotImplementedError("Install chromadb to use ChromaVectorStore") from exc

        self.persist_directory = persist_directory
        self.collection_name = collection_name

        os.makedirs(self.persist_directory, exist_ok=True)

        settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory)
        self._client = chromadb.Client(settings)

        try:
            self._collection = self._client.get_collection(name=self.collection_name)
        except Exception:
            self._collection = self._client.create_collection(name=self.collection_name)

    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        try:
            self._client.get_collection(name=name)
        except Exception:
            self._client.create_collection(name=name, metadata=metadata or {})

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return

        ids = []
        texts = []
        metadatas = []
        embeddings = []

        for d in documents:
            if d.embedding is None:
                raise ValueError(f"Document {d.id} is missing embedding; compute embeddings before inserting")
            ids.append(d.id)
            texts.append(d.content)
            metadatas.append(d.metadata or {})
            embeddings.append(d.embedding)

        self._collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    def query(self, embedding: List[float], top_k: int = 10, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        filter_arg = metadata or {}
        res = self._collection.query(query_embeddings=[embedding], n_results=top_k, where=filter_arg, include=["metadatas", "documents", "ids", "distances"]) 

        docs: List[Document] = []
        if not res:
            return docs

        ids = res.get("ids", [[]])[0]
        documents = res.get("documents", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]

        for _id, text, meta in zip(ids, documents, metadatas):
            docs.append(Document(id=_id, content=text, metadata=meta))

        return docs

    def persist(self) -> None:
        try:
            self._client.persist()
        except Exception:
            logger.debug("Chroma client persist not available or failed; ignoring")

    def delete(self, ids: List[str]) -> None:
        if not ids:
            return
        try:
            self._collection.delete(ids=ids)
        except Exception:
            logger.exception("Failed to delete ids from chroma collection")
