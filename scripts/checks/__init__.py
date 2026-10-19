"""Registry and dispatcher for CNCF compliance checks (Privateer only)."""

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

    handler = REGISTRY.get(ctype)
    if not handler:
        return False, f"No implementation registered for check type: {ctype}", "no-result"

    return handler(control_id, param_names, params, repo_root, repo_url)


# Import the check implementation module to register it
from . import privateer  # noqa: E402, F401
