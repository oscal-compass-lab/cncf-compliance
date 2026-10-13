"""Check implementation: ci-vuln-scan."""

import re
from pathlib import Path
from . import register_check


def _find_workflow_match(keywords: str, repo_root: Path) -> Path | None:
    wf_dir = repo_root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return None
    kws = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    for wf in sorted(wf_dir.glob("*.y*ml")):
        stem = wf.stem.lower()
        if any(k in stem for k in kws):
            return wf
        try:
            content = wf.read_text(encoding="utf-8", errors="ignore").lower()
            if any(k in content for k in kws):
                return wf
        except OSError:
            continue
    return None


@register_check("ci-vuln-scan")
def check_ci_vuln_scan(control_id: str, param_names: list[str], params: dict[str, str],
                       repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Verifies vulnerability scanning in pipeline targets or CI workflows."""
    target = params.get("pipeline-vuln-scan-target", "audit-deps")
    workflows = params.get("vuln-scan-workflows", "codeql,scorecard,trivy,snyk,sonar,vuln,audit,security,actionlint")
    pipeline_file = params.get("pipeline-file", "Makefile")

    f = repo_root / pipeline_file
    if f.is_file() and target:
        if re.search(rf"^{re.escape(target)}\s*:", f.read_text(encoding="utf-8", errors="ignore"), re.M):
            return True, f"Target '{target}' found in {pipeline_file}", "pass"

    matched_wf = _find_workflow_match(workflows, repo_root)
    if matched_wf:
        return True, f"Found CI vulnerability/security scanning workflow: .github/workflows/{matched_wf.name}", "pass"

    return False, f"Target '{target}' not in {pipeline_file} and no scanning workflow in .github/workflows", "fail"
