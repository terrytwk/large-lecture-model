"""FastAPI backend — serves chatbot and dashboard APIs."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import chat, assignments, materials, graph
from backend.db import sync_canvas_assignments
from backend.deps import get_courses


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed SQLite from any already-ingested JSONL files on startup.
    courses = get_courses().get("courses", {})
    for course_id in courses:
        n = sync_canvas_assignments(course_id)
        if n:
            print(f"[startup] seeded {n} assignments for {course_id}")
    yield


app = FastAPI(title="Large Lecture Model API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
app.include_router(materials.router, prefix="/materials", tags=["materials"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
