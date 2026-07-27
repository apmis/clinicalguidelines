"""Exposes the standalone HTTP endpoint for searching clinical guideline passages."""

from fastapi import APIRouter, HTTPException, status

from app.models import (
    GuidelinesAnswerRequest,
    GuidelinesAnswerResponse,
    GuidelinesPipelineInput,
    GuidelinesSearchRequest,
    GuidelinesSearchResponse,
)
from app.pipeline import answer_guideline_question
from app.retrieval import build_guideline_filters, search_guidelines

router = APIRouter(tags=["guidelines"])


@router.post(
    "/copilot/guidelines/search",
    response_model=GuidelinesSearchResponse,
)
def search_copilot_guidelines(
    payload: GuidelinesSearchRequest,
) -> GuidelinesSearchResponse:
    try:
        sources = search_guidelines(
            question=payload.question,
            top_k=payload.top_k,
            filters=build_guideline_filters(payload),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The guideline search service is temporarily unavailable.",
        ) from exc

    return GuidelinesSearchResponse(
        question=payload.question,
        sources=sources,
        retrieval_count=len(sources),
    )


@router.post(
    "/copilot/guidelines/answer",
    response_model=GuidelinesAnswerResponse,
)
def answer_copilot_guidelines(
    payload: GuidelinesAnswerRequest,
) -> GuidelinesAnswerResponse:
    try:
        return answer_guideline_question(
            GuidelinesPipelineInput(question=payload.question)
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The guideline answer service is temporarily unavailable.",
        ) from exc
