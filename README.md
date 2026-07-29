# HealthStack Clinical Guidelines

Standalone FastAPI service for searching clinical guidelines and generating
grounded answers from the prepared NSTG 2022 dataset and relevant PubMed
abstracts. It uses OpenRouter for embeddings and answer generation, Pinecone
for vector search, and NCBI E-utilities for PubMed retrieval.

## Start the service

Requires Python 3.13 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set these required values in `.env`:

```env
PINECONE_API_KEY=your_pinecone_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
PUBMED_API_KEY=your_ncbi_api_key
PUBMED_EMAIL=developer@example.com
```

Run the API:

```bash
uvicorn main:app --reload --port 8011
```

## Streamlit test client

With the API running, open a second terminal in the project directory:

```bash
python -m streamlit run streamlit_app.py
```

The test client opens at `http://127.0.0.1:8502`. It includes:

- a service health check;
- grounded guideline and PubMed answers;
- direct guideline search with optional filters;
- a raw JSON response viewer.

To test an API running elsewhere, set `GUIDELINES_API_URL` before starting
Streamlit or change the base URL in the client sidebar.

## Deploy on Render

The repository includes a `render.yaml` Blueprint for two connected services:

- `healthstack-guidelines-api` runs FastAPI;
- `healthstack-guidelines-ui` runs the Streamlit test client.

Create a new Render Blueprint from this repository and provide the requested
Pinecone, OpenRouter, and PubMed credentials in the Render dashboard. Secret
values are intentionally not stored in source control. The Blueprint passes
the API's Render URL to the Streamlit service automatically.

Endpoints:

```text
GET  /health
POST /api/v1/copilot/guidelines/search
POST /api/v1/copilot/guidelines/answer
```

Example:

```bash
curl -X POST http://127.0.0.1:8011/api/v1/copilot/guidelines/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"How is uncomplicated malaria treated?"}'
```

For answer requests, the query rewriter produces a Pinecone retrieval query and
up to eight PubMed concepts. Guideline retrieval and PubMed retrieval then run
in parallel. PubMed performs a strict `AND` search and a broader `OR` search,
merges PubMed's Best Match rankings, and adds at most three abstract-bearing
articles to the numbered synthesis context. PubMed errors fail soft so the
guideline-only answer path remains available.
Context space is budgeted across all selected sources so large guideline chunks
cannot crowd the selected PubMed abstracts out of synthesis.

The answer response's `sources` list contains typed `guideline` and `pubmed`
records in citation order. It also exposes the PubMed keywords and final Boolean
queries for observability.
Inline answer citations use the same source numbers. When a cited source has a
URL, such as a PubMed article, the citation is returned as a clickable Markdown
link.

PubMed data is provided by the National Library of Medicine. NLM does not
warrant the data or resulting use, and article abstracts may be copyrighted by
their publishers or authors. See the [NCBI disclaimer and copyright
notice](https://www.ncbi.nlm.nih.gov/home/about/policies/).

## Test and index

```bash
python -m unittest discover -s tests
python scripts/index_guidelines_pinecone.py --dry-run
```

To create or validate the index and upload the prepared chunks:

```bash
python scripts/setup_guidelines_index.py
python scripts/index_guidelines_pinecone.py
```

Docker is also supported:

```bash
docker build -t healthstack-guidelines .
docker run --rm -p 8011:8011 --env-file .env healthstack-guidelines
```
