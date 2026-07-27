"""Plans guideline searches, retrieves Pinecone candidates, and ranks sources."""

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from app.clients.openrouter import (
    get_guidelines_embedding_provider,
    get_guidelines_model_provider,
)
from app.clients.pinecone import get_guidelines_index
from app.config import (
    GUIDELINES_EMBEDDING_DIMENSIONS,
    GUIDELINES_MIN_VECTOR_SCORE,
    GUIDELINES_QUERY_MODEL,
    GUIDELINES_RETRIEVAL_TOP_K,
    PINECONE_GUIDELINES_NAMESPACE,
    get_guidelines_settings,
)
from app.models import (
    GuidelineRetrievalPlan,
    GuidelineSource,
    GuidelinesSearchRequest,
)


RETRIEVAL_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "retrieval_query": {"type": "string", "minLength": 1},
        "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 8,
        },
    },
    "required": ["retrieval_query", "keywords"],
    "additionalProperties": False,
}


@lru_cache
def _query_rewriter_prompt() -> str:
    try:
        prompt = (
            files("app")
            .joinpath("prompts", "query_rewriter.md")
            .read_text(encoding="utf-8")
            .strip()
        )
    except (FileNotFoundError, OSError) as exc:
        raise RuntimeError("The guideline query rewriter prompt is unavailable.") from exc
    if not prompt:
        raise RuntimeError("The guideline query rewriter prompt is empty.")
    return prompt


def rewrite_guideline_query(
    question: str,
    patient_context: dict[str, Any] | None = None,
) -> GuidelineRetrievalPlan:
    """Rewrite safely, falling back to the original question on model failure."""
    settings = get_guidelines_settings()
    input_payload: dict[str, Any] = {"question": question}
    if patient_context:
        input_payload["trusted_patient_context"] = patient_context

    try:
        data = get_guidelines_model_provider().generate_json(
            model=GUIDELINES_QUERY_MODEL,
            instructions=_query_rewriter_prompt(),
            input_text=json.dumps(input_payload, default=str),
            schema_name="guideline_retrieval_plan",
            schema=RETRIEVAL_PLAN_SCHEMA,
            max_output_tokens=settings.guidelines_query_max_output_tokens,
            reasoning_effort="none",
        )
        return GuidelineRetrievalPlan.model_validate(data)
    except (RuntimeError, ValueError, TypeError):
        return GuidelineRetrievalPlan(retrieval_query=question, keywords=[])


def build_guideline_filters(payload: GuidelinesSearchRequest) -> dict[str, Any] | None:
    filters: dict[str, Any] = {}
    for field_name in ("country", "publisher", "document_type"):
        value = getattr(payload, field_name)
        if value:
            filters[field_name] = {"$eq": value}
    return filters or None


def _response_matches(response: Any) -> list[Any]:
    if isinstance(response, dict):
        return list(response.get("matches") or [])
    return list(getattr(response, "matches", None) or [])


def _match_value(match: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(match, dict):
        return match.get(field_name, default)
    return getattr(match, field_name, default)


def _metadata_value(metadata: Any, field_name: str, default: Any = None) -> Any:
    if isinstance(metadata, dict):
        return metadata.get(field_name, default)
    return getattr(metadata, field_name, default)


def retrieve_guideline_candidates(
    question: str,
    top_k: int | None = None,
    filters: dict[str, Any] | None = None,
) -> list[GuidelineSource]:
    settings = get_guidelines_settings()
    try:
        provider = get_guidelines_embedding_provider()
        query_vector = provider.embed_query(question)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Could not generate the guideline query embedding.") from exc

    if len(query_vector) != GUIDELINES_EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Guideline query embedding dimensions do not match the configured Pinecone index."
        )

    query_arguments: dict[str, Any] = {
        "vector": query_vector,
        "top_k": top_k or GUIDELINES_RETRIEVAL_TOP_K,
        "namespace": PINECONE_GUIDELINES_NAMESPACE,
        "include_metadata": True,
    }
    if filters:
        query_arguments["filter"] = filters

    try:
        response = get_guidelines_index().query(**query_arguments)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Pinecone guideline search failed.") from exc

    sources: list[GuidelineSource] = []
    for match in _response_matches(response):
        score = float(_match_value(match, "score", 0.0) or 0.0)
        metadata = _match_value(match, "metadata", {}) or {}
        document_id = str(_metadata_value(metadata, "document_id", "nstg-2022"))
        section = str(
            _metadata_value(
                metadata,
                "section",
                _metadata_value(metadata, "subheading_corrected", ""),
            )
            or ""
        )
        text = str(_metadata_value(metadata, "text", "") or "").strip()
        if not text:
            continue

        publication_year = _metadata_value(metadata, "publication_year")
        sources.append(
            GuidelineSource(
                chunk_id=str(_match_value(match, "id", "")),
                document_id=document_id,
                title=str(
                    _metadata_value(
                        metadata,
                        "title",
                        "Nigeria Standard Treatment Guidelines 2022",
                    )
                ),
                publisher=_metadata_value(metadata, "publisher"),
                country=_metadata_value(metadata, "country"),
                publication_year=(
                    int(publication_year) if publication_year is not None else None
                ),
                version=_metadata_value(metadata, "version"),
                condition=_metadata_value(metadata, "condition"),
                section=section or None,
                source_url=_metadata_value(metadata, "source_url"),
                text=text,
                score=score,
            )
        )
    return sources


def select_relevant_guidelines(
    candidates: list[GuidelineSource],
    min_score: float | None = None,
) -> list[GuidelineSource]:
    """Apply deterministic relevance filtering and keep the best duplicate."""
    settings = get_guidelines_settings()
    absolute_threshold = (
        GUIDELINES_MIN_VECTOR_SCORE if min_score is None else min_score
    )
    ranked_candidates = sorted(
        candidates,
        key=lambda source: source.score,
        reverse=True,
    )
    if not ranked_candidates:
        return []
    relative_threshold = (
        ranked_candidates[0].score * settings.guidelines_score_gap_ratio
    )
    threshold = max(absolute_threshold, relative_threshold)

    sources: list[GuidelineSource] = []
    seen: set[tuple[str, str, str]] = set()
    for candidate in ranked_candidates:
        if candidate.score < threshold:
            continue
        deduplication_key = (
            candidate.document_id,
            candidate.section or "",
            candidate.text,
        )
        if deduplication_key in seen:
            continue
        seen.add(deduplication_key)
        sources.append(candidate)
        if len(sources) >= settings.guidelines_max_context_chunks:
            break
    return sources


def search_guidelines(
    question: str,
    top_k: int | None = None,
    filters: dict[str, Any] | None = None,
) -> list[GuidelineSource]:
    """Compatibility wrapper for the existing search endpoint."""
    candidates = retrieve_guideline_candidates(
        question=question,
        top_k=top_k,
        filters=filters,
    )
    return select_relevant_guidelines(candidates)
