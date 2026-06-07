"""Simple query rewriter - minimal implementation."""
from __future__ import annotations

from .rewriter_interface import Rewriter, register_rewriter


@register_rewriter("simple")
class SimpleRewriter(Rewriter):
    def __init__(self, normalize: bool = True):
        self.normalize = normalize

    def rewrite(self, query: str) -> str:
        if not query:
            return query
        q = query.strip()
        if self.normalize:
            q = q.lower()
        return q
