import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("IR_DATASETS_HOME", str(ROOT / "data" / "raw" / "ir_datasets"))
sys.path.insert(0, str(ROOT / ".codex_deps"))
sys.path.insert(0, str(ROOT / "src"))

from ir_project.config import ARTIFACTS_DIR, DEFAULT_DATASET_ID
from ir_project.services.data_service import load_evaluation_data
from ir_project.services.evaluation_service import (
    average_precision,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from ir_project.services.service_container import load_service_container


def main() -> None:
    queries, qrels = load_evaluation_data(DEFAULT_DATASET_ID, max_queries=0)
    retriever = load_service_container().retriever
    values = {"map_at_10": [], "ndcg_at_10": [], "precision_at_10": [], "recall_at_10": []}

    for query_id, query in queries.items():
        relevant = qrels.get(query_id, {})
        if not relevant:
            continue
        results = retriever.search(query, method="bert_rerank", top_k=10)
        values["map_at_10"].append(average_precision(results, relevant, k=10))
        values["ndcg_at_10"].append(ndcg_at_k(results, relevant, k=10))
        values["precision_at_10"].append(precision_at_k(results, relevant, k=10))
        values["recall_at_10"].append(recall_at_k(results, relevant, k=10))

    row = {"method": "bert_rerank"}
    row.update({name: sum(items) / len(items) if items else 0.0 for name, items in values.items()})
    output = ARTIFACTS_DIR / "evaluation_metrics_bert.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    print(row)
    print(f"Saved BERT evaluation to {output}")


if __name__ == "__main__":
    main()
