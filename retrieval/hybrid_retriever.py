"""Hybrid retriever: merges vector and graph results with weighted scoring."""
from __future__ import annotations
from .base import BaseRetriever, Chunk
from .vector_retriever import VectorRetriever
from .graph_retriever import GraphRetriever


class HybridRetriever(BaseRetriever):
    def __init__(
        self,
        vector_retriever: VectorRetriever,
        graph_retriever: GraphRetriever,
        vector_weight: float = 0.7,
    ) -> None:
        self.vector = vector_retriever
        self.graph = graph_retriever
        self.vector_weight = vector_weight
        self.graph_weight = 1.0 - vector_weight

    def retrieve(self, query: str, top_k: int = 8, filters: dict | None = None) -> list[Chunk]:
        v_results = self.vector.retrieve(query, top_k=top_k, filters=filters)
        g_results = self.graph.retrieve(query, top_k=top_k, filters=filters)

        merged: dict[str, Chunk] = {}
        for chunk in v_results:
            merged[chunk.id] = chunk
            if chunk.score is not None:
                chunk.score *= self.vector_weight

        for chunk in g_results:
            if chunk.id in merged:
                if merged[chunk.id].score is not None and chunk.score is not None:
                    merged[chunk.id].score += chunk.score * self.graph_weight
            else:
                if chunk.score is not None:
                    chunk.score *= self.graph_weight
                merged[chunk.id] = chunk

        return sorted(merged.values(), key=lambda c: c.score or 0.0, reverse=True)[:top_k]
