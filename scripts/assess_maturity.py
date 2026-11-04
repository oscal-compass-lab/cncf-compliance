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
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "projects.json"
MATURITIES = ("graduated", "incubating", "sandbox")
RATE_LIMIT_URL = "https://api.github.com/rate_limit"
RATE_LIMIT_TIMEOUT_SECONDS = 15
RESET_MARGIN_SECONDS = 5      # slack after the reported reset time
HEARTBEAT_SECONDS = 300       # log a line at least this often while waiting
MAX_WAIT_SECONDS = 3900       # never wait longer than one window plus a margin
MAX_ATTEMPTS = 2              # one redo after a project that ran out of budget


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def utc_from_epoch(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%H:%M:%S UTC")


def fmt_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m{secs:02d}s"


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


def wait_until(epoch: float, why: str) -> None:
    """Sleep until ``epoch`` (plus a margin), logging a heartbeat while waiting."""
    resume_at = min(epoch + RESET_MARGIN_SECONDS, time.time() + MAX_WAIT_SECONDS)
    print(f"rate limit: {why}; waiting until {utc_from_epoch(resume_at)} [{utc_now()} UTC]",
          flush=True)
    while (left := resume_at - time.time()) > 0:
        time.sleep(min(left, HEARTBEAT_SECONDS))
        left = resume_at - time.time()
        if left > 0:
            print(f"rate limit: still waiting, {fmt_duration(left)} to go [{utc_now()} UTC]",
                  flush=True)


def read_budget_waiting_if_empty() -> dict | None:
    """Current budget; if it is already 0, wait for the window to reset first.

    The budget is back when a fresh reading shows requests remaining (its
    ``reset`` then points to the next window).
    """
    rl = core_rate_limit()
    if rl and rl["remaining"] <= 0:
        wait_until(rl["reset"], "budget is 0")
        rl = core_rate_limit()
        if rl:
            print(f"rate limit: now {rl['remaining']}/{rl['limit']} remaining; next reset "
                  f"{utc_from_epoch(rl['reset'])} [{utc_now()} UTC]", flush=True)
    return rl


def assess_one(url: str) -> tuple[bool, dict | None, dict | None, float]:
    """Assess one project. Returns (ok, budget before, budget after, seconds)."""
    before = read_budget_waiting_if_empty()
    started = time.monotonic()
    ok = True
    for script, args in (("build_project_compliance.py", ["project", url]),
                         ("assess_project.py", [url])):
        r = subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=ROOT, check=False)
        if r.returncode != 0:
            print(f"WARNING: {script} failed for {url}", flush=True)
            ok = False
            break
    return ok, before, core_rate_limit(), time.monotonic() - started


def write_step_summary(maturity: str,
                       rows: list[tuple[str, int | None, int | None, float]],
                       elapsed: float) -> None:
    """Append a table to the GitHub job summary, when running in Actions."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path or not rows:
        return
    lines = [f"### {maturity}: time and GitHub API budget per project", "",
             "| Project | Time | Requests used | Remaining after |", "| --- | ---: | ---: | ---: |"]
    lines += [f"| {url} | {fmt_duration(secs)} | {'?' if used is None else used} | "
              f"{'?' if left is None else left} |" for url, used, left, secs in rows]
    lines += ["", f"Total time: {fmt_duration(elapsed)} for {len(rows)} project(s)."]
    known = [u for _, u, _, _ in rows if u is not None]
    if known:
        lines.append(f"Total requests used: {sum(known)}; largest single project: {max(known)}. "
                     "Other jobs share this budget, so figures can include their requests.")
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
    redone = []
    usage: list[tuple[str, int | None, int | None, float]] = []
    started = time.monotonic()
    for url in to_assess:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"\n=== {url} === attempt {attempt} [{utc_now()} UTC]", flush=True)
            ok, before, after, secs = assess_one(url)
            used = None
            if after:
                if before and before["remaining"] >= after["remaining"]:
                    used = before["remaining"] - after["remaining"]  # else: window reset
                print(f"rate limit: {url} used {'?' if used is None else used} request(s) "
                      f"in {fmt_duration(secs)}; {after['remaining']}/{after['limit']} remaining "
                      f"(window resets {utc_from_epoch(after['reset'])}) [{utc_now()} UTC]",
                      flush=True)
            else:
                print(f"{url} took {fmt_duration(secs)} [{utc_now()} UTC]", flush=True)
            # Two signs that requests may have been refused during the project:
            #  - the budget is 0 afterwards: wait for the reset, then redo it;
            #  - the window rolled over mid-project (the reset time moved on): the
            #    budget may have hit 0 and refilled unseen, so redo it to be safe.
            exhausted = bool(after and after["remaining"] <= 0)
            rolled_over = bool(before and after and after["reset"] > before["reset"])
            if not (exhausted or rolled_over):
                break
            why = ("budget exhausted" if exhausted else
                   "rate-limit window reset mid-project, so exhaustion can't be ruled out")
            print(f"WARNING: {why} during {url}; its result may be incomplete", flush=True)
            if attempt == MAX_ATTEMPTS:
                print(f"WARNING: giving up on a clean result for {url}", flush=True)
                break
            redone.append(url)
            if exhausted:
                wait_until(after["reset"], "waiting for the budget before redoing the project")
        if not ok:
            failed.append(url)
        usage.append((url, used, after["remaining"] if after else None, secs))
    elapsed = time.monotonic() - started
    print(f"\n[{maturity}] Finished {len(to_assess)} project(s) in {fmt_duration(elapsed)} "
          f"[{utc_now()} UTC]", flush=True)
    write_step_summary(maturity, usage, elapsed)

    if redone:
        print(f"\n[{maturity}] Redone after the budget ran out ({len(redone)}):")
        for u in redone:
            print(f"  {u}")
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
