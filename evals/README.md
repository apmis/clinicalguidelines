# Guidelines + PubMed Evals

This directory contains a lightweight live eval for the guideline-answer
pipeline after PubMed retrieval was added.

Run it with:

```bash
python scripts/run_guidelines_evals.py
```

The runner uses the real configured pipeline: query rewriting, Pinecone
guideline retrieval, PubMed retrieval, and answer synthesis. It writes
timestamped JSON/Markdown results under `evals/results/` and also refreshes
`evals/results/latest.json` and `evals/results/latest.md`.

The checks are intentionally simple and deterministic:

- the answer is non-empty
- inline citations point to returned sources and use the correct source URL
- expected source metadata is present
- required answer terms are present
- forbidden answer terms are absent
- PubMed sources are retrieved for cases that prefer PubMed context

These evals are not a clinical gold standard. They are a smoke/regression suite
to catch retrieval regressions, citation mismatches, and obvious grounding
failures before a more formal clinician-reviewed eval set exists.
