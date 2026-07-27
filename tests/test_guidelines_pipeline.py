"""Tests orchestration from query rewriting through grounded synthesis."""

import json
import unittest
from unittest.mock import patch

from app.models import (
    GuidelineRetrievalPlan,
    GuidelineSource,
    GuidelinesPipelineInput,
    PubMedSource,
)
from app.pipeline import answer_guideline_question
from app.synthesis import (
    NO_RELEVANT_GUIDELINES_ANSWER,
    _link_inline_citations,
    _source_context,
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


def _pubmed_source() -> PubMedSource:
    return PubMedSource(
        pmid="12345678",
        title="Treatment of uncomplicated malaria",
        abstract="The regimen was effective in adults with uncomplicated malaria.",
        journal="Clinical Malaria Research",
        publication_date="2025",
        source_url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        relevance_score=0.05,
        matched_searches=["AND", "OR"],
    )


class GuidelinesPipelineTests(unittest.TestCase):
    def test_uses_rewritten_query_for_retrieval_and_original_for_synthesis(self):
        pipeline_input = GuidelinesPipelineInput(
            question="What should I give?",
            patient_context={"diagnosis": "uncomplicated malaria"},
        )
        source = _source()
        pubmed_source = _pubmed_source()

        with (
            patch(
                "app.pipeline.rewrite_guideline_query",
                return_value=GuidelineRetrievalPlan(
                    retrieval_query="uncomplicated malaria treatment",
                    pubmed_keywords=["malaria", "treatment"],
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
                "app.pipeline.search_pubmed_articles",
                return_value=[pubmed_source],
            ) as search_pubmed,
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
        search_pubmed.assert_called_once_with(["malaria", "treatment"])
        synthesize.assert_called_once_with(
            question="What should I give?",
            sources=[source, pubmed_source],
            patient_context={"diagnosis": "uncomplicated malaria"},
        )
        self.assertEqual(response.answer, "Use the guideline regimen [1].")
        self.assertEqual(response.retrieval_count, 2)
        self.assertEqual(response.pubmed_keywords, ["malaria", "treatment"])
        self.assertIn(" AND ", response.pubmed_and_query)
        self.assertIn(" OR ", response.pubmed_or_query)

    def test_pubmed_failure_does_not_discard_guideline_results(self):
        source = _source()
        with (
            patch(
                "app.pipeline.rewrite_guideline_query",
                return_value=GuidelineRetrievalPlan(
                    retrieval_query="malaria treatment",
                    pubmed_keywords=["malaria", "treatment"],
                ),
            ),
            patch(
                "app.pipeline.retrieve_guideline_candidates",
                return_value=[source],
            ),
            patch(
                "app.pipeline.select_relevant_guidelines",
                return_value=[source],
            ),
            patch(
                "app.pipeline.search_pubmed_articles",
                side_effect=RuntimeError("NCBI unavailable"),
            ),
            patch(
                "app.pipeline.synthesize_guideline_answer",
                return_value="Guideline-only answer [1].",
            ) as synthesize,
        ):
            response = answer_guideline_question(
                GuidelinesPipelineInput(question="How is malaria treated?")
            )

        self.assertEqual(response.sources, [source])
        synthesize.assert_called_once_with(
            question="How is malaria treated?",
            sources=[source],
            patient_context=None,
        )

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

    def test_pubmed_abstract_is_numbered_and_identified_in_synthesis_context(self):
        class FakeAnswerProvider:
            def __init__(self):
                self.arguments = None

            def generate_text(self, **kwargs):
                self.arguments = kwargs
                return "Research evidence suggests benefit [1]."

        provider = FakeAnswerProvider()
        source = _pubmed_source()
        with patch(
            "app.synthesis.get_guidelines_model_provider",
            return_value=provider,
        ):
            answer = synthesize_guideline_answer(
                question="What does recent research suggest?",
                sources=[source],
            )

        payload = json.loads(provider.arguments["input_text"])
        context = payload["clinical_evidence_passages"]
        self.assertEqual(
            answer,
            (
                "Research evidence suggests benefit "
                "[1](https://pubmed.ncbi.nlm.nih.gov/12345678/)."
            ),
        )
        self.assertIn("[1] PubMed PMID 12345678", context)
        self.assertIn("URL: https://pubmed.ncbi.nlm.nih.gov/12345678/", context)
        self.assertIn(source.abstract, context)

    def test_links_inline_citations_when_source_url_is_available(self):
        answer = _link_inline_citations(
            "Use the guideline regimen [1]. PubMed evidence adds context [2].",
            [_source(), _pubmed_source()],
        )

        self.assertEqual(
            answer,
            (
                "Use the guideline regimen [1]. PubMed evidence adds context "
                "[2](https://pubmed.ncbi.nlm.nih.gov/12345678/)."
            ),
        )

    def test_normalizes_already_linked_citations_to_source_url(self):
        answer = _link_inline_citations(
            "PubMed evidence adds context [1](https://example.com/existing).",
            [_pubmed_source()],
        )

        self.assertEqual(
            answer,
            (
                "PubMed evidence adds context "
                "[1](https://pubmed.ncbi.nlm.nih.gov/12345678/)."
            ),
        )

    def test_corrects_or_strips_model_generated_citation_links(self):
        answer = _link_inline_citations(
            (
                "Guideline evidence [1](#). PubMed evidence "
                "[2](https://example.com/wrong)."
            ),
            [_source(), _pubmed_source()],
        )

        self.assertEqual(
            answer,
            (
                "Guideline evidence [1]. PubMed evidence "
                "[2](https://pubmed.ncbi.nlm.nih.gov/12345678/)."
            ),
        )

    def test_context_budget_reserves_space_for_pubmed_after_large_guideline(self):
        guideline = _source().model_copy(
            update={"text": "Guideline evidence. " * 100}
        )
        context = _source_context([guideline, _pubmed_source()], 400)

        self.assertLessEqual(len(context), 400)
        self.assertIn("[1] Clinical guideline", context)
        self.assertIn("[2] PubMed PMID 12345678", context)


if __name__ == "__main__":
    unittest.main()
