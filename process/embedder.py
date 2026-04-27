"""HuggingFace sentence-transformers embedding wrapper (local, no API cost)."""
from __future__ import annotations
from sentence_transformers import SentenceTransformer
from retrieval.base import Chunk

_cache: dict[str, SentenceTransformer] = {}


def _get_model(model_name: str, device: str) -> SentenceTransformer:
    key = f"{model_name}:{device}"
    if key not in _cache:
        _cache[key] = SentenceTransformer(model_name, device=device)
    return _cache[key]


def embed_chunks(
    chunks: list[Chunk],
    model_name: str = "BAAI/bge-small-en-v1.5",
    device: str = "cpu",
    batch_size: int = 32,
) -> list[Chunk]:
    model = _get_model(model_name, device)
    embeddings = model.encode(
        [c.text for c in chunks],
        batch_size=batch_size,
        show_progress_bar=True,
    )
    for chunk, emb in zip(chunks, embeddings):
        chunk.embedding = emb.tolist()
    return chunks


def embed_query(
    query: str,
    model_name: str = "BAAI/bge-small-en-v1.5",
    device: str = "cpu",
) -> list[float]:
    return _get_model(model_name, device).encode(query).tolist()
