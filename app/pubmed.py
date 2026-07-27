"""Builds strict and broad PubMed queries and selects relevant articles."""

from functools import lru_cache
import re

from app.clients.pubmed import PubMedClient, RankedPmid
from app.config import PUBMED_EUTILS_BASE_URL, get_guidelines_settings
from app.models import PubMedSource


PUBMED_STOPWORDS = {
    "and",
    "or",
    "the",
    "with",
    "without",
    "for",
    "from",
    "into",
    "management",
    "guideline",
    "guidelines",
    "diagnosis",
    "diagnostic",
    "investigation",
    "investigations",
    "imaging",
    "biopsy",
    "regimen",
    "regimens",
    "dose",
    "doses",
    "dosing",
    "adverse",
    "effects",
    "effect",
    "contraindication",
    "contraindications",
    "monitoring",
    "multimodality",
}


def _clean_terms(keywords: list[str]) -> list[str]:
    terms: list[str] = []
    normalized: set[str] = set()
    for keyword in keywords:
        term = " ".join(str(keyword).replace('"', "").split())
        folded = term.casefold()
        if term and folded not in normalized:
            terms.append(term)
            normalized.add(folded)
    return terms[:8]


def _term_tokens(term: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9]+", term):
        folded = token.casefold()
        if len(folded) < 3 or folded in PUBMED_STOPWORDS or folded in seen:
            continue
        tokens.append(token)
        seen.add(folded)
    return tokens[:4]


def _fielded_token(token: str) -> str:
    return f"{token}[Title/Abstract]"


def _strict_clause(term: str) -> str:
    tokens = _term_tokens(term)
    if not tokens:
        return ""
    if len(tokens) == 1:
        return _fielded_token(tokens[0])
    return "(" + " AND ".join(_fielded_token(token) for token in tokens) + ")"


def _broad_clause(term: str) -> str:
    tokens = _term_tokens(term)
    if not tokens:
        return ""
    if len(tokens) == 1:
        return _fielded_token(tokens[0])
    return "(" + " OR ".join(_fielded_token(token) for token in tokens) + ")"


def build_pubmed_queries(keywords: list[str]) -> tuple[str, str]:
    terms = _clean_terms(keywords)
    if not terms:
        return "", ""
    strict_clauses = [clause for term in terms if (clause := _strict_clause(term))]
    broad_clauses = [clause for term in terms if (clause := _broad_clause(term))]
    return " AND ".join(strict_clauses), " OR ".join(broad_clauses)


@lru_cache
def get_pubmed_client() -> PubMedClient | None:
    settings = get_guidelines_settings()
    if not settings.pubmed_email:
        return None
    return PubMedClient(
        api_key=settings.pubmed_api_key,
        email=settings.pubmed_email,
        tool=settings.pubmed_tool,
        base_url=PUBMED_EUTILS_BASE_URL,
        timeout=settings.pubmed_request_timeout_secs,
    )


def _fuse_rankings(and_pmids: list[str], or_pmids: list[str]) -> list[RankedPmid]:
    scores: dict[str, float] = {}
    matches: dict[str, list[str]] = {}
    searches = (("AND", 2.0, and_pmids), ("OR", 1.0, or_pmids))
    for mode, weight, pmids in searches:
        for rank, pmid in enumerate(pmids, start=1):
            scores[pmid] = scores.get(pmid, 0.0) + weight / (60 + rank)
            matches.setdefault(pmid, []).append(mode)
    return [
        RankedPmid(
            pmid=pmid,
            relevance_score=score,
            matched_searches=tuple(matches[pmid]),
        )
        for pmid, score in sorted(
            scores.items(), key=lambda item: (-item[1], item[0])
        )
    ]


def search_pubmed_articles(keywords: list[str]) -> list[PubMedSource]:
    settings = get_guidelines_settings()
    client = get_pubmed_client()
    if client is None:
        return []

    and_query, or_query = build_pubmed_queries(keywords)
    if not and_query:
        return []
    and_pmids = client.search_pmids(and_query, settings.pubmed_search_top_k)
    or_pmids = (
        client.search_pmids(or_query, settings.pubmed_search_top_k)
        if or_query != and_query
        else and_pmids
    )
    rankings = _fuse_rankings(and_pmids, or_pmids)
    articles = client.fetch_articles(rankings)
    articles.sort(key=lambda item: item.relevance_score, reverse=True)
    return articles[: settings.pubmed_max_context_articles]
