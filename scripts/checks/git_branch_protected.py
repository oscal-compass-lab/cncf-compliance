"""Check implementation: git-branch-protected."""

import json
import os
import re
import urllib.request
from pathlib import Path
from . import register_check

_branch_cache: dict[str, tuple[bool, str]] = {}


@register_check("git-branch-protected")
def check_branch_protected(control_id: str, param_names: list[str], params: dict[str, str],
                           repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies branch protection rules on the default repository branch via GitHub API."""
    branch = params.get("default-branch", "main")
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", repo_url)
    if not m:
        return False, f"Cannot parse GitHub URL: {repo_url}", "fail"

    key = f"{m.group(1)}@{branch}"
    if key in _branch_cache:
        protected, ev = _branch_cache[key]
        return protected, ev, "pass" if protected else "fail"

    headers = {"Accept": "application/vnd.github+json", "User-Agent": "cncf-compliance-assessor"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        f"https://api.github.com/repos/{m.group(1)}/branches/{branch}", headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 fixed https URL
            protected = bool(json.loads(resp.read()).get("protected", False))
        result = (protected, f"Branch '{branch}' protected={protected}")
    except Exception as exc:
        result = (False, f"GitHub API error for branch '{branch}': {type(exc).__name__}")

    _branch_cache[key] = result
    protected, ev = result
    return protected, ev, "pass" if protected else "fail"
