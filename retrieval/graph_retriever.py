"""GraphRAG retriever: augments vector results using Neo4j topic graph.

Flow
----
1. Vector search → baseline chunks (top_k // 2)
2. LLM extracts algorithmic topic keywords from the query
3. Cypher: find matching Topic nodes in Neo4j
4. Cypher: walk PREREQ_OF up to 2 hops to include prerequisite topics
5. Cypher: collect Material IDs reachable via COVERS / TESTS + HAS_MATERIAL
6. ChromaDB: fetch_by_ids() pulls those chunks directly (no re-embedding)
7. Merge, deduplicate, return top_k

If Neo4j is unavailable the retriever falls back to pure vector search so
the chat endpoint never breaks.
"""
from __future__ import annotations

import json
import re

from neo4j import Driver

from . import neo4j_store, vector_store
from .base import BaseRetriever, Chunk
from .vector_retriever import VectorRetriever

_EXTRACT_TOPICS_SYSTEM = (
    "Extract the main algorithmic topics mentioned in this query. "
    "Return ONLY a JSON array of short topic name strings, e.g. "
    '[\"Hashing\", \"Maximum Flow\"]. '
    "If the query contains no specific algorithm/data-structure topics, return []."
)


def _parse_topic_list(text: str) -> list[str]:
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    try:
        result = json.loads(text)
        return [t for t in result if isinstance(t, str)]
    except Exception:
        return []


class GraphRetriever(BaseRetriever):
    def __init__(
        self,
        vector_retriever: VectorRetriever,
        driver: Driver,
        llm_client,
        course_id: str = "6.1220",
    ) -> None:
        self.vector = vector_retriever
        self.driver = driver
        self.llm = llm_client
        self.course_id = course_id

    def retrieve(
        self, query: str, top_k: int = 8, filters: dict | None = None
    ) -> list[Chunk]:
        # ── 1. Vector baseline ──────────────────────────────────────────────
        initial = self.vector.retrieve(query, top_k=max(top_k // 2, 4), filters=filters)
        seen: set[str] = {c.id for c in initial}
        results: list[Chunk] = list(initial)

        # ── 2. Extract query topics via LLM ─────────────────────────────────
        try:
            raw = self.llm.complete(_EXTRACT_TOPICS_SYSTEM, query)
            query_topics = _parse_topic_list(raw)
        except Exception:
            return results[:top_k]

        if not query_topics:
            return results[:top_k]

        # ── 3. Match Topic nodes in Neo4j ────────────────────────────────────
        try:
            matched = neo4j_store.get_topics_for_query(
                self.driver, query_topics, self.course_id
            )
        except Exception:
            return results[:top_k]

        if not matched:
            # Fall back: run extra vector searches on each topic name
            for tname in query_topics[:3]:
                for chunk in self.vector.retrieve(tname, top_k=3, filters=filters):
                    if chunk.id not in seen:
                        results.append(chunk)
                        seen.add(chunk.id)
            return results[:top_k]

        topic_ids = [t["id"] for t in matched]

        # ── 4. Expand with prerequisite topics ───────────────────────────────
        try:
            prereqs = neo4j_store.get_prereq_topics(self.driver, topic_ids)
        except Exception:
            prereqs = []
        all_topic_ids = list(set(topic_ids + [t["id"] for t in prereqs]))

        # ── 5. Resolve to Material IDs reachable from topics ─────────────────
        try:
            material_ids = neo4j_store.get_material_ids_for_topics(
                self.driver, all_topic_ids
            )
        except Exception:
            material_ids = []

        # ── 6. Fetch chunks from ChromaDB by ID (no re-embedding needed) ─────
        if material_ids:
            fetched = vector_store.fetch_by_ids(
                self.vector.collection, material_ids[:12]
            )
            for chunk in fetched:
                if chunk.id not in seen:
                    chunk.score = 0.75  # graph-sourced chunks get a fixed relevance
                    results.append(chunk)
                    seen.add(chunk.id)

        # ── 7. Also do direct vector search on matched topic names ────────────
        for t in matched[:3]:
            for chunk in self.vector.retrieve(t["name"], top_k=3, filters=filters):
                if chunk.id not in seen:
                    results.append(chunk)
                    seen.add(chunk.id)

        return results[:top_k]
