#!/usr/bin/env python3
"""Control -> Privateer (OSPS Baseline) check mapping: single source of truth.

Every CNCF control that is in scope for git repositories (that is, in the
cncf-repo profile, which scripts/generate_profile.py writes from this mapping;
all other catalog controls are out of scope) is in exactly one of:

  MAPPED    control -> (requirement, fidelity, note)
            The control is checked by that requirement of a Privateer plugin:
            an OSPS Baseline requirement of ``github-repo`` (OSPS-...), or a
            requirement of our own ``cncf-controls`` plugin (CNSC-nnn.01, see
            privateer-plugins/cncf-controls) where the Baseline has none. Each
            requirement is used by at most one control, so every mapped
            control has a check no other control shares.
  UNMAPPED  control -> reason
            No unique Privateer check can be defined, for the stated reason.
            The control is reported as "not determined" and is never counted
            as a pass.

Fidelity:
  exact    the OSPS requirement states what the control states.
  partial  a pass is necessary but not sufficient evidence for the control;
           the note says what is not covered.

Run this file to regenerate docs/privateer-check-coverage.md.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "trestle.ws" / "catalogs" / "cncf-controls" / "catalog.json"
COVERAGE_DOC = ROOT / "docs" / "privateer-check-coverage.md"

MAPPED: dict[str, tuple[str, str, str]] = {
    "CNSC-65":  ("OSPS-VM-05.03", "partial", "Covers automated vulnerability evaluation of every change. IDE scanning and configuration scanning are not covered."),
    "CNSC-67":  ("OSPS-QA-06.01", "exact", "CI runs at least one automated test suite before a commit is accepted."),
    "CNSC-69":  ("OSPS-QA-06.02", "partial", "Covers documentation of when and how tests are run, not whether they run locally. Always needs review."),
    "CNSC-82":  ("OSPS-VM-06.02", "partial", "Covers automated evaluation for security weaknesses that blocks violations. Requires a documented policy."),
    "CNSC-121": ("OSPS-SA-03.02", "exact", "Threat modeling and attack surface analysis are performed."),
    "CNSC-155": ("OSPS-DO-07.01", "partial", "Covers documented build instructions with required libraries, SDKs and dependencies, not a machine-recorded build environment."),
    "CNSC-175": ("OSPS-QA-02.01", "exact", "The repository contains a dependency list for direct language dependencies."),
    "CNSC-177": ("OSPS-BR-05.01", "partial", "Covers use of standardized dependency tooling, not a prioritized list of trusted repositories."),
    "CNSC-178": ("OSPS-QA-02.02", "partial", "Covers an SBOM delivered with released assets, not that it is immutable."),
    "CNSC-183": ("OSPS-QA-03.01", "partial", "Covers mandatory passing status checks on the primary branch, not attestations."),
    "CNSC-185": ("OSPS-GV-01.01", "exact", "Documentation lists the members with access to sensitive resources."),
    "CNSC-187": ("OSPS-GV-03.01", "partial", "Covers an explained contribution process, not adherence to it."),
    "CNSC-188": ("OSPS-GV-01.02", "exact", "Documentation describes member roles and responsibilities."),
    "CNSC-182": ("CNSC-182.01", "partial", "Covers the 20 most recent default-branch commits and 10 most recent tags, not the full history. Unsigned commits and tags made by release automation (bot accounts, semantic-release) are excused and counted in the result."),
    "CNSC-184": ("CNSC-184.01", "partial", "Gitleaks scan of the files of the default branch (up to 1 MiB each), not of the Git history. Binary and larger files are skipped."),
    "CNSC-190": ("CNSC-190.01", "exact", "Branch protection or a ruleset restricts pushes or requires approving reviews on the default branch. Reuses the github-repo step of OSPS-AC-03.01."),
    "CNSC-191": ("OSPS-AC-01.01", "exact", "Multi-factor authentication is required for sensitive resources."),
    "CNSC-193": ("OSPS-BR-07.02", "partial", "Covers a documented policy for managing secrets and credentials, including rotation, not key rotation specifically."),
    "CNSC-198": ("CNSC-198.01", "partial", "GitHub secret scanning and push protection are in use (the github-repo step of OSPS-BR-07.01) and the gitleaks scan of the default branch finds no secrets. The scan covers files, not history."),
    "CNSC-199": ("CNSC-199.01", "partial", "Recent default-branch commits are signed (release automation excused) and the branch requires signed commits through branch protection or a ruleset. Enforcement is observable only with admin access."),
    "CNSC-205": ("OSPS-GV-04.01", "partial", "Covers a policy for reviewing collaborators before escalated permissions, not the size of the approved set."),
    "CNSC-265": ("OSPS-QA-07.01", "exact", "The primary branch requires at least one non-author human approval."),
}

_NO_REQ = "The OSPS Baseline has no requirement for this."
_TAKEN = "The only related OSPS requirement is used by {other}, which states it more precisely."

UNMAPPED: dict[str, str] = {
    "CNSC-68":  "The only OSPS test requirement (OSPS-QA-06.01) is used by CNSC-67 and does not distinguish infrastructure tests.",
    "CNSC-71":  "OSPS-QA-07.01 requires one approval, not two, and is used by CNSC-265. A pass would overstate this control.",
    "CNSC-72":  "Code cleanliness and commenting are not evaluated by the OSPS Baseline.",
    "CNSC-73":  "The only OSPS test requirement (OSPS-QA-06.01) is used by CNSC-67 and does not distinguish full infrastructure tests.",
    "CNSC-74":  "The only OSPS test requirement (OSPS-QA-06.01) is used by CNSC-67 and does not identify regression tests.",
    "CNSC-75":  "OSPS-QA-06.03 covers a policy to update tests with changes, not security regression tests driven by emerging threats.",
    "CNSC-78":  "OSPS-SA-03.02 checks that a threat model exists (CNSC-121), not that it drives test priorities.",
    "CNSC-85":  "The Baseline analyses workflows for risks (OSPS-BR-01.x) but does not check that manifests are scanned in CI.",
    "CNSC-150": "Checksum and signature validation of dependencies is not evaluated by the OSPS Baseline.",
    "CNSC-152": "Reproducible builds are not evaluated by the OSPS Baseline.",
    "CNSC-153": "Hash pinning and locking of external requirements are not evaluated by the OSPS Baseline.",
    "CNSC-154": "Build determinism is not evaluated by the OSPS Baseline.",
    "CNSC-156": "OSPS-DO-07.01 (used by CNSC-155) detects build documentation or automation but not automated creation of the build environment.",
    "CNSC-158": "The Baseline does not check that build and CI/CD steps are defined as code.",
    "CNSC-159": "Pipeline standardization across projects is not evaluated by the OSPS Baseline.",
    "CNSC-165": "Separate secured storage for pipeline output is not evaluated by the OSPS Baseline.",
    "CNSC-166": "Immutability of pipeline configuration is not evaluated by the OSPS Baseline.",
    "CNSC-167": "The only related OSPS requirement (OSPS-GV-01.02) is used by CNSC-188, which states it more precisely.",
    "CNSC-168": "Root-of-trust establishment from an offline source is not evaluated by the OSPS Baseline.",
    "CNSC-173": "Verification of third-party artifacts is not evaluated by the OSPS Baseline.",
    "CNSC-174": "OSPS-QA-02.02 covers the project's own SBOM (CNSC-178), not SBOMs required from suppliers.",
    "CNSC-179": "The only OSPS requirement for automated vulnerability evaluation (OSPS-VM-05.03) is used by CNSC-65.",
    "CNSC-180": "License scanning of dependencies is not evaluated by the OSPS Baseline. OSPS-LE-02.01 checks the project's own license.",
    "CNSC-181": "The only OSPS requirement for automated dependency evaluation (OSPS-VM-05.03) is used by CNSC-65.",
    "CNSC-186": "The only OSPS requirement for automated security scanning (OSPS-VM-06.02) is used by CNSC-82. DAST is not evaluated.",
    "CNSC-189": "OSPS-QA-07.01 is used by CNSC-265. It does not test that the author differs from the approver or that there are two reviewers.",
    "CNSC-195": "Secure defaults of the software are not evaluated by the repository-level OSPS Baseline.",
    "CNSC-196": "This umbrella control has no single OSPS equivalent. Related practices are covered by CNSC-175, CNSC-177 and CNSC-178.",
    "CNSC-197": "The OSPS requirement for restricting branch access (OSPS-AC-03.01) is used by CNSC-190. OSPS-AC-02.01 is enforced by GitHub for every project, so it would pass unconditionally.",
    "CNSC-200": "Linear history and force-push protection are not evaluated by the OSPS Baseline. OSPS-AC-03.02 covers branch deletion only.",
    "CNSC-201": "The related OSPS requirements (OSPS-AC-03.01, OSPS-QA-07.01) are used by CNSC-190 and CNSC-265.",
    "CNSC-202": "Monitoring and updating of Git and GitOps tooling is not observable from the repository.",
    "CNSC-259": "The only OSPS requirement for automated vulnerability evaluation (OSPS-VM-05.03) is used by CNSC-65, which this control duplicates.",
}

assert not set(MAPPED) & set(UNMAPPED), "a control is both mapped and unmapped"
_reqs = [v[0] for v in MAPPED.values()]
assert len(_reqs) == len(set(_reqs)), "a requirement is used by more than one control"
assert all(v[1] in ("exact", "partial") for v in MAPPED.values())


def plugin_for(requirement: str) -> str:
    """The Privateer plugin that evaluates a requirement."""
    return "cncf-controls" if requirement.startswith("CNSC-") else "github-repo"


def load_catalog() -> dict[str, tuple[str, str, str]]:
    """control_id -> (group title, control title, statement) from the OSCAL catalog."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["catalog"]
    out: dict[str, tuple[str, str, str]] = {}

    def walk(groups: list[dict]) -> None:
        for g in groups:
            for c in g.get("controls", []):
                statement = next((p.get("prose", "") for p in c.get("parts", [])
                                  if p.get("name") == "statement"), "")
                out[c["id"]] = (g.get("title", ""), c.get("title", ""), statement)
            walk(g.get("groups", []))

    walk(catalog.get("groups", []))
    return out


def _nat(cid: str) -> int:
    return int(cid.split("-")[1])


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def render_coverage() -> str:
    cat = load_catalog()
    total = len(MAPPED) + len(UNMAPPED)
    lines = [
        "# Privateer check coverage",
        "",
        "Generated by [`scripts/privateer_mapping.py`](../scripts/privateer_mapping.py). "
        "Do not edit by hand.",
        "",
        "Every control in the `cncf-repo` profile (the controls in scope for git repositories) "
        "is checked by its own Privateer requirement, or has no check for the stated reason. "
        "Requirements come from two plugins: `github-repo`, which evaluates the "
        "[OSPS Baseline](https://baseline.openssf.org), and our own `cncf-controls` plugin "
        "([`privateer-plugins/cncf-controls`](../privateer-plugins/cncf-controls)), which covers the "
        "five controls the Baseline cannot. No requirement is used by more than one control.",
        "",
        f"- **Controls in scope:** {total}",
        f"- **With a unique Privateer check:** {len(MAPPED)} "
        f"({sum(v[1] == 'exact' for v in MAPPED.values())} exact, "
        f"{sum(v[1] == 'partial' for v in MAPPED.values())} partial)",
        f"- **Without a unique Privateer check:** {len(UNMAPPED)}",
        "",
        "A partial mapping means a pass is necessary but not sufficient evidence for the control. "
        "A control without a check is reported as not determined and never counts as a pass.",
        "",
        "## Controls with a Privateer check",
        "",
        "| Control | Title | Plugin | Requirement | Fidelity | What the check covers |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for cid in sorted(MAPPED, key=_nat):
        osps, fidelity, note = MAPPED[cid]
        lines.append(f"| {cid} | {_cell(cat[cid][1])} | {plugin_for(osps)} | {osps} | {fidelity} | {_cell(note)} |")
    lines += [
        "",
        "## Controls without a Privateer check",
        "",
        "| Control | Title | Reason |",
        "| --- | --- | --- |",
    ]
    for cid in sorted(UNMAPPED, key=_nat):
        lines.append(f"| {cid} | {_cell(cat[cid][1])} | {_cell(UNMAPPED[cid])} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    COVERAGE_DOC.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_DOC.write_text(render_coverage(), encoding="utf-8")
    print(f"Written: {COVERAGE_DOC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
