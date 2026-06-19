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

from ir_project.config import ARTIFACTS_DIR
from ir_project.services.service_container import load_service_container


st.set_page_config(page_title="IR Search System", layout="wide")


@st.cache_resource
def load_services():
    try:
        container = load_service_container()
    except RuntimeError:
        return None, None, None
    return container.metadata, container.retriever, container.rag


metadata, retriever, rag = load_services()

st.title("Information Retrieval System")

if metadata is None:
    st.error(
        "Artifacts are not ready. Run scripts/prepare.py with "
        "--dataset clinicaltrials/2017/trec-pm-2017 --max-docs 0 --max-queries 0"
    )
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
                st.text_area(
                    "Original document",
                    value=doc.get("body", ""),
                    height=320,
                    disabled=True,
                    key=f"search-document-{result.rank}-{result.doc_id}",
                )
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
    chart_path = Path("reports") / "figures" / "evaluation_metrics.png"
    metric_files = [
        ("Base retrieval evaluation", ARTIFACTS_DIR / "evaluation_metrics.csv"),
        ("Query refinement evaluation", ARTIFACTS_DIR / "evaluation_metrics_refined.csv"),
        ("BERT reranking evaluation", ARTIFACTS_DIR / "evaluation_metrics_bert.csv"),
        ("RAG quality evaluation", ARTIFACTS_DIR / "rag_evaluation_metrics.csv"),
    ]
    for title, metrics_path in metric_files:
        if metrics_path.exists():
            st.subheader(title)
            st.dataframe(pd.read_csv(metrics_path), width="stretch")
    if chart_path.exists():
        st.image(str(chart_path))
