"""Registry and dispatcher for CNCF compliance checks."""

from pathlib import Path
from typing import Callable

# Signature: (control_id: str, param_names: list[str], params: dict[str, str], repo_root: Path, repo_url: str) -> (satisfied, evidence, reason)
CheckHandler = Callable[[str, list[str], dict[str, str], Path, str], tuple[bool, str, str]]

REGISTRY: dict[str, CheckHandler] = {}


def register_check(name: str):
    """Decorator to register a check implementation by its check spec identifier."""
    def decorator(fn: CheckHandler):
        REGISTRY[name] = fn
        return fn
    return decorator


def dispatch_check(control_id: str, spec: str, params: dict[str, str],
                   repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Parse check spec and dispatch to the registered check implementation."""
    ctype, _, rest = (s.strip() for s in spec.partition("|"))
    param_names = [n.strip() for n in rest.replace("param:", "", 1).split(";") if n.strip()]

    if ctype == "manual":
        return False, "Manual check - requires human review; not automated.", "other"

    handler = REGISTRY.get(ctype)
    if not handler:
        return False, f"No implementation registered for check type: {ctype}", "other"

    return handler(control_id, param_names, params, repo_root, repo_url)


# Import all separate check implementation modules to register them
from . import file_exists  # noqa: E402, F401
from . import file_contains  # noqa: E402, F401
from . import no_secrets  # noqa: E402, F401
from . import git_commits_signed  # noqa: E402, F401
from . import git_branch_protected  # noqa: E402, F401
from . import makefile_target  # noqa: E402, F401
from . import ci_vuln_scan  # noqa: E402, F401
from . import ci_sast  # noqa: E402, F401
from . import ci_manifest_scan  # noqa: E402, F401
