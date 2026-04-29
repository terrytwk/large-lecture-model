"""POST /chat — streaming RAG chat via Server-Sent Events."""
from __future__ import annotations
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.deps import get_retriever, get_llm_client, get_settings, get_courses
from llm.guardrails import check
from llm.prompts import CHAT_SYSTEM, SOURCE_TEMPLATE
from retrieval.query_parser import parse_lecture_number, lecture_canvas_names

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    course_id: str = "6.1220"
    history: list[dict] = []


@router.post("")
def chat(req: ChatRequest) -> StreamingResponse:
    settings = get_settings()
    course_cfg = get_courses()["courses"][req.course_id]

    blocked, reason = check(
        req.query,
        course_cfg.get("protected_assignments", []),
        settings["guardrails"]["sensitivity"],
    )
    if blocked:
        def blocked_gen():
            yield f"data: {json.dumps({'type': 'delta', 'text': reason})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(blocked_gen(), media_type="text/event-stream")

    retriever = get_retriever(req.course_id)
    chunks = retriever.retrieve(req.query, top_k=settings["retrieval"]["top_k"])

    # If the query names a specific lecture, inject its notes/slides directly
    # so they aren't crowded out by other high-scoring chunks.
    lecture_num = parse_lecture_number(req.query)
    if lecture_num is not None:
        try:
            extra = retriever.retrieve(
                req.query,
                top_k=4,
                filters={"name": {"$in": lecture_canvas_names(lecture_num)}},
            )
            if extra:
                seen = {c.id for c in extra}
                chunks = extra + [c for c in chunks if c.id not in seen]
        except Exception:
            pass  # fall back to unaugmented results

    context = "\n".join(
        SOURCE_TEMPLATE.format(
            source=c.source,
            doc_type=c.doc_type,
            name=c.metadata.get("name") or c.metadata.get("lecture_title", ""),
            text=c.text,
        )
        for c in chunks
    )
    sources = [
        {
            "id": c.id,
            "source": c.source,
            "doc_type": c.doc_type,
            "name": c.metadata.get("name") or c.metadata.get("lecture_title", ""),
            "score": c.score,
        }
        for c in chunks
    ]

    system = CHAT_SYSTEM.format(course_name=course_cfg["name"])
    messages = req.history + [
        {"role": "user", "content": f"{context}\n\nQuestion: {req.query}"}
    ]
    llm = get_llm_client()

    def stream():
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        for delta in llm.stream(system=system, messages=messages):
            yield f"data: {json.dumps({'type': 'delta', 'text': delta})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
