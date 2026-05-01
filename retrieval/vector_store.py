"""ChromaDB vector store: read/write interface."""
from __future__ import annotations
import chromadb
from chromadb.config import Settings
from .base import Chunk


def get_client(db_path: str = "./chroma_db") -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=db_path,
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(client: chromadb.ClientAPI, course_id: str) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=f"llm_{course_id.replace('.', '_')}",
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(collection: chromadb.Collection, chunks: list[Chunk]) -> None:
    collection.upsert(
        ids=[c.id for c in chunks],
        embeddings=[c.embedding for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "source": c.source,
                "course_id": c.course_id,
                "doc_type": c.doc_type,
                **{k: str(v) for k, v in c.metadata.items()},
            }
            for c in chunks
        ],
    )


def fetch_by_ids(collection: chromadb.Collection, ids: list[str]) -> list[Chunk]:
    """Fetch chunks directly by their ChromaDB IDs (no embedding needed)."""
    if not ids:
        return []
    results = collection.get(
        ids=ids,
        include=["documents", "metadatas"],
    )
    return [
        Chunk(
            id=doc_id,
            text=text,
            source=meta.get("source", ""),
            course_id=meta.get("course_id", ""),
            doc_type=meta.get("doc_type", ""),
            metadata={k: v for k, v in meta.items() if k not in ("source", "course_id", "doc_type")},
            score=None,
        )
        for doc_id, text, meta in zip(
            results["ids"],
            results["documents"],
            results["metadatas"],
        )
    ]


def query(
    collection: chromadb.Collection,
    query_embedding: list[float],
    top_k: int = 8,
    where: dict | None = None,
) -> list[Chunk]:
    kwargs: dict = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)
    return [
        Chunk(
            id=doc_id,
            text=text,
            source=meta.get("source", ""),
            course_id=meta.get("course_id", ""),
            doc_type=meta.get("doc_type", ""),
            metadata={k: v for k, v in meta.items() if k not in ("source", "course_id", "doc_type")},
            score=1.0 - dist,  # cosine distance → similarity
        )
        for doc_id, text, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
