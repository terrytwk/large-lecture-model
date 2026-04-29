"""Lightweight parser for extracting structured query intent."""
from __future__ import annotations
import re


def parse_lecture_number(query: str) -> int | None:
    """Return the first lecture number mentioned in the query, or None."""
    match = re.search(r'\blecture\s+(\d+)\b', query, re.IGNORECASE)
    if match:
        n = int(match.group(1))
        if 1 <= n <= 30:
            return n
    return None


def lecture_canvas_names(n: int) -> list[str]:
    """Known Canvas document name patterns for lecture N."""
    return [
        f"Lecture {n} Notes",
        f"Lecture {n} Cliff Notes",
        f"Lecture {n} Slides",
    ]
