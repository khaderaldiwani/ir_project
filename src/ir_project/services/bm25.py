import math
from collections import Counter
from dataclasses import dataclass


@dataclass
class BM25Index:
    doc_ids: list[str]
    tokenized_docs: list[list[str]]
    k1: float = 1.5
    b: float = 0.75

    def __post_init__(self) -> None:
        self.doc_len = [len(doc) for doc in self.tokenized_docs]
        self.avg_doc_len = sum(self.doc_len) / max(len(self.doc_len), 1)
        self.term_freqs = [Counter(doc) for doc in self.tokenized_docs]
        self.doc_freq: Counter[str] = Counter()
        for freqs in self.term_freqs:
            self.doc_freq.update(freqs.keys())
        self.doc_count = len(self.doc_ids)

    def idf(self, term: str) -> float:
        df = self.doc_freq.get(term, 0)
        return math.log(1 + (self.doc_count - df + 0.5) / (df + 0.5))

    def score(self, query_tokens: list[str], doc_index: int, k1: float | None = None, b: float | None = None) -> float:
        k1 = self.k1 if k1 is None else k1
        b = self.b if b is None else b
        freqs = self.term_freqs[doc_index]
        doc_len = self.doc_len[doc_index] or 1
        score = 0.0
        for term in query_tokens:
            tf = freqs.get(term, 0)
            if tf == 0:
                continue
            denominator = tf + k1 * (1 - b + b * doc_len / max(self.avg_doc_len, 1))
            score += self.idf(term) * (tf * (k1 + 1) / denominator)
        return score

    def search(self, query_tokens: list[str], top_k: int = 10, k1: float | None = None, b: float | None = None) -> list[tuple[str, float]]:
        scores = [
            (self.doc_ids[index], self.score(query_tokens, index, k1=k1, b=b))
            for index in range(self.doc_count)
        ]
        scores.sort(key=lambda item: item[1], reverse=True)
        return [(doc_id, score) for doc_id, score in scores[:top_k] if score > 0]
