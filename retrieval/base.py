from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Chunk:
    id: str
    text: str
    source: str     # "canvas" | "gradescope" | "panopto" | "piazza" | "manual"
    course_id: str
    doc_type: str   # "assignment" | "transcript" | "slide" | "post" | "announcement"
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    score: float | None = None


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 8,
        filters: dict | None = None,
    ) -> list[Chunk]: ...
