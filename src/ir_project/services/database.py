import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable


class DocumentStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                body TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_doc_id ON documents(doc_id)")
        return conn

    def reset(self) -> None:
        with closing(self.connect()) as conn:
            with conn:
                conn.execute("DELETE FROM documents")

    def upsert_many(self, rows: Iterable[tuple[str, str, str]]) -> None:
        with closing(self.connect()) as conn:
            with conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO documents(doc_id, title, body) VALUES (?, ?, ?)",
                    rows,
                )

    def get(self, doc_id: str) -> dict[str, str] | None:
        with closing(self.connect()) as conn:
            row = conn.execute(
                "SELECT doc_id, title, body FROM documents WHERE doc_id = ?", (doc_id,)
            ).fetchone()
        if not row:
            return None
        return {"doc_id": row[0], "title": row[1], "body": row[2]}

    def get_many(self, doc_ids: list[str]) -> dict[str, dict[str, str]]:
        if not doc_ids:
            return {}
        result: dict[str, dict[str, str]] = {}
        with closing(self.connect()) as conn:
            for start in range(0, len(doc_ids), 900):
                batch = doc_ids[start : start + 900]
                placeholders = ",".join("?" for _ in batch)
                rows = conn.execute(
                    f"SELECT doc_id, title, body FROM documents WHERE doc_id IN ({placeholders})",
                    batch,
                ).fetchall()
                result.update(
                    {row[0]: {"doc_id": row[0], "title": row[1], "body": row[2]} for row in rows}
                )
        return result

    def count(self) -> int:
        with closing(self.connect()) as conn:
            return int(conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
