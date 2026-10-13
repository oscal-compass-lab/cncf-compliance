"""Check implementation: file-exists."""

from pathlib import Path
from . import register_check


@register_check("file-exists")
def check_file_exists(control_id: str, param_names: list[str], params: dict[str, str],
                      repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies that all specified target paths exist in the repository."""
    paths = [params.get(n, "") for n in param_names]
    missing = [p for p in paths if not p or not (repo_root / p).exists()]
    if missing:
        evidence = f"Missing: {', '.join(missing) or '(no path configured)'}"
        return False, evidence, "fail"
    evidence = f"Found: {', '.join(paths)}"
    return True, evidence, "pass"
