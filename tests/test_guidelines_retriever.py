"""Tests guideline metadata filters, Pinecone querying, scoring, and error handling."""

import unittest
from unittest.mock import patch

from app.guidelines.config import (
    GUIDELINES_EMBEDDING_DIMENSIONS,
    PINECONE_GUIDELINES_NAMESPACE,
)
from app.guidelines.models import GuidelineSource, GuidelinesSearchRequest
from app.guidelines.retrieval import (
    build_guideline_filters,
    select_relevant_guidelines,
    search_guidelines,
)


class FakeProvider:
    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def embed_query(self, text: str) -> list[float]:
        return [0.25] * self.dimensions


class FakeIndex:
    def __init__(self, matches):
        self.matches = matches
        self.query_arguments = None

    def query(self, **kwargs):
        self.query_arguments = kwargs
        return {"matches": self.matches}


class FailingIndex:
    def query(self, **kwargs):
        raise ValueError("network failed")


class GuidelinesRetrieverTests(unittest.TestCase):
    def test_builds_only_requested_metadata_filters(self):
        request = GuidelinesSearchRequest(
            question="malaria treatment",
            country="Nigeria",
            document_type="treatment_guideline",
        )

        filters = build_guideline_filters(request)

        self.assertEqual(
            filters,
            {
                "country": {"$eq": "Nigeria"},
                "document_type": {"$eq": "treatment_guideline"},
            },
        )

    def test_selects_highest_scoring_unique_relevant_sources(self):
        common = {
            "document_id": "nstg-2022",
            "title": "Nigeria Standard Treatment Guidelines 2022",
            "section": "TREATMENT",
        }
        candidates = [
            GuidelineSource(
                chunk_id="duplicate-low",
                text="Use the treatment passage.",
                score=0.61,
                **common,
            ),
            GuidelineSource(
                chunk_id="different",
                text="Monitor the patient.",
                score=0.74,
                **common,
            ),
            GuidelineSource(
                chunk_id="duplicate-high",
                text="Use the treatment passage.",
                score=0.82,
                **common,
            ),
            GuidelineSource(
                chunk_id="below-threshold",
                text="Weak match.",
                score=0.10,
                **common,
            ),
        ]

        sources = select_relevant_guidelines(candidates, min_score=0.5)

        self.assertEqual(
            [source.chunk_id for source in sources],
            ["duplicate-high", "different"],
        )

    def test_drops_candidates_far_below_the_best_similarity_score(self):
        common = {
            "document_id": "nstg-2022",
            "title": "Nigeria Standard Treatment Guidelines 2022",
            "section": "TREATMENT",
        }
        candidates = [
            GuidelineSource(
                chunk_id="best",
                text="Best passage.",
                score=0.80,
                **common,
            ),
            GuidelineSource(
                chunk_id="near-best",
                text="Related passage.",
                score=0.66,
                **common,
            ),
            GuidelineSource(
                chunk_id="tail",
                text="Weak tail passage.",
                score=0.60,
                **common,
            ),
        ]

        sources = select_relevant_guidelines(candidates, min_score=0.2)

        self.assertEqual(
            [source.chunk_id for source in sources],
            ["best", "near-best"],
        )

    def test_queries_namespace_and_removes_low_score_and_duplicates(self):
        metadata = {
            "document_id": "nstg-2022",
            "title": "Nigeria Standard Treatment Guidelines 2022",
            "country": "Nigeria",
            "condition": "MALARIA",
            "section": "TREATMENT",
            "text": "Use the retrieved treatment passage.",
        }
        index = FakeIndex(
            [
                {"id": "one", "score": 0.91, "metadata": metadata},
                {"id": "duplicate", "score": 0.90, "metadata": metadata},
                {
                    "id": "low",
                    "score": 0.01,
                    "metadata": {**metadata, "text": "Low score passage."},
                },
            ]
        )

        with (
            patch(
                "app.guidelines.retrieval.get_guidelines_embedding_provider",
                return_value=FakeProvider(GUIDELINES_EMBEDDING_DIMENSIONS),
            ),
            patch(
                "app.guidelines.retrieval.get_guidelines_index",
                return_value=index,
            ),
        ):
            sources = search_guidelines(
                "malaria treatment",
                top_k=5,
                filters={"country": {"$eq": "Nigeria"}},
            )

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].chunk_id, "one")
        self.assertEqual(
            index.query_arguments["namespace"],
            PINECONE_GUIDELINES_NAMESPACE,
        )
        self.assertEqual(index.query_arguments["top_k"], 5)
        self.assertEqual(
            index.query_arguments["filter"],
            {"country": {"$eq": "Nigeria"}},
        )

    def test_converts_pinecone_failure_to_runtime_error(self):
        with (
            patch(
                "app.guidelines.retrieval.get_guidelines_embedding_provider",
                return_value=FakeProvider(GUIDELINES_EMBEDDING_DIMENSIONS),
            ),
            patch(
                "app.guidelines.retrieval.get_guidelines_index",
                return_value=FailingIndex(),
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Pinecone guideline search failed",
            ):
                search_guidelines("malaria treatment")


if __name__ == "__main__":
    unittest.main()
