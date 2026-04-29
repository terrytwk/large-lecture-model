"""Splits RawDocuments into Chunks with metadata preserved."""
from __future__ import annotations
import re
from retrieval.base import Chunk
from ingest.base import RawDocument

CHUNK_SIZE = 512   # approximate word count per chunk
OVERLAP = 50       # word overlap between adjacent chunks


def chunk_documents(docs: list[RawDocument]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in docs:
        if doc.doc_type == "transcript":
            chunks.extend(_chunk_transcript(doc))
        elif doc.doc_type in ("slide", "file"):
            chunks.extend(_chunk_text(doc))
        else:
            # assignments, announcements, posts: single chunk each
            chunks.append(_make_chunk(doc, doc.content, 0))
    return chunks


def _chunk_text(doc: RawDocument) -> list[Chunk]:
    words = doc.content.split()
    chunks: list[Chunk] = []
    i, idx = 0, 0
    while i < len(words):
        window = words[i : i + CHUNK_SIZE]
        chunks.append(_make_chunk(doc, " ".join(window), idx))
        i += CHUNK_SIZE - OVERLAP
        idx += 1
    return chunks


def _chunk_transcript(doc: RawDocument) -> list[Chunk]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", doc.content) if p.strip()]
    chunks: list[Chunk] = []
    buffer: list[str] = []
    word_count = 0
    idx = 0
    for para in paragraphs:
        words = para.split()
        if word_count + len(words) > CHUNK_SIZE and buffer:
            chunks.append(_make_chunk(doc, " ".join(buffer), idx))
            buffer, word_count, idx = [], 0, idx + 1
        buffer.append(para)
        word_count += len(words)
    if buffer:
        chunks.append(_make_chunk(doc, " ".join(buffer), idx))
    return chunks


def _make_chunk(doc: RawDocument, text: str, idx: int) -> Chunk:
    # Prepend a context header so lecture/week/topic end up in the embedding,
    # not just in metadata (which the vector search can't see).
    parts = [doc.metadata.get("name", "")]
    if doc.metadata.get("module"):
        parts.append(doc.metadata["module"])
    if doc.metadata.get("topic"):
        parts.append(doc.metadata["topic"])
    header = " | ".join(p for p in parts if p)
    full_text = f"[{header}]\n{text}" if header else text

    return Chunk(
        id=f"{doc.id}-chunk{idx}",
        text=full_text,
        source=doc.source,
        course_id=doc.course_id,
        doc_type=doc.doc_type,
        metadata=doc.metadata,
    )
