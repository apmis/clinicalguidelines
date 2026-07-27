import json
import os
import sqlite3
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class Trace:
    id: str
    timestamp: str
    question: str
    latency_ms: float
    retrieval_query: str = ""
    pubmed_keywords: list[str] = field(default_factory=list)
    pubmed_and_query: str | None = None
    pubmed_or_query: str | None = None
    answer: str = ""
    guideline_count: int = 0
    pubmed_count: int = 0
    retrieval_count: int = 0
    answer_tokens_approx: int = 0
    model_query: str = ""
    model_answer: str = ""
    embedding_model: str = ""
    error: str | None = None
    status: str = "success"


_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    question TEXT NOT NULL DEFAULT '',
    latency_ms REAL NOT NULL DEFAULT 0,
    retrieval_query TEXT NOT NULL DEFAULT '',
    pubmed_keywords TEXT NOT NULL DEFAULT '[]',
    pubmed_and_query TEXT,
    pubmed_or_query TEXT,
    answer TEXT NOT NULL DEFAULT '',
    guideline_count INTEGER NOT NULL DEFAULT 0,
    pubmed_count INTEGER NOT NULL DEFAULT 0,
    retrieval_count INTEGER NOT NULL DEFAULT 0,
    answer_tokens_approx INTEGER NOT NULL DEFAULT 0,
    model_query TEXT NOT NULL DEFAULT '',
    model_answer TEXT NOT NULL DEFAULT '',
    embedding_model TEXT NOT NULL DEFAULT '',
    error TEXT,
    status TEXT NOT NULL DEFAULT 'success'
);
"""


def _trace_to_sql_params(trace: Trace) -> dict:
    return {
        "id": trace.id,
        "timestamp": trace.timestamp,
        "question": trace.question,
        "latency_ms": trace.latency_ms,
        "retrieval_query": trace.retrieval_query,
        "pubmed_keywords": json.dumps(trace.pubmed_keywords, ensure_ascii=False),
        "pubmed_and_query": trace.pubmed_and_query,
        "pubmed_or_query": trace.pubmed_or_query,
        "answer": trace.answer,
        "guideline_count": trace.guideline_count,
        "pubmed_count": trace.pubmed_count,
        "retrieval_count": trace.retrieval_count,
        "answer_tokens_approx": trace.answer_tokens_approx,
        "model_query": trace.model_query,
        "model_answer": trace.model_answer,
        "embedding_model": trace.embedding_model,
        "error": trace.error,
        "status": trace.status,
    }


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "question": row["question"],
        "latency_ms": row["latency_ms"],
        "retrieval_query": row["retrieval_query"],
        "pubmed_keywords": json.loads(row["pubmed_keywords"] or "[]"),
        "pubmed_and_query": row["pubmed_and_query"],
        "pubmed_or_query": row["pubmed_or_query"],
        "answer": row["answer"],
        "guideline_count": row["guideline_count"],
        "pubmed_count": row["pubmed_count"],
        "retrieval_count": row["retrieval_count"],
        "answer_tokens_approx": row["answer_tokens_approx"],
        "model_query": row["model_query"],
        "model_answer": row["model_answer"],
        "embedding_model": row["embedding_model"],
        "error": row["error"],
        "status": row["status"],
    }


def _trace_to_dict(trace: Trace) -> dict:
    return {
        "id": trace.id,
        "timestamp": trace.timestamp,
        "question": trace.question,
        "latency_ms": trace.latency_ms,
        "retrieval_query": trace.retrieval_query,
        "pubmed_keywords": list(trace.pubmed_keywords),
        "pubmed_and_query": trace.pubmed_and_query,
        "pubmed_or_query": trace.pubmed_or_query,
        "answer": trace.answer,
        "guideline_count": trace.guideline_count,
        "pubmed_count": trace.pubmed_count,
        "retrieval_count": trace.retrieval_count,
        "answer_tokens_approx": trace.answer_tokens_approx,
        "model_query": trace.model_query,
        "model_answer": trace.model_answer,
        "embedding_model": trace.embedding_model,
        "error": trace.error,
        "status": trace.status,
    }


def _default_db_path() -> str:
    return os.environ.get(
        "TRACES_DB_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "traces.db"),
    )


class TraceStore:
    def __init__(self, max_traces: int = 500, db_path: str | None = None):
        self._max = max_traces
        self._db_path = db_path or _default_db_path()
        self._lock = threading.Lock()
        self._mem_cache: list[dict] = []

        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_TABLE_DDL)
        self._conn.commit()
        self._load_cache()

    def _load_cache(self):
        rows = self._conn.execute(
            "SELECT * FROM traces ORDER BY rowid DESC"
        ).fetchall()
        self._mem_cache = [_row_to_dict(r) for r in rows]

    def add(self, trace: Trace):
        with self._lock:
            params = _trace_to_sql_params(trace)
            self._conn.execute(
                """INSERT INTO traces (id, timestamp, question, latency_ms,
                   retrieval_query, pubmed_keywords, pubmed_and_query,
                   pubmed_or_query, answer, guideline_count, pubmed_count,
                   retrieval_count, answer_tokens_approx, model_query,
                   model_answer, embedding_model, error, status)
                   VALUES (:id, :timestamp, :question, :latency_ms,
                   :retrieval_query, :pubmed_keywords, :pubmed_and_query,
                   :pubmed_or_query, :answer, :guideline_count, :pubmed_count,
                   :retrieval_count, :answer_tokens_approx, :model_query,
                   :model_answer, :embedding_model, :error, :status)""",
                params,
            )
            self._conn.commit()
            self._mem_cache.insert(0, _trace_to_dict(trace))

            count = self._conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
            if count > self._max:
                excess = count - self._max
                self._conn.execute(
                    "DELETE FROM traces WHERE id IN (SELECT id FROM traces ORDER BY rowid ASC LIMIT ?)",
                    (excess,),
                )
                self._conn.commit()
                del self._mem_cache[-excess:]

    def list(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return self._mem_cache[:limit]

    def get(self, trace_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM traces WHERE id = ?", (trace_id,)
            ).fetchone()
            if row is None:
                return None
            return _row_to_dict(row)

    def summary(self) -> dict:
        with self._lock:
            total = len(self._mem_cache)
            if total == 0:
                return {
                    "total_requests": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "avg_latency_ms": 0,
                    "avg_retrieval_count": 0,
                }
            success = sum(1 for t in self._mem_cache if t["status"] == "success")
            latencies = [t["latency_ms"] for t in self._mem_cache]
            retrievals = [t["retrieval_count"] for t in self._mem_cache]
            return {
                "total_requests": total,
                "success_count": success,
                "error_count": total - success,
                "avg_latency_ms": round(sum(latencies) / len(latencies), 1),
                "avg_retrieval_count": round(sum(retrievals) / len(retrievals), 1),
            }

    def clear(self):
        with self._lock:
            self._conn.execute("DELETE FROM traces")
            self._conn.commit()
            self._mem_cache.clear()


store = TraceStore()
