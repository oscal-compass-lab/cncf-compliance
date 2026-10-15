"""Wrapper around Privateer (pvtr) and its plugins.

Two plugins are run as two services of one ``pvtr run``: ``github-repo``
(OSPS Baseline requirements) and our own ``cncf-controls`` (the CNCF MUST
controls, see privateer-plugins/cncf-controls). Privateer evaluates a whole
repository in a single run, so this module runs it once per repository and
caches the flattened results. Individual ``privateer`` checks then look their
requirement up here instead of running Privateer themselves.

Install the pinned binaries with scripts/privateer/install.sh. A GitHub token
must be available in GITHUB_TOKEN; it is handed to pvtr through a temporary
0600 config file that is removed as soon as the run ends.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIVATEER_DIR = ROOT / ".privateer"
PVTR = PRIVATEER_DIR / "bin" / "pvtr"
PLUGINS_DIR = PRIVATEER_DIR / "plugins"
RESULTS_DIR = PRIVATEER_DIR / "evaluation_results"

# pvtr only detects plugins registered with `pvtr install --local`; they are
# then addressed as local/<name>. Requirement ids are unique across catalogs
# (OSPS-... versus CNSC-...), so results are keyed by requirement alone.
PLUGINS = {
    # service name: (plugin binary name, catalog)
    "target": ("github-repo", "osps-baseline"),
    "must": ("cncf-controls", "cncf-must-controls"),
}
APPLICABILITY = ["maturity-1", "maturity-2", "maturity-3"]
RUN_TIMEOUT_SECONDS = 240


class PrivateerError(Exception):
    """Privateer could not produce results for the repository."""


# repo key -> parsed results, or the PrivateerError from the first attempt so a
# missing binary or token is not retried for every control.
_cache: dict[str, dict | PrivateerError] = {}


def evaluate(repo_url: str) -> dict:
    """Return ``{"requirements": {requirement_id: assessment_log}}``.

    Each log carries the ``plugin`` that produced it.

    Raises PrivateerError when Privateer is unavailable or the run failed.
    """
    key = repo_url.strip().rstrip("/").lower()
    cached = _cache.get(key)
    if cached is None:
        try:
            cached = _run(repo_url)
        except PrivateerError as exc:
            cached = exc
        _cache[key] = cached
    if isinstance(cached, PrivateerError):
        raise cached
    return cached


def _run(repo_url: str) -> dict:
    m = re.search(r"github\.com[:/]([^/]+)/(.+?)(?:\.git)?/*$", repo_url)
    if not m:
        raise PrivateerError(f"not a GitHub repository URL: {repo_url}")
    owner, repo = m.groups()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise PrivateerError("GITHUB_TOKEN is not set")
    exes = [PVTR] + [PRIVATEER_DIR / "bin" / name for name, _ in PLUGINS.values()]
    for exe in exes:
        if not exe.exists():
            raise PrivateerError(f"{exe.name} is not installed; run scripts/privateer/install.sh")

    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    for exe in exes[1:]:
        try:
            subprocess.run(
                [str(PVTR), "install", "--local", str(exe), "-b", str(PLUGINS_DIR)],
                check=True, capture_output=True, text=True, timeout=60,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            raise PrivateerError(f"could not register the {exe.name} plugin: {type(exc).__name__}")

    out_dir = RESULTS_DIR / f"{owner}--{repo}"
    out_dir.mkdir(parents=True, exist_ok=True)
    for service in PLUGINS:
        (out_dir / service / f"{service}.json").unlink(missing_ok=True)

    config = {
        "loglevel": "error",
        "write": True,
        "output": "json",
        "services": {
            service: {
                "plugin": f"local/{name}",
                "policy": {"catalogs": [catalog], "applicability": APPLICABILITY},
                "vars": {"owner": owner, "repo": repo, "token": token},
            }
            for service, (name, catalog) in PLUGINS.items()
        },
    }
    with tempfile.TemporaryDirectory(prefix="pvtr-") as tmp:
        cfg = Path(tmp) / "config.json"
        fd = os.open(cfg, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f)
        try:
            proc = subprocess.run(
                [str(PVTR), "run", "-c", str(cfg), "-b", str(PLUGINS_DIR), "-w", str(out_dir)],
                check=False, capture_output=True, text=True, timeout=RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise PrivateerError(f"pvtr run timed out after {RUN_TIMEOUT_SECONDS}s")

    requirements: dict[str, dict] = {}
    missing = []
    for service, (name, _catalog) in PLUGINS.items():
        result_file = out_dir / service / f"{service}.json"
        if not result_file.exists():
            missing.append(name)
            continue
        data = json.loads(result_file.read_text(encoding="utf-8"))
        plugin = f"{data.get('plugin-name', name)} {data.get('plugin-version', '')}".strip()
        for suite in data.get("evaluation-suites", []):
            for ev in suite.get("control-evaluations", {}).get("evaluations", []):
                for log in ev.get("assessment-logs", []):
                    log["plugin"] = plugin
                    requirements[log["requirement"]["entry-id"]] = log
    if missing and not requirements:
        detail = " ".join(proc.stderr.split())[-300:].replace(token, "***")
        raise PrivateerError(f"pvtr produced no results ({detail or 'no output'})")
    # A plugin that produced nothing leaves its requirements unevaluated, which
    # privateer.py reports as "no-result", never as a pass.
    return {"requirements": requirements}
