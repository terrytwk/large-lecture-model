from __future__ import annotations
import chromadb
from .base import BaseRetriever, Chunk
from . import vector_store
from process.embedder import embed_query


class VectorRetriever(BaseRetriever):
    def __init__(
        self,
        collection: chromadb.Collection,
        embed_model: str = "BAAI/bge-small-en-v1.5",
        device: str = "cpu",
    ) -> None:
        self.collection = collection
        self.embed_model = embed_model
        self.device = device

    def retrieve(self, query: str, top_k: int = 8, filters: dict | None = None) -> list[Chunk]:
        q_emb = embed_query(query, self.embed_model, self.device)
        return vector_store.query(self.collection, q_emb, top_k=top_k, where=filters)
