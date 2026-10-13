"""Check implementation: ci-sast."""

import re
from pathlib import Path
from . import register_check
from .ci_vuln_scan import _find_workflow_match


@register_check("ci-sast")
def check_ci_sast(control_id: str, param_names: list[str], params: dict[str, str],
                  repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies static application security testing (SAST) in pipeline targets or CI workflows."""
    target = params.get("sast-target", "sast")
    workflows = params.get("sast-workflows", "codeql,scorecard,sonar,sast,gosec,bandit,semgrep,ruff")
    pipeline_file = params.get("pipeline-file", "Makefile")

    f = repo_root / pipeline_file
    if f.is_file() and target:
        if re.search(rf"^{re.escape(target)}\s*:", f.read_text(encoding="utf-8", errors="ignore"), re.M):
            return True, f"Target '{target}' found in {pipeline_file}", "pass"

    matched_wf = _find_workflow_match(workflows, repo_root)
    if matched_wf:
        return True, f"Found CI SAST workflow: .github/workflows/{matched_wf.name}", "pass"

    return False, f"Target '{target}' not in {pipeline_file} and no SAST workflow in .github/workflows", "fail"
