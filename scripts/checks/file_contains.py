"""Check implementation: file-contains."""

import re
from pathlib import Path
from . import register_check


@register_check("file-contains")
def check_file_contains(control_id: str, param_names: list[str], params: dict[str, str],
                        repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies that a specific regex pattern is found inside a target file."""
    if len(param_names) < 2:
        return False, "Check misconfigured: requires file and pattern parameters", "fail"

    target_file = params.get(param_names[0], "")
    pattern = params.get(param_names[1], "")

    f = repo_root / target_file
    if not f.is_file():
        return False, f"File not found: {target_file}", "fail"

    try:
        ok = re.search(pattern, f.read_text(encoding="utf-8", errors="ignore")) is not None
    except re.error as exc:
        return False, f"Invalid regex pattern {pattern!r}: {exc}", "fail"

    evidence = f"Pattern {pattern!r} {'found' if ok else 'not found'} in {target_file}"
    return ok, evidence, "pass" if ok else "fail"
