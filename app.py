import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("IR_DATASETS_HOME", str(ROOT / "data" / "raw" / "ir_datasets"))
os.environ.setdefault("TMP", str(ROOT / ".tmp"))
os.environ.setdefault("TEMP", str(ROOT / ".tmp"))

sys.path.insert(0, str(ROOT / ".codex_deps"))
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
import pandas as pd

from ir_project.config import ARTIFACTS_DIR, resolve_artifact_path
from ir_project.services.database import DocumentStore
from ir_project.services.indexing_service import load_index
from ir_project.services.rag_service import RagService
from ir_project.services.retrieval_service import RetrievalService


st.set_page_config(page_title="IR Search System", layout="wide")


@st.cache_resource
def load_services():
    metadata_path = ARTIFACTS_DIR / "dataset_metadata.json"
    if not metadata_path.exists():
        return None, None, None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    index = load_index()
    store = DocumentStore(resolve_artifact_path(metadata["db_path"], "documents.sqlite"))
    retriever = RetrievalService(index, store)
    rag = RagService(retriever, store)
    return metadata, retriever, rag


metadata, retriever, rag = load_services()

st.title("Information Retrieval System")

if metadata is None:
    st.error("Artifacts are not ready. Run: python scripts/prepare.py --max-docs 250000 --max-queries 50")
    st.stop()

with st.sidebar:
    st.subheader("Configuration")
    st.write(f"Dataset: `{metadata['dataset_id']}`")
    st.write(f"Documents: `{metadata['actual_docs']}`")
    method = st.selectbox(
        "Retrieval method",
        [
            "hybrid_parallel",
            "hybrid_serial",
            "bm25",
            "tfidf",
            "embedding",
            "bert_rerank",
        ],
    )
    top_k = st.slider("Top K", min_value=5, max_value=20, value=10)
    k1 = st.slider("BM25 k1", min_value=0.2, max_value=3.0, value=1.5, step=0.1)
    b = st.slider("BM25 b", min_value=0.0, max_value=1.0, value=0.75, step=0.05)
    use_refinement = st.checkbox("Query refinement", value=True)

search_tab, rag_tab, metrics_tab = st.tabs(["Search", "RAG Chat", "Evaluation"])

with search_tab:
    query = st.text_input("Search query", value="lung cancer EGFR adult")
    if st.button("Search", type="primary"):
        try:
            results = retriever.search(query, method=method, top_k=top_k, k1=k1, b=b, refine=use_refinement)
            docs = rag.store.get_many([result.doc_id for result in results])
            for result in results:
                doc = docs.get(result.doc_id, {})
                st.markdown(f"#### {result.rank}. `{result.doc_id}`")
                st.caption(f"{result.method} score: {result.score:.4f}")
                st.write(" ".join(doc.get("body", "").split())[:1500])
        except RuntimeError as exc:
            st.error(str(exc))

with rag_tab:
    question = st.text_input("Ask a question", value="Which clinical trials discuss lung cancer and EGFR?")
    if st.button("Generate grounded answer"):
        try:
            answer = rag.answer(question, method=method, top_k=min(top_k, 8), refine=use_refinement)
            st.markdown(answer.answer)
            st.subheader("Sources")
            for source in answer.sources:
                st.markdown(f"**{source['rank']}. `{source['doc_id']}`** score `{source['score']}`")
                st.write(source["snippet"])
        except RuntimeError as exc:
            st.error(str(exc))

with metrics_tab:
    metrics_path = ARTIFACTS_DIR / "evaluation_metrics.csv"
    chart_path = Path("reports") / "figures" / "evaluation_metrics.png"
    if metrics_path.exists():
        st.dataframe(pd.read_csv(metrics_path), use_container_width=True)
    else:
        st.info("Run python scripts/evaluate.py to generate metrics.")
    if chart_path.exists():
        st.image(str(chart_path))
