#!/usr/bin/env python3
"""Build OSCAL compliance artifacts for CNCF projects.

The cncf-repo profile comprises the controls in scope for git repositories; all
other catalog controls are out of scope. Every control in the profile has its
own Privateer check (see privateer_mapping.py), or is recorded as not checked,
with the reason.

Two sub-commands:

  base
      Write the shared cncf-repo Component Definition into the trestle
      workspace: one rule and one check per control.
      Run once, or whenever the catalog/profile/mapping changes.

  project <repo-url>
      Write, for the project:

        component-definitions/<slug>/component-definition.json
            Per-project comp def - imports the base.

        system-security-plans/<slug>/system-security-plan.json
            SSP - binds the per-project comp def to the cncf-repo profile.

        assessment-plans/<slug>/assessment-plan.json
            Assessment Plan - references the SSP, selects all profile
            controls for assessment.

Usage
-----
  python scripts/build_project_compliance.py base [--trestle-ws PATH]
  python scripts/build_project_compliance.py project <repo-url> [--trestle-ws PATH]
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import oscal_factory as factory
from privateer_mapping import MAPPED, UNMAPPED, load_catalog, plugin_for
from trestle.oscal import component as comp
from trestle.oscal import ssp as ssp_mod

# Re-export so callers that import CNCF_OSCAL_NS from here still work.
CNCF_OSCAL_NS = factory.CNCF_OSCAL_NS


# ---------------------------------------------------------------------------
# Control requirements table
# One rule + check per in-scope control, generated from the Privateer mapping
# in privateer_mapping.py (the single source of truth).
# ---------------------------------------------------------------------------

_catalog = load_catalog()


def _natural(cid: str) -> int:
    return int(cid.split("-")[1])


def _build_requirements() -> list[dict]:
    reqs = []
    for n, cid in enumerate(sorted(set(MAPPED) | set(UNMAPPED), key=_natural), start=1):
        _group, title, statement = _catalog[cid]
        if cid in MAPPED:
            osps, fidelity, _note = MAPPED[cid]
            check = f"privateer | plugin: {plugin_for(osps)}; requirement: {osps}"
            check_title = f"Privateer {osps} ({fidelity})"
        else:
            check = "no-check"
            check_title = "No Privateer check found, native or plugin"
        reqs.append({
            "control_id": cid,
            "rule_id": f"RULE-{n:02d}",
            "rule_title": title,
            "check_id": f"CHECK-{n:02d}",
            "check_title": check_title,
            "rule": statement,
            "check": check,
            "requirement": MAPPED[cid][0] if cid in MAPPED else "",
            "params": [],
        })
    return reqs


REQUIREMENTS = _build_requirements()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(repo_url: str) -> str:
    """Turn a GitHub URL into a filesystem-safe slug, e.g. oscal-compass--compliance-trestle."""
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", repo_url)
    path = m.group(1) if m else repo_url
    return re.sub(r"[^a-zA-Z0-9._-]", "--", path)


def _repo_name(repo_url: str) -> str:
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", repo_url)
    return m.group(1) if m else repo_url


def remote_head_commit(repo_url: str) -> str:
    """Short commit id of the remote HEAD, or "" if it cannot be read."""
    try:
        r = subprocess.run(["git", "ls-remote", repo_url, "HEAD"],
                           capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.split()[0][:7] if r.returncode == 0 and r.stdout.strip() else ""


# ---------------------------------------------------------------------------
# Base component definition builder
# ---------------------------------------------------------------------------

def build_base_comp_def() -> comp.Model:
    profile_href = "trestle://profiles/cncf-repo/profile.json"

    # 1. Software Component — Rule_Id + Rule_Description props, one
    #    implemented-requirement per control carrying Rule_Id.
    sw_props = []
    sw_implemented = []
    for i, req in enumerate(REQUIREMENTS):
        remarks = f"rule_set_{i:02d}"
        sw_props.extend([
            factory.cncf_prop("Rule_Id", req["rule_id"], remarks),
            factory.cncf_prop("Rule_Description",
                              f"{req['rule_title']}: {req['rule']}", remarks),
        ])
        sw_implemented.append(comp.ImplementedRequirement(
            uuid=factory.new_uuid(),
            **{"control-id": req["control_id"]},
            description="",
            props=[factory.cncf_prop("Rule_Id", req["rule_id"])],
        ))

    sw_control_impl = comp.ControlImplementation(
        uuid=factory.new_uuid(),
        source=profile_href,
        description="Software compliance rules implementing cncf-repo profile controls.",
        **{"implemented-requirements": sw_implemented},
    )

    sw_component = factory.software_component(
        title="CNCF Source Repository",
        description="Shared software component representing any CNCF source repository.",
        purpose="Define compliance rules for CNCF source repositories.",
        sw_props=sw_props,
        control_implementations=[sw_control_impl],
    )

    # 2. Validation Components — Rule_Id / Check_Id / Check_Description /
    #    Target_Component props, one group per requirement. Controls with a
    #    Privateer check are split by the plugin that runs them, so the
    #    component says whether a check is provided by Privateer itself
    #    (privateer-native: the github-repo plugin) or by our own plugin
    #    (privateer-plugins: cncf-controls). Controls for which no Privateer
    #    check was found are recorded in not-checked so every rule still has a Check_Id.
    plugin_props: dict[str, list] = {"github-repo": [], "cncf-controls": []}
    no_check_props = []
    for i, req in enumerate(REQUIREMENTS):
        remarks = f"check_set_{i:02d}"
        if req["check"].startswith("privateer"):
            props = plugin_props[plugin_for(req["requirement"])]
        else:
            props = no_check_props
        props.extend([
            factory.cncf_prop("Rule_Id", req["rule_id"], remarks),
            factory.cncf_prop("Check_Id", req["check_id"], remarks),
            factory.cncf_prop("Check_Description", req["check"], remarks),
            factory.cncf_prop("Target_Component", "CNCF Source Repository", remarks),
        ])

    privateer_component = factory.validation_component(
        title="privateer-native",
        description=(
            "Checks provided by Privateer (pvtr) itself: its github-repo plugin evaluates the "
            "OpenSSF Open Source Project Security Baseline (OSPS) for a GitHub repository. "
            "Each control has its own OSPS requirement."
        ),
        purpose="Validate CNCF controls using OSPS Baseline requirement results from Privateer.",
        val_props=plugin_props["github-repo"],
    )
    cncf_component = factory.validation_component(
        title="privateer-plugins",
        description=(
            "Checks provided by the cncf-controls Privateer plugin written for this project "
            "(privateer-plugins/cncf-controls), which evaluates the five CNCF controls the "
            "OSPS Baseline does not cover. It runs alongside github-repo in the same pvtr run."
        ),
        purpose="Validate five CNCF controls using requirement results from the cncf-controls plugin.",
        val_props=plugin_props["cncf-controls"],
    )
    no_check_component = factory.validation_component(
        title="not-checked",
        description=(
            "Controls that are in scope for git repositories but have no "
            "Privateer check, native or plugin (no-check). They are reported as not determined and never "
            "count as a pass. The reason for each is in docs/privateer-check-coverage.md."
        ),
        purpose="Record in-scope controls that are not yet automatically assessed.",
        val_props=no_check_props,
    )

    md = factory.org_metadata(
        "CNCF Source Repository — Shared Base Component Definition",
        org_name="CNCF TAG Security and Compliance",
    )

    return factory.component_definition(
        md=md, components=[sw_component, privateer_component, cncf_component, no_check_component]
    )


# ---------------------------------------------------------------------------
# Per-project component definition builder
# ---------------------------------------------------------------------------

def build_project_comp_def(repo_url: str, repo_name: str) -> comp.Model:
    profile_href = "trestle://profiles/cncf-repo/profile.json"
    base_href = "trestle://component-definitions/cncf-repo/component-definition.json"

    ci_kwargs: dict = {
        "uuid": factory.new_uuid(),
        "source": profile_href,
        "description": f"Control implementations for {repo_name}, inherited from the shared cncf-repo base.",
    }
    # At least one implemented-requirement is required by OSCAL schema;
    # we declare a single placeholder that defers all rules to the base.
    ci_kwargs["implemented-requirements"] = [
        comp.ImplementedRequirement(
            uuid=factory.new_uuid(),
            **{"control-id": "CNSC-71"},
            description=(
                "All control implementations are inherited from the shared base "
                "component definition."
            ),
        )
    ]

    component = factory.project_software_component(
        repo_name=repo_name,
        repo_url=repo_url,
        control_implementations=[comp.ControlImplementation(**ci_kwargs)],
    )

    md = factory.org_metadata(
        f"Component Definition — {repo_name}",
        org_name=repo_name,
        org_href=repo_url,
    )

    return factory.component_definition(
        md=md,
        components=[component],
        imports=[comp.ImportComponentDefinition(href=base_href)],
    )


# ---------------------------------------------------------------------------
# SSP builder
# ---------------------------------------------------------------------------

def build_ssp(
    repo_url: str,
    repo_name: str,
    slug: str,
    trestle_ws: Path,
) -> ssp_mod.Model:
    profile_href = "trestle://profiles/cncf-repo/profile.json"
    base_href    = "trestle://component-definitions/cncf-repo/component-definition.json"
    proj_href    = f"trestle://component-definitions/{slug}/component-definition.json"

    # ------------------------------------------------------------------ #
    # Build system-implementation/components by converting every          #
    # DefinedComponent from both comp-defs into a SystemComponent.        #
    # Original UUIDs are preserved so by-components references resolve.   #
    # ------------------------------------------------------------------ #
    base_cd = json.loads(
        (trestle_ws / "component-definitions" / "cncf-repo" / "component-definition.json")
        .read_text(encoding="utf-8")
    )["component-definition"]
    proj_cd = json.loads(
        (trestle_ws / "component-definitions" / slug / "component-definition.json")
        .read_text(encoding="utf-8")
    )["component-definition"]

    # Load each DefinedComponent via trestle's pydantic model so the factory
    # receives a typed object.
    from trestle.oscal.component import DefinedComponent as DefComp

    system_components = []
    for raw in base_cd["components"]:
        dc = DefComp(**raw)
        system_components.append(factory.system_component_from_defined(dc, base_href))
    for raw in proj_cd["components"]:
        dc = DefComp(**raw)
        system_components.append(factory.system_component_from_defined(dc, proj_href))

    # The per-project software component UUID drives by-components references.
    # It is the first (and only) software component in the per-project comp-def.
    proj_sw_uuid = proj_cd["components"][0]["uuid"]

    # ------------------------------------------------------------------ #
    # One implemented-requirement per control.                            #
    # ------------------------------------------------------------------ #
    implemented = [
        ssp_mod.ImplementedRequirement(
            uuid=factory.new_uuid(),
            **{"control-id": cid},
            **{"by-components": [
                ssp_mod.ByComponent(
                    **{"component-uuid": proj_sw_uuid},
                    uuid=factory.new_uuid(),
                    description=f"Repository component implements {cid}.",
                )
            ]},
        )
        for cid in dict.fromkeys(r["control_id"] for r in REQUIREMENTS)
    ]

    return factory.system_security_plan(
        repo_name=repo_name,
        repo_url=repo_url,
        profile_href=profile_href,
        system_components=system_components,
        implemented=implemented,
    )


# ---------------------------------------------------------------------------
# Assessment plan builder
# ---------------------------------------------------------------------------

def build_ap(repo_name: str, slug: str) -> factory.ap_mod.Model:
    control_ids = list(dict.fromkeys(r["control_id"] for r in REQUIREMENTS))
    return factory.assessment_plan(
        repo_name=repo_name,
        slug=slug,
        control_ids=control_ids,
    )


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_base(trestle_ws: Path) -> int:
    print("Building shared base component definition...")
    model = build_base_comp_def()
    out_dir = trestle_ws / "component-definitions" / "cncf-repo"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "component-definition.json"
    out_path.write_text(
        model.model_dump_json(indent=2, exclude_none=True, by_alias=True),
        encoding="utf-8",
    )
    print(f"  Written: {out_path}  ({len(REQUIREMENTS)} requirements)")
    return 0


def cmd_project(repo_url: str, trestle_ws: Path) -> int:
    slug = _slug(repo_url)
    repo_name = _repo_name(repo_url)
    print(f"Project : {repo_name}")
    print(f"Slug    : {slug}")

    # 1. Per-project comp def
    cd_model = build_project_comp_def(repo_url, repo_name)
    cd_dir = trestle_ws / "component-definitions" / slug
    cd_dir.mkdir(parents=True, exist_ok=True)
    cd_path = cd_dir / "component-definition.json"
    cd_path.write_text(
        cd_model.model_dump_json(indent=2, exclude_none=True, by_alias=True),
        encoding="utf-8",
    )
    print(f"  Written: {cd_path}")

    # 2. SSP
    ssp_model = build_ssp(repo_url, repo_name, slug, trestle_ws)
    ssp_dir = trestle_ws / "system-security-plans" / slug
    ssp_dir.mkdir(parents=True, exist_ok=True)
    ssp_path = ssp_dir / "system-security-plan.json"
    ssp_path.write_text(
        ssp_model.model_dump_json(indent=2, exclude_none=True, by_alias=True),
        encoding="utf-8",
    )
    print(f"  Written: {ssp_path}")

    # 3. Assessment plan
    ap_model = build_ap(repo_name, slug)
    ap_dir = trestle_ws / "assessment-plans" / slug
    ap_dir.mkdir(parents=True, exist_ok=True)
    ap_path = ap_dir / "assessment-plan.json"
    ap_path.write_text(
        ap_model.model_dump_json(indent=2, exclude_none=True, by_alias=True),
        encoding="utf-8",
    )
    print(f"  Written: {ap_path}")

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--trestle-ws", default="trestle.ws",
        help="Path to the trestle workspace root (default: trestle.ws)",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("base", help="Build the shared cncf-repo base component definition.")

    p_proj = sub.add_parser("project", help="Build comp-def, SSP, and AP for a project repo.")
    p_proj.add_argument("repo_url", help="GitHub repository URL, e.g. https://github.com/org/repo")

    args = parser.parse_args()
    trestle_ws = Path(args.trestle_ws)

    if args.cmd == "base":
        return cmd_base(trestle_ws)
    if args.cmd == "project":
        return cmd_project(args.repo_url, trestle_ws)
    return 1


if __name__ == "__main__":
    sys.exit(main())
