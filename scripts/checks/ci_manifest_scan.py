"""Check implementation: ci-manifest-scan."""

import re
from pathlib import Path
from . import register_check
from .ci_vuln_scan import _find_workflow_match


@register_check("ci-manifest-scan")
def check_ci_manifest_scan(control_id: str, param_names: list[str], params: dict[str, str],
                           repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies manifest scanning/linting in pipeline targets or CI workflows."""
    target = params.get("manifest-scan-target", "act-lint")
    workflows = params.get("manifest-scan-workflows", "actionlint,kube-linter,yamllint,checkov,trivy,lint")
    pipeline_file = params.get("pipeline-file", "Makefile")

    f = repo_root / pipeline_file
    if f.is_file() and target:
        if re.search(rf"^{re.escape(target)}\s*:", f.read_text(encoding="utf-8", errors="ignore"), re.M):
            return True, f"Target '{target}' found in {pipeline_file}", "pass"

    matched_wf = _find_workflow_match(workflows, repo_root)
    if matched_wf:
        return True, f"Found CI manifest scanning workflow: .github/workflows/{matched_wf.name}", "pass"

    return False, f"Target '{target}' not in {pipeline_file} and no manifest scanning workflow in .github/workflows", "fail"
