"""Canvas LMS ingestion via the official REST API."""
import os
import requests
from .base import BaseIngestor, RawDocument


class CanvasIngestor(BaseIngestor):
    BASE_URL = "https://canvas.mit.edu/api/v1"

    def __init__(self, course_id: str, config: dict) -> None:
        super().__init__(course_id, config)
        self.token = os.environ["CANVAS_API_TOKEN"]
        self.canvas_course_id = config["canvas_course_id"]
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _paginate(self, url: str, params: dict | None = None) -> list[dict]:
        results: list[dict] = []
        while url:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            results.extend(resp.json())
            url = resp.links.get("next", {}).get("url", "")
            params = None
        return results

    def fetch(self) -> list[RawDocument]:
        docs: list[RawDocument] = []
        docs.extend(self._fetch_syllabus())
        docs.extend(self._fetch_assignments())
        docs.extend(self._fetch_announcements())
        return docs

    def _fetch_syllabus(self) -> list[RawDocument]:
        url = f"{self.BASE_URL}/courses/{self.canvas_course_id}"
        resp = self.session.get(url, params={"include[]": "syllabus_body"})
        resp.raise_for_status()
        body = resp.json().get("syllabus_body") or ""
        if not body:
            return []
        return [
            RawDocument(
                id=f"canvas-syllabus-{self.canvas_course_id}",
                source="canvas",
                course_id=self.course_id,
                doc_type="announcement",
                content=body,
                metadata={"name": "Syllabus"},
            )
        ]

    def _fetch_assignments(self) -> list[RawDocument]:
        url = f"{self.BASE_URL}/courses/{self.canvas_course_id}/assignments"
        items = self._paginate(url)
        return [
            RawDocument(
                id=f"canvas-assignment-{a['id']}",
                source="canvas",
                course_id=self.course_id,
                doc_type="assignment",
                content=a.get("description") or "",
                metadata={
                    "name": a["name"],
                    "due_at": a.get("due_at"),
                    "points_possible": a.get("points_possible"),
                    "html_url": a.get("html_url"),
                },
            )
            for a in items
        ]

    def _fetch_announcements(self) -> list[RawDocument]:
        url = f"{self.BASE_URL}/courses/{self.canvas_course_id}/discussion_topics"
        items = self._paginate(url, params={"only_announcements": True})
        return [
            RawDocument(
                id=f"canvas-announcement-{a['id']}",
                source="canvas",
                course_id=self.course_id,
                doc_type="announcement",
                content=a.get("message") or "",
                metadata={"name": a["title"], "posted_at": a.get("posted_at")},
            )
            for a in items
        ]
