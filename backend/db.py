"""SQLite database for structured assignment and deadline data."""
from __future__ import annotations
from sqlalchemy import Boolean, Column, Float, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True)
    course_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    source = Column(String)          # "canvas" | "gradescope"
    due_at = Column(String)
    submitted = Column(Boolean, default=False)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    topics = Column(String)          # JSON-encoded list


_engine = None


def get_engine(db_url: str = "sqlite:///./llm.db"):
    global _engine
    if _engine is None:
        _engine = create_engine(db_url)
        Base.metadata.create_all(_engine)
    return _engine


def get_session(db_url: str = "sqlite:///./llm.db") -> Session:
    return Session(get_engine(db_url))
