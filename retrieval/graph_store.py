"""Concept graph for GraphRAG — placeholder using NetworkX for unit tests.

Production target: Neo4j via the official `neo4j` Python driver (bolt://localhost:7687).
Node labels: Topic, Lecture, Assignment, PiazzaThread, Course.
Relationship types: COVERS, ASSESSED_BY, DISCUSSED_IN, PREREQ_OF, BELONGS_TO.

This file will be replaced by neo4j_store.py once the Neo4j implementation lands.
"""
from __future__ import annotations
import json
from pathlib import Path
import networkx as nx


def build_graph() -> nx.DiGraph:
    return nx.DiGraph()


def add_topic(g: nx.DiGraph, name: str) -> None:
    g.add_node(name, type="topic")


def add_lecture(g: nx.DiGraph, lecture_id: str, title: str, week: int) -> None:
    g.add_node(lecture_id, type="lecture", title=title, week=week)


def add_assignment(g: nx.DiGraph, assignment_id: str, name: str, due_at: str) -> None:
    g.add_node(assignment_id, type="assignment", name=name, due_at=due_at)


def link(g: nx.DiGraph, src: str, dst: str, relation: str) -> None:
    g.add_edge(src, dst, relation=relation)


def topics_for_node(g: nx.DiGraph, node_id: str) -> list[str]:
    """Topic nodes reachable from a lecture or assignment via outgoing edges."""
    if node_id not in g:
        return []
    return [
        n for n in nx.descendants(g, node_id)
        if g.nodes[n].get("type") == "topic"
    ]


def nodes_covering_topic(g: nx.DiGraph, topic: str) -> list[dict]:
    """Lectures and assignments with a direct edge to this topic."""
    if topic not in g:
        return []
    return [
        {"id": pred, **g.nodes[pred]}
        for pred in g.predecessors(topic)
        if g.nodes[pred].get("type") in ("lecture", "assignment")
    ]


def save(g: nx.DiGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nx.node_link_data(g)), encoding="utf-8")


def load(path: Path) -> nx.DiGraph:
    return nx.node_link_graph(json.loads(path.read_text(encoding="utf-8")), directed=True)
