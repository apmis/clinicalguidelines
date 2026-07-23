"""Loads prepared guideline chunks and runs the dry-run or live Pinecone ingestion job."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.guidelines.indexing.service import (
    index_guideline_chunks,
    load_guideline_chunks,
)
from app.guidelines.config import GUIDELINES_DATA_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embed prepared clinical guideline chunks and upsert them to Pinecone."
    )
    parser.add_argument(
        "--path",
        default=GUIDELINES_DATA_PATH,
        help="Directory containing prepared guideline chunk JSON files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and count chunks without calling OpenRouter or Pinecone.",
    )
    parser.add_argument(
        "--replace-document",
        action="store_true",
        help="Delete this document's existing Pinecone records before upserting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chunks = load_guideline_chunks(args.path)
    stats = index_guideline_chunks(
        chunks,
        dry_run=args.dry_run,
        replace_document=args.replace_document,
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
