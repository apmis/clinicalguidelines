# Guidelines Vector Search

This document explains the standalone guideline RAG service.

## What Was Built

We added a small, isolated guideline retrieval and answer service.

Its job is simple:

1. Read prepared guideline chunk files from `data/guidelines/nstg-2022/chunks`.
2. Use OpenRouter to create embeddings for those chunks.
3. Store those embeddings in Pinecone.
4. Accept a clinical question.
5. Use a small model through OpenRouter to produce a structured retrieval query.
6. Use OpenRouter to embed the retrieval query.
7. Search Pinecone for candidate guideline chunks while searching PubMed with
   strict `AND` and broad `OR` queries.
8. Apply absolute and best-score-relative relevance thresholds to guidelines.
9. Merge PubMed Best Match rankings and retain the best three abstracts.
10. Remove duplicate guideline passages and cap the combined context.
11. Use a reasoning model through OpenRouter to answer from numbered evidence.
12. Return the answer, retrieval details, and typed sources.

This does not use MongoDB yet. It was intentionally built with minimal contact with the existing codebase.

## Current Status

The Pinecone index has been created and loaded.

- Pinecone index name: `healthstack-guidelines`
- Pinecone namespace: `clinical-guidelines-v1`
- Embedding model: `openai/text-embedding-3-small`
- Embedding dimensions: `1024`
- Guideline chunks loaded: `1207`
- Guideline chunks embedded: `1207`
- Guideline chunks uploaded to Pinecone: `1207`

A test search for `malaria treatment in adults` returned relevant guideline chunks, so the vector search path is working.

## Important Design Choice

OpenRouter is the only model gateway used by the guideline service.

That means the same OpenRouter API key is used for:

- embedding guideline chunks before uploading them to Pinecone
- embedding user questions before searching Pinecone
- structured query rewriting
- grounded answer generation

The OpenAI `text-embedding-3-small` model is accessed through OpenRouter using
the `openai/text-embedding-3-small` model slug. OpenRouter's Chat Completions
API is used for query rewriting and grounded answer generation. Model names are
configuration values, so these stages can be swapped without changing the
pipeline.

## Package Layout

```text
app/
|-- api.py              HTTP routes
|-- config.py           environment-backed settings
|-- models.py           shared validated data contracts
|-- pipeline.py         end-to-end RAG orchestration
|-- pubmed.py           Boolean queries, rank fusion, and article selection
|-- retrieval.py        query rewriting, vector search, and relevance selection
|-- synthesis.py        grounded answer generation
|-- prompts/
|   |-- query_rewriter.md
|   `-- synthesis.md
|-- clients/
|   |-- openrouter.py   embeddings and model generation
|   |-- pinecone.py     vector database connection
|   `-- pubmed.py       NCBI ESearch and EFetch transport/XML parsing
`-- indexing/
    `-- service.py      chunk loading and Pinecone uploads
```

`indexing` does not depend on the request pipeline. The runtime dependency
direction is `api -> pipeline -> retrieval/synthesis -> clients`.

Prompt content lives only in `app/prompts/query_rewriter.md` and
`app/prompts/synthesis.md`. The files are packaged with the service
and versioned through source control.

## Files Added

### `app/config.py`

Loads settings for the standalone guideline service.

It reads values like:

- `PINECONE_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_API_BASE`
- `PUBMED_API_KEY`
- `PUBMED_EMAIL`

Non-secret index, embedding, batching, retrieval, timeout, and data-path values
are fixed constants in this module and cannot be overridden by environment
variables.

### `app/clients/openrouter.py`

Wraps OpenRouter embedding and Chat Completions API calls.

It provides:

- guideline text chunks
- user search questions
- structured query rewriting
- grounded answer generation

### `app/clients/pinecone.py`

Creates the Pinecone client and connects to the guideline index using the fixed
production host in `app/config.py`.

### `app/indexing/service.py`

Loads the prepared guideline JSON files, validates them, creates vector records, and uploads them to Pinecone.

Each Pinecone vector gets a stable ID like:

```text
nstg-2022:MAL_006
```

### `app/retrieval.py`

Rewrites questions and searches Pinecone for relevant guideline chunks.

It:

1. produces a structured retrieval query and PubMed search concepts
2. falls back to the original question if rewriting fails
3. embeds the retrieval query through OpenRouter
4. queries Pinecone
5. filters weak matches
6. removes duplicates
7. returns source chunks

Candidate retrieval and relevance selection are separate functions. The
selection stage combines:

- `GUIDELINES_MIN_VECTOR_SCORE`: absolute similarity floor
- `GUIDELINES_SCORE_GAP_RATIO`: required score relative to the best match
- `GUIDELINES_MAX_CONTEXT_CHUNKS`: maximum passages sent to synthesis

### `app/synthesis.py`

Builds numbered guideline and PubMed context and generates an answer with inline
`[n]` citations. Citation links are normalized after generation: if source `n`
has a URL, the answer returns `[n](url)`; if it does not, the citation remains
plain `[n]`. This keeps PubMed citations clickable while preventing the model
from inventing placeholder or mismatched citation links. If no source passes
relevance selection, it abstains without calling the answer model.

### `app/pipeline.py`

Orchestrates query rewriting, parallel Pinecone/PubMed retrieval, relevance
selection, and answer synthesis. It accepts optional trusted patient context
internally, but the public API does not expose that field yet. PubMed failure is
non-fatal so guideline retrieval can still produce an answer.

### `app/models.py`

Defines the request and response shapes for the guideline API.

### `app/api.py`

Defines the guideline search and complete RAG answer routes.

### `app_main.py`

Creates a standalone FastAPI app for the guideline search service.

This lets us run and test the guideline endpoint without starting the full existing backend.

### `scripts/setup_guidelines_index.py`

Creates or verifies the Pinecone index.

It checks:

- index name
- vector dimension
- similarity metric
- index host
- index readiness

### `scripts/index_guidelines_pinecone.py`

Runs the embedding and upload process.

It loads the guideline chunks, embeds them through OpenRouter, and upserts them into Pinecone.

### `.env.example`

Shows the environment variables needed for this feature.

It contains placeholder values only. Real keys belong in `.env`.

### `data/guidelines/nstg-2022/chunks`

Contains the prepared guideline chunks copied from `guidelines_backend`.

These are the files that were embedded and uploaded to Pinecone.

### `data/guidelines/nstg-2022/manifest.json`

Describes the copied guideline chunk dataset.

### Tests

The following tests were added:

- `tests/test_guidelines_ingestion.py`
- `tests/test_guidelines_retriever.py`
- `tests/test_guidelines_api.py`

These test loading, ingestion behavior, retrieval behavior, and the API route.

## Environment Variables

The real values should live in `.env`.

Example:

```env
PINECONE_API_KEY=your_pinecone_api_key_here

OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
OPENROUTER_HTTP_REFERER=http://localhost:8011
OPENROUTER_APP_TITLE=Healthstack Guidelines
PUBMED_API_KEY=your_ncbi_api_key_here
PUBMED_EMAIL=developer@example.com
PUBMED_TOOL=healthstack_guidelines
PUBMED_SEARCH_TOP_K=10
PUBMED_MAX_CONTEXT_ARTICLES=3
GUIDELINES_SCORE_GAP_RATIO=0.8
GUIDELINES_MAX_CONTEXT_CHUNKS=4
GUIDELINES_QUERY_MAX_OUTPUT_TOKENS=300
GUIDELINES_ANSWER_MAX_OUTPUT_TOKENS=1600
GUIDELINES_ANSWER_REASONING_EFFORT=low
GUIDELINES_MAX_CONTEXT_CHARACTERS=24000
```

The fixed values are declared in `app/config.py`:

- Pinecone index: `healthstack-guidelines`
- Pinecone host: `healthstack-guidelines-gddfi1b.svc.aped-4627-b74a.pinecone.io`
- Pinecone namespace: `clinical-guidelines-v1`
- Pinecone location: `aws`, `us-east-1`
- Embedding model: `openai/text-embedding-3-small`
- Embedding dimensions: `1024`
- Embedding/upsert batch sizes: `50` / `100`
- Retrieval top-k and score floor: `8` / `0.2`
- Request timeout: `60` seconds
- Data path: `data/guidelines/nstg-2022/chunks`
- Query rewriting model: `openai/gpt-5.4-nano`
- Answer synthesis model: `openai/gpt-5.4-nano`

Do not put real keys in `.env.example`.

`.env` is ignored by git.

## How To Create Or Check The Pinecone Index

Run:

```bash
.venv/bin/python scripts/setup_guidelines_index.py
```

This creates the Pinecone index if it does not exist.

It also prints the index host. That host should be placed in `.env` as:

```env
PINECONE_GUIDELINES_INDEX_HOST=your_pinecone_index_host_here
```

## How To Upload Guideline Chunks To Pinecone

Run:

```bash
.venv/bin/python scripts/index_guidelines_pinecone.py
```

Expected result:

```json
{
  "chunks_loaded": 1207,
  "chunks_embedded": 1207,
  "chunks_upserted": 1207,
  "documents": ["nstg-2022"],
  "dry_run": false,
  "namespace": "clinical-guidelines-v1"
}
```

## How To Run The Standalone Guideline API

Run:

```bash
.venv/bin/uvicorn main:app --reload --port 8011
```

Health check:

```bash
curl http://127.0.0.1:8011/health
```

Search endpoint:

```bash
curl -X POST http://127.0.0.1:8011/api/v1/copilot/guidelines/search \
  -H "Content-Type: application/json" \
  -d '{"question":"malaria treatment in adults","top_k":3}'
```

Complete RAG endpoint:

```bash
curl -X POST http://127.0.0.1:8011/api/v1/copilot/guidelines/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"How should uncomplicated malaria be treated in an adult?"}'
```

The public answer request intentionally contains only `question`. The internal
pipeline input already supports optional trusted `patient_context`, which can be
populated later by the authenticated backend rather than accepted directly from
an untrusted client.
