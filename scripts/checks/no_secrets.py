"""Check implementation: no-secrets-in-files."""

import re
from pathlib import Path
from . import register_check

SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|secret|api.?key|private.?key|token)\s*=\s*['\"][^'\"]{6,}"
)


@register_check("no-secrets-in-files")
def check_no_secrets(control_id: str, param_names: list[str], params: dict[str, str],
                     repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Scans repository files for hardcoded secrets or credentials."""
    extensions_raw = params.get("secrets-scan-extensions", "py,sh,yaml,yml,env,cfg,ini")
    excludes_raw = params.get("secrets-scan-exclude-paths", ".venv,trestle.ws,.git,dist")

    excludes = {e.strip() for e in excludes_raw.split(",") if e.strip()}
    extensions = [e.strip() for e in extensions_raw.split(",") if e.strip()]

    findings: list[str] = []
    for ext in extensions:
        for f in repo_root.rglob(f"*.{ext}"):
            rel = f.relative_to(repo_root)
            if excludes & set(rel.parts) or not f.is_file():
                continue
            try:
                if SECRET_PATTERN.search(f.read_text(encoding="utf-8", errors="ignore")):
                    findings.append(str(rel))
            except OSError:
                continue

    if findings:
        shown = ", ".join(findings[:5]) + (f" (+{len(findings) - 5} more)" if len(findings) > 5 else "")
        return False, f"Potential hardcoded secrets in: {shown}", "fail"

    return True, "No hardcoded secrets detected", "pass"
