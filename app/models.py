"""Shared validated models for guideline retrieval and answer generation."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_required_text(value: str) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError("Value must not be blank.")
    return cleaned


class GuidelinesSearchRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    country: str | None = None
    publisher: str | None = None
    document_type: str | None = None

    @field_validator(
        "question",
        "country",
        "publisher",
        "document_type",
        mode="before",
    )
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class GuidelinesAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, value: str) -> str:
        return _clean_required_text(value)


class GuidelinesPipelineInput(BaseModel):
    """Internal input that trusted backend context can extend later."""

    question: str = Field(min_length=1)
    patient_context: dict[str, Any] | None = None

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, value: str) -> str:
        return _clean_required_text(value)


class GuidelineRetrievalPlan(BaseModel):
    retrieval_query: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)

    @field_validator("retrieval_query", mode="before")
    @classmethod
    def clean_retrieval_query(cls, value: str) -> str:
        return _clean_required_text(value)

    @field_validator("keywords", mode="before")
    @classmethod
    def clean_keywords(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        cleaned: list[str] = []
        for keyword in value:
            text = str(keyword).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned[:8]


class GuidelineSource(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    publisher: str | None = None
    country: str | None = None
    publication_year: int | None = None
    version: str | None = None
    condition: str | None = None
    section: str | None = None
    source_url: str | None = None
    text: str
    score: float


class GuidelinesSearchResponse(BaseModel):
    question: str
    sources: list[GuidelineSource] = Field(default_factory=list)
    retrieval_count: int


class GuidelinesAnswerResponse(BaseModel):
    question: str
    retrieval_query: str
    answer: str
    sources: list[GuidelineSource] = Field(default_factory=list)
    retrieval_count: int
