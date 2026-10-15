"""Check implementation: privateer.

Spec form: ``privateer | plugin: github-repo; requirement: OSPS-GV-03.01``
(or ``plugin: cncf-controls; requirement: CNSC-182.01``)

The result comes from the Privateer run for the repository (see
privateer_client). Only Passed and Failed are decisive. Anything else (Needs
Review, Unknown, Not Applicable, Not Run, or Privateer being unavailable) is
reported as "no-result" so it is never counted as a pass.
"""

from pathlib import Path
from . import register_check
from . import privateer_client


@register_check("privateer")
def check_privateer(control_id: str, param_names: list[str], params: dict[str, str],
                    repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Look up one requirement in the Privateer results."""
    # dispatch_check splits the spec on ';', so each entry is "key: value".
    requirement = next(
        (n.partition(":")[2].strip() for n in param_names if n.startswith("requirement:")), ""
    )
    if not requirement:
        return False, "No Privateer requirement configured for this control.", "no-result"

    try:
        run = privateer_client.evaluate(repo_url)
    except privateer_client.PrivateerError as exc:
        return False, f"Privateer unavailable: {exc}", "no-result"

    log = run["requirements"].get(requirement)
    if log is None:
        return False, f"Privateer did not evaluate {requirement}.", "no-result"

    status = log.get("result", "Unknown")
    confidence = log.get("confidence-level")
    message = " ".join(str(log.get("message", "")).split())
    evidence = f"Privateer {log['plugin']} {requirement}: {status}"
    if confidence:
        evidence += f" ({confidence} confidence)"
    if message:
        evidence += f". {message}"

    if status == "Passed":
        return True, evidence, "pass"
    if status == "Failed":
        return False, evidence, "fail"
    return False, evidence, "no-result"
