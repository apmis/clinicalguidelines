"""Interactive Streamlit client for testing the Clinical Guidelines API."""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = os.getenv(
    "GUIDELINES_API_URL",
    "http://127.0.0.1:8011",
)
REQUEST_TIMEOUT_SECONDS = 120


def normalize_api_url(value: str) -> str:
    """Return a base API URL without a trailing slash."""
    normalized = value.strip().rstrip("/")
    if normalized and "://" not in normalized:
        normalized = f"http://{normalized}"
    return normalized


def request_api(
    api_url: str,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Call the API and return a decoded JSON object."""
    response = requests.request(
        method,
        f"{normalize_api_url(api_url)}{path}",
        json=payload,
        timeout=timeout,
    )

    try:
        body = response.json()
    except ValueError:
        body = {}

    if not response.ok:
        detail = body.get("detail") if isinstance(body, dict) else None
        message = detail or response.text or f"HTTP {response.status_code}"
        raise RuntimeError(f"{response.status_code}: {message}")

    if not isinstance(body, dict):
        raise RuntimeError("The API returned an unexpected response.")
    return body


def render_source(source: dict[str, Any], index: int) -> None:
    """Render one guideline or PubMed source."""
    source_type = source.get("source_type", "guideline")
    title = source.get("title") or "Untitled source"
    label = "PubMed" if source_type == "pubmed" else "Guideline"

    with st.expander(f"{index}. {title} · {label}"):
        if source_type == "pubmed":
            metadata = [
                source.get("journal"),
                source.get("publication_date"),
                f"PMID {source['pmid']}" if source.get("pmid") else None,
            ]
            st.caption(" · ".join(str(item) for item in metadata if item))
            st.write(source.get("abstract") or "No abstract was returned.")

            authors = source.get("authors") or []
            if authors:
                st.caption(f"Authors: {', '.join(authors)}")
        else:
            metadata = [
                source.get("publisher"),
                source.get("country"),
                str(source["publication_year"])
                if source.get("publication_year")
                else None,
                source.get("section"),
            ]
            st.caption(" · ".join(str(item) for item in metadata if item))
            st.write(source.get("text") or "No passage was returned.")

            score = source.get("score")
            if isinstance(score, (int, float)):
                st.caption(f"Vector score: {score:.3f}")

        source_url = source.get("source_url")
        if source_url:
            st.link_button("Open source", source_url)


def render_answer(result: dict[str, Any]) -> None:
    """Render an answer endpoint response."""
    st.subheader("Grounded answer")
    st.markdown(result.get("answer") or "_No answer was returned._")

    sources = result.get("sources") or []
    guideline_count = sum(
        source.get("source_type", "guideline") == "guideline"
        for source in sources
    )
    pubmed_count = sum(
        source.get("source_type") == "pubmed" for source in sources
    )

    metric_columns = st.columns(3)
    metric_columns[0].metric(
        "Sources",
        result.get("retrieval_count", len(sources)),
    )
    metric_columns[1].metric("Guidelines", guideline_count)
    metric_columns[2].metric("PubMed", pubmed_count)

    with st.expander("Retrieval details"):
        st.markdown("**Rewritten query**")
        st.code(result.get("retrieval_query") or "Not returned")

        keywords = result.get("pubmed_keywords") or []
        if keywords:
            st.markdown("**PubMed keywords**")
            st.write(", ".join(keywords))

        query_columns = st.columns(2)
        with query_columns[0]:
            st.markdown("**Strict AND query**")
            st.code(result.get("pubmed_and_query") or "Not used")
        with query_columns[1]:
            st.markdown("**Broader OR query**")
            st.code(result.get("pubmed_or_query") or "Not used")

    if sources:
        st.subheader("Evidence sources")
        for index, source in enumerate(sources, start=1):
            render_source(source, index)
    else:
        st.info("The API returned no evidence sources.")


def render_search_results(result: dict[str, Any]) -> None:
    """Render a search endpoint response."""
    sources = result.get("sources") or []
    st.subheader(f"Search results ({result.get('retrieval_count', len(sources))})")

    if not sources:
        st.info("No guideline passages matched this search.")
        return

    for index, source in enumerate(sources, start=1):
        render_source(source, index)


def show_request_error(exc: Exception) -> None:
    """Turn request failures into useful test-client feedback."""
    if isinstance(exc, requests.ConnectionError):
        st.error(
            "Could not reach the API. Start FastAPI on port 8011, "
            "then check the API URL in the sidebar."
        )
    elif isinstance(exc, requests.Timeout):
        st.error(
            "The API request timed out. External model, Pinecone, or PubMed "
            "requests may still be pending."
        )
    else:
        st.error(f"API request failed: {exc}")


def render_sidebar() -> str:
    """Render API connection controls and return the selected base URL."""
    with st.sidebar:
        st.header("API connection")
        api_url = st.text_input(
            "Base URL",
            value=st.session_state.get("api_url", DEFAULT_API_URL),
            help="The URL of the running FastAPI service.",
        )
        api_url = normalize_api_url(api_url)
        st.session_state.api_url = api_url

        if st.button("Check connection", use_container_width=True):
            try:
                health = request_api(
                    api_url,
                    "GET",
                    "/health",
                    timeout=5,
                )
                if health.get("status") == "ok":
                    st.success("API is healthy")
                else:
                    st.warning(f"Unexpected health response: {health}")
            except (requests.RequestException, RuntimeError) as exc:
                show_request_error(exc)

        if api_url:
            st.link_button(
                "Open API documentation",
                f"{api_url}/docs",
                use_container_width=True,
            )

        st.divider()
        st.caption(
            "The answer and search tools require valid Pinecone and "
            "OpenRouter credentials in the API's `.env` file."
        )

    return api_url


def main() -> None:
    st.set_page_config(
        page_title="Clinical Guidelines Tester",
        page_icon="🩺",
        layout="wide",
    )

    st.title("Clinical Guidelines Tester")
    st.caption(
        "Test guideline retrieval and grounded clinical answers against the "
        "local HealthStack API."
    )

    api_url = render_sidebar()
    answer_tab, search_tab, raw_tab = st.tabs(
        ["Ask a question", "Search guidelines", "Raw response"]
    )

    with answer_tab:
        with st.form("answer_form"):
            question = st.text_area(
                "Clinical question",
                value="How is uncomplicated malaria treated?",
                height=110,
                placeholder="Enter a clinical question…",
            )
            answer_submitted = st.form_submit_button(
                "Generate grounded answer",
                type="primary",
                use_container_width=True,
            )

        if answer_submitted:
            if not question.strip():
                st.warning("Enter a clinical question first.")
            else:
                with st.spinner(
                    "Searching guidelines and PubMed, then generating an answer…"
                ):
                    try:
                        result = request_api(
                            api_url,
                            "POST",
                            "/api/v1/copilot/guidelines/answer",
                            payload={"question": question.strip()},
                        )
                        st.session_state.latest_response = result
                        st.session_state.latest_response_type = "answer"
                        render_answer(result)
                    except (requests.RequestException, RuntimeError) as exc:
                        show_request_error(exc)

    with search_tab:
        with st.form("search_form"):
            search_question = st.text_input(
                "Search query",
                value="malaria treatment",
                placeholder="Enter a condition, intervention, or question…",
            )
            top_k = st.slider("Maximum results", 1, 20, 8)

            with st.expander("Optional filters"):
                filter_columns = st.columns(3)
                country = filter_columns[0].text_input(
                    "Country",
                    placeholder="e.g. Nigeria",
                )
                publisher = filter_columns[1].text_input(
                    "Publisher",
                    placeholder="e.g. Federal Ministry of Health",
                )
                document_type = filter_columns[2].text_input(
                    "Document type",
                    placeholder="e.g. treatment guideline",
                )

            search_submitted = st.form_submit_button(
                "Search guideline passages",
                type="primary",
                use_container_width=True,
            )

        if search_submitted:
            if not search_question.strip():
                st.warning("Enter a search query first.")
            else:
                payload: dict[str, Any] = {
                    "question": search_question.strip(),
                    "top_k": top_k,
                }
                optional_filters = {
                    "country": country,
                    "publisher": publisher,
                    "document_type": document_type,
                }
                payload.update(
                    {
                        key: value.strip()
                        for key, value in optional_filters.items()
                        if value.strip()
                    }
                )

                with st.spinner("Searching guideline passages…"):
                    try:
                        result = request_api(
                            api_url,
                            "POST",
                            "/api/v1/copilot/guidelines/search",
                            payload=payload,
                        )
                        st.session_state.latest_response = result
                        st.session_state.latest_response_type = "search"
                        render_search_results(result)
                    except (requests.RequestException, RuntimeError) as exc:
                        show_request_error(exc)

    with raw_tab:
        latest_response = st.session_state.get("latest_response")
        if latest_response:
            response_type = st.session_state.get(
                "latest_response_type",
                "API",
            )
            st.caption(f"Latest {response_type} response")
            st.json(latest_response)
        else:
            st.info(
                "Submit an answer or search request to inspect its raw JSON "
                "response here."
            )


if __name__ == "__main__":
    main()
