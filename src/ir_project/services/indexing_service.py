from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from ir_project.config import ARTIFACTS_DIR
from ir_project.services.bm25 import BM25Index
from ir_project.services.database import DocumentStore
from ir_project.services.text_processing import TextProcessor


@dataclass
class SearchIndex:
    doc_ids: list[str]
    tfidf_vectorizer: TfidfVectorizer
    tfidf_matrix: sparse.csr_matrix
    svd_model: TruncatedSVD
    embedding_matrix: np.ndarray
    bm25: BM25Index
    processor: TextProcessor


def build_index(
    doc_ids: list[str],
    db_path: Path,
    artifact_path: Path = ARTIFACTS_DIR / "search_index.joblib",
    max_features: int = 80_000,
    embedding_dims: int = 256,
) -> SearchIndex:
    store = DocumentStore(db_path)
    docs = store.get_many(doc_ids)
    processor = TextProcessor()
    raw_texts = [docs[doc_id]["body"] for doc_id in doc_ids if doc_id in docs]
    kept_doc_ids = [doc_id for doc_id in doc_ids if doc_id in docs]
    clean_texts = [processor.normalize(text) for text in raw_texts]
    tokenized_docs = [text.split() for text in clean_texts]

    tfidf_vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        token_pattern=None,
        lowercase=False,
        max_features=max_features,
        norm="l2",
    )
    tfidf_matrix = tfidf_vectorizer.fit_transform(clean_texts)

    dims = min(embedding_dims, max(2, min(tfidf_matrix.shape) - 1))
    svd_model = TruncatedSVD(n_components=dims, random_state=42)
    embedding_matrix = normalize(svd_model.fit_transform(tfidf_matrix))

    bm25 = BM25Index(kept_doc_ids, tokenized_docs)
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
    joblib.dump(index, artifact_path, compress=3)
    return index


def load_index(artifact_path: Path = ARTIFACTS_DIR / "search_index.joblib") -> SearchIndex:
    return joblib.load(artifact_path)
