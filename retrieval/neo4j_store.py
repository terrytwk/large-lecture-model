"""Neo4j graph store for GraphRAG.

Schema
------
Node labels:
  (:Course   {id, name, term})
  (:Week     {id, number, label, course_id})
  (:Lecture  {id, number, title, date, course_id, duration_sec, panopto_id})
  (:Topic    {id, name, course_id, description})
  (:Assignment {id, name, type, due_at, course_id, protected, points_possible})
  (:Material {id, display_name, doc_type, source, course_id})

Relationship types:
  (Course)-[:HAS_WEEK]->(Week)
  (Week)-[:HAS_LECTURE]->(Lecture)
  (Week)-[:HAS_ASSIGNMENT]->(Assignment)
  (Lecture)-[:COVERS]->(Topic)
  (Assignment)-[:TESTS]->(Topic)
  (Topic)-[:PREREQ_OF]->(Topic)       # prereq -> advanced
  (Lecture)-[:HAS_MATERIAL]->(Material)
  (Assignment)-[:HAS_MATERIAL]->(Material)

Material IDs match ChromaDB chunk IDs so the graph retriever can call
vector_store.fetch_by_ids() directly without an extra embedding step.
"""
from __future__ import annotations

from neo4j import Driver, GraphDatabase


# ── Connection ────────────────────────────────────────────────────────────────

def connect(uri: str, user: str, password: str) -> Driver:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def create_indexes(driver: Driver) -> None:
    """Create uniqueness constraints and a full-text index. Idempotent."""
    with driver.session() as s:
        for label in ("Course", "Week", "Lecture", "Topic", "Assignment", "Material"):
            s.run(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
        s.run(
            """CREATE FULLTEXT INDEX topicNameIdx IF NOT EXISTS
               FOR (t:Topic) ON EACH [t.name]"""
        )


# ── Upserts (all MERGE — idempotent, safe to re-run) ─────────────────────────

def upsert_course(driver: Driver, course_id: str, name: str, term: str = "") -> None:
    with driver.session() as s:
        s.run(
            "MERGE (c:Course {id:$id}) SET c.name=$name, c.term=$term",
            id=course_id, name=name, term=term,
        )


def upsert_week(driver: Driver, course_id: str, number: int, label: str) -> str:
    week_id = f"{course_id}-w{number}"
    with driver.session() as s:
        s.run(
            "MERGE (w:Week {id:$id}) SET w.number=$num, w.label=$label, w.course_id=$cid",
            id=week_id, num=number, label=label, cid=course_id,
        )
        s.run(
            "MATCH (c:Course {id:$cid}),(w:Week {id:$wid}) MERGE (c)-[:HAS_WEEK]->(w)",
            cid=course_id, wid=week_id,
        )
    return week_id


def upsert_lecture(
    driver: Driver,
    lecture_id: str,
    number: int,
    title: str,
    date: str,
    course_id: str,
    week_number: int,
    duration_sec: float = 0.0,
    panopto_id: str = "",
) -> None:
    week_id = f"{course_id}-w{week_number}"
    with driver.session() as s:
        s.run(
            """MERGE (l:Lecture {id:$id})
               SET l.number=$num, l.title=$title, l.date=$date,
                   l.course_id=$cid, l.duration_sec=$dur, l.panopto_id=$pid""",
            id=lecture_id, num=number, title=title, date=date,
            cid=course_id, dur=duration_sec, pid=panopto_id,
        )
        s.run(
            "MATCH (w:Week {id:$wid}),(l:Lecture {id:$lid}) MERGE (w)-[:HAS_LECTURE]->(l)",
            wid=week_id, lid=lecture_id,
        )


def upsert_topic(
    driver: Driver,
    topic_id: str,
    name: str,
    course_id: str,
    description: str = "",
) -> None:
    with driver.session() as s:
        s.run(
            "MERGE (t:Topic {id:$id}) SET t.name=$name, t.course_id=$cid, t.description=$desc",
            id=topic_id, name=name, cid=course_id, desc=description,
        )


def upsert_assignment(
    driver: Driver,
    assignment_id: str,
    name: str,
    assignment_type: str,
    due_at: str,
    course_id: str,
    week_number: int | None,
    protected: bool = False,
    points_possible: float = 0.0,
) -> None:
    with driver.session() as s:
        s.run(
            """MERGE (a:Assignment {id:$id})
               SET a.name=$name, a.type=$type, a.due_at=$due,
                   a.course_id=$cid, a.protected=$prot, a.points_possible=$pts""",
            id=assignment_id, name=name, type=assignment_type, due=due_at,
            cid=course_id, prot=protected, pts=points_possible,
        )
        if week_number is not None:
            s.run(
                "MATCH (w:Week {id:$wid}),(a:Assignment {id:$aid}) MERGE (w)-[:HAS_ASSIGNMENT]->(a)",
                wid=f"{course_id}-w{week_number}", aid=assignment_id,
            )


def upsert_material(
    driver: Driver,
    material_id: str,
    display_name: str,
    doc_type: str,
    source: str,
    course_id: str,
) -> None:
    with driver.session() as s:
        s.run(
            """MERGE (m:Material {id:$id})
               SET m.display_name=$name, m.doc_type=$dtype, m.source=$src, m.course_id=$cid""",
            id=material_id, name=display_name, dtype=doc_type, src=source, cid=course_id,
        )


# ── Relationship helpers ──────────────────────────────────────────────────────

def lecture_covers_topic(driver: Driver, lecture_id: str, topic_id: str) -> None:
    with driver.session() as s:
        s.run(
            "MATCH (l:Lecture {id:$lid}),(t:Topic {id:$tid}) MERGE (l)-[:COVERS]->(t)",
            lid=lecture_id, tid=topic_id,
        )


def assignment_tests_topic(driver: Driver, assignment_id: str, topic_id: str) -> None:
    with driver.session() as s:
        s.run(
            "MATCH (a:Assignment {id:$aid}),(t:Topic {id:$tid}) MERGE (a)-[:TESTS]->(t)",
            aid=assignment_id, tid=topic_id,
        )


def topic_prereq_of(driver: Driver, prereq_id: str, advanced_id: str) -> None:
    """Edge direction: (prereq)-[:PREREQ_OF]->(advanced)."""
    with driver.session() as s:
        s.run(
            "MATCH (p:Topic {id:$pid}),(a:Topic {id:$aid}) MERGE (p)-[:PREREQ_OF]->(a)",
            pid=prereq_id, aid=advanced_id,
        )


def lecture_has_material(driver: Driver, lecture_id: str, material_id: str) -> None:
    with driver.session() as s:
        s.run(
            "MATCH (l:Lecture {id:$lid}),(m:Material {id:$mid}) MERGE (l)-[:HAS_MATERIAL]->(m)",
            lid=lecture_id, mid=material_id,
        )


def assignment_has_material(driver: Driver, assignment_id: str, material_id: str) -> None:
    with driver.session() as s:
        s.run(
            "MATCH (a:Assignment {id:$aid}),(m:Material {id:$mid}) MERGE (a)-[:HAS_MATERIAL]->(m)",
            aid=assignment_id, mid=material_id,
        )


# ── Query helpers (called by GraphRetriever) ──────────────────────────────────

def get_topics_for_query(
    driver: Driver, topic_names: list[str], course_id: str
) -> list[dict]:
    """Return Topic nodes whose name contains any of the query terms (case-insensitive)."""
    with driver.session() as s:
        result = s.run(
            """MATCH (t:Topic)
               WHERE t.course_id = $cid
                 AND any(name IN $names WHERE toLower(t.name) CONTAINS toLower(name))
               RETURN t.id AS id, t.name AS name""",
            cid=course_id, names=topic_names,
        )
        return [dict(r) for r in result]


def get_material_ids_for_topics(driver: Driver, topic_ids: list[str]) -> list[str]:
    """Material IDs reachable from Topics via Lectures (COVERS) or Assignments (TESTS)."""
    with driver.session() as s:
        result = s.run(
            """MATCH (t:Topic)<-[:COVERS|TESTS]-(n)-[:HAS_MATERIAL]->(m:Material)
               WHERE t.id IN $tids
               RETURN DISTINCT m.id AS id""",
            tids=topic_ids,
        )
        return [r["id"] for r in result]


def get_prereq_topics(driver: Driver, topic_ids: list[str]) -> list[dict]:
    """Walk up to 2 hops back along PREREQ_OF to find prerequisite topics."""
    with driver.session() as s:
        result = s.run(
            """MATCH (p:Topic)-[:PREREQ_OF*1..2]->(t:Topic)
               WHERE t.id IN $tids
               RETURN DISTINCT p.id AS id, p.name AS name""",
            tids=topic_ids,
        )
        return [dict(r) for r in result]


def get_full_subgraph(driver: Driver, course_id: str) -> dict:
    """All nodes + edges for a course — consumed by the /api/graph endpoint."""
    with driver.session() as s:
        nodes_res = s.run(
            """MATCH (n)
               WHERE n.course_id = $cid
                 AND (n:Topic OR n:Lecture OR n:Assignment OR n:Week)
               RETURN
                 labels(n)[0]   AS label,
                 n.id           AS id,
                 n.name         AS name,
                 n.title        AS title,
                 n.number       AS number,
                 n.due_at       AS due_at,
                 n.description  AS description""",
            cid=course_id,
        )
        nodes = [dict(r) for r in nodes_res]

        edges_res = s.run(
            """MATCH (a)-[r]->(b)
               WHERE a.course_id = $cid AND b.course_id = $cid
                 AND type(r) IN
                     ['COVERS','TESTS','PREREQ_OF','HAS_LECTURE','HAS_ASSIGNMENT']
               RETURN a.id AS source, b.id AS target, type(r) AS type""",
            cid=course_id,
        )
        edges = [dict(r) for r in edges_res]

    return {"nodes": nodes, "edges": edges}
