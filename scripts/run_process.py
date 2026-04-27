"""Chunk, embed, and index all raw documents for a course into ChromaDB."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def load_raw_docs(course_id: str):
    from ingest.base import RawDocument
    docs = []
    for jsonl in (ROOT / "data/raw").rglob(f"{course_id}/documents.jsonl"):
        for line in jsonl.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            d["file_path"] = Path(d["file_path"]) if d.get("file_path") else None
            docs.append(RawDocument(**d))
    return docs


def main(course_id: str) -> None:
    s = yaml.safe_load((ROOT / "config/settings.yaml").read_text())

    from process.chunker import chunk_documents
    from process.embedder import embed_chunks
    from retrieval.vector_store import get_client, get_collection, upsert_chunks

    print(f"Loading raw documents for {course_id}...")
    docs = load_raw_docs(course_id)
    print(f"  {len(docs)} documents")

    print("Chunking...")
    chunks = chunk_documents(docs)
    print(f"  {len(chunks)} chunks")

    print(f"Embedding with {s['embedding']['model']}...")
    chunks = embed_chunks(
        chunks,
        model_name=s["embedding"]["model"],
        device=s["embedding"]["device"],
        batch_size=s["embedding"]["batch_size"],
    )

    print("Indexing into ChromaDB...")
    collection = get_collection(get_client(s["chroma_db_path"]), course_id)
    upsert_chunks(collection, chunks)
    print(f"  Done — {len(chunks)} chunks indexed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", default="6.1220")
    args = parser.parse_args()
    main(args.course)
