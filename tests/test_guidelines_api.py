"""Tests the standalone guideline endpoint response and service-unavailable behavior."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.guidelines.api import (
    answer_copilot_guidelines,
    search_copilot_guidelines,
)
from app.guidelines.models import (
    GuidelinesAnswerRequest,
    GuidelinesAnswerResponse,
    GuidelineSource,
    GuidelinesSearchRequest,
)


class GuidelinesApiTests(unittest.TestCase):
    def setUp(self):
        self.payload = GuidelinesSearchRequest(
            question="How is uncomplicated malaria treated?",
            top_k=3,
            country="Nigeria",
        )

    def test_returns_retrieved_sources_without_mongodb_context(self):
        source = GuidelineSource(
            chunk_id="nstg-2022:MAL_001",
            document_id="nstg-2022",
            title="Nigeria Standard Treatment Guidelines 2022",
            country="Nigeria",
            condition="MALARIA",
            section="TREATMENT",
            text="Retrieved treatment passage.",
            score=0.88,
        )
        with (
            patch(
                "app.guidelines.api.search_guidelines",
                return_value=[source],
            ) as search,
        ):
            response = search_copilot_guidelines(self.payload)

        search.assert_called_once_with(
            question=self.payload.question,
            top_k=3,
            filters={"country": {"$eq": "Nigeria"}},
        )
        self.assertEqual(response.retrieval_count, 1)

    def test_maps_provider_failure_to_service_unavailable(self):
        with (
            patch(
                "app.guidelines.api.search_guidelines",
                side_effect=RuntimeError("Pinecone failed"),
            ),
        ):
            with self.assertRaises(HTTPException) as caught:
                search_copilot_guidelines(self.payload)

        self.assertEqual(caught.exception.status_code, 503)

    def test_answer_endpoint_accepts_only_question_and_returns_grounded_result(self):
        source = GuidelineSource(
            chunk_id="nstg-2022:MAL_001",
            document_id="nstg-2022",
            title="Nigeria Standard Treatment Guidelines 2022",
            text="Retrieved treatment passage.",
            score=0.88,
        )
        expected = GuidelinesAnswerResponse(
            question="How is malaria treated?",
            retrieval_query="uncomplicated malaria treatment",
            answer="Use the recommended regimen [1].",
            sources=[source],
            retrieval_count=1,
        )

        with patch(
            "app.guidelines.api.answer_guideline_question",
            return_value=expected,
        ) as answer:
            response = answer_copilot_guidelines(
                GuidelinesAnswerRequest(question="How is malaria treated?")
            )

        self.assertEqual(response, expected)
        pipeline_input = answer.call_args.args[0]
        self.assertEqual(pipeline_input.question, "How is malaria treated?")
        self.assertIsNone(pipeline_input.patient_context)

    def test_answer_request_rejects_client_supplied_patient_context(self):
        with self.assertRaises(ValidationError):
            GuidelinesAnswerRequest(
                question="How is malaria treated?",
                patient_context={"age": 42},
            )

    def test_answer_endpoint_maps_pipeline_failure_to_service_unavailable(self):
        with patch(
            "app.guidelines.api.answer_guideline_question",
            side_effect=RuntimeError("model failed"),
        ):
            with self.assertRaises(HTTPException) as caught:
                answer_copilot_guidelines(
                    GuidelinesAnswerRequest(question="malaria treatment")
                )

        self.assertEqual(caught.exception.status_code, 503)

if __name__ == "__main__":
    unittest.main()
