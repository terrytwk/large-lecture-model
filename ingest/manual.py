"""Manual file ingestor: processes files dropped into data/manual/{course_id}/."""
from pathlib import Path
import pymupdf
from .base import BaseIngestor, RawDocument


class ManualIngestor(BaseIngestor):
    SUPPORTED = {".pdf", ".vtt", ".html", ".txt", ".md"}

    def __init__(self, course_id: str, config: dict, manual_dir: Path) -> None:
        super().__init__(course_id, config)
        self.manual_dir = manual_dir / course_id

    def fetch(self) -> list[RawDocument]:
        docs: list[RawDocument] = []
        if not self.manual_dir.exists():
            return docs
        for path in self.manual_dir.rglob("*"):
            if path.suffix.lower() not in self.SUPPORTED:
                continue
            docs.extend(self._process_file(path))
        return docs

    def _process_file(self, path: Path) -> list[RawDocument]:
        if path.suffix.lower() == ".pdf":
            return self._process_pdf(path)
        content = path.read_text(encoding="utf-8", errors="ignore")
        return [
            RawDocument(
                id=f"manual-{path.stem}",
                source="manual",
                course_id=self.course_id,
                doc_type="file",
                content=content,
                metadata={"filename": path.name},
                file_path=path,
            )
        ]

    def _process_pdf(self, path: Path) -> list[RawDocument]:
        doc = pymupdf.open(path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if not text.strip():
                continue
            pages.append(
                RawDocument(
                    id=f"manual-{path.stem}-p{i + 1}",
                    source="manual",
                    course_id=self.course_id,
                    doc_type="slide",
                    content=text,
                    metadata={"filename": path.name, "page": i + 1},
                    file_path=path,
                )
            )
        return pages
