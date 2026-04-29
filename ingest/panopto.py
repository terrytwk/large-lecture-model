"""Panopto ingestion: fetches transcripts for all lecture sessions in a folder.

Auth: browser session cookie (.ASPXAUTH) set via PANOPTO_COOKIE env var.

To get your cookie:
    1. Open any Panopto video at mit.hosted.panopto.com and log in via MIT SSO
    2. Open DevTools → Application → Cookies → mit.hosted.panopto.com
    3. Copy the value of the .ASPXAUTH cookie
    4. Set in .env:  PANOPTO_COOKIE=.ASPXAUTH=<value>

Fallback (no cookie):
    Place pre-downloaded .srt files in data/manual/<course_id>/panopto/
    File naming: <lecture_title>.srt  (e.g. "Lecture 1 Recording.srt")
    Use the graphRAG/download_panopto.py script with --session-id and --cookie.
"""
from __future__ import annotations
import os
import re
from pathlib import Path
import requests

from .base import BaseIngestor, RawDocument

PANOPTO_HOST = "https://mit.hosted.panopto.com"


def _parse_srt(text: str) -> str:
    """Strip SRT sequence numbers and timestamps, return plain transcript text."""
    lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d+$", line):          # sequence number
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}", line):  # timestamp line
            continue
        lines.append(line)
    return " ".join(lines)


def _parse_vtt(text: str) -> str:
    """Strip VTT timestamps and header, return plain transcript text."""
    lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line == "WEBVTT":
            continue
        if re.match(r"^\d{2}:\d{2}", line):   # timestamp line
            continue
        if re.match(r"^\d+$", line):           # cue number
            continue
        lines.append(line)
    return " ".join(lines)


class PanoptoIngestor(BaseIngestor):
    def __init__(self, course_id: str, config: dict, manual_dir: Path | None = None) -> None:
        super().__init__(course_id, config)
        self.folder_id = config.get("panopto_folder_id", "")
        self.manual_dir = (manual_dir or Path("data/manual")) / course_id / "panopto"

        cookie = os.environ.get("PANOPTO_COOKIE", "")
        self.session = requests.Session()
        if cookie:
            self.session.headers["Cookie"] = cookie

    # ── public ────────────────────────────────────────────────────────────────

    def fetch(self) -> list[RawDocument]:
        docs: list[RawDocument] = []

        if os.environ.get("PANOPTO_COOKIE") and self.folder_id:
            print("  [panopto] fetching sessions via API...")
            docs.extend(self._fetch_from_api())
        else:
            print("  [panopto] PANOPTO_COOKIE or panopto_folder_id not set — skipping API")

        docs.extend(self._fetch_from_manual())
        return docs

    # ── API path ───────────────────────────────────────────────────────────────

    def _fetch_from_api(self) -> list[RawDocument]:
        sessions = self._list_sessions()
        print(f"  [panopto] found {len(sessions)} sessions in folder")
        docs: list[RawDocument] = []
        for s in sessions:
            doc = self._fetch_session_transcript(s)
            if doc:
                docs.append(doc)
        return docs

    def _list_sessions(self) -> list[dict]:
        """Page through /api/v1/folders/{id}/sessions."""
        results: list[dict] = []
        page = 0
        while True:
            resp = self.session.get(
                f"{PANOPTO_HOST}/Panopto/api/v1/folders/{self.folder_id}/sessions",
                params={"pageNumber": page, "pageSize": 25, "sortField": "CreatedDate", "sortOrder": "Asc"},
                timeout=30,
            )
            if not resp.ok:
                print(f"  [panopto] folder listing failed — HTTP {resp.status_code}. Check cookie/folder_id.")
                break
            data = resp.json()
            batch = data.get("Results", [])
            results.extend(batch)
            if len(batch) < 25:
                break
            page += 1
        return results

    def _fetch_session_transcript(self, session: dict) -> RawDocument | None:
        session_id = session.get("Id", "")
        name = session.get("Name", session_id)
        date = session.get("CreatedDate", "")
        duration = session.get("Duration")

        print(f"    [transcript] {name}")
        srt_text = self._download_captions(session_id)
        if not srt_text:
            print(f"    [no captions] {name}")
            return None

        return RawDocument(
            id=f"panopto-{session_id}",
            source="panopto",
            course_id=self.course_id,
            doc_type="transcript",
            content=_parse_srt(srt_text),
            metadata={
                "name": name,
                "session_id": session_id,
                "date": date,
                "duration_sec": duration,
            },
        )

    def _download_captions(self, session_id: str) -> str | None:
        """Three-strategy caption fetch, mirroring graphRAG/download_panopto.py."""

        # 1. REST API → CaptionDownloadUrl
        resp = self.session.get(
            f"{PANOPTO_HOST}/Panopto/api/v1/sessions/{session_id}",
            timeout=30,
        )
        if resp.ok:
            cap_url = resp.json().get("CaptionDownloadUrl")
            if cap_url:
                content = self._get_text(cap_url)
                if content and len(content) > 10:
                    return content

        # 2. GenerateSRT with language param
        for url in [
            f"{PANOPTO_HOST}/Panopto/Pages/Transcription/GenerateSRT.ashx?id={session_id}&language=English_USA",
            f"{PANOPTO_HOST}/Panopto/Pages/Transcription/GenerateSRT.ashx?id={session_id}",
        ]:
            content = self._get_text(url)
            if content and len(content) > 10:
                return content

        return None

    def _get_text(self, url: str) -> str | None:
        try:
            resp = self.session.get(url, timeout=30)
            if resp.ok:
                return resp.text
        except Exception as exc:
            print(f"    [warn] {url}: {exc}")
        return None

    # ── manual fallback ────────────────────────────────────────────────────────

    def _fetch_from_manual(self) -> list[RawDocument]:
        """Load any .srt or .vtt files dropped into data/manual/<course>/panopto/."""
        if not self.manual_dir.exists():
            return []

        docs: list[RawDocument] = []
        for path in sorted(self.manual_dir.rglob("*")):
            suffix = path.suffix.lower()
            if suffix not in (".srt", ".vtt"):
                continue

            raw = path.read_text(encoding="utf-8", errors="ignore")
            text = _parse_srt(raw) if suffix == ".srt" else _parse_vtt(raw)
            if not text.strip():
                continue

            print(f"  [panopto/manual] {path.name}")
            docs.append(RawDocument(
                id=f"panopto-manual-{path.stem}",
                source="panopto",
                course_id=self.course_id,
                doc_type="transcript",
                content=text,
                metadata={"name": path.stem, "filename": path.name},
                file_path=path,
            ))
        return docs

    # ── video download (TODO) ──────────────────────────────────────────────────

    def download_videos(self, session_id: str, out_dir: Path) -> None:  # noqa: ARG002
        """
        TODO: Download all video streams for a session using ffmpeg.

        Approach (from graphRAG/download_panopto.py):
          1. GET /Panopto/Pages/Viewer/DeliveryInfo.aspx?deliveryId={session_id}&responseType=json
             → parse Delivery.Streams[].StreamHttpUrl
          2. For each stream URL, run:
             ffmpeg -headers "Cookie: {cookie}" -i {url} -c copy {out_path}
          3. Optionally transcribe with Whisper if no captions exist.

        Requires: ffmpeg installed (brew install ffmpeg)
        """
        raise NotImplementedError("Video download not yet implemented. See graphRAG/download_panopto.py.")
