"""Entry point: build the Neo4j concept graph for one or more courses.

Usage
-----
    python scripts/build_graph.py                    # all courses in courses.yaml
    python scripts/build_graph.py --course-id 6.1220

Prerequisites
-------------
  1. Neo4j running (Docker or Desktop):
       docker run -p 7474:7474 -p 7687:7687 \\
         -e NEO4J_AUTH=neo4j/yourpassword neo4j:5
  2. NEO4J_PASSWORD env var set (or set neo4j.password in config/settings.yaml)
  3. Course data ingested: data/raw/{course_id}/ must have documents.jsonl files
  4. llm.db seeded: run the FastAPI backend once (it auto-syncs assignments on startup)

After running, open http://localhost:7474 (Neo4j Browser) to explore the graph.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from llm.client import LLMClient
from process.graph_builder import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Neo4j concept graph for a course.")
    parser.add_argument(
        "--course-id",
        default=None,
        help="Course ID to build (e.g. 6.1220). Omit to build all courses in courses.yaml.",
    )
    args = parser.parse_args()

    settings = yaml.safe_load(Path("config/settings.yaml").read_text())
    courses_cfg = yaml.safe_load(Path("config/courses.yaml").read_text())

    llm = LLMClient(
        model=settings["llm"]["model"],
        max_tokens=settings["llm"]["max_tokens"],
    )

    if args.course_id:
        course_ids = [args.course_id]
    else:
        course_ids = list(courses_cfg.get("courses", {}).keys())

    for course_id in course_ids:
        print(f"\n{'='*60}")
        print(f"Building graph for: {course_id}")
        print("=" * 60)
        build_graph(course_id, settings, llm)


if __name__ == "__main__":
    main()
