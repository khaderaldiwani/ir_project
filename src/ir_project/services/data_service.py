from collections import defaultdict
from dataclasses import dataclass
import gzip
from pathlib import Path

from ir_project.config import ARTIFACTS_DIR, DEFAULT_DATASET_ID, DEFAULT_MAX_DOCS, DEFAULT_MAX_QUERIES
from ir_project.services.database import DocumentStore

import ir_datasets


@dataclass
class PreparedDataset:
    dataset_id: str
    doc_ids: list[str]
    queries: dict[str, str]
    qrels: dict[str, dict[str, int]]
    db_path: Path


def _doc_text(doc) -> tuple[str, str, str]:
    doc_id = str(getattr(doc, "doc_id"))
    title = getattr(doc, "title", "") or ""
    parts = []
    fields = getattr(doc, "_fields", None)
    if fields:
        for field in fields:
            if field == "doc_id":
                continue
            value = getattr(doc, field, None)
            if value:
                label = field.replace("_", " ").title()
                parts.append(f"{label}: {_stringify(value)}")
    else:
        for field in ["title", "text", "body", "abstract", "description", "summary", "detailed_description", "condition", "eligibility"]:
            value = getattr(doc, field, None)
            if value:
                parts.append(_stringify(value))
    body = "\n".join(parts) if parts else str(doc)
    return doc_id, title, body


def _query_text(query) -> tuple[str, str]:
    query_id = str(getattr(query, "query_id"))
    fields = getattr(query, "_fields", None)
    if fields:
        parts = []
        for field in fields:
            if field == "query_id":
                continue
            value = getattr(query, field, None)
            if value:
                parts.append(_stringify(value))
        return query_id, " ".join(parts)
    text = getattr(query, "text", None) or getattr(query, "title", None) or str(query)
    return query_id, _stringify(text)


def prepare_dataset(
    dataset_id: str = DEFAULT_DATASET_ID,
    max_docs: int = DEFAULT_MAX_DOCS,
    max_queries: int = DEFAULT_MAX_QUERIES,
    db_path: Path | None = None,
    reset_store: bool = False,
) -> PreparedDataset:
    dataset = ir_datasets.load(dataset_id)
    db_path = db_path or ARTIFACTS_DIR / "documents.sqlite"
    store = DocumentStore(db_path)
    if reset_store:
        store.reset()

    queries = dict(_query_text(query) for query in dataset.queries_iter())
    selected_query_ids = list(queries) if max_queries <= 0 else list(queries)[:max_queries]
    queries = {qid: queries[qid] for qid in selected_query_ids}

    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    relevant_doc_ids: set[str] = set()
    for qrel in dataset.qrels_iter():
        query_id = str(qrel.query_id)
        if query_id not in queries:
            continue
        relevance = int(getattr(qrel, "relevance", 0))
        doc_id = str(qrel.doc_id)
        qrels[query_id][doc_id] = relevance
        if relevance > 0:
            relevant_doc_ids.add(doc_id)

    doc_rows: list[tuple[str, str, str]] = []
    doc_ids: list[str] = []
    seen: set[str] = set()

    docs_store = dataset.docs_store()
    if relevant_doc_ids:
        relevant_docs = docs_store.get_many(list(relevant_doc_ids))
        if isinstance(relevant_docs, dict):
            relevant_docs = relevant_docs.values()
        for doc in relevant_docs:
            doc_id, title, body = _doc_text(doc)
            if doc_id not in seen:
                seen.add(doc_id)
                doc_ids.append(doc_id)
                doc_rows.append((doc_id, title, body))

    for doc in dataset.docs_iter():
        if max_docs > 0 and len(doc_ids) >= max_docs:
            break
        doc_id, title, body = _doc_text(doc)
        if doc_id in seen:
            continue
        seen.add(doc_id)
        doc_ids.append(doc_id)
        doc_rows.append((doc_id, title, body))
        if len(doc_rows) >= 10_000:
            store.upsert_many(doc_rows)
            doc_rows.clear()

    if doc_rows:
        store.upsert_many(doc_rows)

    return PreparedDataset(
        dataset_id=dataset_id,
        doc_ids=doc_ids,
        queries=queries,
        qrels=dict(qrels),
        db_path=db_path,
    )


def _stringify(value) -> str:
    if isinstance(value, (list, tuple, set)):
        return " ".join(_stringify(item) for item in value if item)
    return str(value)


def prepare_local_msmarco(
    collection_path: Path,
    queries_path: Path,
    qrels_path: Path,
    max_docs: int = DEFAULT_MAX_DOCS,
    max_queries: int = DEFAULT_MAX_QUERIES,
    db_path: Path | None = None,
) -> PreparedDataset:
    db_path = db_path or ARTIFACTS_DIR / "documents.sqlite"
    store = DocumentStore(db_path)

    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    selected_query_ids: list[str] = []
    relevant_doc_ids: set[str] = set()
    with _open_text(qrels_path) as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            query_id, _, doc_id, relevance = parts[:4]
            if query_id not in selected_query_ids:
                if len(selected_query_ids) >= max_queries:
                    continue
                selected_query_ids.append(query_id)
            if query_id in selected_query_ids:
                rel = int(float(relevance))
                qrels[query_id][doc_id] = rel
                if rel > 0:
                    relevant_doc_ids.add(doc_id)

    queries: dict[str, str] = {}
    with _open_text(queries_path) as file:
        for line in file:
            query_id, text = line.rstrip("\n").split("\t", 1)
            if query_id in selected_query_ids:
                queries[query_id] = text

    doc_rows: list[tuple[str, str, str]] = []
    doc_ids: list[str] = []
    seen: set[str] = set()
    with _open_text(collection_path) as file:
        for line in file:
            parts = line.rstrip("\n").split("\t", 1)
            if len(parts) != 2:
                continue
            doc_id, text = parts
            must_keep = doc_id in relevant_doc_ids
            if not must_keep and len(doc_ids) >= max_docs:
                continue
            if doc_id in seen:
                continue
            seen.add(doc_id)
            doc_ids.append(doc_id)
            doc_rows.append((doc_id, "", text))
            if len(doc_rows) >= 10_000:
                store.upsert_many(doc_rows)
                doc_rows.clear()
            if len(doc_ids) >= max_docs and relevant_doc_ids.issubset(seen):
                break

    if doc_rows:
        store.upsert_many(doc_rows)

    return PreparedDataset(
        dataset_id="local-msmarco-passage",
        doc_ids=doc_ids,
        queries=queries,
        qrels=dict(qrels),
        db_path=db_path,
    )


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")
