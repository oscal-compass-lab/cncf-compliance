#!/usr/bin/env python3
"""Assess every enabled CNCF project of one maturity level.

For each project in data/projects.json with the given maturity, run
build_project_compliance.py (comp-def, SSP, assessment plan) and then
assess_project.py (run Privateer, write the report and update
data/projects.json).

A project that fails is logged and skipped; it does not stop the others and
does not make this script fail.

Prefer the per-level entry points: assess_graduated.py, assess_incubating.py,
assess_sandbox.py.

Usage
-----
  python scripts/assess_maturity.py {graduated,incubating,sandbox}
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "projects.json"
MATURITIES = ("graduated", "incubating", "sandbox")
RATE_LIMIT_URL = "https://api.github.com/rate_limit"
RATE_LIMIT_TIMEOUT_SECONDS = 15


def core_rate_limit() -> dict | None:
    """The token's REST ("core") budget: {"remaining", "limit", "reset"}, or None.

    GET /rate_limit does not count against the limit. Never raises: a failure
    here must not stop an assessment.
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return None
    request = urllib.request.Request(RATE_LIMIT_URL, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "cncf-compliance-assess",
    })
    try:
        with urllib.request.urlopen(request, timeout=RATE_LIMIT_TIMEOUT_SECONDS) as r:  # noqa: S310 (fixed https URL)
            return json.load(r)["resources"]["core"]
    except Exception as exc:  # noqa: BLE001 - diagnostics only
        print(f"rate limit: could not read ({type(exc).__name__})", flush=True)
        return None


def write_step_summary(maturity: str, rows: list[tuple[str, int | None, int | None]]) -> None:
    """Append a table to the GitHub job summary, when running in Actions."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path or not rows:
        return
    lines = [f"### GitHub API budget used per {maturity} project", "",
             "| Project | Requests used | Remaining after |", "| --- | ---: | ---: |"]
    lines += [f"| {url} | {'?' if used is None else used} | {'?' if left is None else left} |"
              for url, used, left in rows]
    known = [u for _, u, _ in rows if u is not None]
    if known:
        lines += ["", f"Total used: {sum(known)}; largest single project: {max(known)}. "
                      "Other jobs share this budget, so figures can include their requests."]
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def assess_maturity(maturity: str) -> int:
    if maturity not in MATURITIES:
        print(f"maturity must be one of {', '.join(MATURITIES)}", file=sys.stderr)
        return 2

    projects = [p for p in json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if p.get("maturity") == maturity]
    to_assess = [p["repo_url"] for p in projects if p.get("repo_url")]
    print(f"[{maturity}] Assessing {len(to_assess)} project(s), "
          f"skipping {len(projects) - len(to_assess)}.", flush=True)

    failed = []
    usage: list[tuple[str, int | None, int | None]] = []
    for url in to_assess:
        print(f"\n=== {url} ===", flush=True)
        before = core_rate_limit()
        for script, args in (("build_project_compliance.py", ["project", url]),
                             ("assess_project.py", [url])):
            r = subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                               cwd=ROOT, check=False)
            if r.returncode != 0:
                print(f"WARNING: {script} failed for {url}", flush=True)
                failed.append(url)
                break
        after = core_rate_limit()
        if before and after:
            used = before["remaining"] - after["remaining"]
            if used < 0:  # the hourly window reset between the two readings
                used = None
            print(f"rate limit: {url} used {'?' if used is None else used} request(s); "
                  f"{after['remaining']}/{after['limit']} remaining", flush=True)
            if after["remaining"] == 0:
                print(f"WARNING: GitHub API rate limit exhausted (resets at epoch "
                      f"{after['reset']}); later results may be incomplete", flush=True)
            usage.append((url, used, after["remaining"]))
        else:
            usage.append((url, None, None))
    write_step_summary(maturity, usage)

    if failed:
        print(f"\n[{maturity}] Failed assessments ({len(failed)}):")
        for u in failed:
            print(f"  {u}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("maturity", choices=MATURITIES)
    return assess_maturity(ap.parse_args().maturity)


if __name__ == "__main__":
    sys.exit(main())
