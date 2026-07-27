"""Validates prepared guideline chunks, embeds them, and uploads them to Pinecone."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.clients.openrouter import (
    EmbeddingProvider,
    get_guidelines_embedding_provider,
)
from app.clients.pinecone import get_guidelines_index
from app.config import (
    GUIDELINES_EMBED_BATCH_SIZE,
    GUIDELINES_EMBEDDING_DIMENSIONS,
    GUIDELINES_EMBEDDING_MODEL,
    GUIDELINES_UPSERT_BATCH_SIZE,
    PINECONE_GUIDELINES_NAMESPACE,
)

NSTG_DOCUMENT_METADATA: dict[str, Any] = {
    "document_id": "nstg-2022",
    "title": "Nigeria Standard Treatment Guidelines 2022",
    "publisher": "Federal Ministry of Health Nigeria",
    "country": "Nigeria",
    "publication_year": 2022,
    "version": "2022",
    "document_type": "treatment_guideline",
    "source_url": "",
}


@dataclass(slots=True)
class GuidelineChunk:
    vector_id: str
    text: str
    metadata: dict[str, Any]


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read guideline chunk {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Guideline chunk must be a JSON object: {path}")
    return data


def load_guideline_chunks(
    directory: str | Path,
    document_metadata: dict[str, Any] | None = None,
) -> list[GuidelineChunk]:
    root = Path(directory)
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"Guideline chunk directory does not exist: {root}")

    base_metadata = dict(NSTG_DOCUMENT_METADATA)
    if document_metadata:
        base_metadata.update(document_metadata)

    chunks: list[GuidelineChunk] = []
    seen_ids: set[str] = set()
    for path in sorted(root.rglob("*.json")):
        data = _load_json_object(path)
        original_chunk_id = str(data.get("chunk_id") or "").strip()
        text = str(data.get("text") or "").strip()
        if not original_chunk_id:
            raise RuntimeError(f"Guideline chunk is missing chunk_id: {path}")
        if not text:
            raise RuntimeError(f"Guideline chunk is missing text: {path}")

        vector_id = f"{base_metadata['document_id']}:{original_chunk_id}"
        if vector_id in seen_ids:
            raise RuntimeError(f"Duplicate guideline chunk ID: {vector_id}")
        seen_ids.add(vector_id)

        section = str(
            data.get("subheading_corrected")
            or data.get("subheading")
            or data.get("condition")
            or ""
        ).strip()
        metadata = {
            **base_metadata,
            "original_chunk_id": original_chunk_id,
            "condition": str(data.get("condition") or "").strip(),
            "section": section,
            "subheading": str(data.get("subheading") or "").strip(),
            "source": str(data.get("source") or base_metadata["title"]).strip(),
            "text": text,
        }
        chunks.append(GuidelineChunk(vector_id=vector_id, text=text, metadata=metadata))

    if not chunks:
        raise RuntimeError(f"No JSON guideline chunks were found in {root}")
    return chunks


def _upsert_batch(
    chunks: list[GuidelineChunk],
    embeddings: list[list[float]],
) -> None:
    if len(chunks) != len(embeddings):
        raise RuntimeError("Guideline embedding count did not match the chunk count.")

    vectors = []
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        if len(embedding) != GUIDELINES_EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"Embedding for {chunk.vector_id} has {len(embedding)} dimensions; "
                f"expected {GUIDELINES_EMBEDDING_DIMENSIONS}."
            )
        vectors.append(
            {
                "id": chunk.vector_id,
                "values": embedding,
                "metadata": {
                    **chunk.metadata,
                    "embedding_model": GUIDELINES_EMBEDDING_MODEL,
                    "embedding_dimensions": GUIDELINES_EMBEDDING_DIMENSIONS,
                },
            }
        )

    get_guidelines_index().upsert(
        vectors=vectors,
        namespace=PINECONE_GUIDELINES_NAMESPACE,
    )


def index_guideline_chunks(
    chunks: list[GuidelineChunk],
    *,
    dry_run: bool = False,
    replace_document: bool = False,
    provider: EmbeddingProvider | None = None,
) -> dict[str, Any]:
    document_ids = sorted(
        {str(chunk.metadata.get("document_id") or "") for chunk in chunks}
    )
    stats: dict[str, Any] = {
        "chunks_loaded": len(chunks),
        "chunks_embedded": 0,
        "chunks_upserted": 0,
        "documents": document_ids,
        "dry_run": dry_run,
    }
    if dry_run:
        return stats

    stats["namespace"] = PINECONE_GUIDELINES_NAMESPACE
    index = get_guidelines_index()
    if replace_document:
        for document_id in document_ids:
            index.delete(
                filter={"document_id": {"$eq": document_id}},
                namespace=PINECONE_GUIDELINES_NAMESPACE,
            )

    embedding_provider = provider or get_guidelines_embedding_provider()
    batch_size = max(
        1,
        min(
            GUIDELINES_EMBED_BATCH_SIZE,
            GUIDELINES_UPSERT_BATCH_SIZE,
        ),
    )
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        embeddings = embedding_provider.embed_document_chunks(
            [chunk.text for chunk in batch]
        )
        stats["chunks_embedded"] += len(embeddings)
        _upsert_batch(batch, embeddings)
        stats["chunks_upserted"] += len(batch)

    return stats
