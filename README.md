# HealthStack Clinical Guidelines

Standalone FastAPI service for searching clinical guidelines and generating
grounded answers from the prepared NSTG 2022 dataset. It uses OpenRouter for
embeddings and answer generation, and Pinecone for vector search.

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
```

Run the API:

```bash
uvicorn main:app --reload --port 8011
```

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
