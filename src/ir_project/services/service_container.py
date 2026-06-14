import json
from dataclasses import dataclass

from ir_project.config import ARTIFACTS_DIR, resolve_artifact_path
from ir_project.services.database import DocumentStore
from ir_project.services.indexing_service import load_index
from ir_project.services.rag_service import RagService
from ir_project.services.retrieval_service import RetrievalService


@dataclass
class ServiceContainer:
    metadata: dict
    store: DocumentStore
    retriever: RetrievalService
    rag: RagService


def load_service_container() -> ServiceContainer:
    metadata_path = ARTIFACTS_DIR / "dataset_metadata.json"
    if not metadata_path.exists():
        raise RuntimeError("Dataset metadata is missing. Run scripts/prepare.py first.")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    store = DocumentStore(resolve_artifact_path(metadata["db_path"], "documents.sqlite"))
    retriever = RetrievalService(load_index(), store)
    return ServiceContainer(
        metadata=metadata,
        store=store,
        retriever=retriever,
        rag=RagService(retriever, store),
    )
