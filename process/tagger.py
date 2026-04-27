"""LLM-assisted topic tagging for assignments and announcements."""
from __future__ import annotations
import json
from retrieval.base import Chunk

_SYSTEM = (
    "You extract topic tags from course content. "
    "Return a JSON array of 3-8 short topic strings (e.g. 'dynamic programming', 'graph BFS'). "
    "JSON only, no explanation."
)


def tag_chunk(chunk: Chunk, client: "LLMClient") -> list[str]:  # noqa: F821
    if chunk.doc_type not in ("assignment", "announcement"):
        return []
    response = client.complete(system=_SYSTEM, user=chunk.text[:2000])
    try:
        tags = json.loads(response)
        return [t for t in tags if isinstance(t, str)]
    except (json.JSONDecodeError, TypeError):
        return []
