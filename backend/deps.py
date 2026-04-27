"""Shared FastAPI dependency providers (loaded once, reused across requests)."""
from __future__ import annotations
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
