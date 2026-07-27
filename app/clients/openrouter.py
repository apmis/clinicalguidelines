"""OpenRouter embedding and chat-completion clients for guideline RAG."""

import json
import urllib.error
import urllib.request
from typing import Any, Protocol

from app.config import (
    GUIDELINES_EMBEDDING_DIMENSIONS,
    GUIDELINES_EMBEDDING_MODEL,
    GUIDELINES_REQUEST_TIMEOUT_SECS,
    get_guidelines_settings,
)


class EmbeddingProvider(Protocol):
    dimensions: int
    model_name: str

    def embed_document_chunks(self, chunks: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class GuidelinesModelProvider(Protocol):
    def generate_text(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        max_output_tokens: int,
        reasoning_effort: str | None = None,
    ) -> str: ...

    def generate_json(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]: ...


class _OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        http_referer: str,
        app_title: str,
        timeout: int,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.http_referer = http_referer
        self.app_title = app_title
        self.timeout = timeout

    def _post_json(
        self,
        path: str,
        payload: dict[str, Any],
        operation: str,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.http_referer,
                "X-Title": self.app_title,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"OpenRouter guideline {operation} failed: {detail}"
            ) from exc
        except (TimeoutError, urllib.error.URLError) as exc:
            raise RuntimeError(
                f"OpenRouter guideline {operation} request failed."
            ) from exc


class OpenRouterGuidelinesEmbeddingProvider(_OpenRouterClient):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        http_referer: str,
        app_title: str,
        model_name: str,
        dimensions: int,
        timeout: int,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            http_referer=http_referer,
            app_title=app_title,
            timeout=timeout,
        )
        self.model_name = model_name
        self.dimensions = dimensions

    def _embed(self, texts: list[str]) -> list[list[float]]:
        body = self._post_json(
            "/embeddings",
            {
                "input": texts,
                "model": self.model_name,
                "dimensions": self.dimensions,
                "provider": {
                    "order": ["openai"],
                    "allow_fallbacks": False,
                },
            },
            "embedding",
        )
        rows = sorted(body.get("data") or [], key=lambda item: item.get("index", 0))
        if len(rows) != len(texts):
            raise RuntimeError(
                "OpenRouter guideline embedding count did not match the input."
            )
        return [row["embedding"] for row in rows]

    def embed_document_chunks(self, chunks: list[str]) -> list[list[float]]:
        return self._embed(chunks)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


def _chat_content(body: dict[str, Any]) -> str:
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    if message.get("refusal"):
        raise RuntimeError("The guideline model refused the request.")

    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        text = "\n".join(
            str(part.get("text") or "").strip()
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ).strip()
    else:
        text = ""

    if not text:
        raise RuntimeError("The guideline model returned no text.")
    return text


class OpenRouterGuidelinesModelProvider(_OpenRouterClient):
    def _base_payload(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        max_output_tokens: int,
        reasoning_effort: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "max_completion_tokens": max_output_tokens,
        }
        if reasoning_effort:
            payload["reasoning"] = {
                "effort": reasoning_effort,
                "exclude": True,
            }
        return payload

    def generate_text(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        max_output_tokens: int,
        reasoning_effort: str | None = None,
    ) -> str:
        payload = self._base_payload(
            model=model,
            instructions=instructions,
            input_text=input_text,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
        )
        return _chat_content(
            self._post_json("/chat/completions", payload, "generation")
        )

    def generate_json(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int,
        reasoning_effort: str | None = None,
    ) -> dict[str, Any]:
        payload = self._base_payload(
            model=model,
            instructions=instructions,
            input_text=input_text,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
        )
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        }
        payload["provider"] = {"require_parameters": True}
        try:
            content = _chat_content(
                self._post_json("/chat/completions", payload, "generation")
            )
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("The guideline model returned invalid JSON.") from exc


def _client_settings() -> dict[str, Any]:
    settings = get_guidelines_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for guideline RAG.")
    return {
        "api_key": settings.openrouter_api_key,
        "base_url": settings.openrouter_api_base,
        "http_referer": settings.openrouter_http_referer,
        "app_title": settings.openrouter_app_title,
        "timeout": GUIDELINES_REQUEST_TIMEOUT_SECS,
    }


def get_guidelines_embedding_provider() -> EmbeddingProvider:
    return OpenRouterGuidelinesEmbeddingProvider(
        **_client_settings(),
        model_name=GUIDELINES_EMBEDDING_MODEL,
        dimensions=GUIDELINES_EMBEDDING_DIMENSIONS,
    )


def get_guidelines_model_provider() -> GuidelinesModelProvider:
    return OpenRouterGuidelinesModelProvider(**_client_settings())
