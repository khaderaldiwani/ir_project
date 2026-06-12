import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".codex_deps"))
sys.path.insert(0, str(ROOT / "src"))

from ir_project.config import ARTIFACTS_DIR
from ir_project.services.bert_reranker import DEFAULT_BERT_MODEL


def main() -> None:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "sentence-transformers is not installed. Run: python -m pip install sentence-transformers"
        ) from exc

    cache_dir = ARTIFACTS_DIR / "bert_model_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(DEFAULT_BERT_MODEL, cache_folder=str(cache_dir))
    vectors = model.encode(["BERT model is ready."], normalize_embeddings=True)
    print(f"Loaded {DEFAULT_BERT_MODEL}")
    print(f"Embedding shape: {vectors.shape}")
    print(f"Cache directory: {cache_dir}")


if __name__ == "__main__":
    main()
