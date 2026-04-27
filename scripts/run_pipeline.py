"""End-to-end pipeline: ingest → process → index."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).parent


def run(script: str, extra: list[str]) -> None:
    cmd = [sys.executable, str(SCRIPTS / script)] + extra
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", default="6.1220")
    parser.add_argument("--sources", nargs="+", default=["canvas", "manual"])
    args = parser.parse_args()

    run("run_ingest.py", ["--course", args.course, "--sources"] + args.sources)
    run("run_process.py", ["--course", args.course])
