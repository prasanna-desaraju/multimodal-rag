from app.pipelines.rag_pipeline import RagPipeline
from app.models.document import Document


class DummyRewriter:
    def rewrite(self, query: str) -> str:
        return query + " rewritten"


class DummyRetriever:
    def retrieve(self, query: str, top_k: int = 5):
        return [Document(id="d1", content="content1", metadata={}), Document(id="d2", content="content2", metadata={})]


class DummyReranker:
    def rerank(self, query: str, documents, top_k: int = 5):
        # reverse order
        return list(reversed(documents))


class DummyRefiner:
    def refine(self, original_query: str, documents):
        # keep only first document
        return documents[:1]


class DummyContextBuilder:
    def build_context(self, query, reranked_chunks, token_budget: int):
        entries = []
        parts = []
        for d in reranked_chunks:
            entries.append(d)
            parts.append(d.content)
        return {"context": "\n\n".join(parts), "entries": entries, "used_tokens": sum(len(p.split()) for p in parts)}


class DummyGenerator:
    def generate(self, query: str, inserted_context, timeout=None, retries=3, **kwargs):
        return {"text": f"Answer based on {len(inserted_context)} docs"}


def test_rag_pipeline_end_to_end():
    pipeline = RagPipeline(
        rewriter=DummyRewriter(),
        retriever=DummyRetriever(),
        reranker=DummyReranker(),
        refiner=DummyRefiner(),
        context_builder=DummyContextBuilder(),
        generator=DummyGenerator(),
        top_k=2,
        token_budget=50,
    )

    out = pipeline.run("hello")
    assert out["original_query"] == "hello"
    assert out["rewritten_query"].endswith("rewritten")
    assert len(out["retrieved"]) == 2
    assert len(out["reranked"]) == 2
    assert len(out["refined"]) == 1
    assert "context" in out and out["context"]
    assert out["generated"]["text"] == "Answer based on 1 docs"
