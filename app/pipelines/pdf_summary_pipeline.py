"""Pipeline to summarize PDFs end-to-end using the existing RAG infra.

Flow:
PDF -> DoclingLoader -> Chunking -> Embedding -> VectorDB -> Retrieve Key Chunks -> Generate

The pipeline is dependency-injected and reuses existing components (loader,
chunkers, embedders, vectordb, retriever, generator, context builder).
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
import logging

from ..ingestion.docling_loader import DoclingLoader
from ..chunking.chunker_interface import CHUNKER_REGISTRY
from ..models.document import Document
from ..embeddings.embedding_interface import get_embedder
from ..vectordb.vectordb_interface import get_vectordb
from ..retrieval.retriever_interface import get_retriever
from .rag_pipeline import RagPipeline
from ..retrieval.context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class PdfSummaryPipeline:
    def __init__(
        self,
        loader: Optional[DoclingLoader] = None,
        embedder_name: str = "sentence-transformers",
        vectordb_name: str = "chroma",
        embedder_kwargs: Optional[Dict] = None,
        vectordb_kwargs: Optional[Dict] = None,
        context_builder: Optional[ContextBuilder] = None,
    ) -> None:
        self.loader = loader or DoclingLoader()
        self.embedder_name = embedder_name
        self.vectordb_name = vectordb_name
        self.embedder_kwargs = embedder_kwargs or {}
        self.vectordb_kwargs = vectordb_kwargs or {}
        self.context_builder = context_builder

    def _select_text_chunker(self):
        for c in CHUNKER_REGISTRY:
            try:
                if c.can_handle("text"):
                    return c
            except Exception:
                continue
        raise RuntimeError("No text chunker available")

    def ingest_and_index(self, source: str, persist: bool = True, chunk_size: int = 512, overlap: int = 64) -> List[Document]:
        """Load documents from `source`, chunk, embed, and insert into the Vector DB.

        Returns the list of chunk `Document`s that were indexed.
        """
        docs = self.loader.load(source)
        if not docs:
            return []

        chunker = self._select_text_chunker()

        chunks: List[Document] = []
        for doc in docs:
            pieces = chunker.chunk(doc.content, source_file=doc.metadata.get("source"), page_number=doc.metadata.get("page"), metadata={"source_doc_id": doc.id}, chunk_size=chunk_size, overlap=overlap)
            for ch in pieces:
                chunks.append(Document(id=ch.chunk_id, content=ch.content, metadata={**(ch.metadata or {}), "source_file": ch.source_file, "page_number": ch.page_number}))

        if not chunks:
            return []

        # Compute embeddings
        embedder = get_embedder(self.embedder_name, **self.embedder_kwargs)
        texts = [c.content for c in chunks]
        embeddings = embedder.embed_documents(texts)
        for d, emb in zip(chunks, embeddings):
            d.embedding = emb

        # Insert into vectordb
        vectordb = get_vectordb(self.vectordb_name, **self.vectordb_kwargs)
        vectordb.add_documents(chunks)
        if persist:
            try:
                vectordb.persist()
            except Exception:
                logger.exception("Failed to persist vectordb; continuing")

        return chunks

    def summarize(self, source: str, generator, rewriter=None, retriever_name: str = "vector", reranker=None, refiner=None, top_k: int = 8, token_budget: int = 1024) -> Dict[str, Any]:
        """Produce structured summaries for the given PDF `source`.

        Returns a dict with keys: `executive_summary`, `detailed_summary`, `key_insights`,
        `action_items`, `important_tables`, `important_figures`, plus intermediate artifacts.
        """
        # Ensure indexing is done (idempotent if already present)
        self.ingest_and_index(source)

        # Build components for RAG
        rewriter = rewriter or (lambda query: query)
        # get retriever instance (vector retriever using configured embedder/vectordb)
        retriever = get_retriever(retriever_name, embedder_name=self.embedder_name, vectordb_name=self.vectordb_name, embedder_kwargs=self.embedder_kwargs, vectordb_kwargs=self.vectordb_kwargs)
        context_builder = self.context_builder
        if context_builder is None:
            from ..retrieval.context_builder import DefaultContextBuilder

            context_builder = DefaultContextBuilder()

        # Use RagPipeline to generate grounded content
        # Wrap rewriter if it's a callable
        if not hasattr(rewriter, "rewrite"):
            class _InlineRewriter:
                def rewrite(self, q):
                    return rewriter(q)

            rewriter_obj = _InlineRewriter()
        else:
            rewriter_obj = rewriter

        pipeline = RagPipeline(rewriter=rewriter_obj, retriever=retriever, context_builder=context_builder, generator=generator, reranker=reranker, refiner=refiner, top_k=top_k, token_budget=token_budget)

        # Structured query prompting the generator to output the requested sections
        structured_query = (
            "Produce the following sections based on the provided context:\n"
            "1) Executive Summary\n"
            "2) Detailed Summary\n"
            "3) Key Insights (bullet points)\n"
            "4) Action Items (clear, assignable tasks)\n"
            "5) Important Tables (list tables and why they're important)\n"
            "6) Important Figures (list figures and why they're important)\n"
            "Provide each section clearly labeled. Use only the provided context to support claims."
        )

        out = pipeline.run(structured_query)

        # Attempt to parse generator output into sections by splitting on headings.
        text = out.get("generated", {}).get("text", "")
        # Simple heuristics: split by numbered headings
        sections = {"full_text": text}
        for idx, key in enumerate(["executive_summary", "detailed_summary", "key_insights", "action_items", "important_tables", "important_figures"], start=1):
            marker = f"{idx})"
            # find marker and next marker
            start = text.find(marker)
            if start != -1:
                # find next marker
                next_marker = text.find(f"{idx+1})") if idx < 6 else -1
                if next_marker != -1:
                    content = text[start:next_marker].strip()
                else:
                    content = text[start:].strip()
                sections[key] = content
            else:
                sections[key] = ""

        # Merge pipeline intermediate results for observability
        sections["_pipeline"] = out
        return sections

