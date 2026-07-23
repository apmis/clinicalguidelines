"""Loads configuration for the standalone guideline search and indexing service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


PINECONE_GUIDELINES_INDEX_NAME = "healthstack-guidelines"
PINECONE_GUIDELINES_INDEX_HOST = (
    "healthstack-guidelines-gddfi1b.svc.aped-4627-b74a.pinecone.io"
)
PINECONE_GUIDELINES_NAMESPACE = "clinical-guidelines-v1"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

GUIDELINES_EMBEDDING_MODEL = "openai/text-embedding-3-small"
GUIDELINES_EMBEDDING_DIMENSIONS = 1024
GUIDELINES_EMBED_BATCH_SIZE = 50
GUIDELINES_UPSERT_BATCH_SIZE = 100
GUIDELINES_RETRIEVAL_TOP_K = 8
GUIDELINES_MIN_VECTOR_SCORE = 0.2
GUIDELINES_REQUEST_TIMEOUT_SECS = 60
GUIDELINES_DATA_PATH = "data/guidelines/nstg-2022/chunks"
GUIDELINES_QUERY_MODEL = "openai/gpt-5.4-nano"
GUIDELINES_ANSWER_MODEL = "openai/gpt-5.4-nano"


class GuidelinesSettings(BaseSettings):
    pinecone_api_key: str | None = None

    openrouter_api_key: str | None = None
    openrouter_api_base: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str = "http://localhost:8011"
    openrouter_app_title: str = "Healthstack Guidelines"
    guidelines_score_gap_ratio: float = 0.8
    guidelines_max_context_chunks: int = 4
    guidelines_query_max_output_tokens: int = 300
    guidelines_answer_max_output_tokens: int = 1600
    guidelines_answer_reasoning_effort: str = "low"
    guidelines_max_context_characters: int = 24000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_guidelines_settings() -> GuidelinesSettings:
    return GuidelinesSettings()
