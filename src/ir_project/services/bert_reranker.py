from dataclasses import dataclass

import numpy as np

from ir_project.config import ARTIFACTS_DIR
from ir_project.services.database import DocumentStore
from ir_project.services.retrieval_service import SearchResult


DEFAULT_BERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class BertReranker:
    store: DocumentStore
    model_name: str = DEFAULT_BERT_MODEL
    max_chars: int = 1200

    def __post_init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "BERT reranking requires sentence-transformers. Install it with: "
                "python -m pip install sentence-transformers"
            ) from exc

        cache_dir = ARTIFACTS_DIR / "bert_model_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.model = SentenceTransformer(self.model_name, cache_folder=str(cache_dir))

    def rerank(self, query: str, candidates: list[SearchResult], top_k: int) -> list[SearchResult]:
        if not candidates:
            return []
        docs = self.store.get_many([candidate.doc_id for candidate in candidates])
        pairs: list[tuple[SearchResult, str]] = []
        for candidate in candidates:
            doc = docs.get(candidate.doc_id)
            if not doc:
                continue
            text = " ".join(doc["body"].split())[: self.max_chars]
            if text:
                pairs.append((candidate, text))
        if not pairs:
            return []

        query_embedding = self.model.encode([query], normalize_embeddings=True)
        doc_embeddings = self.model.encode([text for _, text in pairs], normalize_embeddings=True)
        scores = np.asarray(doc_embeddings @ query_embedding.T).ravel()

        ranked_indices = np.argsort(scores)[::-1][:top_k]
        results: list[SearchResult] = []
        for rank, index in enumerate(ranked_indices, start=1):
            original, _ = pairs[int(index)]
            results.append(
                SearchResult(
                    doc_id=original.doc_id,
                    score=float(scores[int(index)]),
                    rank=rank,
                    method="BERT-Rerank",
                )
            )
        return results
