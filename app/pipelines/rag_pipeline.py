"""RAG pipeline orchestration.

This module provides `RagPipeline`, a small, dependency-injected
orchestrator that runs: rewrite -> retrieve -> rerank -> refine -> insert -> generate.

Each stage is injected via the constructor and may be a concrete
implementation conforming to the interfaces in `app.retrieval` and
`app.generation`.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
import logging

from ..models.document import Document
from ..retrieval.rewriter_interface import Rewriter
from ..retrieval.retriever_interface import Retriever
from ..retrieval.reranker_interface import Reranker
from ..retrieval.refiner_interface import Refiner
from ..retrieval.context_builder import ContextBuilder
from ..generation.generator_interface import Generator

logger = logging.getLogger(__name__)


class RagPipeline:
    def __init__(
        self,
        rewriter: Rewriter,
        retriever: Retriever,
        context_builder: ContextBuilder,
        generator: Generator,
        reranker: Optional[Reranker] = None,
        refiner: Optional[Refiner] = None,
        top_k: int = 10,
        token_budget: int = 1024,
    ) -> None:
        self.rewriter = rewriter
        self.retriever = retriever
        self.reranker = reranker
        self.refiner = refiner
        self.context_builder = context_builder
        self.generator = generator
        self.top_k = top_k
        self.token_budget = token_budget

    def run(self, query: str, generate_timeout: Optional[float] = None, generate_retries: int = 3) -> Dict[str, Any]:
        """Execute the RAG pipeline and return a structured result.

        The returned dict includes intermediate artifacts to aid debugging
        and testing. Stages that are not provided are skipped.
        """
        result: Dict[str, Any] = {"original_query": query}

        # 1. Rewrite
        try:
            rewritten = self.rewriter.rewrite(query)
        except Exception:
            logger.exception("Rewriter failed; falling back to original query")
            rewritten = query
        result["rewritten_query"] = rewritten

        # 2. Retrieve
        retrieved: List[Document] = []
        try:
            retrieved = self.retriever.retrieve(rewritten, top_k=self.top_k)
        except Exception:
            logger.exception("Retriever failed; returning empty results")
            retrieved = []
        result["retrieved"] = retrieved

        # 3. Rerank (optional)
        reranked: List[Document] = retrieved
        if self.reranker is not None:
            try:
                reranked = self.reranker.rerank(rewritten, retrieved, top_k=self.top_k)
            except Exception:
                logger.exception("Reranker failed; using retrieved order")
                reranked = retrieved
        result["reranked"] = reranked

        # 4. Refine (optional)
        refined: List[Document] = reranked
        if self.refiner is not None:
            try:
                refined = self.refiner.refine(query, reranked)
            except Exception:
                logger.exception("Refiner failed; using reranked results")
                refined = reranked
        result["refined"] = refined

        # 5. Insert / build context
        try:
            ctx = self.context_builder.build_context(query, refined, token_budget=self.token_budget)
            context_text = ctx.get("context", "")
            entries = ctx.get("entries", [])
        except Exception:
            logger.exception("ContextBuilder failed; using concatenated refined content")
            context_text = "\n\n".join([d.content for d in refined])
            entries = []

        result["context"] = context_text
        result["context_entries"] = entries

        # 6. Generate
        try:
            generated = self.generator.generate(query, inserted_context=refined, timeout=generate_timeout, retries=generate_retries)
            result["generated"] = generated
        except Exception:
            logger.exception("Generator failed")
            result["generated"] = {"text": "", "error": "generation_failed"}

        return result

