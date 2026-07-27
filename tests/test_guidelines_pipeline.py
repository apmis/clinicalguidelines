"""Tests orchestration from query rewriting through grounded synthesis."""

import unittest
from unittest.mock import patch

from app.models import (
    GuidelineRetrievalPlan,
    GuidelineSource,
    GuidelinesPipelineInput,
)
from app.pipeline import answer_guideline_question
from app.synthesis import (
    NO_RELEVANT_GUIDELINES_ANSWER,
    synthesize_guideline_answer,
)


def _source(chunk_id: str = "nstg-2022:MAL_006") -> GuidelineSource:
    return GuidelineSource(
        chunk_id=chunk_id,
        document_id="nstg-2022",
        title="Nigeria Standard Treatment Guidelines 2022",
        country="Nigeria",
        condition="MALARIA",
        section="TREATMENT",
        text="Treat uncomplicated malaria with the recommended first-line regimen.",
        score=0.82,
    )


class GuidelinesPipelineTests(unittest.TestCase):
    def test_uses_rewritten_query_for_retrieval_and_original_for_synthesis(self):
        pipeline_input = GuidelinesPipelineInput(
            question="What should I give?",
            patient_context={"diagnosis": "uncomplicated malaria"},
        )
        source = _source()

        with (
            patch(
                "app.pipeline.rewrite_guideline_query",
                return_value=GuidelineRetrievalPlan(
                    retrieval_query="uncomplicated malaria treatment",
                    keywords=["malaria", "treatment"],
                ),
            ) as rewrite,
            patch(
                "app.pipeline.retrieve_guideline_candidates",
                return_value=[source],
            ) as retrieve,
            patch(
                "app.pipeline.select_relevant_guidelines",
                return_value=[source],
            ) as select,
            patch(
                "app.pipeline.synthesize_guideline_answer",
                return_value="Use the guideline regimen [1].",
            ) as synthesize,
        ):
            response = answer_guideline_question(pipeline_input)

        rewrite.assert_called_once_with(
            question="What should I give?",
            patient_context={"diagnosis": "uncomplicated malaria"},
        )
        retrieve.assert_called_once_with("uncomplicated malaria treatment")
        select.assert_called_once_with([source])
        synthesize.assert_called_once_with(
            question="What should I give?",
            sources=[source],
            patient_context={"diagnosis": "uncomplicated malaria"},
        )
        self.assertEqual(response.answer, "Use the guideline regimen [1].")
        self.assertEqual(response.retrieval_count, 1)

    def test_empty_sources_abstain_without_calling_model(self):
        with patch(
            "app.synthesis.get_guidelines_model_provider"
        ) as provider:
            answer = synthesize_guideline_answer(
                question="An unrelated question",
                sources=[],
            )

        provider.assert_not_called()
        self.assertEqual(answer, NO_RELEVANT_GUIDELINES_ANSWER)


if __name__ == "__main__":
    unittest.main()
