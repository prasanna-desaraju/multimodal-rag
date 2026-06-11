"""Streamlit application for the Multimodal RAG demo.

This UI is intentionally thin: it wires user actions to the business
logic implemented in `app.pipelines` and `app.retrieval`. The UI is
modular and keeps business logic out of the view layer.
"""
from __future__ import annotations

import streamlit as st
import sys
import tempfile
import os
from typing import Optional

# Ensure project root is on sys.path so absolute imports like `app.*` work
# when Streamlit runs this file as a script.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.pipelines.pdf_summary_pipeline import PdfSummaryPipeline
from app.pipelines.rag_pipeline import RagPipeline
from app.retrieval.rewriter_interface import get_rewriter
from app.retrieval.retriever_interface import get_retriever
from app.retrieval.context_builder import DefaultContextBuilder
from app.generation.generator_interface import get_generator


def save_uploaded_file(uploaded) -> str:
    suffix = os.path.splitext(uploaded.name)[1] if uploaded is not None else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        return tmp.name


def build_generator(provider: str, api_key: Optional[str], endpoint: Optional[str]):
    try:
        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if endpoint:
            kwargs["endpoint"] = endpoint
        gen = get_generator(provider, **kwargs)
        return gen
    except Exception as e:
        st.error(f"Failed to construct generator: {e}")
        return None


def build_rag_for_ui(generator):
    # Simple defaults: simple rewriter, vector retriever, default context builder
    rewriter = get_rewriter("simple")
    retriever = get_retriever("vector")
    context_builder = DefaultContextBuilder()
    pipeline = RagPipeline(rewriter=rewriter, retriever=retriever, context_builder=context_builder, generator=generator)
    return pipeline


def pipeline_visualization(st_container, pipeline_state: dict):
    # Simple visualization: list the stages with status
    stages = ["Rewrite", "Retrieve", "Rerank", "Refine", "Insert", "Generate"]
    cols = st_container.columns(len(stages))
    for i, s in enumerate(stages):
        status = pipeline_state.get(s.lower(), "idle")
        if status == "done":
            cols[i].success(s)
        elif status == "running":
            cols[i].info(s)
        else:
            cols[i].write(s)


def main():
    st.set_page_config(layout="wide", page_title="Multimodal RAG")
    st.sidebar.title("Inputs")

    uploaded_pdf = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
    uploaded_images = st.sidebar.file_uploader("Upload Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    uploaded_docx = st.sidebar.file_uploader("Upload DOCX", type=["docx"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Generator")
    generator_provider = st.sidebar.selectbox("Provider", options=["grok", "dummy"], index=0)
    api_key = st.sidebar.text_input("API Key (optional)")
    endpoint = st.sidebar.text_input("Endpoint (optional)")

    st.sidebar.markdown("---")
    st.sidebar.info("Pipeline is modular: components are injected from code.")

    generator = None
    if generator_provider:
        generator = build_generator(generator_provider, api_key or None, endpoint or None)

    # Main layout
    st.title("Multimodal RAG — Demo UI")
    left, right = st.columns([3, 1])

    with left:
        tabs = st.tabs(["Document Summary", "Ask Questions", "Retrieved Chunks", "Reranked Chunks", "Generated Response"]) 

        # Document Summary tab
        with tabs[0]:
            st.header("Document Summary")
            if uploaded_pdf:
                path = save_uploaded_file(uploaded_pdf)
                if generator is None:
                    st.warning("Select a generator provider and ensure configuration in the sidebar.")
                else:
                    st.info("Summarizing PDF — this may take a while")
                    pdf_pipeline = PdfSummaryPipeline()
                    with st.spinner("Running PDF summarization pipeline..."):
                        sections = pdf_pipeline.summarize(path, generator=generator)

                    # Pipeline visualization
                    st.subheader("Pipeline")
                    pipeline_visualization(st, {"rewrite": "done", "retrieve": "done", "rerank": "done", "refine": "done", "insert": "done", "generate": "done"})

                    st.subheader("Executive Summary")
                    st.write(sections.get("executive_summary") or sections.get("full_text")[:500])

                    st.subheader("Detailed Summary")
                    st.write(sections.get("detailed_summary"))

                    st.subheader("Key Insights")
                    st.write(sections.get("key_insights"))

                    st.subheader("Action Items")
                    st.write(sections.get("action_items"))

                    st.subheader("Important Tables")
                    st.write(sections.get("important_tables"))

                    st.subheader("Important Figures")
                    st.write(sections.get("important_figures"))
            else:
                st.info("Upload a PDF in the sidebar to summarize it.")

        # Ask Questions tab
        with tabs[1]:
            st.header("Ask Questions")
            query = st.text_input("Enter your question about the uploaded documents")
            if st.button("Ask"):
                if generator is None:
                    st.error("Configure a generator in the sidebar first.")
                else:
                    pipeline = build_rag_for_ui(generator)
                    with st.spinner("Running RAG pipeline..."):
                        out = pipeline.run(query)

                    st.subheader("Pipeline Visualization")
                    # Basic status mapping
                    pipeline_visualization(st, {"rewrite": "done", "retrieve": "done", "rerank": "done", "refine": "done", "insert": "done", "generate": "done"})

                    st.subheader("Generated Answer")
                    gen = out.get("generated", {})
                    st.write(gen.get("text") if isinstance(gen, dict) else str(gen))

        # Retrieved Chunks tab
        with tabs[2]:
            st.header("Retrieved Chunks")
            if uploaded_pdf:
                path = save_uploaded_file(uploaded_pdf)
                # reuse pdf pipeline to get intermediate retrieval artifacts
                pdf_pipeline = PdfSummaryPipeline()
                with st.spinner("Indexing and retrieving key chunks..."):
                    sections = pdf_pipeline.summarize(path, generator=generator)
                pipeline_art = sections.get("_pipeline", {})
                retrieved = pipeline_art.get("retrieved", [])
                if not retrieved:
                    st.info("No retrieved chunks yet")
                else:
                    for d in retrieved:
                        st.write(f"ID: {d.id} — {d.content[:200]}")
            else:
                st.info("Upload a PDF to view retrieved chunks.")

        # Reranked Chunks tab
        with tabs[3]:
            st.header("Reranked Chunks")
            if uploaded_pdf:
                path = save_uploaded_file(uploaded_pdf)
                pdf_pipeline = PdfSummaryPipeline()
                with st.spinner("Indexing and reranking..."):
                    sections = pdf_pipeline.summarize(path, generator=generator)
                pipeline_art = sections.get("_pipeline", {})
                reranked = pipeline_art.get("reranked", [])
                if not reranked:
                    st.info("No reranked chunks")
                else:
                    for d in reranked:
                        st.write(f"ID: {d.id} — {d.content[:200]}")
            else:
                st.info("Upload a PDF to view reranked chunks.")

        # Generated Response tab
        with tabs[4]:
            st.header("Generated Response")
            st.info("Run the 'Ask Questions' flow to populate generated responses.")

    with right:
        st.header("Pipeline Diagram")
        st.markdown("Rewrite → Retrieve → Rerank → Refine → Insert → Generate")
        st.caption("Stages are executed in order; components are injectable.")


if __name__ == "__main__":
    main()
