from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class RawDocument:
    id: str
    source: str    # "canvas" | "gradescope" | "panopto" | "piazza" | "manual"
    course_id: str
    doc_type: str  # "assignment" | "transcript" | "slide" | "post" | "announcement" | "file"
    content: str
    metadata: dict = field(default_factory=dict)
    file_path: Path | None = None


class BaseIngestor(ABC):
    def __init__(self, course_id: str, config: dict) -> None:
        self.course_id = course_id
        self.config = config

    @abstractmethod
    def fetch(self) -> list[RawDocument]: ...

    def save(self, docs: list[RawDocument], out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        records = []
        for doc in docs:
            d = doc.__dict__.copy()
            d["file_path"] = str(d["file_path"]) if d["file_path"] else None
            records.append(d)
        (out_dir / "documents.jsonl").write_text(
            "\n".join(json.dumps(r) for r in records),
            encoding="utf-8",
        )
