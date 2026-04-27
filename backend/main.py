"""FastAPI backend — serves chatbot and dashboard APIs."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import chat, assignments, materials

app = FastAPI(title="Large Lecture Model API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
app.include_router(materials.router, prefix="/materials", tags=["materials"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
