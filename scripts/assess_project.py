#!/usr/bin/env python3
"""Run the automated checks for a CNCF project and write OSCAL assessment results.

Reads, from the trestle workspace:
  * the shared base component definition  (check spec per control + default params)
  * the project's SSP                     (probed param values for this project)
Runs each control's check against a clone of the project's repository and writes:

  <trestle-ws>/assessment-results/<slug>/assessment-results.json

Each control yields one observation (the evidence) and one finding
(satisfied / not-satisfied).  Controls whose check type is "manual" - or that
cannot be meaningfully checked against a clone - are reported as not-satisfied
with reason "other" so they are never counted as passes.

Usage:
    python scripts/assess_project.py <repo-url> [--trestle-ws PATH] [--clone-dir PATH]

Set GITHUB_TOKEN to authenticate GitHub API calls (higher rate limit).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from trestle.oscal import OSCAL_VERSION
from trestle.oscal import assessment_results as ar_mod
from trestle.oscal import common

from build_project_compliance import REQUIREMENTS, _repo_name, _slug, clone_repo, _git
from checks import dispatch_check

# Checks that read the clone's own .git/config say nothing about how project
# developers access the upstream repo, so they are not evaluated automatically.
NOT_ASSESSABLE_ON_CLONE = {"CNSC-192"}


def run_check(control_id: str, spec: str, params: dict[str, str],
              repo_root: Path, repo_url: str) -> tuple[bool, str, str]:
    """Return (satisfied, evidence, reason) where reason is pass/fail/other."""
    if control_id in NOT_ASSESSABLE_ON_CLONE:
        return False, "Not assessable against a clone of the repository.", "other"
    return dispatch_check(control_id, spec, params, repo_root, repo_url)


# ---------------------------------------------------------------------------
# Load check specs, defaults and project params from the workspace
# ---------------------------------------------------------------------------

def load_base(path: Path) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return ({control_id: check_spec}, {param_id: default}, {control_id: rule}) from the base comp def."""
    data = json.loads(path.read_text(encoding="utf-8"))["component-definition"]
    specs: dict[str, str] = {}
    defaults: dict[str, str] = {}
    rules: dict[str, str] = {}

    rule_to_desc: dict[str, str] = {}
    rule_to_check: dict[str, str] = {}
    ctrl_to_rule: dict[str, str] = {}

    for c in data["components"]:
        # Extract rule and check metadata from component-level props
        curr_rule_id = None
        for p in c.get("props", []):
            name = p.get("name")
            val = p.get("value")
            if name == "Rule_Id":
                curr_rule_id = val
            elif name == "Rule_Description" and curr_rule_id:
                rule_to_desc[curr_rule_id] = val
            elif name == "Check_Description" and curr_rule_id:
                rule_to_check[curr_rule_id] = val

        for ci in c.get("control-implementations", []):
            for sp in ci.get("set-parameters", []):
                defaults[sp["param-id"]] = sp["values"][0]
            for ir in ci.get("implemented-requirements", []):
                cid = ir["control-id"]
                for p in ir.get("props", []):
                    if p.get("name") == "Rule_Id":
                        ctrl_to_rule[cid] = p["value"]

    for cid, rid in ctrl_to_rule.items():
        if rid in rule_to_check:
            specs[cid] = rule_to_check[rid]
        if rid in rule_to_desc:
            rules[cid] = rule_to_desc[rid]

    # Defaults from REQUIREMENTS for all parameters
    for req in REQUIREMENTS:
        cid = req["control_id"]
        specs.setdefault(cid, req["check"])
        rules.setdefault(cid, req["rule"])
        for p in req["params"]:
            defaults.setdefault(p["id"], p["default"])

    return specs, defaults, rules


def load_ssp_params(path: Path) -> dict[str, str]:
    """Flatten the SSP's per-control set-parameters into one param-id -> value map."""
    ssp = json.loads(path.read_text(encoding="utf-8"))["system-security-plan"]
    out: dict[str, str] = {}
    for ir in ssp["control-implementation"]["implemented-requirements"]:
        for sp in ir.get("set-parameters", []):
            if sp.get("values"):
                out[sp["param-id"]] = sp["values"][0]
    return out


# ---------------------------------------------------------------------------
# Assessment results builder
# ---------------------------------------------------------------------------

def build_results(repo_name: str, slug: str, outcomes: list[dict], start: datetime) -> ar_mod.Model:
    now = datetime.now(tz=timezone.utc)
    reason_map = {"pass": common.Reason.pass_, "fail": common.Reason.fail, "other": common.Reason.other}
    observations, findings = [], []
    for o in outcomes:
        obs_uuid = str(uuid.uuid4())
        observations.append(common.Observation(
            uuid=obs_uuid,
            title=f"{o['control_id']} evidence",
            description=o["evidence"],
            methods=[common.Methods.TEST if o["spec"] != "manual" else common.Methods.INTERVIEW],
            collected=now,
        ))
        findings.append(common.Finding(
            uuid=str(uuid.uuid4()),
            title=f"{o['control_id']} {o['spec'].split('|')[0].strip()}",
            description=o["rule"],
            target=common.FindingTarget(
                type=common.FindingTargetTypeValidValues.objective_id,
                **{"target-id": o["control_id"]},
                status=common.ObjectiveStatus(
                    state=(common.ObjectiveStatusStateValidValues.satisfied if o["ok"]
                           else common.ObjectiveStatusStateValidValues.not_satisfied),
                    reason=reason_map[o["reason"]],
                ),
            ),
            **{"related-observations": [common.RelatedObservation(**{"observation-uuid": obs_uuid})]},
        ))

    result = ar_mod.Result(
        uuid=str(uuid.uuid4()),
        title=f"Automated assessment - {repo_name}",
        description="Automated evidence checks defined by the cncf-repo component definition.",
        start=start,
        end=now,
        **{"reviewed-controls": common.ReviewedControls(
            **{"control-selections": [common.ControlSelections(
                **{"include-controls": [common.SelectControlById(**{"control-id": o["control_id"]})
                                        for o in outcomes]}
            )]}
        )},
        observations=observations,
        findings=findings,
    )
    return ar_mod.Model(**{"assessment-results": ar_mod.AssessmentResults(
        uuid=str(uuid.uuid4()),
        metadata=common.Metadata(
            title=f"Assessment Results - {repo_name}",
            **{"last-modified": now},
            version="1.0",
            **{"oscal-version": OSCAL_VERSION},
        ),
        **{"import-ap": ar_mod.ImportAp(
            href=f"trestle://assessment-plans/{slug}/assessment-plan.json")},
        results=[result],
    )})


# ---------------------------------------------------------------------------
# Level, human-readable report, and project record update
# ---------------------------------------------------------------------------

# Any MUST control that is not satisfied makes the whole project "Fail".
MUST_CONTROLS = {"CNSC-182", "CNSC-184", "CNSC-190", "CNSC-198", "CNSC-199"}

# Fraction of assessable (automated) SHOULD controls that must be satisfied.
LEVELS = [("Gold", 0.90), ("Silver", 0.75), ("Bronze", 0.60), ("Baseline Pass Only", 0.50)]

# Badge SVG paths for each pipeline level.
# Reports live in reports/<slug>.md, so paths are relative to that directory
# (one level up from repo root to reach badges/).
LEVEL_BADGES = {
    "Gold":               "../badges/gold.svg",
    "Silver":             "../badges/silver.svg",
    "Bronze":             "../badges/bronze.svg",
    "Baseline Pass Only": "../badges/baseline-pass-only.svg",
    "Fail":               "../badges/fail.svg",
    "TBD":                "../badges/tbd.svg",
    "Not Assessed":       "../badges/tbd.svg",
}

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def compute_level(outcomes: list[dict]) -> tuple[str, str]:
    """Return (level, explanation). Manual / not-assessable controls are excluded from the ratio."""
    failed_must = sorted(o["control_id"] for o in outcomes
                         if o["control_id"] in MUST_CONTROLS and not o["ok"])
    if failed_must:
        return "Fail", f"MUST controls not satisfied: {', '.join(failed_must)}"
    should = [o for o in outcomes if o["control_id"] not in MUST_CONTROLS and o["reason"] != "other"]
    if not should:
        return "Not Assessed", "No automated SHOULD controls were evaluated"
    ratio = sum(o["ok"] for o in should) / len(should)
    detail = f"{sum(o['ok'] for o in should)}/{len(should)} automated SHOULD controls satisfied ({ratio:.0%})"
    for name, threshold in LEVELS:
        if ratio >= threshold:
            return name, detail
    return "Fail", detail


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _result_label(o: dict) -> str:
    return "PASS" if o["ok"] else "FAIL" if o["reason"] == "fail" else "N/A"


def render_report(repo_name: str, repo_url: str, commit: str, level: str, detail: str,
                  outcomes: list[dict], assessed_at: datetime) -> str:
    passed = sum(o["ok"] for o in outcomes)
    na = sum(o["reason"] == "other" for o in outcomes)
    failed = len(outcomes) - passed - na
    badge_path = LEVEL_BADGES.get(level, LEVEL_BADGES["TBD"])
    lines = [
        f"# CNCF controls report: {repo_name}",
        "",
        f"![cncf-controls: {level}]({badge_path})",
        "",
        f"- **Repository:** [{repo_url}]({repo_url})",
        f"- **Commit assessed:** `{commit or 'unknown'}`",
        f"- **Assessed at:** {assessed_at:%Y-%m-%d %H:%M} UTC",
        f"- **Level:** **{level}**. {detail}",
        f"- **Totals:** {passed} satisfied, {failed} failed, {na} not automated (of {len(outcomes)} controls)",
        "",
        "Levels: *Fail* if any MUST control is not satisfied; otherwise *Baseline Pass Only* at 50%, *Bronze* at 60%, "
        "*Silver* at 75%, *Gold* at 90% of automated SHOULD controls. "
        "MUST controls: " + ", ".join(sorted(MUST_CONTROLS)) + ". "
        "Manual and non-assessable controls (N/A) are excluded from the percentage and never count as passes.",
        "",
        "## Results by control",
        "",
        "| Control | Priority | Result | Requirement | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for o in outcomes:
        kind = "MUST" if o["control_id"] in MUST_CONTROLS else "SHOULD"
        lines.append(f"| {o['control_id']} | {kind} | {_result_label(o)} | "
                     f"{_cell(o['rule'])} | {_cell(o['evidence'])} |")
    lines.append("")
    lines.append("Generated by `scripts/assess_project.py`. "
                 "Machine-readable results are in the OSCAL assessment-results file for this project.")
    return "\n".join(lines) + "\n"


def _norm_url(url: str) -> str:
    return re.sub(r"(\.git)?/*$", "", url.strip().lower())


def update_project_record(repo_url: str, level: str, report_rel: str) -> bool:
    """Write level + report link into data/projects.json and refresh the README tables."""
    import update_readme as ur

    projects = ur.load_projects()
    matched = False
    for p in projects:
        if _norm_url(p.get("repo_url", "")) == _norm_url(repo_url):
            p["cncf_controls_status"] = level
            p["cncf_controls_report"] = report_rel
            matched = True
    if not matched:
        return False
    ur.DATA_FILE.write_text(json.dumps(projects, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ur.update_readme(ur.render_tables(projects))
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo_url")
    ap.add_argument("--trestle-ws", default="trestle.ws")
    ap.add_argument("--clone-dir", default="/tmp/cncf-compliance-clones")
    args = ap.parse_args()

    ws = Path(args.trestle_ws)
    slug, repo_name = _slug(args.repo_url), _repo_name(args.repo_url)
    base_path = ws / "component-definitions" / "cncf-repo" / "component-definition.json"
    ssp_path = ws / "system-security-plans" / slug / "system-security-plan.json"
    for p in (base_path, ssp_path):
        if not p.exists():
            print(f"Missing {p}; run build_project_compliance.py first.", file=sys.stderr)
            return 1

    specs, defaults, comp_rules = load_base(base_path)
    params = {**defaults, **load_ssp_params(ssp_path)}

    start = datetime.now(tz=timezone.utc)
    repo_root = clone_repo(args.repo_url, Path(args.clone_dir))

    rules = {**{r["control_id"]: r["rule"] for r in REQUIREMENTS}, **comp_rules}
    outcomes = []
    for cid, spec in specs.items():
        rule = rules.get(cid, cid)
        ok, evidence, reason = run_check(cid, spec, params, repo_root, args.repo_url)
        outcomes.append({"control_id": cid, "spec": spec, "rule": rule,
                         "ok": ok, "evidence": evidence, "reason": reason})

    model = build_results(repo_name, slug, outcomes, start)
    out = ws / "assessment-results" / slug / "assessment-results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(model.model_dump_json(indent=2, exclude_none=True, by_alias=True), encoding="utf-8")

    passed = sum(o["ok"] for o in outcomes)
    manual = sum(o["reason"] == "other" for o in outcomes)
    print(f"Written: {out}")
    print(f"Satisfied {passed}/{len(outcomes)}  (failed {len(outcomes) - passed - manual}, not automated {manual})")

    level, detail = compute_level(outcomes)
    report_rel = f"reports/{slug}.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"{slug}.md").write_text(
        render_report(repo_name, args.repo_url, _git(["rev-parse", "--short", "HEAD"], repo_root),
                      level, detail, outcomes, datetime.now(tz=timezone.utc)),
        encoding="utf-8",
    )
    print(f"Written: {report_rel}")
    print(f"Level: {level} ({detail})")

    if update_project_record(args.repo_url, level, report_rel):
        print("Updated data/projects.json and README.md")
    else:
        print(f"No entry in data/projects.json with repo_url {args.repo_url}; README not updated.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
