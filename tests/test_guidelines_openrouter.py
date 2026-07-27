"""Tests the guideline service's OpenRouter transport and payloads."""

import json
import unittest
from unittest.mock import patch

from app.clients.openrouter import (
    OpenRouterGuidelinesEmbeddingProvider,
    OpenRouterGuidelinesModelProvider,
)


class FakeResponse:
    def __init__(self, body: dict):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")


class GuidelinesOpenRouterTests(unittest.TestCase):
    def test_embeddings_use_openrouter_with_openai_model_and_fixed_dimensions(self):
        provider = OpenRouterGuidelinesEmbeddingProvider(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            http_referer="http://localhost:8011",
            app_title="Healthstack Guidelines",
            model_name="openai/text-embedding-3-small",
            dimensions=1024,
            timeout=60,
        )

        with patch(
            "app.clients.openrouter.urllib.request.urlopen",
            return_value=FakeResponse(
                {
                    "data": [
                        {"index": 1, "embedding": [0.2, 0.3]},
                        {"index": 0, "embedding": [0.0, 0.1]},
                    ]
                }
            ),
        ) as urlopen:
            vectors = provider.embed_document_chunks(["first", "second"])

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/embeddings")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(payload["model"], "openai/text-embedding-3-small")
        self.assertEqual(payload["dimensions"], 1024)
        self.assertEqual(payload["provider"]["order"], ["openai"])
        self.assertFalse(payload["provider"]["allow_fallbacks"])
        self.assertEqual(vectors, [[0.0, 0.1], [0.2, 0.3]])

    def test_structured_generation_uses_openrouter_chat_completions(self):
        provider = OpenRouterGuidelinesModelProvider(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            http_referer="http://localhost:8011",
            app_title="Healthstack Guidelines",
            timeout=60,
        )
        result_body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "retrieval_query": "malaria treatment dose",
                                "keywords": ["malaria", "dose"],
                            }
                        )
                    }
                }
            ]
        }

        with patch(
            "app.clients.openrouter.urllib.request.urlopen",
            return_value=FakeResponse(result_body),
        ) as urlopen:
            result = provider.generate_json(
                model="openai/gpt-5.4-nano",
                instructions="Rewrite the question.",
                input_text="What is the malaria dose?",
                schema_name="guideline_retrieval_plan",
                schema={"type": "object"},
                max_output_tokens=300,
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(
            request.full_url,
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(payload["model"], "openai/gpt-5.4-nano")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(
            payload["response_format"]["json_schema"]["name"],
            "guideline_retrieval_plan",
        )
        self.assertTrue(payload["provider"]["require_parameters"])
        self.assertEqual(result["keywords"], ["malaria", "dose"])


if __name__ == "__main__":
    unittest.main()
