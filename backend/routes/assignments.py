"""GET /assignments — assignment list with deadlines and submission status."""
import json
from fastapi import APIRouter
from backend.db import Assignment, get_session
from backend.deps import get_courses

router = APIRouter()


@router.get("")
def list_assignments(course_id: str = "6.1220") -> dict:
    course_cfg = get_courses()["courses"].get(course_id, {})

    with get_session() as session:
        rows = (
            session.query(Assignment)
            .filter(Assignment.course_id == course_id)
            .order_by(Assignment.due_at)
            .all()
        )

    assignments = [
        {
            "id": r.id,
            "name": r.name,
            "source": r.source,
            "due_at": r.due_at,
            "submitted": bool(r.submitted),
            "score": r.score,
            "max_score": r.max_score,
            "topics": json.loads(r.topics or "[]"),
            "html_url": r.html_url,
        }
        for r in rows
    ]

    return {
        "course_id": course_id,
        "course_name": course_cfg.get("name", ""),
        "assignments": assignments,
    }
