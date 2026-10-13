"""Check implementation: git-commits-signed."""

import re
import subprocess
from pathlib import Path
from . import register_check


def _git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=cwd, timeout=30)
    return r.stdout.strip()


@register_check("git-commits-signed")
def check_commits_signed(control_id: str, param_names: list[str], params: dict[str, str],
                         repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies that recent git commits carry valid GPG or SSH cryptographic signatures."""
    lookback = params.get("signed-commits-lookback", "10")
    exempt_pattern = params.get("signed-commits-exempt-pattern", "")

    n = int(lookback) if lookback.isdigit() else 10
    raw = [s for s in _git(["log", f"-{n}", "--format=%G?|%an|%s"], repo_root).splitlines() if s.strip()]
    if not raw:
        return False, "No commits found", "fail"

    exempt_re = re.compile(exempt_pattern) if exempt_pattern else None
    evaluated = []
    exempted = 0

    for line in raw:
        sig, _, rest = line.partition("|")
        author, _, msg = rest.partition("|")
        sig = sig.strip()
        is_bot = "bot" in author.lower() or author == "semantic-release"
        is_release_msg = bool(exempt_re and exempt_re.search(msg.strip()))

        if sig == "N" and is_bot and is_release_msg:
            exempted += 1
            continue
        evaluated.append(sig)

    if not evaluated:
        return True, f"All {exempted} recent commits were excused release bot commits", "pass"

    unsigned = sum(1 for s in evaluated if s == "N")
    signed = len(evaluated) - unsigned
    details = f"{signed}/{len(evaluated)} recent commits carry a signature"
    if exempted > 0:
        details += f" ({exempted} release bot commits excused)"

    ok = unsigned == 0
    return ok, details, "pass" if ok else "fail"
