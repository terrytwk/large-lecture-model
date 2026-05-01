"""Build (or refresh) the Neo4j knowledge graph for one course.

What it does
------------
1. Creates Course, Week, Lecture, Assignment, Material nodes from the
   already-ingested JSONL files + llm.db.
2. Uses the LLM to tag each lecture with the algorithmic Topics it covers,
   and each (non-protected) assignment with the Topics it tests.
3. Asks the LLM to infer PREREQ_OF edges between all discovered Topics.
4. All writes use MERGE so re-runs are fully idempotent.

Run
---
    python -m process.graph_builder --course-id 6.1220

Requires Neo4j running on bolt://localhost:7687 (or override via settings.yaml).
Set NEO4J_PASSWORD env var before running.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from llm.client import LLMClient
from retrieval import neo4j_store


# ── LLM prompt templates ──────────────────────────────────────────────────────

_LECTURE_TOPICS_SYSTEM = """\
You are a computer science education assistant.
Given a lecture title and a short excerpt from its transcript, list the main
algorithmic topics covered. Be specific — use standard CS terminology.

Return ONLY a valid JSON array, no markdown, no explanation:
[{"name": "Topic Name", "description": "One sentence."}]"""

_ASSIGNMENT_TOPICS_SYSTEM = """\
You are a computer science education assistant.
Given an assignment name from an algorithms course, list the algorithmic topics
it likely tests. Use the assignment name as your only signal.

Return ONLY a valid JSON array of strings, no markdown:
["Topic Name 1", "Topic Name 2"]"""

_PREREQ_SYSTEM = """\
You are an algorithms professor. Given the list of topics from an algorithms course,
identify direct prerequisite relationships: A is a prerequisite of B means students
must understand A before tackling B.

Only include clear, well-established dependencies. Skip if uncertain.

Return ONLY a valid JSON array, no markdown:
[{"prereq": "Topic A", "advanced": "Topic B"}]"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json(text: str) -> Any:
    """Strip markdown fences and parse the first JSON value."""
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    start = next((i for i, c in enumerate(text) if c in "[{"), 0)
    return json.loads(text[start:])


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _week_from_label(label: str) -> int | None:
    m = re.search(r"Week\s+(\d+)", label)
    return int(m.group(1)) if m else None


def _lecture_num_from_name(name: str) -> int | None:
    """'L03: Amortized Analysis (Tue 2/10/2026)' → 3"""
    m = re.match(r"L(\d+):", name)
    return int(m.group(1)) if m else None


def _assignment_type(name: str) -> str:
    n = name.lower()
    if "problem set" in n or re.search(r"\bps\s*\d", n):
        return "problem_set"
    if "warm-up" in n or "warmup" in n:
        return "warmup"
    if "quiz" in n:
        return "quiz"
    if "exam" in n or "final" in n:
        return "exam"
    return "other"


def _week_from_due_at(due_at: str, spring_break_after_week: int = 7) -> int | None:
    """Estimate week number from ISO due_at string.

    6.1220 Spring 2026 starts Feb 2. Week 8 is spring break (no assignments).
    Assignments due after spring break jump from week 7 to week 9 in the DB.
    """
    if not due_at:
        return None
    try:
        due_dt = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
        week1_start = datetime(2026, 2, 2, tzinfo=timezone.utc)
        delta_days = (due_dt - week1_start).days
        if delta_days < 0:
            return None
        raw_week = delta_days // 7 + 1
        # Shift by 1 to skip spring break week
        if raw_week > spring_break_after_week:
            raw_week += 1
        return min(max(1, raw_week), 12)
    except Exception:
        return None


# ── Main builder ──────────────────────────────────────────────────────────────

def build_graph(course_id: str, settings: dict, llm: LLMClient) -> None:
    # Connect to Neo4j
    neo4j_cfg = settings["neo4j"]
    password = os.environ.get("NEO4J_PASSWORD") or neo4j_cfg.get("password", "")
    driver = neo4j_store.connect(neo4j_cfg["uri"], neo4j_cfg["user"], password)
    neo4j_store.create_indexes(driver)

    # Load course config
    courses_cfg = yaml.safe_load(Path("config/courses.yaml").read_text())
    course_cfg = courses_cfg["courses"][course_id]
    course_name = course_cfg["name"]
    protected_prefixes: list[str] = course_cfg.get("protected_assignments", [])

    def is_protected(name: str) -> bool:
        return any(p.lower() in name.lower() for p in protected_prefixes)

    # Load raw JSONL files
    canvas_path = Path(f"data/raw/canvas/{course_id}/documents.jsonl")
    panopto_path = Path(f"data/raw/panopto/{course_id}/documents.jsonl")

    canvas_docs: list[dict] = (
        [json.loads(l) for l in canvas_path.read_text().splitlines() if l.strip()]
        if canvas_path.exists() else []
    )
    panopto_docs: list[dict] = (
        [json.loads(l) for l in panopto_path.read_text().splitlines() if l.strip()]
        if panopto_path.exists() else []
    )

    # ── 1. Course ─────────────────────────────────────────────────────────────
    neo4j_store.upsert_course(driver, course_id, course_name, "Spring 2026")
    print(f"[graph] Course: {course_name} ({course_id})")

    # ── 2. Weeks (from Canvas module labels) ──────────────────────────────────
    week_labels: set[str] = set()
    for doc in canvas_docs:
        label = doc.get("metadata", {}).get("module", "")
        if "Week" in label:
            week_labels.add(label)

    week_label_to_num: dict[str, int] = {}
    for label in sorted(week_labels):
        n = _week_from_label(label)
        if n:
            neo4j_store.upsert_week(driver, course_id, n, label)
            week_label_to_num[label] = n
    print(f"[graph] Weeks: {sorted(week_label_to_num.values())}")

    # ── 3. Build lecture-number → week-number map from Canvas slide filenames ─
    # e.g. "L06_Hashing-I.pdf" in "Week 4: February 23–March 1" → L6 = week 4
    lec_to_week: dict[int, int] = {}
    for doc in canvas_docs:
        if doc.get("doc_type") != "slide":
            continue
        fn = doc.get("metadata", {}).get("display_name", "")
        lm = re.match(r"L(\d+)_", fn)
        if not lm:
            continue
        lnum = int(lm.group(1))
        module = doc.get("metadata", {}).get("module", "")
        wnum = week_label_to_num.get(module)
        if wnum and lnum not in lec_to_week:
            lec_to_week[lnum] = wnum

    # ── 4. Lectures (from Panopto transcripts) ────────────────────────────────
    # Only include numbered lectures (L01–L19), not review/prob sessions
    lecture_docs: dict[int, dict] = {}
    for pdoc in panopto_docs:
        name = pdoc.get("metadata", {}).get("name", "")
        lnum = _lecture_num_from_name(name)
        if lnum:
            lecture_docs[lnum] = pdoc

    for lnum, pdoc in sorted(lecture_docs.items()):
        name = pdoc["metadata"]["name"]
        # "L06: Hashing I (Tue 2/24/2026)" → title="Hashing I", date="2/24/2026"
        title_m = re.match(r"L\d+:\s*(.+?)\s*\(", name)
        title = title_m.group(1) if title_m else name
        date_m = re.search(r"\((?:Tue|Thu|Mon|Wed|Fri)\s+(\d+/\d+/\d+)\)", name)
        date = date_m.group(1) if date_m else ""
        week_num = lec_to_week.get(lnum, 1)

        neo4j_store.upsert_lecture(
            driver,
            lecture_id=pdoc["id"],
            number=lnum,
            title=title,
            date=date,
            course_id=course_id,
            week_number=week_num,
            duration_sec=pdoc.get("metadata", {}).get("duration_sec", 0.0),
            panopto_id=pdoc.get("metadata", {}).get("session_id", ""),
        )

    print(f"[graph] Lectures: {len(lecture_docs)}")

    # ── 5. Materials ──────────────────────────────────────────────────────────
    # Canvas slides
    for doc in canvas_docs:
        if doc.get("doc_type") not in ("slide", "assignment", "practice", "announcement"):
            continue
        meta = doc.get("metadata", {})
        neo4j_store.upsert_material(
            driver,
            material_id=doc["id"],
            display_name=meta.get("display_name", ""),
            doc_type=doc["doc_type"],
            source="canvas",
            course_id=course_id,
        )
        # Link slides to their lecture
        fn = meta.get("display_name", "")
        lm = re.match(r"L(\d+)_", fn)
        if lm:
            lnum = int(lm.group(1))
            if lnum in lecture_docs:
                neo4j_store.lecture_has_material(driver, lecture_docs[lnum]["id"], doc["id"])

    # Panopto transcripts (the transcript IS the primary material for the lecture)
    for pdoc in panopto_docs:
        name = pdoc.get("metadata", {}).get("name", "")
        neo4j_store.upsert_material(
            driver,
            material_id=pdoc["id"],
            display_name=name,
            doc_type="transcript",
            source="panopto",
            course_id=course_id,
        )
        lnum = _lecture_num_from_name(name)
        if lnum and lnum in lecture_docs:
            neo4j_store.lecture_has_material(driver, lecture_docs[lnum]["id"], pdoc["id"])

    print(f"[graph] Materials: {len(canvas_docs) + len(panopto_docs)} documents")

    # ── 6. Assignments (from llm.db which is kept current by the backend) ─────
    conn = sqlite3.connect("llm.db")
    db_rows = conn.execute(
        "SELECT id, name, due_at FROM assignments WHERE course_id=?", (course_id,)
    ).fetchall()
    conn.close()

    for aid, aname, due_at in db_rows:
        neo4j_store.upsert_assignment(
            driver,
            assignment_id=aid,
            name=aname,
            assignment_type=_assignment_type(aname),
            due_at=due_at or "",
            course_id=course_id,
            week_number=_week_from_due_at(due_at),
            protected=is_protected(aname),
        )

    print(f"[graph] Assignments: {len(db_rows)}")

    # ── 7. LLM topic tagging — lectures ──────────────────────────────────────
    print("\n[graph] Tagging lectures with topics via LLM …")
    all_topics: dict[str, str] = {}  # name → topic_id

    def ensure_topic(name: str, description: str = "") -> str:
        topic_id = f"{course_id}-{_slugify(name)}"
        if name not in all_topics:
            neo4j_store.upsert_topic(driver, topic_id, name, course_id, description)
            all_topics[name] = topic_id
        return all_topics[name]

    for lnum, pdoc in sorted(lecture_docs.items()):
        lname = pdoc["metadata"]["name"]
        excerpt = pdoc.get("content", "")[:600]
        try:
            raw = llm.complete(
                _LECTURE_TOPICS_SYSTEM,
                f"Lecture: {lname}\n\nTranscript excerpt:\n{excerpt}",
            )
            items = _parse_json(raw)
        except Exception as e:
            print(f"  L{lnum:02d}: LLM error ({e})")
            continue

        tagged: list[str] = []
        for item in items:
            if isinstance(item, dict):
                tname = item.get("name", "")
                tdesc = item.get("description", "")
            else:
                tname, tdesc = str(item), ""
            if not tname:
                continue
            tid = ensure_topic(tname, tdesc)
            neo4j_store.lecture_covers_topic(driver, pdoc["id"], tid)
            tagged.append(tname)
        print(f"  L{lnum:02d} ({lname.split(':')[1].split('(')[0].strip()}): {tagged}")

    # ── 8. LLM topic tagging — assignments ───────────────────────────────────
    print("\n[graph] Tagging assignments with topics via LLM …")
    for aid, aname, _ in db_rows:
        if is_protected(aname):
            print(f"  {aname}: skipped (protected)")
            continue
        try:
            raw = llm.complete(_ASSIGNMENT_TOPICS_SYSTEM, f"Assignment: {aname}")
            items = _parse_json(raw)
        except Exception as e:
            print(f"  {aname}: LLM error ({e})")
            continue

        tagged = []
        for item in items:
            tname = str(item) if not isinstance(item, dict) else item.get("name", "")
            if tname:
                tid = ensure_topic(tname)
                neo4j_store.assignment_tests_topic(driver, aid, tid)
                tagged.append(tname)
        print(f"  {aname}: {tagged}")

    # ── 9. Prerequisite relationships ─────────────────────────────────────────
    print(f"\n[graph] Building PREREQ_OF edges across {len(all_topics)} topics …")
    topic_list_text = "\n".join(f"- {t}" for t in sorted(all_topics))
    try:
        raw = llm.complete(_PREREQ_SYSTEM, f"Topics:\n{topic_list_text}")
        prereqs = _parse_json(raw)
        count = 0
        for rel in prereqs:
            p = rel.get("prereq", "")
            a = rel.get("advanced", "")
            if p in all_topics and a in all_topics:
                neo4j_store.topic_prereq_of(driver, all_topics[p], all_topics[a])
                count += 1
        print(f"  {count} PREREQ_OF edges written")
    except Exception as e:
        print(f"  Error: {e}")

    driver.close()
    print(f"\n[graph] ✓ Graph built for {course_id}  "
          f"({len(all_topics)} topics, {len(lecture_docs)} lectures, "
          f"{len(db_rows)} assignments)")
