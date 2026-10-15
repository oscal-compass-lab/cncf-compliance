"""Check implementation: privateer.

Spec form: ``privateer | plugin: github-repo; requirement: OSPS-GV-03.01``
(or ``plugin: cncf-controls; requirement: CNSC-182.01``)

The result comes from the Privateer run for the repository (see
privateer_client). Only Passed and Failed are decisive. Anything else (Needs
Review, Unknown, Not Applicable, Not Run, or Privateer being unavailable) is
reported as "no-result" so it is never counted as a pass.
"""

import html
import re
import sys
from pathlib import Path
from . import register_check
from . import privateer_client

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from privateer_mapping import plugin_for  # noqa: E402


# "Privateer <plugin> <version> <requirement>: <Status>[ (<n> confidence)]. <message>"
_EVIDENCE_RE = re.compile(
    r"^Privateer (?P<plugin>\S+) (?P<version>\S+) (?P<req>\S+): (?P<status>[A-Za-z ]+?)"
    r"(?: \((?P<conf>\w+) confidence\))?(?:\. (?P<msg>.*))?$",
    re.S,
)


def evidence_with_hover(evidence: str) -> str:
    """HTML for a report cell: the finding, with its provenance on hover.

    The hover text says first whether the check is supplied by Privateer itself
    or by our own plug-in. Evidence not in the Privateer format is returned as
    plain text.
    """
    m = _EVIDENCE_RE.match(evidence)
    if not m:
        return evidence
    if plugin_for(m["req"]) == "github-repo":
        supplier = f"Check supplied by Privateer (plugin {m['plugin']} {m['version']})"
    else:
        supplier = (
            f"Check supplied by our own plug-in ({m['plugin']} {m['version']}; "
            "0.0.0 means an unreleased local build)"
        )
    tip = f"{supplier}. Requirement {m['req']}. Result: {m['status']}" + (
        f", {m['conf']} confidence (how sure the check is)." if m["conf"] else "."
    )
    return f'<span title="{html.escape(tip, quote=True)}">{m["msg"] or m["status"]}</span>'


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
