"""GraphRAG retriever: augments vector results with graph-traversed concept expansion.

Flow: query → vector search → read node IDs from chunk metadata →
      traverse graph to find related topics → fetch chunks for related nodes.
"""
from __future__ import annotations
import networkx as nx
from .base import BaseRetriever, Chunk
from .vector_retriever import VectorRetriever
from . import graph_store


class GraphRetriever(BaseRetriever):
    def __init__(self, vector_retriever: VectorRetriever, graph: nx.DiGraph) -> None:
        self.vector = vector_retriever
        self.graph = graph

    def retrieve(self, query: str, top_k: int = 8, filters: dict | None = None) -> list[Chunk]:
        initial = self.vector.retrieve(query, top_k=top_k // 2 or 4, filters=filters)

        # expand: for each retrieved node find related topics, then nodes covering those topics
        extra_queries: set[str] = set()
        for chunk in initial:
            node_id = chunk.metadata.get("node_id")
            if node_id and node_id in self.graph:
                for topic in graph_store.topics_for_node(self.graph, node_id):
                    extra_queries.add(topic)

        seen = {c.id for c in initial}
        if extra_queries:
            # use each topic as an additional query term to pull related chunks
            for topic in list(extra_queries)[:3]:
                for chunk in self.vector.retrieve(topic, top_k=4, filters=filters):
                    if chunk.id not in seen:
                        initial.append(chunk)
                        seen.add(chunk.id)

        return initial[:top_k]
