"""GET /materials/search — semantic search over course materials."""
from fastapi import APIRouter
from backend.deps import get_retriever

router = APIRouter()


@router.get("/search")
def search(q: str, course_id: str = "6.1220", doc_type: str | None = None) -> dict:
    retriever = get_retriever(course_id)
    filters = {"doc_type": doc_type} if doc_type else None
    chunks = retriever.retrieve(q, top_k=8, filters=filters)
    return {
        "results": [
            {
                "id": c.id,
                "text": c.text[:400],
                "source": c.source,
                "doc_type": c.doc_type,
                "metadata": c.metadata,
                "score": c.score,
            }
            for c in chunks
        ]
    }
