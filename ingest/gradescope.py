"""Gradescope ingestion via unofficial session-based scraper.

Reference: https://github.com/nyuoss/gradescope-api
"""
import os
from .base import BaseIngestor, RawDocument


class GradescopeIngestor(BaseIngestor):
    def __init__(self, course_id: str, config: dict) -> None:
        super().__init__(course_id, config)
        self.email = os.environ["GRADESCOPE_EMAIL"]
        self.password = os.environ["GRADESCOPE_PASSWORD"]
        self.gs_course_id = config["gradescope_course_id"]

    def fetch(self) -> list[RawDocument]:
        # TODO: implement using gradescopeapi or custom session scraper
        # from gradescopeapi.classes.connection import GSConnection
        # conn = GSConnection(); conn.login(self.email, self.password)
        # assignments = conn.get_assignments(self.gs_course_id)
        # NOTE: run anonymizer on any feedback content before returning
        raise NotImplementedError
