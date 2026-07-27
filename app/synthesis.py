"""Generates a clinical answer grounded only in selected guideline passages."""

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from app.clients.openrouter import get_guidelines_model_provider
from app.config import GUIDELINES_ANSWER_MODEL, get_guidelines_settings
from app.models import GuidelineSource


NO_RELEVANT_GUIDELINES_ANSWER = (
    "I could not find a sufficiently relevant passage in the available clinical "
    "guidelines to answer this question safely."
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


def _source_context(sources: list[GuidelineSource], max_characters: int) -> str:
    blocks: list[str] = []
    used = 0
    for number, source in enumerate(sources, start=1):
        heading = " | ".join(
            value
            for value in (
                source.title,
                source.condition,
                source.section,
            )
            if value
        )
        block = f"[{number}] {heading}\n{source.text.strip()}"
        if blocks and used + len(block) > max_characters:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks)


def synthesize_guideline_answer(
    question: str,
    sources: list[GuidelineSource],
    patient_context: dict[str, Any] | None = None,
) -> str:
    if not sources:
        return NO_RELEVANT_GUIDELINES_ANSWER

    settings = get_guidelines_settings()
    input_payload: dict[str, Any] = {
        "question": question,
        "guideline_passages": _source_context(
            sources,
            settings.guidelines_max_context_characters,
        ),
    }
    if patient_context:
        input_payload["trusted_patient_context"] = patient_context

    return get_guidelines_model_provider().generate_text(
        model=GUIDELINES_ANSWER_MODEL,
        instructions=_synthesis_prompt(),
        input_text=json.dumps(input_payload, default=str),
        max_output_tokens=settings.guidelines_answer_max_output_tokens,
        reasoning_effort=settings.guidelines_answer_reasoning_effort,
    )
