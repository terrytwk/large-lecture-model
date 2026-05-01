"""Shared FastAPI dependency providers (loaded once, reused across requests)."""
from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path
import yaml
from retrieval.vector_store import get_client, get_collection
from retrieval.vector_retriever import VectorRetriever
from llm.client import LLMClient


@lru_cache
def get_settings() -> dict:
    return yaml.safe_load(Path("config/settings.yaml").read_text())


@lru_cache
def get_courses() -> dict:
    return yaml.safe_load(Path("config/courses.yaml").read_text())


def get_retriever(course_id: str = "6.1220") -> VectorRetriever:
    s = get_settings()
    collection = get_collection(get_client(s["chroma_db_path"]), course_id)
    return VectorRetriever(
        collection=collection,
        embed_model=s["embedding"]["model"],
        device=s["embedding"]["device"],
    )


def get_llm_client() -> LLMClient:
    s = get_settings()
    return LLMClient(model=s["llm"]["model"], max_tokens=s["llm"]["max_tokens"])


def get_neo4j_driver():
    """Return a Neo4j Driver, or None if Neo4j is not configured / reachable.

    Routes that depend on this should catch None and return 503.
    Decorated with lru_cache so the driver is reused across requests.
    """
    s = get_settings()
    cfg = s.get("neo4j", {})
    uri = cfg.get("uri", "bolt://localhost:7687")
    user = cfg.get("user", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD") or cfg.get("password", "")
    try:
        from retrieval.neo4j_store import connect
        return connect(uri, user, password)
    except Exception:
        return None
