from dataclasses import dataclass

from ir_project.services.database import DocumentStore
from ir_project.services.retrieval_service import RetrievalService


@dataclass
class RagAnswer:
    answer: str
    sources: list[dict[str, str]]


class RagService:
    def __init__(self, retriever: RetrievalService, store: DocumentStore):
        self.retriever = retriever
        self.store = store

    def answer(self, question: str, method: str = "hybrid_parallel", top_k: int = 5) -> RagAnswer:
        results = self.retriever.search(question, method=method, top_k=top_k)
        documents = self.store.get_many([result.doc_id for result in results])
        sources = []
        snippets = []
        for result in results:
            doc = documents.get(result.doc_id)
            if not doc:
                continue
            body = " ".join(doc["body"].split())
            snippet = body[:700]
            sources.append(
                {
                    "doc_id": result.doc_id,
                    "rank": str(result.rank),
                    "score": f"{result.score:.4f}",
                    "snippet": snippet,
                }
            )
            snippets.append(f"[{result.rank}] {snippet}")

        if not snippets:
            return RagAnswer(
                "Documents were retrieved, but their original text was not found in the local document store. "
                "Check that artifacts/documents.sqlite exists next to search_index.joblib.",
                sources,
            )

        answer = (
            "Based on the retrieved documents, the strongest evidence is summarized below:\n\n"
            + "\n\n".join(snippets[:3])
            + "\n\nThis is an extractive RAG answer: it grounds the response in the retrieved passages and lists the source document ids."
        )
        return RagAnswer(answer=answer, sources=sources)
