"""Canvas LMS ingestion via the official REST API."""
import os
import re
import requests

try:
    import pymupdf  # type: ignore
    _HAS_PYMUPDF = True
except ImportError:
    _HAS_PYMUPDF = False

from .base import BaseIngestor, RawDocument


_DOC_TYPE_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"lecture \d+.*(notes?|slides?|cliff|supplement)", re.I), "slide"),
    (re.compile(r"recitation \d+", re.I), "slide"),
    (re.compile(r"quiz \d+ review", re.I), "slide"),
    (re.compile(r"probability (cheat|review)", re.I), "slide"),
    (re.compile(r"solutions? to practice", re.I), "practice"),
    (re.compile(r"practice problems?", re.I), "practice"),
    (re.compile(r"problem set \d+", re.I), "assignment"),
    (re.compile(r"warm.?up set \d+", re.I), "assignment"),
    (re.compile(r"quiz \d+", re.I), "assignment"),
]


def _infer_doc_type(title: str) -> str:
    for pat, dtype in _DOC_TYPE_RULES:
        if pat.search(title):
            return dtype
    return "slide"


def _extract_pdf_text(data: bytes, name: str) -> str:
    if not _HAS_PYMUPDF:
        return ""
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except Exception as exc:
        print(f"    [pdf error] {name}: {exc}")
        return ""


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
            data = resp.json()
            results.extend(data if isinstance(data, list) else [data])
            url = resp.links.get("next", {}).get("url", "")
            params = None
        return results

    def fetch(self) -> list[RawDocument]:
        docs: list[RawDocument] = []
        docs.extend(self._fetch_syllabus())
        docs.extend(self._fetch_assignments())
        docs.extend(self._fetch_announcements())
        modules = self._get_all_modules()
        docs.extend(self._fetch_module_structure(modules))
        docs.extend(self._fetch_module_files(modules))
        return docs

    # ── core fetchers ──────────────────────────────────────────────────────────

    def _fetch_syllabus(self) -> list[RawDocument]:
        resp = self.session.get(
            f"{self.BASE_URL}/courses/{self.canvas_course_id}",
            params={"include[]": "syllabus_body"},
        )
        resp.raise_for_status()
        body = resp.json().get("syllabus_body") or ""
        if not body:
            return []
        return [RawDocument(
            id=f"canvas-syllabus-{self.canvas_course_id}",
            source="canvas",
            course_id=self.course_id,
            doc_type="announcement",
            content=body,
            metadata={"name": "Syllabus"},
        )]

    def _fetch_assignments(self) -> list[RawDocument]:
        items = self._paginate(f"{self.BASE_URL}/courses/{self.canvas_course_id}/assignments")
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
        items = self._paginate(
            f"{self.BASE_URL}/courses/{self.canvas_course_id}/discussion_topics",
            params={"only_announcements": True},
        )
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

    # ── modules ────────────────────────────────────────────────────────────────

    def _get_all_modules(self) -> list[dict]:
        modules = self._paginate(
            f"{self.BASE_URL}/courses/{self.canvas_course_id}/modules",
            params={"include[]": "items", "per_page": "50"},
        )
        # If a module has more items than returned, fetch them individually
        for mod in modules:
            if mod.get("items_count", 0) > len(mod.get("items", [])):
                mod["items"] = self._paginate(
                    f"{self.BASE_URL}/courses/{self.canvas_course_id}/modules/{mod['id']}/items",
                    params={"per_page": "50"},
                )
        return modules

    def _fetch_module_structure(self, modules: list[dict]) -> list[RawDocument]:
        """One document per week that summarises topics, lectures, and files."""
        docs = []
        for mod in modules:
            items = mod.get("items", [])
            if not items:
                continue
            lines = [f"# {mod['name']}"]
            for item in items:
                itype, title = item["type"], item["title"]
                if itype == "SubHeader":
                    lines.append(f"\n## {title}")
                elif itype == "ExternalTool":
                    lines.append(f"- Recording: {title}")
                elif itype in ("Assignment", "File"):
                    lines.append(f"- {itype}: {title}")
            docs.append(RawDocument(
                id=f"canvas-module-{mod['id']}",
                source="canvas",
                course_id=self.course_id,
                doc_type="announcement",
                content="\n".join(lines),
                metadata={"name": mod["name"], "module_id": str(mod["id"])},
            ))
        return docs

    def _fetch_module_files(self, modules: list[dict]) -> list[RawDocument]:
        """Download every unique PDF File item across all modules and extract text."""
        docs: list[RawDocument] = []
        seen: set[str] = set()

        for mod in modules:
            module_name = mod["name"]
            current_topic: str | None = None

            for item in mod.get("items", []):
                if item["type"] == "SubHeader":
                    current_topic = item["title"]
                    continue
                if item["type"] != "File":
                    continue

                content_id = item.get("content_id")
                if not content_id or str(content_id) in seen:
                    continue
                seen.add(str(content_id))

                doc = self._fetch_file_doc(
                    content_id=int(content_id),
                    item_title=item["title"],
                    module_name=module_name,
                    topic=current_topic,
                )
                if doc:
                    docs.append(doc)

        return docs

    def _fetch_file_doc(
        self,
        content_id: int,
        item_title: str,
        module_name: str,
        topic: str | None,
    ) -> RawDocument | None:
        resp = self.session.get(f"{self.BASE_URL}/files/{content_id}")
        if not resp.ok:
            print(f"    [skip] {item_title} — HTTP {resp.status_code}")
            return None

        meta = resp.json()
        content_type = meta.get("content-type", "")
        display_name = meta.get("display_name", item_title)
        download_url = meta.get("url", "")

        if not download_url or "pdf" not in content_type.lower():
            print(f"    [skip non-pdf] {display_name} ({content_type})")
            return None

        print(f"    [download] {display_name}")
        dl = self.session.get(download_url, allow_redirects=True)
        if not dl.ok:
            print(f"    [fail] {display_name} — HTTP {dl.status_code}")
            return None

        text = _extract_pdf_text(dl.content, display_name)
        return RawDocument(
            id=f"canvas-file-{content_id}",
            source="canvas",
            course_id=self.course_id,
            doc_type=_infer_doc_type(item_title),
            content=text or f"[PDF: {display_name}]",
            metadata={
                "name": item_title,
                "display_name": display_name,
                "file_id": str(content_id),
                "module": module_name,
                "topic": topic or "",
            },
        )
