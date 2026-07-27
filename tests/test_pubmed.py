"""Tests PubMed Boolean queries, ranking fusion, transport, and XML parsing."""

import json
import unittest
import urllib.parse
from unittest.mock import patch

from app.clients.pubmed import PubMedClient, RankedPmid
from app.config import GuidelinesSettings
from app.pubmed import build_pubmed_queries, search_pubmed_articles


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self.body


ARTICLE_XML = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>123</PMID>
      <Article>
        <Journal>
          <JournalIssue><PubDate><Year>2025</Year><Month>Jul</Month></PubDate></JournalIssue>
          <Title>Journal of Testing</Title>
        </Journal>
        <ArticleTitle>A <i>malaria</i> treatment study</ArticleTitle>
        <Abstract>
          <AbstractText Label="RESULTS">Treatment improved outcomes.</AbstractText>
          <AbstractText Label="CONCLUSIONS">Further study is needed.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><ForeName>Ada</ForeName><LastName>Okafor</LastName></Author>
        </AuthorList>
        <PublicationTypeList><PublicationType>Clinical Trial</PublicationType></PublicationTypeList>
      </Article>
    </MedlineCitation>
    <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1/test</ArticleId></ArticleIdList></PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class PubMedTests(unittest.TestCase):
    def test_builds_strict_and_broad_queries_from_safe_terms(self):
        and_query, or_query = build_pubmed_queries(
            ["malaria", " adult treatment ", "Malaria", 'dose "schedule"']
        )

        self.assertEqual(
            and_query,
            "malaria[Title/Abstract] AND "
            "(adult[Title/Abstract] AND treatment[Title/Abstract]) AND "
            "schedule[Title/Abstract]",
        )
        self.assertIn(" OR ", or_query)
        self.assertNotIn('"Malaria"', or_query)

    def test_relaxes_long_pubmed_concepts_to_fielded_tokens(self):
        and_query, or_query = build_pubmed_queries(
            [
                "breast neoplasms management guidelines",
                "chemotherapy regimens vincristine Oncovin dosing",
            ]
        )

        self.assertEqual(
            and_query,
            (
                "(breast[Title/Abstract] AND neoplasms[Title/Abstract]) AND "
                "(chemotherapy[Title/Abstract] AND vincristine[Title/Abstract] "
                "AND Oncovin[Title/Abstract])"
            ),
        )
        self.assertEqual(
            or_query,
            (
                "(breast[Title/Abstract] OR neoplasms[Title/Abstract]) OR "
                "(chemotherapy[Title/Abstract] OR vincristine[Title/Abstract] "
                "OR Oncovin[Title/Abstract])"
            ),
        )

    def test_search_includes_ncbi_identity_and_api_key(self):
        client = PubMedClient(
            api_key="test-key",
            email="developer@example.com",
            tool="healthstack_guidelines",
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            timeout=20,
        )
        body = json.dumps({"esearchresult": {"idlist": ["123", "456"]}}).encode()
        with patch(
            "app.clients.pubmed.urllib.request.urlopen",
            return_value=FakeResponse(body),
        ) as urlopen:
            pmids = client.search_pmids('"malaria"[Title/Abstract]', 10)

        request = urlopen.call_args.args[0]
        parameters = urllib.parse.parse_qs(urllib.parse.urlparse(request.full_url).query)
        self.assertEqual(pmids, ["123", "456"])
        self.assertEqual(parameters["email"], ["developer@example.com"])
        self.assertEqual(parameters["tool"], ["healthstack_guidelines"])
        self.assertEqual(parameters["api_key"], ["test-key"])
        self.assertEqual(parameters["sort"], ["relevance"])

    def test_parses_pubmed_xml_into_typed_source(self):
        client = PubMedClient(
            api_key=None,
            email="developer@example.com",
            tool="healthstack_guidelines",
            base_url="https://example.test",
            timeout=20,
        )
        with patch(
            "app.clients.pubmed.urllib.request.urlopen",
            return_value=FakeResponse(ARTICLE_XML),
        ):
            sources = client.fetch_articles(
                [RankedPmid("123", 0.5, ("AND", "OR"))]
            )

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0].title, "A malaria treatment study")
        self.assertEqual(sources[0].authors, ["Ada Okafor"])
        self.assertEqual(sources[0].publication_date, "2025 Jul")
        self.assertEqual(sources[0].doi, "10.1/test")
        self.assertIn("RESULTS: Treatment improved outcomes.", sources[0].abstract)

    def test_runs_and_and_or_searches_and_limits_context_to_three(self):
        class FakeClient:
            def __init__(self):
                self.queries = []

            def search_pmids(self, query, retmax):
                self.queries.append(query)
                if " AND " in query:
                    return ["strict", "shared"]
                return ["broad", "shared", "extra"]

            def fetch_articles(self, rankings):
                from app.models import PubMedSource

                return [
                    PubMedSource(
                        pmid=item.pmid,
                        title=f"Article {item.pmid}",
                        abstract="Relevant abstract.",
                        source_url=f"https://pubmed.ncbi.nlm.nih.gov/{item.pmid}/",
                        relevance_score=item.relevance_score,
                        matched_searches=list(item.matched_searches),
                    )
                    for item in rankings
                ]

        client = FakeClient()
        settings = GuidelinesSettings(
            pubmed_email="developer@example.com",
            pubmed_search_top_k=10,
            pubmed_max_context_articles=3,
        )
        with (
            patch("app.pubmed.get_pubmed_client", return_value=client),
            patch("app.pubmed.get_guidelines_settings", return_value=settings),
        ):
            sources = search_pubmed_articles(["malaria", "treatment"])

        self.assertEqual(len(client.queries), 2)
        self.assertIn(" AND ", client.queries[0])
        self.assertIn(" OR ", client.queries[1])
        self.assertEqual(len(sources), 3)
        self.assertEqual(sources[0].pmid, "shared")
        self.assertIn("shared", [source.pmid for source in sources])


if __name__ == "__main__":
    unittest.main()
