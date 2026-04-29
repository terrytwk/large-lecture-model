"""SQLite database for structured assignment and deadline data."""
from __future__ import annotations
import json
from pathlib import Path
from sqlalchemy import Boolean, Column, Float, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True)
    course_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    source = Column(String)           # "canvas" | "gradescope"
    due_at = Column(String)
    submitted = Column(Boolean, default=False)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    topics = Column(String)           # JSON-encoded list
    html_url = Column(String, nullable=True)


_engine = None


def get_engine(db_url: str = "sqlite:///./llm.db"):
    global _engine
    if _engine is None:
        _engine = create_engine(db_url)
        Base.metadata.create_all(_engine)
        _migrate(db_url)
    return _engine


def _migrate(db_url: str) -> None:
    """Add columns introduced after initial schema creation (safe no-op if exists)."""
    engine = create_engine(db_url)
    with engine.connect() as conn:
        cols = {
            r[1] for r in conn.execute(text("PRAGMA table_info(assignments)")).fetchall()
        }
        if "html_url" not in cols:
            conn.execute(text("ALTER TABLE assignments ADD COLUMN html_url TEXT"))
            conn.commit()


def get_session(db_url: str = "sqlite:///./llm.db") -> Session:
    return Session(get_engine(db_url))


def sync_canvas_assignments(course_id: str) -> int:
    """Read data/raw/canvas/{course_id}/documents.jsonl and upsert assignments into SQLite.

    Returns the number of rows upserted.
    """
    jsonl = Path(f"data/raw/canvas/{course_id}/documents.jsonl")
    if not jsonl.exists():
        return 0

    docs = [json.loads(line) for line in jsonl.read_text().splitlines() if line.strip()]
    # Only real assignment entries have a due_at in their metadata
    rows = [
        d for d in docs
        if d.get("doc_type") == "assignment" and d.get("metadata", {}).get("due_at")
    ]

    with get_session() as session:
        for doc in rows:
            meta = doc["metadata"]
            existing = session.get(Assignment, doc["id"])
            if existing is None:
                session.add(Assignment(
                    id=doc["id"],
                    course_id=doc["course_id"],
                    name=meta["name"],
                    source="canvas",
                    due_at=meta.get("due_at"),
                    submitted=False,
                    score=None,
                    max_score=meta.get("points_possible"),
                    topics=json.dumps([]),
                    html_url=meta.get("html_url"),
                ))
            else:
                # Preserve submitted/score/topics set by other sources; only refresh metadata.
                existing.name = meta["name"]
                existing.due_at = meta.get("due_at")
                existing.max_score = meta.get("points_possible")
                existing.html_url = meta.get("html_url")
        session.commit()

    return len(rows)
