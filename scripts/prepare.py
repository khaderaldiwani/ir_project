import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("IR_DATASETS_HOME", str(ROOT / "data" / "raw" / "ir_datasets"))
os.environ.setdefault("TMP", str(ROOT / ".tmp"))
os.environ.setdefault("TEMP", str(ROOT / ".tmp"))

sys.path.insert(0, str(ROOT / ".codex_deps"))
sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ir_project.config import ARTIFACTS_DIR, DEFAULT_DATASET_ID, DEFAULT_MAX_DOCS, DEFAULT_MAX_QUERIES, ensure_dirs
from ir_project.services.data_service import prepare_dataset, prepare_local_msmarco
from ir_project.services.indexing_service import build_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare dataset and build all retrieval indexes.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET_ID)
    parser.add_argument("--local-msmarco", action="store_true", help="Use local MS MARCO TSV files instead of ir_datasets.")
    parser.add_argument("--collection-path", default="data/raw/msmarco/collection.tsv")
    parser.add_argument("--queries-path", default="data/raw/msmarco/queries.tsv")
    parser.add_argument("--qrels-path", default="data/raw/msmarco/qrels.txt")
    parser.add_argument("--max-docs", type=int, default=DEFAULT_MAX_DOCS, help="0 means use all documents.")
    parser.add_argument("--max-queries", type=int, default=DEFAULT_MAX_QUERIES, help="0 means use all queries.")
    parser.add_argument("--embedding-dims", type=int, default=256)
    parser.add_argument("--max-features", type=int, default=30_000)
    parser.add_argument("--min-df", type=int, default=2)
    parser.add_argument("--max-df", type=float, default=0.95)
    args = parser.parse_args()

    ensure_dirs()
    if args.local_msmarco:
        prepared = prepare_local_msmarco(
            ROOT / args.collection_path,
            ROOT / args.queries_path,
            ROOT / args.qrels_path,
            max_docs=args.max_docs,
            max_queries=args.max_queries,
        )
    else:
        prepared = prepare_dataset(args.dataset, max_docs=args.max_docs, max_queries=args.max_queries, reset_store=True)
    build_index(
        prepared.doc_ids,
        prepared.db_path,
        embedding_dims=args.embedding_dims,
        max_features=args.max_features,
        min_df=args.min_df,
        max_df=args.max_df,
    )

    metadata = {
        "dataset_id": prepared.dataset_id,
        "max_docs": "all" if args.max_docs <= 0 else args.max_docs,
        "actual_docs": len(prepared.doc_ids),
        "queries": len(prepared.queries),
        "qrels_queries": len(prepared.qrels),
        "db_path": str(prepared.db_path),
        "max_features": args.max_features,
        "min_df": args.min_df,
        "max_df": args.max_df,
    }
    (ARTIFACTS_DIR / "dataset_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
