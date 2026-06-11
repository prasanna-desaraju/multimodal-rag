"""High-level retrieval orchestration using Rewriter -> Retriever -> Refiner.

This module uses the factory functions to instantiate the requested
components so they remain pluggable and follow the Factory Pattern.
"""
from __future__ import annotations

from typing import List, Optional, Dict

from .rewriter_interface import get_rewriter
from .retriever_interface import get_retriever
from .refiner_interface import get_refiner

from ..models.document import Document


def run_pipeline(
    query: str,
    rewriter: str = "simple",
    retriever: str = "vector",
    reranker: str = None,
    refiner: str = "simple",
    top_k: int = 5,
    component_kwargs: Optional[Dict] = None,
) -> List[Document]:
    component_kwargs = component_kwargs or {}

    rw_kwargs = component_kwargs.get("rewriter", {})
    rt_kwargs = component_kwargs.get("retriever", {})
    rf_kwargs = component_kwargs.get("refiner", {})

    rwr = get_rewriter(rewriter, **rw_kwargs)
    rewritten = rwr.rewrite(query)

    rtr = get_retriever(retriever, **rt_kwargs)
    docs = rtr.retrieve(rewritten, top_k=top_k)

    # Optional reranking step
    if reranker:
        from .reranker_interface import get_reranker

        rr_kwargs = component_kwargs.get("reranker", {})
        rkr = get_reranker(reranker, **rr_kwargs)
        docs = rkr.rerank(rewritten, docs, top_k=top_k)

    rfr = get_refiner(refiner, **rf_kwargs)
    refined = rfr.refine(query, docs)

    return refined
