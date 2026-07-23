# HealthStack Guidelines Implementation

Standalone clinical-guideline retrieval and grounded-answer service for
HealthStack. It has no MongoDB, patient, authentication, or copilot-service
dependency.

The service:

1. embeds prepared NSTG 2022 guideline chunks through OpenRouter;
2. stores and retrieves their vectors in Pinecone;
3. rewrites clinical questions into retrieval-oriented queries;
4. filters and deduplicates matching passages; and
5. generates a grounded answer with numbered source citations.

## Repository layout

```text
app/guidelines/                  Guideline retrieval and answer pipeline
app/guidelines_main.py           Standalone FastAPI application
data/guidelines/nstg-2022/       Prepared guideline chunks and manifest
scripts/setup_guidelines_index.py
scripts/index_guidelines_pinecone.py
tests/                           Guideline-only test suite
docs/guidelines-vector-search.md Detailed implementation notes
```

## Local setup

Python 3.13 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The transferred local `.env` contains the current `PINECONE_API_KEY` and
`OPENROUTER_API_KEY` values and is ignored by Git. For a fresh environment:

```bash
cp .env.example .env
```

Then set the two required keys:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

The remaining settings in `.env.example` are optional and have working
defaults.

## Run the API

```bash
uvicorn app.guidelines_main:app --reload --port 8011
```

Available endpoints:

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

## Index setup and ingestion

Validate all prepared chunks without making external API calls:

```bash
python scripts/index_guidelines_pinecone.py --dry-run
```

Create or validate the Pinecone index, then upload the chunks:

```bash
python scripts/setup_guidelines_index.py
python scripts/index_guidelines_pinecone.py
```

Chunk IDs are stable, so ingestion can be safely rerun.

## Tests

```bash
python -m unittest discover -s tests
```

## Docker

```bash
docker build -t healthstack-guidelines .
docker run --rm -p 8011:8011 --env-file .env healthstack-guidelines
```

For implementation details, configuration constants, and index information,
see [docs/guidelines-vector-search.md](docs/guidelines-vector-search.md).
