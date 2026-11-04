#!/usr/bin/env python3
"""Merge per-level assessment results and regenerate the README tables.

Each parallel assessment job (graduated, incubating, sandbox) leaves its own
copy of data/projects.json, named projects-<level>.json. This script takes the
entries of each level from its file, writes the combined list to
data/projects.json, and rewrites the README project tables.

A level with no file (for example its job failed) keeps the entries already in
data/projects.json, so earlier results are not lost.

Usage
-----
  python scripts/merge_assessments.py projects-graduated.json [projects-incubating.json ...]
"""

import json
import sys
from pathlib import Path

import update_readme as ur


def merge(projects: list[dict], level_files: list[Path]) -> list[dict]:
    by_id = {p["id"]: p for p in projects}
    for path in level_files:
        level = path.stem.removeprefix("projects-")
        for p in json.loads(path.read_text(encoding="utf-8")):
            if p.get("maturity") == level and p["id"] in by_id:
                by_id[p["id"]] = p
    return [by_id[p["id"]] for p in projects]


def main() -> int:
    level_files = [Path(a) for a in sys.argv[1:]]
    missing = [str(f) for f in level_files if not f.is_file()]
    if missing:
        print(f"File(s) not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    projects = merge(ur.load_projects(), level_files)
    ur.DATA_FILE.write_text(json.dumps(projects, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    ur.update_readme(ur.render_tables(projects))
    print(f"Merged {len(level_files)} level file(s); {len(projects)} projects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
