from dataclasses import dataclass

from ir_project.services.rag_service import RagService
from ir_project.services.text_processing import TextProcessor


@dataclass
class RagMetricRow:
    source_precision_at_5: float
    source_recall_at_5: float
    answer_query_coverage: float
    citation_coverage: float
    groundedness: float


def evaluate_rag(
    rag: RagService,
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
    method: str = "hybrid_parallel",
    top_k: int = 5,
) -> RagMetricRow:
    processor = TextProcessor()
    precision_values = []
    recall_values = []
    query_coverage_values = []
    citation_values = []
    groundedness_values = []

    for query_id, query in queries.items():
        relevant = {doc_id for doc_id, rel in qrels.get(query_id, {}).items() if rel > 0}
        if not relevant:
            continue
        response = rag.answer(query, method=method, top_k=top_k)
        source_ids = [source["doc_id"] for source in response.sources]
        hits = sum(doc_id in relevant for doc_id in source_ids)
        precision_values.append(hits / top_k)
        recall_values.append(hits / len(relevant))

        query_tokens = set(processor.tokenize(query))
        answer_tokens = set(processor.tokenize(response.answer))
        query_coverage_values.append(
            len(query_tokens & answer_tokens) / len(query_tokens) if query_tokens else 0.0
        )

        cited = sum(f"[{source['rank']}]" in response.answer for source in response.sources)
        citation_values.append(cited / len(response.sources) if response.sources else 0.0)

        source_docs = rag.store.get_many([source["doc_id"] for source in response.sources])
        source_text = " ".join(" ".join(doc["body"].split()) for doc in source_docs.values())
        grounded = sum(
            " ".join(item.split("] ", 1)[-1].split()) in source_text
            for item in response.evidence
        )
        denominator = len(response.evidence)
        groundedness_values.append(grounded / denominator if denominator else 0.0)

    return RagMetricRow(
        source_precision_at_5=_mean(precision_values),
        source_recall_at_5=_mean(recall_values),
        answer_query_coverage=_mean(query_coverage_values),
        citation_coverage=_mean(citation_values),
        groundedness=_mean(groundedness_values),
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
