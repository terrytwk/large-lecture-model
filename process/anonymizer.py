"""PII removal for Piazza posts and Gradescope feedback.

Uses spaCy NER for person names + regex for emails and MIT Kerberos IDs.
Entity map is shared across a batch so one person gets one consistent pseudonym
(Student_A, Student_B, ...) throughout a thread.
"""
from __future__ import annotations
import re
import spacy

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
_STUDENT_ID_RE = re.compile(r"\b\d{9}\b")

_nlp: spacy.Language | None = None


def _get_nlp() -> spacy.Language:
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def anonymize(text: str, entity_map: dict[str, str] | None = None) -> tuple[str, dict[str, str]]:
    """Strip PII from text. Returns (clean_text, entity_map) so maps can be reused across a batch."""
    if entity_map is None:
        entity_map = {}
    counter = [len(entity_map)]

    def pseudonym(original: str) -> str:
        if original not in entity_map:
            n = counter[0]
            entity_map[original] = f"Student_{chr(65 + n % 26)}{n // 26 or ''}"
            counter[0] += 1
        return entity_map[original]

    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _STUDENT_ID_RE.sub("[STUDENT_ID]", text)

    doc = _get_nlp()(text)
    replacements = [
        (ent.start_char, ent.end_char, pseudonym(ent.text))
        for ent in doc.ents
        if ent.label_ == "PERSON"
    ]
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]

    return text, entity_map


def anonymize_batch(texts: list[str]) -> list[str]:
    """Anonymize related texts (e.g., one Piazza thread) with a shared entity map."""
    entity_map: dict[str, str] = {}
    results = []
    for text in texts:
        clean, entity_map = anonymize(text, entity_map)
        results.append(clean)
    return results
