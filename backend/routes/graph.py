"""GET /graph — return the Neo4j concept subgraph for a course.

Response shape (React Flow compatible):
{
  "nodes": [{"id": str, "type": str, "data": {"label": str, ...}}],
  "edges": [{"id": str, "source": str, "target": str, "label": str}]
}
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver

from backend.deps import get_neo4j_driver
from retrieval import neo4j_store

router = APIRouter()

_NODE_TYPE_MAP = {
    "Topic": "topic",
    "Lecture": "lecture",
    "Assignment": "assignment",
    "Week": "week",
}


def _display_label(node: dict) -> str:
    """Pick the best human-readable label from a raw Neo4j node dict."""
    return (
        node.get("title")
        or node.get("name")
        or node.get("id", "")
    )


@router.get("")
def get_graph(
    course_id: str = "6.1220",
    driver: Driver = Depends(get_neo4j_driver),
) -> dict:
    try:
        raw = neo4j_store.get_full_subgraph(driver, course_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}") from exc

    nodes = [
        {
            "id": n["id"],
            "type": _NODE_TYPE_MAP.get(n.get("label", ""), "default"),
            "data": {
                "label": _display_label(n),
                "number": n.get("number"),
                "due_at": n.get("due_at"),
                "description": n.get("description"),
            },
        }
        for n in raw["nodes"]
    ]

    edges = [
        {
            "id": f"{e['source']}-{e['type']}-{e['target']}",
            "source": e["source"],
            "target": e["target"],
            "label": e["type"],
        }
        for e in raw["edges"]
    ]

    return {"nodes": nodes, "edges": edges}
