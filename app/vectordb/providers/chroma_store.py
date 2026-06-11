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
    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = "default"):
        try:
            import chromadb
            from chromadb.config import Settings
        except Exception as exc:
            raise NotImplementedError("Install chromadb to use ChromaVectorStore") from exc

        # Allow override via environment variable to avoid legacy DB collisions.
        env_dir = os.getenv("CHROMA_PERSIST_DIR")
        self.persist_directory = persist_directory or env_dir or "./chroma_db_v2"
        self.collection_name = collection_name

        os.makedirs(self.persist_directory, exist_ok=True)

        settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory)
        try:
            self._client = chromadb.Client(settings)
        except ValueError as e:
            # Chroma raises a ValueError when the on-disk database was created
            # with a legacy configuration. For developer convenience we fall
            # back to an in-memory client so the demo can run without
            # requiring users to migrate existing data. If the user intends
            # to keep prior data, they should run the migration tool as the
            # error message suggests (pip install chroma-migrate; chroma-migrate).
            logger.warning("Chroma legacy data detected: %s. Falling back to in-memory Chroma client.", e)
            logger.info(
                "To persist existing data, install 'chroma-migrate' and run 'chroma-migrate', then set CHROMA_PERSIST_DIR to a new directory."
            )
            # Create a default in-memory client by not passing Settings.
            # This avoids Pydantic validation errors for fields like
            # `persist_directory` which must be a string when provided.
            self._client = chromadb.Client()

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

        def _sanitize_value(v):
            # Primitive types that Chroma accepts directly
            from numbers import Number
            try:
                import numpy as _np
            except Exception:
                _np = None

            if v is None:
                return ""
            if isinstance(v, (str, bool, Number)):
                return v
            if _np is not None and isinstance(v, _np.generic):
                # numpy scalar
                return v.item()
            if _np is not None and isinstance(v, (_np.ndarray,)):
                return v.tolist()
            if isinstance(v, (list, tuple)):
                return [_sanitize_value(x) for x in v]
            if isinstance(v, dict):
                return {str(k): _sanitize_value(val) for k, val in v.items()}
            # Fallback: convert to string
            return str(v)

        for d in documents:
            if d.embedding is None:
                raise ValueError(f"Document {d.id} is missing embedding; compute embeddings before inserting")
            ids.append(str(d.id))
            texts.append(str(d.content))
            raw_meta = d.metadata or {}
            try:
                sanitized = {str(k): _sanitize_value(v) for k, v in raw_meta.items()}
            except Exception:
                sanitized = {str(k): str(v) for k, v in (raw_meta or {}).items()}
            # Include small structured metadata for tracing
            if d.id is not None:
                sanitized.setdefault("doc_id", str(d.id))
            metadatas.append(sanitized)
            # Normalize embeddings to plain Python lists of floats
            emb = d.embedding
            try:
                # handle numpy arrays
                import numpy as _np
                if _np is not None and isinstance(emb, _np.ndarray):
                    emb = emb.tolist()
            except Exception:
                pass
            embeddings.append([float(x) for x in emb])

        self._collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    def query(self, embedding: List[float], top_k: int = 10, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": top_k,
            "include": ["metadatas", "documents", "distances"],
        }
        if metadata:
            # Only pass the `where` filter if metadata is provided and non-empty.
            query_kwargs["where"] = metadata

        res = self._collection.query(**query_kwargs)

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
