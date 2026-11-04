#!/usr/bin/env python3
"""Assess every enabled CNCF project of one maturity level.

For each project in data/projects.json with the given maturity, run
build_project_compliance.py (comp-def, SSP, assessment plan) and then
assess_project.py (run Privateer, write the report and update
data/projects.json).

A project that fails or runs past its time limit is rolled back to its previous
result, logged and skipped; it does not stop the others and does not make this
script fail. With ASSESS_PUSH=1 each finished project is committed and pushed.

Usage
-----
  python scripts/assess_maturity.py {graduated,incubating,sandbox}
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from build_project_compliance import _slug
from checks.privateer_client import PRIVATEER_FAILED_EXIT

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
# Longest one project may take (build + assess, excluding rate-limit waits).
# There is deliberately no limit on the whole run: it may take as long as it
# likes while it keeps moving on to the next project.
PROJECT_TIMEOUT_SECONDS = int(os.environ.get("ASSESS_PROJECT_TIMEOUT", "1200"))
TIME_FORMAT = "%Y-%m-%d %H:%M:%S UTC"
# Publishing after each project (only when ASSESS_PUSH=1, as set in the workflow).
PUSH_PATHS = ("README.md", "data/projects.json", "reports", "trestle.ws")
GIT_TIMEOUT_SECONDS = 120
PUSH_ATTEMPTS = 3


def utc_from_epoch(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime(TIME_FORMAT)


def log(message: str = "") -> None:
    """The one way this script writes to the log: every line gets the UTC date and time."""
    stamp = datetime.now(timezone.utc).strftime(TIME_FORMAT)
    for line in message.splitlines() or [""]:
        print(f"[{stamp}] {line}", flush=True)


def fmt_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m{secs:02d}s"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          timeout=GIT_TIMEOUT_SECONDS, check=False)


def _git_problem(result: subprocess.CompletedProcess) -> str:
    """The most telling line of git's output: a fatal/error line if there is one."""
    lines = (result.stderr or result.stdout or "").strip().splitlines()
    for line in lines:
        if line.startswith(("fatal:", "error:")):
            return line[:200]
    return lines[-1][:200] if lines else f"exit status {result.returncode}"


def push_progress(url: str) -> None:
    """Commit and push what is in the working tree, so the repository stays current.

    The working tree only ever holds whole projects (see ``project_snapshot``).

    Does nothing unless ASSESS_PUSH=1. Never raises and never stops the run: if
    the push fails, the commit stays local and goes out with the next project's.
    """
    if os.environ.get("ASSESS_PUSH") != "1":
        return
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    try:
        _git("add", "--", *PUSH_PATHS)
        if _git("diff", "--cached", "--quiet").returncode == 0:
            log(f"git: nothing new to commit for {url}")
            return
        committed = _git("commit", "-m", f"Assess {url}")
        if committed.returncode != 0:
            log(f"WARNING: git commit failed for {url}: {_git_problem(committed)}")
            return
        for attempt in range(1, PUSH_ATTEMPTS + 1):
            # -X theirs: in a rebase that favours our commit, so where an edit
            # collides with this run's generated tables, the run's version wins.
            synced = _git("pull", "--rebase", "--autostash", "-X", "theirs", "origin", branch)
            if synced.returncode == 0:
                pushed = _git("push", "origin", f"HEAD:{branch}")
                if pushed.returncode == 0:
                    log(f"git: pushed {url} to {branch}")
                    return
                synced = pushed
            log(f"WARNING: git sync attempt {attempt}/{PUSH_ATTEMPTS} failed: {_git_problem(synced)}")
            _git("rebase", "--abort")
        log(f"WARNING: could not push {url}; it stays committed locally and is retried "
            "with the next project")
    except (subprocess.SubprocessError, OSError) as exc:
        log(f"WARNING: git publish failed for {url} ({type(exc).__name__})")


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
        log(f"rate limit: could not read ({type(exc).__name__})")
        return None


def wait_until(epoch: float, why: str) -> None:
    """Sleep until ``epoch`` (plus a margin), logging a heartbeat while waiting."""
    resume_at = min(epoch + RESET_MARGIN_SECONDS, time.time() + MAX_WAIT_SECONDS)
    log(f"rate limit: {why}; waiting until {utc_from_epoch(resume_at)}")
    while (left := resume_at - time.time()) > 0:
        time.sleep(min(left, HEARTBEAT_SECONDS))
        left = resume_at - time.time()
        if left > 0:
            log(f"rate limit: still waiting, {fmt_duration(left)} to go")


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
            log(f"rate limit: now {rl['remaining']}/{rl['limit']} remaining; next reset "
                f"{utc_from_epoch(rl['reset'])}")
    return rl


def _timestamp_lines(stream) -> None:
    """Copy ``stream`` to the log, one stamped line at a time."""
    for line in stream:
        log(line.rstrip("\r\n"))


def run_with_deadline(cmd: list[str], seconds: float) -> int | None:
    """Run ``cmd`` and return its exit status, or None if it ran past ``seconds``.

    The command runs in its own process group so a timeout also kills anything
    it started (for example the pvtr plugins), not just the Python process.
    Every line it prints is logged with the UTC date and time it was written.
    """
    proc = subprocess.Popen(
        cmd, cwd=ROOT, start_new_session=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},  # so the time is when it was printed
    )
    pump = threading.Thread(target=_timestamp_lines, args=(proc.stdout,), daemon=True)
    pump.start()
    try:
        return proc.wait(timeout=max(seconds, 1))
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        return None
    finally:
        pump.join(timeout=10)


def project_paths(url: str) -> list[Path]:
    """Everything one project's assessment writes (the README and projects.json are shared)."""
    slug = _slug(url)
    return [
        *(ROOT / "trestle.ws" / kind / slug for kind in (
            "component-definitions", "system-security-plans",
            "assessment-plans", "assessment-results")),
        ROOT / "reports" / f"{slug}.md",
        DATA_FILE,
        ROOT / "README.md",
    ]


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def save_state(paths: list[Path], keep: Path) -> None:
    """Copy each path that exists into ``keep`` (numbered by position)."""
    for i, path in enumerate(paths):
        if path.is_dir():
            shutil.copytree(path, keep / str(i))
        elif path.is_file():
            shutil.copy2(path, keep / str(i))


def restore_state(paths: list[Path], keep: Path) -> None:
    """Put every path back as ``save_state`` found it, deleting what was not there."""
    for i, path in enumerate(paths):
        _remove(path)
        saved = keep / str(i)
        if saved.is_dir():
            shutil.copytree(saved, path)
        elif saved.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, path)


def assess_one(url: str) -> tuple[bool, dict | None, dict | None, float]:
    """Assess one project. Returns (ok, budget before, budget after, seconds).

    All or nothing: either the project's complete new result is in the working
    tree, or - if it failed or was stopped - everything it wrote is rolled back
    and its previous result is left exactly as it was.

    The project as a whole gets PROJECT_TIMEOUT_SECONDS; a project that takes
    longer is stopped and reported as failed so the run can move on.
    """
    before = read_budget_waiting_if_empty()
    started = time.monotonic()
    deadline = started + PROJECT_TIMEOUT_SECONDS
    ok = True
    paths = project_paths(url)
    with tempfile.TemporaryDirectory(prefix="assess-keep-") as tmp:
        keep = Path(tmp)
        save_state(paths, keep)
        for script, args in (("build_project_compliance.py", ["project", url]),
                             ("assess_project.py", [url])):
            status = run_with_deadline([sys.executable, str(SCRIPTS / script), *args],
                                       deadline - time.monotonic())
            if status is None:
                log(f"WARNING: {script} for {url} exceeded the {fmt_duration(PROJECT_TIMEOUT_SECONDS)} "
                    "project limit and was stopped")
                ok = False
                break
            if status == PRIVATEER_FAILED_EXIT:
                log(f"WARNING: Privateer could not evaluate {url}; "
                    "keeping its previous result (ASSESS_PRIVATEER_FAILURE=keep-previous)")
                ok = False
                break
            if status != 0:
                log(f"WARNING: {script} failed for {url}")
                ok = False
                break
        if not ok:
            restore_state(paths, keep)
            log(f"{url}: rolled back to its previous result; moving on")
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


def window_rolled_over(before: dict | None, after: dict | None) -> bool:
    """True if a new rate-limit window began while the project was running.

    Within one window the remaining count only goes down, so a higher count
    afterwards than before means the budget was refilled in between, and may
    have hit 0 first.
    """
    if not (before and after):
        return False
    return after["remaining"] > before["remaining"]


def assess_maturity(maturity: str) -> int:
    if maturity not in MATURITIES:
        print(f"maturity must be one of {', '.join(MATURITIES)}", file=sys.stderr)
        return 2

    projects = [p for p in json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if p.get("maturity") == maturity]
    to_assess = [p["repo_url"] for p in projects if p.get("repo_url")]
    log(f"[{maturity}] Assessing {len(to_assess)} project(s), "
        f"skipping {len(projects) - len(to_assess)}.")

    failed = []
    redone = []
    usage: list[tuple[str, int | None, int | None, float]] = []
    started = time.monotonic()
    for url in to_assess:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            log(f"=== {url} === attempt {attempt}")
            ok, before, after, secs = assess_one(url)
            used = None
            if after:
                if before and before["remaining"] >= after["remaining"]:
                    used = before["remaining"] - after["remaining"]  # else: window reset
                log(f"rate limit: {url} used {'?' if used is None else used} request(s) "
                    f"in {fmt_duration(secs)}; {after['remaining']}/{after['limit']} remaining "
                    f"(window resets {utc_from_epoch(after['reset'])})")
            else:
                log(f"{url} took {fmt_duration(secs)}")
            # Two signs that requests may have been refused during the project:
            #  - the budget is 0 afterwards: wait for the reset, then redo it;
            #  - the window rolled over mid-project: the budget may have hit 0 and
            #    refilled unseen, so redo it to be safe.
            exhausted = bool(after and after["remaining"] <= 0)
            rolled_over = window_rolled_over(before, after)
            if not (exhausted or rolled_over):
                break
            why = ("budget exhausted" if exhausted else
                   "rate-limit window reset mid-project, so exhaustion can't be ruled out")
            log(f"WARNING: {why} during {url}; its result may be incomplete")
            if attempt == MAX_ATTEMPTS:
                log(f"WARNING: giving up on a clean result for {url}")
                break
            redone.append(url)
            if exhausted:
                wait_until(after["reset"], "waiting for the budget before redoing the project")
        if not ok:
            failed.append(url)
        push_progress(url)
        usage.append((url, used, after["remaining"] if after else None, secs))
    elapsed = time.monotonic() - started
    log(f"[{maturity}] Finished {len(to_assess)} project(s) in {fmt_duration(elapsed)}")
    write_step_summary(maturity, usage, elapsed)

    if redone:
        log(f"[{maturity}] Redone after the budget ran out ({len(redone)}):")
        for u in redone:
            log(f"  {u}")
    if failed:
        log(f"[{maturity}] Failed assessments ({len(failed)}):")
        for u in failed:
            log(f"  {u}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("maturity", choices=MATURITIES)
    return assess_maturity(ap.parse_args().maturity)


if __name__ == "__main__":
    sys.exit(main())
