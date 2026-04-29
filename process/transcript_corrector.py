"""Corrects ASR transcription errors in lecture transcripts using lecture materials as context.

For each transcript RawDocument, finds slide/note docs from the same lecture (matched by
lecture number in the document name), then calls the LLM to fix mis-transcribed technical
terms, algorithm names, data structures, and proper nouns.

Run via run_process.py --correct-transcripts. Each transcript costs ~N/3000 LLM calls
where N is the transcript word count.
"""
from __future__ import annotations
import re
from dataclasses import replace

from ingest.base import RawDocument

SEGMENT_WORDS = 3000   # words per LLM call — balances cost vs. context
CONTEXT_CHARS = 8000   # max chars of slide content passed per call

_SYSTEM = (
    "You are a transcript editor for a computer science lecture. "
    "Your only task is to fix automatic speech recognition (ASR) errors using the provided "
    "lecture materials as ground truth for correct terminology. "
    "Fix mis-transcribed technical terms, algorithm names, data structures, and proper nouns. "
    "Do not rewrite, restructure, or add content — keep the spoken language style. "
    "Return only the corrected transcript text with no explanation or preamble."
)


def correct_transcripts(docs: list[RawDocument], llm) -> list[RawDocument]:
    """Replace transcript content in-place (returns new list) with LLM-corrected text."""
    transcripts = [d for d in docs if d.doc_type == "transcript"]
    context_docs = [d for d in docs if d.doc_type != "transcript"]

    if not transcripts:
        return docs

    lecture_context = _build_lecture_context(context_docs)
    print(f"  [corrector] {len(transcripts)} transcripts, "
          f"{len(lecture_context)} lecture context(s) available")

    corrected_by_id: dict[str, RawDocument] = {}
    for doc in transcripts:
        name = doc.metadata.get("name", doc.id)
        context = _find_context(doc, lecture_context)
        if not context:
            print(f"  [corrector] no matching lecture context for '{name}' — skipping")
            continue
        print(f"  [corrector] '{name}' ({len(doc.content.split())} words)...")
        corrected_text = _correct_doc(doc.content, name, context, llm)
        corrected_by_id[doc.id] = replace(doc, content=corrected_text)

    return [corrected_by_id.get(d.id, d) for d in docs]


# ── context building ───────────────────────────────────────────────────────────

def _build_lecture_context(docs: list[RawDocument]) -> dict[str, str]:
    """Map lecture number string → combined slide/note text (capped at CONTEXT_CHARS)."""
    buckets: dict[str, list[str]] = {}
    for doc in docs:
        if doc.doc_type not in ("slide", "file", "practice"):
            continue
        # Try name first, fall back to module field
        num = _lecture_num(doc.metadata.get("name", "")) or _lecture_num(
            doc.metadata.get("module", "")
        )
        if num:
            buckets.setdefault(num, []).append(doc.content[:4000])

    return {
        k: "\n\n---\n\n".join(v)[:CONTEXT_CHARS]
        for k, v in buckets.items()
    }


def _find_context(doc: RawDocument, lecture_context: dict[str, str]) -> str:
    num = _lecture_num(doc.metadata.get("name", ""))
    return lecture_context.get(num, "") if num else ""


def _lecture_num(text: str) -> str | None:
    """Extract bare lecture number from strings like 'Lecture 04 - Sorting' → '4'."""
    m = re.search(r'\blecture\s+0?(\d+)\b', text, re.IGNORECASE)
    return m.group(1) if m else None


# ── LLM correction ─────────────────────────────────────────────────────────────

def _correct_doc(transcript: str, lecture_name: str, context: str, llm) -> str:
    words = transcript.split()
    if not words:
        return transcript
    segments: list[str] = []
    for i in range(0, len(words), SEGMENT_WORDS):
        segment = " ".join(words[i : i + SEGMENT_WORDS])
        seg_num = i // SEGMENT_WORDS + 1
        total = (len(words) + SEGMENT_WORDS - 1) // SEGMENT_WORDS
        print(f"    segment {seg_num}/{total}...")
        segments.append(_correct_segment(segment, lecture_name, context, llm))
    return " ".join(segments)


def _correct_segment(segment: str, lecture_name: str, context: str, llm) -> str:
    user = (
        f"Lecture: {lecture_name}\n\n"
        f"Lecture materials (use for correct terminology):\n"
        f"<context>\n{context}\n</context>\n\n"
        f"Fix any ASR transcription errors in this excerpt:\n"
        f"<transcript>\n{segment}\n</transcript>"
    )
    try:
        return llm.complete(_SYSTEM, user)
    except Exception as exc:
        print(f"    [corrector] LLM call failed ({exc}) — keeping original")
        return segment
