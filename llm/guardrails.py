"""Academic integrity guardrail — classifies queries before retrieval.

Sensitivity modes (config/settings.yaml guardrails.sensitivity):
  permissive   — block only explicit solution-seeking patterns
  conservative — also block any query that mentions a protected assignment by name
"""
from __future__ import annotations
import re

_SOLUTION_RE = re.compile(
    r"\b(solve|solution to|answer to|write the code for|implement for me"
    r"|give me the (answer|solution|code)|complete (this )?(problem|question|pset|ps)\s*\d"
    r"|do (problem|question|pset|ps)\s*\d)\b",
    re.IGNORECASE,
)


def _permissive(query: str, protected: list[str]) -> tuple[bool, str]:
    if _SOLUTION_RE.search(query):
        return True, "I can explain concepts and point you to materials, but I can't solve assignment problems directly."
    return False, ""


def _conservative(query: str, protected: list[str]) -> tuple[bool, str]:
    blocked, reason = _permissive(query, protected)
    if blocked:
        return blocked, reason
    for name in protected:
        if name.lower() in query.lower():
            return True, f"Queries about {name} are restricted while the assignment is active."
    return False, ""


def check(
    query: str,
    protected_names: list[str],
    sensitivity: str = "permissive",
) -> tuple[bool, str]:
    if sensitivity == "conservative":
        return _conservative(query, protected_names)
    return _permissive(query, protected_names)
