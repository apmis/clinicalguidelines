import json
import time
import uuid
from datetime import datetime, timezone

from starlette.requests import Request
from starlette.responses import Response

from app.config import (
    GUIDELINES_ANSWER_MODEL,
    GUIDELINES_EMBEDDING_MODEL,
    GUIDELINES_QUERY_MODEL,
)
from app.monitor.store import Trace, store

MONITORED_PATH = "/api/v1/copilot/guidelines/answer"


async def capture_trace(request: Request, call_next):
    if request.url.path.rstrip("/") != MONITORED_PATH or request.method != "POST":
        return await call_next(request)

    body = await request.body()
    question = ""
    if body:
        try:
            question = json.loads(body).get("question", "")
        except (json.JSONDecodeError, TypeError):
            pass

    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start) * 1000

    trace_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now(timezone.utc).isoformat()

    resp_body = await _consume_response_body(response)
    if resp_body:
        _log_trace(resp_body, question, latency_ms, trace_id, timestamp, response.status_code)
        return Response(
            content=resp_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type or "application/json",
        )

    return response


async def _consume_response_body(response) -> bytes:
    try:
        return response.body or b""
    except Exception:
        pass

    chunks: list[bytes] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks)


def _log_trace(
    resp_body: bytes,
    question: str,
    latency_ms: float,
    trace_id: str,
    timestamp: str,
    status_code: int,
):
    try:
        data = json.loads(resp_body)
    except (json.JSONDecodeError, TypeError):
        return

    if 200 <= status_code < 300:
        guideline_count = sum(
            1 for s in data.get("sources", []) if s.get("source_type") == "guideline"
        )
        pubmed_count = sum(
            1 for s in data.get("sources", []) if s.get("source_type") == "pubmed"
        )
        trace = Trace(
            id=trace_id,
            timestamp=timestamp,
            question=data.get("question", question),
            latency_ms=round(latency_ms, 1),
            retrieval_query=data.get("retrieval_query", ""),
            pubmed_keywords=data.get("pubmed_keywords", []),
            pubmed_and_query=data.get("pubmed_and_query"),
            pubmed_or_query=data.get("pubmed_or_query"),
            answer=data.get("answer", ""),
            guideline_count=guideline_count,
            pubmed_count=pubmed_count,
            retrieval_count=data.get("retrieval_count", 0),
            answer_tokens_approx=max(1, len(data.get("answer", "")) // 4),
            model_query=GUIDELINES_QUERY_MODEL,
            model_answer=GUIDELINES_ANSWER_MODEL,
            embedding_model=GUIDELINES_EMBEDDING_MODEL,
            status="success",
        )
        store.add(trace)
    else:
        trace = Trace(
            id=trace_id,
            timestamp=timestamp,
            question=question,
            latency_ms=round(latency_ms, 1),
            model_query=GUIDELINES_QUERY_MODEL,
            model_answer=GUIDELINES_ANSWER_MODEL,
            embedding_model=GUIDELINES_EMBEDDING_MODEL,
            error=data.get("detail", "Unknown error"),
            status="error",
        )
        store.add(trace)
