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
    course_cfg = cfg["courses"][course_id]

    from ingest.canvas import CanvasIngestor
    from ingest.manual import ManualIngestor

    ingestor_map = {
        "canvas": lambda: CanvasIngestor(course_id, course_cfg),
        "manual": lambda: ManualIngestor(course_id, course_cfg, ROOT / "data/manual"),
        # "gradescope": lambda: GradescopeIngestor(course_id, course_cfg),
        # "panopto":    lambda: PanoptoIngestor(course_id, course_cfg),
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
