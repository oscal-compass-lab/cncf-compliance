"""Check implementation: makefile-target."""

import re
from pathlib import Path
from . import register_check


@register_check("makefile-target")
def check_make_target(control_id: str, param_names: list[str], params: dict[str, str],
                      repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies that a specific target is declared in the pipeline file."""
    target = params.get(param_names[0], "") if param_names else ""
    pipeline_file = params.get("pipeline-file", "Makefile")

    f = repo_root / pipeline_file
    if not f.is_file():
        return False, f"{pipeline_file} not found", "fail"

    ok = re.search(rf"^{re.escape(target)}\s*:", f.read_text(encoding="utf-8", errors="ignore"), re.M) is not None
    evidence = f"Target '{target}' {'found' if ok else 'not found'} in {pipeline_file}"
    return ok, evidence, "pass" if ok else "fail"
