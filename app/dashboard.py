import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import (
    GUIDELINES_ANSWER_MODEL,
    GUIDELINES_EMBEDDING_MODEL,
    GUIDELINES_QUERY_MODEL,
)
from app.models import (
    ClinicalEvidenceSource,
    GuidelinesAnswerRequest,
    GuidelinesAnswerResponse,
    GuidelinesPipelineInput,
    GuidelineSource,
    PubMedSource,
)
from app.monitor.store import Trace, store
from app.pipeline import answer_guideline_question

router = APIRouter()

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    html_path = _STATIC_DIR / "dashboard.html"
    if not html_path.exists():
        return HTMLResponse(
            content="<h1>Dashboard not found</h1>", status_code=404
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@router.get("/dashboard/api/traces")
async def get_traces(limit: int = 50):
    return JSONResponse(content={
        "traces": store.list(limit=limit),
        "summary": store.summary(),
    })


@router.get("/dashboard/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    trace = store.get(trace_id)
    if trace is None:
        return JSONResponse(content={"detail": "Trace not found"}, status_code=404)
    return JSONResponse(content=trace)


@router.delete("/dashboard/api/traces")
async def clear_traces():
    store.clear()
    return JSONResponse(content={"status": "ok"})


@router.post("/dashboard/answer")
async def monitored_answer(payload: GuidelinesAnswerRequest):
    pipeline_input = GuidelinesPipelineInput(question=payload.question)
    trace_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now(timezone.utc).isoformat()

    start = time.perf_counter()
    error = None
    try:
        response = answer_guideline_question(pipeline_input)
    except RuntimeError as exc:
        error = str(exc)
        latency_ms = (time.perf_counter() - start) * 1000

        trace = Trace(
            id=trace_id,
            timestamp=timestamp,
            question=pipeline_input.question,
            latency_ms=round(latency_ms, 1),
            model_query=GUIDELINES_QUERY_MODEL,
            model_answer=GUIDELINES_ANSWER_MODEL,
            embedding_model=GUIDELINES_EMBEDDING_MODEL,
            error=error,
            status="error",
        )
        store.add(trace)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The guideline answer service is temporarily unavailable.",
        ) from exc

    latency_ms = (time.perf_counter() - start) * 1000

    guideline_sources = [s for s in response.sources if isinstance(s, GuidelineSource)]
    pubmed_sources = [s for s in response.sources if isinstance(s, PubMedSource)]

    trace = Trace(
        id=trace_id,
        timestamp=timestamp,
        question=response.question,
        latency_ms=round(latency_ms, 1),
        retrieval_query=response.retrieval_query,
        pubmed_keywords=response.pubmed_keywords,
        pubmed_and_query=response.pubmed_and_query,
        pubmed_or_query=response.pubmed_or_query,
        answer=response.answer,
        guideline_count=len(guideline_sources),
        pubmed_count=len(pubmed_sources),
        retrieval_count=response.retrieval_count,
        answer_tokens_approx=max(1, len(response.answer) // 4),
        model_query=GUIDELINES_QUERY_MODEL,
        model_answer=GUIDELINES_ANSWER_MODEL,
        embedding_model=GUIDELINES_EMBEDDING_MODEL,
        status="success",
    )
    store.add(trace)

    return GuidelinesAnswerResponse(
        question=response.question,
        retrieval_query=response.retrieval_query,
        pubmed_keywords=response.pubmed_keywords,
        pubmed_and_query=response.pubmed_and_query,
        pubmed_or_query=response.pubmed_or_query,
        answer=response.answer,
        sources=response.sources,
        retrieval_count=response.retrieval_count,
    )
