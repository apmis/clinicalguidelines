"""Orchestrates query planning, parallel retrieval, and grounded synthesis."""

import logging
from concurrent.futures import ThreadPoolExecutor

from app.models import GuidelinesAnswerResponse, GuidelinesPipelineInput, PubMedSource
from app.retrieval import (
    rewrite_guideline_query,
    retrieve_guideline_candidates,
    select_relevant_guidelines,
)
from app.pubmed import build_pubmed_queries, search_pubmed_articles
from app.synthesis import synthesize_guideline_answer


logger = logging.getLogger(__name__)


def _search_pubmed_safely(keywords: list[str]) -> list[PubMedSource]:
    try:
        return search_pubmed_articles(keywords)
    except RuntimeError:
        logger.warning("PubMed retrieval failed; continuing with guideline evidence.")
        return []


def answer_guideline_question(
    pipeline_input: GuidelinesPipelineInput,
) -> GuidelinesAnswerResponse:
    plan = rewrite_guideline_query(
        question=pipeline_input.question,
        patient_context=pipeline_input.patient_context,
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        guideline_future = executor.submit(
            retrieve_guideline_candidates, plan.retrieval_query
        )
        pubmed_future = executor.submit(
            _search_pubmed_safely, plan.pubmed_keywords
        )
        candidates = guideline_future.result()
        pubmed_sources = pubmed_future.result()
    sources = select_relevant_guidelines(candidates)
    evidence = [*sources, *pubmed_sources]
    answer = synthesize_guideline_answer(
        question=pipeline_input.question,
        sources=evidence,
        patient_context=pipeline_input.patient_context,
    )
    pubmed_and_query, pubmed_or_query = build_pubmed_queries(plan.pubmed_keywords)
    return GuidelinesAnswerResponse(
        question=pipeline_input.question,
        retrieval_query=plan.retrieval_query,
        pubmed_keywords=plan.pubmed_keywords,
        pubmed_and_query=pubmed_and_query or None,
        pubmed_or_query=pubmed_or_query or None,
        answer=answer,
        sources=evidence,
        retrieval_count=len(evidence),
    )
