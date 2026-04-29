"""Run ingestors for a given course and save raw documents to data/raw/."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def main(course_id: str, sources: list[str]) -> None:
    cfg = yaml.safe_load((ROOT / "config/courses.yaml").read_text())
    courses = {str(k): v for k, v in cfg["courses"].items()}
    course_cfg = courses[course_id]

    def _canvas():
        from ingest.canvas import CanvasIngestor
        return CanvasIngestor(course_id, course_cfg)

    def _manual():
        from ingest.manual import ManualIngestor
        return ManualIngestor(course_id, course_cfg, ROOT / "data/manual")

    def _panopto():
        from ingest.panopto import PanoptoIngestor
        return PanoptoIngestor(course_id, course_cfg, ROOT / "data/manual")

    ingestor_map = {
        "canvas": _canvas,
        "manual": _manual,
        "panopto": _panopto,
        # "gradescope": lambda: GradescopeIngestor(course_id, course_cfg),
        # "piazza":     lambda: PiazzaIngestor(course_id, course_cfg),
    }

    for source in sources:
        if source not in ingestor_map:
            print(f"Unknown source '{source}' — skipping.", file=sys.stderr)
            continue
        print(f"[{source}] Fetching...")
        ingestor = ingestor_map[source]()
        docs = ingestor.fetch()
        out_dir = ROOT / "data/raw" / source / course_id
        ingestor.save(docs, out_dir)
        print(f"[{source}] Saved {len(docs)} documents → {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", default="6.1220")
    parser.add_argument("--sources", nargs="+", default=["canvas", "manual"])
    args = parser.parse_args()
    main(args.course, args.sources)
