import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("IR_DATASETS_HOME", str(ROOT / "data" / "raw" / "ir_datasets"))
os.environ.setdefault("TMP", str(ROOT / ".tmp"))
os.environ.setdefault("TEMP", str(ROOT / ".tmp"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".tmp" / "matplotlib"))

sys.path.insert(0, str(ROOT / ".codex_deps"))
sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ir_project.config import ARTIFACTS_DIR, DEFAULT_DATASET_ID, DEFAULT_MAX_QUERIES, ensure_dirs
from ir_project.services.data_service import prepare_dataset, prepare_local_msmarco
from ir_project.services.evaluation_service import evaluate, save_metrics_chart
from ir_project.services.indexing_service import load_index
from ir_project.services.retrieval_service import RetrievalService


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval methods with MAP, nDCG, P@10, and Recall.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET_ID)
    parser.add_argument("--local-msmarco", action="store_true", help="Use local MS MARCO TSV files instead of ir_datasets.")
    parser.add_argument("--collection-path", default="data/raw/msmarco/collection.tsv")
    parser.add_argument("--queries-path", default="data/raw/msmarco/queries.tsv")
    parser.add_argument("--qrels-path", default="data/raw/msmarco/qrels.txt")
    parser.add_argument("--max-queries", type=int, default=DEFAULT_MAX_QUERIES)
    parser.add_argument("--refine", action="store_true", help="Evaluate after query refinement.")
    args = parser.parse_args()

    ensure_dirs()
    metadata_path = ARTIFACTS_DIR / "dataset_metadata.json"
    max_docs = 250_000
    if metadata_path.exists():
        max_docs = json.loads(metadata_path.read_text(encoding="utf-8")).get("actual_docs", max_docs)

    if args.local_msmarco:
        prepared = prepare_local_msmarco(
            ROOT / args.collection_path,
            ROOT / args.queries_path,
            ROOT / args.qrels_path,
            max_docs=max_docs,
            max_queries=args.max_queries,
        )
    else:
        prepared = prepare_dataset(args.dataset, max_docs=max_docs, max_queries=args.max_queries)
    retriever = RetrievalService(load_index())
    rows = evaluate(retriever, prepared.queries, prepared.qrels, refine=args.refine)

    csv_path = ARTIFACTS_DIR / ("evaluation_metrics_refined.csv" if args.refine else "evaluation_metrics.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["method", "map", "ndcg", "precision_at_10", "recall"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
            print(row)
    chart_path = save_metrics_chart(
        rows,
        output_path=(ARTIFACTS_DIR.parent / "reports" / "figures" / ("evaluation_metrics_refined.png" if args.refine else "evaluation_metrics.png")),
    )
    print(f"Saved metrics to {csv_path}")
    print(f"Saved chart to {chart_path}")


if __name__ == "__main__":
    main()
