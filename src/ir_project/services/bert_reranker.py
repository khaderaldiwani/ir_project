from dataclasses import dataclass
import shutil

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
        _materialize_huggingface_cache_links(cache_dir)
        local_model = _local_cached_model_path(cache_dir)
        model_source = str(local_model) if local_model else self.model_name
        self.model = SentenceTransformer(model_source, cache_folder=str(cache_dir))

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


def _materialize_huggingface_cache_links(cache_dir) -> None:
    """Convert copied Linux symlink placeholders in HF cache into real files on Windows."""
    for snapshot_dir in cache_dir.glob("models--*/snapshots/*"):
        if not snapshot_dir.is_dir():
            continue
        blobs_dir = snapshot_dir.parents[1] / "blobs"
        if not blobs_dir.exists():
            continue
        for path in snapshot_dir.rglob("*"):
            if not path.is_file() or path.stat().st_size > 256:
                continue
            try:
                target = path.read_text(encoding="utf-8").strip()
            except UnicodeDecodeError:
                continue
            if "/blobs/" not in target.replace("\\", "/"):
                continue
            blob = blobs_dir / target.rsplit("/", 1)[-1]
            if blob.exists():
                shutil.copyfile(blob, path)


def _local_cached_model_path(cache_dir):
    for snapshot_dir in cache_dir.glob("models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*"):
        if (snapshot_dir / "modules.json").exists() and (snapshot_dir / "config.json").exists():
            return snapshot_dir
    return None
