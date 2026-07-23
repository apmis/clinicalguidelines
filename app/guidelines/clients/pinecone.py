"""Creates and caches the Pinecone index connection used by the guideline service."""

from functools import lru_cache
from typing import Any

from pinecone import Pinecone

from app.guidelines.config import (
    PINECONE_GUIDELINES_INDEX_HOST,
    PINECONE_GUIDELINES_INDEX_NAME,
    get_guidelines_settings,
)


@lru_cache
def get_guidelines_index() -> Any:
    settings = get_guidelines_settings()
    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is not configured.")

    client = Pinecone(api_key=settings.pinecone_api_key)
    if PINECONE_GUIDELINES_INDEX_HOST:
        return client.Index(host=PINECONE_GUIDELINES_INDEX_HOST)
    return client.Index(PINECONE_GUIDELINES_INDEX_NAME)


def clear_guidelines_index_cache() -> None:
    get_guidelines_index.cache_clear()
