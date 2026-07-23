"""Creates the Pinecone guideline index or verifies that its vector settings are correct."""

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pinecone import Pinecone, ServerlessSpec

from app.guidelines.config import (
    GUIDELINES_EMBEDDING_DIMENSIONS,
    PINECONE_CLOUD,
    PINECONE_GUIDELINES_INDEX_NAME,
    PINECONE_REGION,
    get_guidelines_settings,
)


def _value(source: Any, field_name: str) -> Any:
    if isinstance(source, dict):
        return source.get(field_name)
    return getattr(source, field_name, None)


def main() -> None:
    settings = get_guidelines_settings()
    if not settings.pinecone_api_key:
        raise SystemExit("PINECONE_API_KEY is not configured.")

    client = Pinecone(api_key=settings.pinecone_api_key)
    index_name = PINECONE_GUIDELINES_INDEX_NAME
    created = False
    if not client.has_index(index_name):
        client.create_index(
            name=index_name,
            vector_type="dense",
            dimension=GUIDELINES_EMBEDDING_DIMENSIONS,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=PINECONE_CLOUD,
                region=PINECONE_REGION,
            ),
            deletion_protection="disabled",
            tags={"service": "healthstack", "content": "clinical-guidelines"},
        )
        created = True

    description = client.describe_index(index_name)
    dimension = int(_value(description, "dimension") or 0)
    metric = str(_value(description, "metric") or "")
    if dimension != GUIDELINES_EMBEDDING_DIMENSIONS:
        raise SystemExit(
            f"Index dimension is {dimension}; expected "
            f"{GUIDELINES_EMBEDDING_DIMENSIONS}. Create a new index."
        )
    if metric != "cosine":
        raise SystemExit(f"Index metric is {metric}; expected cosine.")

    print(
        json.dumps(
            {
                "created": created,
                "name": index_name,
                "host": _value(description, "host"),
                "dimension": dimension,
                "metric": metric,
                "status": _value(description, "status"),
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
