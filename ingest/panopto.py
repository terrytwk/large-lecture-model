"""Panopto ingestion: downloads .vtt transcript files per lecture session.

Auth: Panopto OAuth2 or MIT SSO session cookies.
Fallback: pre-downloaded .vtt files placed in data/manual/ are handled by ManualIngestor.
"""
import os
import re
import requests
from .base import BaseIngestor, RawDocument


class PanoptoIngestor(BaseIngestor):
    def __init__(self, course_id: str, config: dict) -> None:
        super().__init__(course_id, config)
        self.folder_id = config.get("panopto_folder_id", "")
        self.server = os.environ.get("PANOPTO_SERVER", "mit.hosted.panopto.com")

    def fetch(self) -> list[RawDocument]:
        # TODO: implement session listing + .vtt download
        # GET https://{server}/Panopto/api/v1/folders/{folder_id}/sessions
        # For each session: GET .../sessions/{id}/captions -> download .vtt
        raise NotImplementedError

    def _parse_vtt(self, vtt_content: str) -> str:
        """Strip VTT timestamps and metadata, return plain transcript text."""
        lines = []
        for line in vtt_content.splitlines():
            if re.match(r"^\d{2}:\d{2}", line):
                continue
            if line.strip() in ("WEBVTT", ""):
                continue
            if re.match(r"^\d+$", line.strip()):
                continue
            lines.append(line.strip())
        return " ".join(lines)
