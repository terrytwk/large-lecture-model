"""Integration tests for vector retrieval (requires ChromaDB, no network)."""
import pytest
from retrieval.base import Chunk
from retrieval.vector_store import get_client, get_collection, upsert_chunks, query


@pytest.fixture
def collection(tmp_path):
    return get_collection(get_client(str(tmp_path / "chroma")), "test")


def _chunk(id: str, text: str) -> Chunk:
    return Chunk(id=id, text=text, source="manual", course_id="test", doc_type="slide", embedding=[0.1] * 384)


def test_upsert_and_query(collection):
    upsert_chunks(collection, [_chunk("c1", "dynamic programming")])
    results = query(collection, [0.1] * 384, top_k=1)
    assert len(results) == 1
    assert results[0].id == "c1"
