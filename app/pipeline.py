"""Orchestrates query planning, retrieval, relevance selection, and synthesis."""

from app.models import (
    GuidelinesAnswerResponse,
    GuidelinesPipelineInput,
)
from app.retrieval import (
    rewrite_guideline_query,
    retrieve_guideline_candidates,
    select_relevant_guidelines,
)
from app.synthesis import synthesize_guideline_answer


def answer_guideline_question(
    pipeline_input: GuidelinesPipelineInput,
) -> GuidelinesAnswerResponse:
    plan = rewrite_guideline_query(
        question=pipeline_input.question,
        patient_context=pipeline_input.patient_context,
    )
    candidates = retrieve_guideline_candidates(plan.retrieval_query)
    sources = select_relevant_guidelines(candidates)
    answer = synthesize_guideline_answer(
        question=pipeline_input.question,
        sources=sources,
        patient_context=pipeline_input.patient_context,
    )
    return GuidelinesAnswerResponse(
        question=pipeline_input.question,
        retrieval_query=plan.retrieval_query,
        answer=answer,
        sources=sources,
        retrieval_count=len(sources),
    )
