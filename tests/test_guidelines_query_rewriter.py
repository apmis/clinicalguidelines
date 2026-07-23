"""Tests structured retrieval-query planning and its safe fallback."""

import unittest
from unittest.mock import patch

from app.guidelines.retrieval import rewrite_guideline_query


class FakeModelProvider:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.arguments = None

    def generate_json(self, **kwargs):
        self.arguments = kwargs
        if self.error:
            raise self.error
        return self.result


class GuidelineQueryRewriterTests(unittest.TestCase):
    def test_returns_structured_retrieval_plan(self):
        provider = FakeModelProvider(
            {
                "retrieval_query": (
                    "Uncomplicated malaria in adults: diagnosis, first-line "
                    "treatment, dose, monitoring, and escalation."
                ),
                "keywords": ["malaria", "adult", "treatment", "monitoring"],
            }
        )

        with patch(
            "app.guidelines.retrieval.get_guidelines_model_provider",
            return_value=provider,
        ):
            plan = rewrite_guideline_query("How do I treat malaria?")

        self.assertIn("Uncomplicated malaria", plan.retrieval_query)
        self.assertEqual(plan.keywords[0], "malaria")
        self.assertEqual(
            provider.arguments["schema_name"],
            "guideline_retrieval_plan",
        )

    def test_falls_back_to_original_question_when_planner_fails(self):
        provider = FakeModelProvider(error=RuntimeError("model unavailable"))

        with patch(
            "app.guidelines.retrieval.get_guidelines_model_provider",
            return_value=provider,
        ):
            plan = rewrite_guideline_query("Gentamicin dose")

        self.assertEqual(plan.retrieval_query, "Gentamicin dose")
        self.assertEqual(plan.keywords, [])


if __name__ == "__main__":
    unittest.main()
