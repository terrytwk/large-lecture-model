"""Piazza ingestion via piazza-api library.

PII anonymization runs immediately on fetched content — no raw student data is stored.
Fallback: manually exported HTML files from Piazza are handled by ManualIngestor.
"""
import os
from .base import BaseIngestor, RawDocument


class PiazzaIngestor(BaseIngestor):
    def __init__(self, course_id: str, config: dict) -> None:
        super().__init__(course_id, config)
        self.email = os.environ["PIAZZA_EMAIL"]
        self.password = os.environ["PIAZZA_PASSWORD"]
        self.piazza_course_id = config["piazza_course_id"]

    def fetch(self) -> list[RawDocument]:
        # TODO: implement using piazza-api
        # from piazza_api import Piazza
        # p = Piazza()
        # p.user_login(email=self.email, password=self.password)
        # network = p.network(self.piazza_course_id)
        # for post in network.iter_all_posts():
        #     content = anonymize(post["history"][0]["content"])
        #     yield RawDocument(...)
        raise NotImplementedError
