from app.pipelines.pdf_summary_pipeline import PdfSummaryPipeline
from app.models.document import Document


class DummyLoader:
    def load(self, source: str):
        return [Document(id="doc1", content="This is a test PDF content with table and figure.", metadata={"source": source})]


class DummyChunker:
    def can_handle(self, modality: str):
        return modality == "text"

    def chunk(self, payload, source_file=None, page_number=None, metadata=None, chunk_size=512, overlap=64):
        from app.models.chunk import Chunk

        return [Chunk.create(content=payload, modality="text", source_file=source_file, metadata=metadata)]


class DummyEmbedder:
    def embed_documents(self, texts):
        return [[float(len(t))] for t in texts]

    def embed_query(self, text):
        return [float(len(text))]


class DummyVectorStore:
    def __init__(self):
        self.docs = {}

    def add_documents(self, documents):
        for d in documents:
            self.docs[d.id] = d

    def query(self, embedding, top_k=10, metadata=None):
        return list(self.docs.values())[:top_k]

    def persist(self):
        pass

    def delete(self, ids):
        for i in ids:
            self.docs.pop(i, None)


class DummyGenerator:
    def generate(self, query, inserted_context, timeout=None, retries=3, **kwargs):
        return {"text": "1) Executive...\n2) Detailed...\n3) Key Insights...\n4) Action Items...\n5) Important Tables...\n6) Important Figures..."}


def test_pdf_summary_pipeline_with_dummies(monkeypatch):
    loader = DummyLoader()
    pipeline = PdfSummaryPipeline(loader=loader, embedder_name="dummy", vectordb_name="dummy")

    # Patch chunker registry to use DummyChunker
    from app.chunking.chunker_interface import CHUNKER_REGISTRY
    CHUNKER_REGISTRY.clear()
    CHUNKER_REGISTRY.append(DummyChunker())

    # Patch embedder factory
    from app.embeddings import embedding_interface

    embedding_interface.EMBEDDER_REGISTRY["dummy"] = lambda **kwargs: DummyEmbedder()

    # Patch vectordb factory
    from app.vectordb import vectordb_interface

    vectordb_interface.VECTORDB_REGISTRY["dummy"] = lambda **kwargs: DummyVectorStore()

    out = pipeline.summarize("/tmp/fake.pdf", generator=DummyGenerator())
    assert "executive_summary" in out
    assert "detailed_summary" in out
    assert "key_insights" in out
    assert "action_items" in out
    assert "important_tables" in out
    assert "important_figures" in out
