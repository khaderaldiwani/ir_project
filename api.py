import os
import sys
import csv
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("IR_DATASETS_HOME", str(ROOT / "data" / "raw" / "ir_datasets"))
os.environ.setdefault("TMP", str(ROOT / ".tmp"))
os.environ.setdefault("TEMP", str(ROOT / ".tmp"))
sys.path.insert(0, str(ROOT / ".codex_deps"))
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ir_project.services.service_container import ServiceContainer, load_service_container
from ir_project.config import ARTIFACTS_DIR


app = FastAPI(
    title="Information Retrieval Service API",
    version="1.0.0",
    description="REST API gateway for retrieval, RAG, and evaluation artifacts.",
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    method: str = "hybrid_parallel"
    top_k: int = Field(default=10, ge=1, le=100)
    k1: float = Field(default=1.5, ge=0.1, le=5.0)
    b: float = Field(default=0.75, ge=0.0, le=1.0)
    refine: bool = False


class RagRequest(SearchRequest):
    top_k: int = Field(default=5, ge=1, le=20)


@lru_cache(maxsize=1)
def services() -> ServiceContainer:
    return load_service_container()


@app.get("/health")
def health() -> dict:
    container = services()
    return {
        "status": "ok",
        "dataset": container.metadata["dataset_id"],
        "documents": container.store.count(),
    }


@app.post("/search")
def search(request: SearchRequest) -> dict:
    container = services()
    try:
        results = container.retriever.search(
            request.query,
            method=request.method,
            top_k=request.top_k,
            k1=request.k1,
            b=request.b,
            refine=request.refine,
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    docs = container.store.get_many([result.doc_id for result in results])
    return {
        "query": request.query,
        "method": request.method,
        "results": [
            {
                "rank": result.rank,
                "doc_id": result.doc_id,
                "score": result.score,
                "text": docs.get(result.doc_id, {}).get("body", ""),
            }
            for result in results
        ],
    }


@app.post("/rag")
def rag(request: RagRequest) -> dict:
    container = services()
    try:
        answer = container.rag.answer(
            request.query,
            method=request.method,
            top_k=request.top_k,
            refine=request.refine,
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "query": request.query,
        "answer": answer.answer,
        "evidence": answer.evidence,
        "sources": answer.sources,
    }


@app.get("/metrics")
def metrics() -> dict:
    files = {
        "base": "evaluation_metrics.csv",
        "refined": "evaluation_metrics_refined.csv",
        "bert": "evaluation_metrics_bert.csv",
        "rag": "rag_evaluation_metrics.csv",
    }
    payload = {}
    for name, filename in files.items():
        path = ARTIFACTS_DIR / filename
        if path.exists():
            with path.open(encoding="utf-8", newline="") as file:
                payload[name] = list(csv.DictReader(file))
    return payload
