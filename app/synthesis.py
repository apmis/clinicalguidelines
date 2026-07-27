"""Generates a clinical answer grounded only in selected evidence passages."""

import json
import re
from functools import lru_cache
from importlib.resources import files
from typing import Any

from app.clients.openrouter import get_guidelines_model_provider
from app.config import GUIDELINES_ANSWER_MODEL, get_guidelines_settings
from app.models import ClinicalEvidenceSource, GuidelineSource, PubMedSource


NO_RELEVANT_GUIDELINES_ANSWER = (
    "I could not find sufficiently relevant clinical evidence to answer this "
    "question safely."
)


@lru_cache
def _synthesis_prompt() -> str:
    try:
        prompt = (
            files("app")
            .joinpath("prompts", "synthesis.md")
            .read_text(encoding="utf-8")
            .strip()
        )
    except (FileNotFoundError, OSError) as exc:
        raise RuntimeError("The guideline synthesis prompt is unavailable.") from exc
    if not prompt:
        raise RuntimeError("The guideline synthesis prompt is empty.")
    return prompt


def _source_heading(source: ClinicalEvidenceSource) -> str:
    if isinstance(source, GuidelineSource):
        return " | ".join(
            value
            for value in (
                "Clinical guideline",
                source.title,
                source.condition,
                source.section,
            )
            if value
        )
    return " | ".join(
        value
        for value in (
            f"PubMed PMID {source.pmid}",
            source.title,
            source.journal,
            source.publication_date,
        )
        if value
    )


def _source_text(source: ClinicalEvidenceSource) -> str:
    if isinstance(source, PubMedSource):
        return source.abstract.strip()
    return source.text.strip()


def _source_url(source: ClinicalEvidenceSource) -> str | None:
    url = source.source_url
    if isinstance(url, str) and url.strip():
        return url.strip()
    return None


def _source_context(
    sources: list[ClinicalEvidenceSource], max_characters: int
) -> str:
    blocks: list[str] = []
    used = 0
    for number, source in enumerate(sources, start=1):
        if blocks:
            used += 2
        remaining = max_characters - used
        remaining_sources = len(sources) - number + 1
        if remaining <= 0:
            break
        allocation = max(1, remaining // remaining_sources)
        url = _source_url(source)
        url_line = f"\nURL: {url}" if url else ""
        block = f"[{number}] {_source_heading(source)}{url_line}\n{_source_text(source)}"
        if len(block) > allocation:
            block = (
                "…"
                if allocation == 1
                else block[: allocation - 1].rstrip() + "…"
            )
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def _link_inline_citations(answer: str, sources: list[ClinicalEvidenceSource]) -> str:
    citation_urls = {
        str(index): url
        for index, source in enumerate(sources, start=1)
        if (url := _source_url(source))
    }

    def replace(match: re.Match[str]) -> str:
        citation_number = match.group("number")
        url = citation_urls.get(citation_number)
        if not url:
            return f"[{citation_number}]"
        return f"[{citation_number}]({url})"

    return re.sub(r"\[(?P<number>\d+)\](?:\([^)]*\))?", replace, answer)


def synthesize_guideline_answer(
    question: str,
    sources: list[ClinicalEvidenceSource],
    patient_context: dict[str, Any] | None = None,
) -> str:
    if not sources:
        return NO_RELEVANT_GUIDELINES_ANSWER

    settings = get_guidelines_settings()
    input_payload: dict[str, Any] = {
        "question": question,
        "clinical_evidence_passages": _source_context(
            sources,
            settings.guidelines_max_context_characters,
        ),
    }
    if patient_context:
        input_payload["trusted_patient_context"] = patient_context

    answer = get_guidelines_model_provider().generate_text(
        model=GUIDELINES_ANSWER_MODEL,
        instructions=_synthesis_prompt(),
        input_text=json.dumps(input_payload, default=str),
        max_output_tokens=settings.guidelines_answer_max_output_tokens,
        reasoning_effort=settings.guidelines_answer_reasoning_effort,
    )
    return _link_inline_citations(answer, sources)
