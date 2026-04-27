"""GET /assignments — assignment list with deadlines and submission status."""
from fastapi import APIRouter
from backend.deps import get_courses

router = APIRouter()


@router.get("")
def list_assignments(course_id: str = "6.1220") -> dict:
    # TODO: query SQLite (backend/db.py) once Canvas + Gradescope data is ingested
    course_cfg = get_courses()["courses"].get(course_id, {})
    return {
        "course_id": course_id,
        "course_name": course_cfg.get("name", ""),
        "assignments": [],
    }
