from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt

from ir_project.config import FIGURES_DIR, TOP_K
from ir_project.services.retrieval_service import RetrievalService, SearchResult


@dataclass
class MetricRow:
    method: str
    map_at_depth: float
    ndcg_at_10: float
    precision_at_10: float
    recall_at_depth: float


def average_precision(results: list[SearchResult], relevant: dict[str, int], k: int | None = None) -> float:
    positive = {doc_id for doc_id, rel in relevant.items() if rel > 0}
    if not positive:
        return 0.0
    hits = 0
    precision_sum = 0.0
    evaluated = results if k is None else results[:k]
    for rank, result in enumerate(evaluated, start=1):
        if result.doc_id in positive:
            hits += 1
            precision_sum += hits / rank
    return precision_sum / len(positive)


def ndcg_at_k(results: list[SearchResult], relevant: dict[str, int], k: int = TOP_K) -> float:
    def dcg(gains: list[int]) -> float:
        value = 0.0
        for index, gain in enumerate(gains, start=1):
            value += (2**gain - 1) / __import__("math").log2(index + 1)
        return value

    gains = [int(relevant.get(result.doc_id, 0)) for result in results[:k]]
    ideal = sorted([int(rel) for rel in relevant.values() if rel > 0], reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    return dcg(gains) / ideal_dcg if ideal_dcg > 0 else 0.0


def precision_at_k(results: list[SearchResult], relevant: dict[str, int], k: int = TOP_K) -> float:
    positive = {doc_id for doc_id, rel in relevant.items() if rel > 0}
    if not positive:
        return 0.0
    hits = sum(1 for result in results[:k] if result.doc_id in positive)
    return hits / k


def recall_at_k(results: list[SearchResult], relevant: dict[str, int], k: int | None = None) -> float:
    positive = {doc_id for doc_id, rel in relevant.items() if rel > 0}
    if not positive:
        return 0.0
    evaluated = results if k is None else results[:k]
    hits = sum(1 for result in evaluated if result.doc_id in positive)
    return hits / len(positive)


def evaluate(
    retriever: RetrievalService,
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
    methods: list[str] | None = None,
    retrieval_depth: int = 1000,
    metric_k: int = TOP_K,
    refine: bool = False,
) -> list[MetricRow]:
    methods = methods or ["tfidf", "bm25", "embedding", "hybrid_parallel", "hybrid_serial"]
    rows: list[MetricRow] = []
    for method in methods:
        ap_values = []
        ndcg_values = []
        p10_values = []
        recall_values = []
        for query_id, query_text in queries.items():
            relevant = qrels.get(query_id, {})
            if not relevant:
                continue
            results = retriever.search(query_text, method=method, top_k=retrieval_depth, refine=refine)
            ap_values.append(average_precision(results, relevant, k=retrieval_depth))
            ndcg_values.append(ndcg_at_k(results, relevant, k=metric_k))
            p10_values.append(precision_at_k(results, relevant, k=metric_k))
            recall_values.append(recall_at_k(results, relevant, k=retrieval_depth))
        rows.append(
            MetricRow(
                method=method,
                map_at_depth=_mean(ap_values),
                ndcg_at_10=_mean(ndcg_values),
                precision_at_10=_mean(p10_values),
                recall_at_depth=_mean(recall_values),
            )
        )
    return rows


def save_metrics_chart(rows: list[MetricRow], output_path: Path = FIGURES_DIR / "evaluation_metrics.png") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels = [row.method for row in rows]
    metrics = {
        "MAP@depth": [row.map_at_depth for row in rows],
        "nDCG@10": [row.ndcg_at_10 for row in rows],
        "P@10": [row.precision_at_10 for row in rows],
        "Recall@depth": [row.recall_at_depth for row in rows],
    }
    x = range(len(labels))
    width = 0.18
    plt.figure(figsize=(12, 6))
    for idx, (metric, values) in enumerate(metrics.items()):
        offsets = [item + (idx - 1.5) * width for item in x]
        plt.bar(offsets, values, width=width, label=metric)
    plt.xticks(list(x), labels, rotation=20, ha="right")
    plt.ylim(0, 1.0)
    plt.ylabel("Score")
    plt.title("IR Evaluation Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
