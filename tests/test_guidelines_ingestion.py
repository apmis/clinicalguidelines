"""Tests guideline chunk validation, stable IDs, batching, and Pinecone ingestion behavior."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import (
    GUIDELINES_EMBEDDING_DIMENSIONS,
    PINECONE_GUIDELINES_NAMESPACE,
)
from app.indexing.service import (
    GuidelineChunk,
    index_guideline_chunks,
    load_guideline_chunks,
)


class FakeEmbeddingProvider:
    def __init__(self, dimensions: int):
        self.dimensions = dimensions
        self.provider_name = "fake"
        self.model_name = "fake-embedding"
        self.calls: list[list[str]] = []

    def embed_document_chunks(self, chunks: list[str]) -> list[list[float]]:
        self.calls.append(chunks)
        return [[0.1] * self.dimensions for _ in chunks]


class FakeIndex:
    def __init__(self):
        self.upsert_calls = []
        self.delete_calls = []

    def upsert(self, **kwargs):
        self.upsert_calls.append(kwargs)

    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)


class GuidelinesIngestionTests(unittest.TestCase):
    def test_loads_prepared_chunk_with_stable_namespaced_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "HTN_001.json"
            path.write_text(
                json.dumps(
                    {
                        "chunk_id": "HTN_001",
                        "condition": "HYPERTENSION",
                        "subheading": "TREATMENT",
                        "subheading_corrected": "DRUG TREATMENT",
                        "source": "NSTG 2022",
                        "text": "A prepared guideline passage.",
                    }
                ),
                encoding="utf-8",
            )

            chunks = load_guideline_chunks(directory)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].vector_id, "nstg-2022:HTN_001")
        self.assertEqual(chunks[0].metadata["section"], "DRUG TREATMENT")
        self.assertEqual(chunks[0].metadata["country"], "Nigeria")

    def test_dry_run_does_not_create_provider_or_index(self):
        chunks = [
            GuidelineChunk(
                vector_id="nstg-2022:ONE",
                text="text",
                metadata={"document_id": "nstg-2022"},
            )
        ]

        with patch(
            "app.indexing.service.get_guidelines_index"
        ) as get_index:
            stats = index_guideline_chunks(chunks, dry_run=True)

        get_index.assert_not_called()
        self.assertEqual(stats["chunks_loaded"], 1)
        self.assertEqual(stats["chunks_upserted"], 0)

    def test_indexes_with_configured_namespace_and_dimensions(self):
        chunks = [
            GuidelineChunk(
                vector_id=f"nstg-2022:{index}",
                text=f"text {index}",
                metadata={"document_id": "nstg-2022"},
            )
            for index in range(3)
        ]
        provider = FakeEmbeddingProvider(GUIDELINES_EMBEDDING_DIMENSIONS)
        index = FakeIndex()

        with patch(
            "app.indexing.service.get_guidelines_index",
            return_value=index,
        ):
            stats = index_guideline_chunks(chunks, provider=provider)

        self.assertEqual(stats["chunks_upserted"], 3)
        self.assertEqual(
            index.upsert_calls[0]["namespace"],
            PINECONE_GUIDELINES_NAMESPACE,
        )
        self.assertEqual(
            len(index.upsert_calls[0]["vectors"][0]["values"]),
            GUIDELINES_EMBEDDING_DIMENSIONS,
        )

    def test_replace_only_deletes_matching_document_in_namespace(self):
        chunks = [
            GuidelineChunk(
                vector_id="nstg-2022:ONE",
                text="text",
                metadata={"document_id": "nstg-2022"},
            )
        ]
        provider = FakeEmbeddingProvider(GUIDELINES_EMBEDDING_DIMENSIONS)
        index = FakeIndex()

        with patch(
            "app.indexing.service.get_guidelines_index",
            return_value=index,
        ):
            index_guideline_chunks(
                chunks,
                replace_document=True,
                provider=provider,
            )

        self.assertEqual(
            index.delete_calls,
            [
                {
                    "filter": {"document_id": {"$eq": "nstg-2022"}},
                    "namespace": PINECONE_GUIDELINES_NAMESPACE,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
