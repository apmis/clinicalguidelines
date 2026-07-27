"""Small NCBI E-utilities client for PubMed search and abstract retrieval."""

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Literal

from app.models import PubMedSource


@dataclass(frozen=True)
class RankedPmid:
    pmid: str
    relevance_score: float
    matched_searches: tuple[Literal["AND", "OR"], ...]


def _element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


class PubMedClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        email: str,
        tool: str,
        base_url: str,
        timeout: int,
    ) -> None:
        self.api_key = api_key
        self.email = email
        self.tool = tool
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._request_interval = 0.11 if api_key else 0.34
        self._request_lock = threading.Lock()
        self._last_request_at = 0.0

    def _parameters(self, values: dict[str, Any]) -> dict[str, Any]:
        parameters = {**values, "email": self.email, "tool": self.tool}
        if self.api_key:
            parameters["api_key"] = self.api_key
        return parameters

    def _get(self, endpoint: str, parameters: dict[str, Any]) -> bytes:
        query = urllib.parse.urlencode(self._parameters(parameters))
        request = urllib.request.Request(
            f"{self.base_url}/{endpoint}?{query}",
            headers={"User-Agent": f"{self.tool}/1.0 ({self.email})"},
        )
        try:
            self._wait_for_rate_limit()
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"PubMed request failed: {detail}") from exc
        except (TimeoutError, urllib.error.URLError) as exc:
            raise RuntimeError("PubMed is temporarily unavailable.") from exc

    def _wait_for_rate_limit(self) -> None:
        """Keep this process below NCBI's per-key or per-IP request limit."""
        with self._request_lock:
            now = time.monotonic()
            wait = self._request_interval - (now - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
            self._last_request_at = time.monotonic()

    def search_pmids(self, query: str, retmax: int) -> list[str]:
        payload = self._get(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": retmax,
                "sort": "relevance",
            },
        )
        try:
            data = json.loads(payload.decode("utf-8"))
            return [str(pmid) for pmid in data["esearchresult"]["idlist"]]
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
            raise RuntimeError("PubMed returned an invalid search response.") from exc

    def fetch_articles(self, ranked_pmids: list[RankedPmid]) -> list[PubMedSource]:
        if not ranked_pmids:
            return []
        payload = self._get(
            "efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(item.pmid for item in ranked_pmids),
                "retmode": "xml",
            },
        )
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise RuntimeError("PubMed returned invalid article data.") from exc

        rankings = {item.pmid: item for item in ranked_pmids}
        articles: list[PubMedSource] = []
        for record in root.findall(".//PubmedArticle"):
            citation = record.find("MedlineCitation")
            article = citation.find("Article") if citation is not None else None
            pmid = _element_text(citation.find("PMID") if citation is not None else None)
            ranking = rankings.get(pmid)
            if article is None or ranking is None:
                continue

            title = _element_text(article.find("ArticleTitle"))
            abstract_parts: list[str] = []
            for part in article.findall("./Abstract/AbstractText"):
                text = _element_text(part)
                if not text:
                    continue
                label = (part.attrib.get("Label") or "").strip()
                abstract_parts.append(f"{label}: {text}" if label else text)
            abstract = "\n".join(abstract_parts)
            if not title or not abstract:
                continue

            authors: list[str] = []
            for author in article.findall("./AuthorList/Author"):
                collective = _element_text(author.find("CollectiveName"))
                personal = " ".join(
                    value
                    for value in (
                        _element_text(author.find("ForeName")),
                        _element_text(author.find("LastName")),
                    )
                    if value
                )
                name = collective or personal
                if name:
                    authors.append(name)

            journal = _element_text(article.find("./Journal/Title")) or None
            pub_date = article.find("./Journal/JournalIssue/PubDate")
            publication_date = None
            if pub_date is not None:
                publication_date = (
                    _element_text(pub_date.find("MedlineDate"))
                    or " ".join(
                        value
                        for value in (
                            _element_text(pub_date.find("Year")),
                            _element_text(pub_date.find("Month")),
                            _element_text(pub_date.find("Day")),
                        )
                        if value
                    )
                    or None
                )

            doi = None
            for article_id in record.findall("./PubmedData/ArticleIdList/ArticleId"):
                if article_id.attrib.get("IdType") == "doi":
                    doi = _element_text(article_id) or None
                    break

            articles.append(
                PubMedSource(
                    pmid=pmid,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    journal=journal,
                    publication_date=publication_date,
                    doi=doi,
                    publication_types=[
                        text
                        for item in article.findall("./PublicationTypeList/PublicationType")
                        if (text := _element_text(item))
                    ],
                    source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    relevance_score=ranking.relevance_score,
                    matched_searches=list(ranking.matched_searches),
                )
            )
        return articles
