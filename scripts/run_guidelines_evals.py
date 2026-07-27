"""Run lightweight live evals for guideline plus PubMed answer retrieval.

This intentionally uses the real pipeline and configured providers. It is not a
unit test; it is a smoke/regression eval for retrieval quality and citation
discipline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.models import GuidelinesPipelineInput
from app.pipeline import answer_guideline_question


DEFAULT_CASES_PATH = Path("evals/guidelines_pubmed_eval_cases.json")
DEFAULT_RESULTS_DIR = Path("evals/results")


@dataclass
class EvalChecks:
    answered: bool
    citations_valid: bool
    required_terms_present: bool
    forbidden_terms_absent: bool
    expected_sources_present: bool
    pubmed_retrieved_when_preferred: bool


def _contains_all(text: str, terms: list[str]) -> bool:
    folded = text.casefold()
    return all(term.casefold() in folded for term in terms)


def _contains_none(text: str, terms: list[str]) -> bool:
    folded = text.casefold()
    return all(term.casefold() not in folded for term in terms)


def _source_blob(sources: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for source in sources:
        parts.extend(
            str(source.get(field) or "")
            for field in (
                "source_type",
                "chunk_id",
                "document_id",
                "title",
                "condition",
                "section",
                "pmid",
                "journal",
                "source_url",
            )
        )
    return "\n".join(parts)


def _citations_valid(answer: str, sources: list[dict[str, Any]]) -> bool:
    source_count = len(sources)
    for match in re.finditer(r"\[(?P<number>\d+)\](?:\((?P<url>[^)]*)\))?", answer):
        number = int(match.group("number"))
        if number < 1 or number > source_count:
            return False
        expected_url = str(sources[number - 1].get("source_url") or "").strip()
        actual_url = match.group("url")
        if actual_url and actual_url != expected_url:
            return False
        if expected_url and actual_url is None:
            return False
    return True


def _case_passed(checks: EvalChecks) -> bool:
    return all(asdict(checks).values())


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    response = answer_guideline_question(
        GuidelinesPipelineInput(question=case["question"])
    )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    payload = response.model_dump(mode="json")
    sources = payload["sources"]
    source_blob = _source_blob(sources)
    pubmed_sources = [
        source for source in sources if source.get("source_type") == "pubmed"
    ]

    checks = EvalChecks(
        answered=bool(payload["answer"].strip()),
        citations_valid=_citations_valid(payload["answer"], sources),
        required_terms_present=_contains_all(
            payload["answer"], case.get("required_answer_terms", [])
        ),
        forbidden_terms_absent=_contains_none(
            payload["answer"], case.get("forbidden_answer_terms", [])
        ),
        expected_sources_present=_contains_all(
            source_blob, case.get("expected_source_terms", [])
        ),
        pubmed_retrieved_when_preferred=(
            bool(pubmed_sources) if case.get("prefer_pubmed") else True
        ),
    )

    return {
        "id": case["id"],
        "question": case["question"],
        "passed": _case_passed(checks),
        "checks": asdict(checks),
        "elapsed_ms": elapsed_ms,
        "retrieval_count": payload["retrieval_count"],
        "guideline_count": sum(
            1 for source in sources if source.get("source_type") == "guideline"
        ),
        "pubmed_count": len(pubmed_sources),
        "cited_sources": sorted(
            {int(match) for match in re.findall(r"\[(\d+)\]", payload["answer"])}
        ),
        "pubmed_pmids": [source["pmid"] for source in pubmed_sources],
        "pubmed_keywords": payload["pubmed_keywords"],
        "pubmed_and_query": payload["pubmed_and_query"],
        "pubmed_or_query": payload["pubmed_or_query"],
        "answer": payload["answer"],
        "sources": sources,
    }


def _write_markdown(results: dict[str, Any], path: Path) -> None:
    lines = [
        "# Guidelines + PubMed Eval Results",
        "",
        f"Run: `{results['run_started_at']}`",
        "",
        f"Passed: `{results['passed_count']}/{results['case_count']}`",
        "",
        "| Case | Pass | Guidelines | PubMed | Cited | Notes |",
        "|---|---:|---:|---:|---|---|",
    ]
    for item in results["cases"]:
        failed_checks = [
            name for name, passed in item["checks"].items() if not passed
        ]
        notes = "ok" if not failed_checks else ", ".join(failed_checks)
        cited = ", ".join(f"[{number}]" for number in item["cited_sources"])
        lines.append(
            "| {id} | {passed} | {guideline_count} | {pubmed_count} | {cited} | {notes} |".format(
                id=item["id"],
                passed="yes" if item["passed"] else "no",
                guideline_count=item["guideline_count"],
                pubmed_count=item["pubmed_count"],
                cited=cited or "-",
                notes=notes,
            )
        )
    lines.append("")
    lines.append("## Case Details")
    for item in results["cases"]:
        lines.extend(
            [
                "",
                f"### {item['id']}",
                "",
                f"Question: {item['question']}",
                "",
                f"Checks: `{json.dumps(item['checks'], sort_keys=True)}`",
                "",
                f"PubMed PMIDs: `{', '.join(item['pubmed_pmids']) or '-'}`",
                "",
                "Answer:",
                "",
                item["answer"],
            ]
        )
    content = "\n".join(line.rstrip() for line in lines) + "\n"
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    args.results_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()
    results = {
        "run_started_at": started_at,
        "case_count": len(cases),
        "cases": [],
    }

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']}: {case['question']}", flush=True)
        try:
            item = _run_case(case)
        except Exception as exc:
            item = {
                "id": case["id"],
                "question": case["question"],
                "passed": False,
                "checks": {"runtime_error": False},
                "error": str(exc),
            }
        results["cases"].append(item)
        print(
            "    {status}".format(status="PASS" if item["passed"] else "FAIL"),
            flush=True,
        )

    results["passed_count"] = sum(1 for item in results["cases"] if item["passed"])
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.results_dir / f"guidelines_pubmed_eval_{timestamp}.json"
    markdown_path = args.results_dir / f"guidelines_pubmed_eval_{timestamp}.md"
    latest_json_path = args.results_dir / "latest.json"
    latest_markdown_path = args.results_dir / "latest.md"

    serialized = json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    json_path.write_text(serialized, encoding="utf-8")
    latest_json_path.write_text(serialized, encoding="utf-8")
    _write_markdown(results, markdown_path)
    _write_markdown(results, latest_markdown_path)

    print(
        "Passed {passed}/{total}".format(
            passed=results["passed_count"], total=results["case_count"]
        )
    )
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")


if __name__ == "__main__":
    main()
