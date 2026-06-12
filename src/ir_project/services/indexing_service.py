from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import normalize

from ir_project.config import ARTIFACTS_DIR
from ir_project.services.bm25 import SparseBM25Index
from ir_project.services.database import DocumentStore
from ir_project.services.text_processing import TextProcessor


@dataclass
class SearchIndex:
    doc_ids: list[str]
    tfidf_vectorizer: TfidfVectorizer
    tfidf_matrix: sparse.csr_matrix
    svd_model: TruncatedSVD
    embedding_matrix: np.ndarray
    bm25: SparseBM25Index
    processor: TextProcessor


def build_index(
    doc_ids: list[str],
    db_path: Path,
    artifact_path: Path = ARTIFACTS_DIR / "search_index.joblib",
    max_features: int = 30_000,
    embedding_dims: int = 256,
    min_df: int = 2,
    max_df: float = 0.95,
) -> SearchIndex:
    print(f"Loading {len(doc_ids):,} documents from SQLite...", flush=True)
    store = DocumentStore(db_path)
    docs = store.get_many(doc_ids)
    processor = TextProcessor()
    raw_texts = [docs[doc_id]["body"] for doc_id in doc_ids if doc_id in docs]
    kept_doc_ids = [doc_id for doc_id in doc_ids if doc_id in docs]
    print("Running project preprocessing...", flush=True)
    clean_texts = [processor.normalize(text) for text in raw_texts]

    print(f"Building TF-IDF: max_features={max_features}, min_df={min_df}, max_df={max_df}...", flush=True)
    tfidf_vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
        lowercase=False,
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
        norm="l2",
        dtype=np.float32,
    )
    tfidf_matrix = tfidf_vectorizer.fit_transform(clean_texts)

    dims = min(embedding_dims, max(2, min(tfidf_matrix.shape) - 1))
    print(f"Building LSA embeddings with {dims} dimensions...", flush=True)
    svd_model = TruncatedSVD(n_components=dims, random_state=42)
    embedding_matrix = normalize(svd_model.fit_transform(tfidf_matrix))

    print("Building sparse BM25 matrix using the same preprocessed tokens...", flush=True)
    count_vectorizer = CountVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
        lowercase=False,
        vocabulary=tfidf_vectorizer.vocabulary_,
        dtype=np.float32,
    )
    count_matrix = count_vectorizer.fit_transform(clean_texts).tocsr()
    doc_len = np.asarray(count_matrix.sum(axis=1)).ravel().astype(np.float32)
    avg_doc_len = float(doc_len.mean()) if doc_len.size else 0.0
    doc_freq = np.asarray((count_matrix > 0).sum(axis=0)).ravel().astype(np.float32)
    doc_count = max(len(kept_doc_ids), 1)
    idf = np.log1p((doc_count - doc_freq + 0.5) / (doc_freq + 0.5)).astype(np.float32)
    bm25 = SparseBM25Index(kept_doc_ids, count_vectorizer, count_matrix, doc_len, avg_doc_len, idf)
    index = SearchIndex(
        doc_ids=kept_doc_ids,
        tfidf_vectorizer=tfidf_vectorizer,
        tfidf_matrix=tfidf_matrix,
        svd_model=svd_model,
        embedding_matrix=embedding_matrix,
        bm25=bm25,
        processor=processor,
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving index to {artifact_path}...", flush=True)
    joblib.dump(index, artifact_path, compress=3)
    return index


def load_index(artifact_path: Path = ARTIFACTS_DIR / "search_index.joblib") -> SearchIndex:
    return joblib.load(artifact_path)
