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
from ir_project.services.rag_evaluation_service import evaluate_rag
from ir_project.services.service_container import load_service_container


def main() -> None:
    queries, qrels = load_evaluation_data(DEFAULT_DATASET_ID, max_queries=0)
    container = load_service_container()
    row = evaluate_rag(container.rag, queries, qrels)
    output = ARTIFACTS_DIR / "rag_evaluation_metrics.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.__dict__))
        writer.writeheader()
        writer.writerow(row.__dict__)
    print(row)
    print(f"Saved RAG evaluation to {output}")


if __name__ == "__main__":
    main()
