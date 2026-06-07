from app.retrieval.context_builder import DefaultContextBuilder, ContextEntry


def test_default_context_builder_basic():
    chunks = [
        {"chunk_id": "a", "content": "This is a short chunk.", "metadata": {"src": "doc1"}, "score": 0.9},
        {"chunk_id": "b", "content": "This is another chunk.", "metadata": {"src": "doc2"}, "score": 0.8},
        {"chunk_id": "c", "content": "This is a short chunk.", "metadata": {"src": "doc1-dup"}, "score": 0.5},
    ]

    builder = DefaultContextBuilder()
    out = builder.build_context(query="x", reranked_chunks=chunks, token_budget=10)

    # ensure deduplication removed duplicate content
    assert isinstance(out["entries"], list)
    assert len(out["entries"]) <= 2
    # ensure metadata preserved
    for e in out["entries"]:
        assert isinstance(e, ContextEntry)
        assert "src" in e.metadata

