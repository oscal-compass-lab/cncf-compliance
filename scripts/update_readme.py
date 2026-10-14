#!/usr/bin/env python3
"""Refresh CNCF project metadata and regenerate the README project tables.

1. Downloads the latest CNCF landscape metadata.
2. Keeps CNCF projects (graduated / incubating / sandbox) in data/projects.json,
   adding a ``cncf_controls_status`` column (default "TBD"). Statuses already
   present in data/projects.json are preserved across runs.
3. Rewrites the section of README.md between the BEGIN/END markers with one
   table per maturity level, each sorted alphabetically.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

LANDSCAPE_BASE = "https://landscape.cncf.io"
LANDSCAPE_DATA_URL = f"{LANDSCAPE_BASE}/data/full.json"
DEFAULT_STATUS = "TBD"
TIMEOUT_SECONDS = 60

STATUS_TOOLTIPS = {
    "Gold": "Exceptional compliance: satisfied 100% of MUST controls and >= 90% of automated SHOULD controls",
    "Silver": "Strong compliance: satisfied 100% of MUST controls and >= 75% of automated SHOULD controls",
    "Bronze": "Good compliance: satisfied 100% of MUST controls and >= 60% of automated SHOULD controls",
    "Baseline Pass Only": "Minimum compliance: satisfied 100% of MUST controls and >= 50% of automated SHOULD controls (below Bronze tier)",
    "Fail": "Non-compliant: failed one or more MUST controls, or satisfied < 50% of automated SHOULD controls",
    "TBD": "Assessment pending",
}

# Map each pipeline level to its badge SVG (relative to repo root).
STATUS_BADGES = {
    "Gold":               "badges/gold.svg",
    "Silver":             "badges/silver.svg",
    "Bronze":             "badges/bronze.svg",
    "Baseline Pass Only": "badges/baseline-pass-only.svg",
    "Fail":               "badges/fail.svg",
    "TBD":                "badges/tbd.svg",
}

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "projects.json"
README_FILE = ROOT / "README.md"

BEGIN_SHARED = "<!-- BEGIN SHARED OSCAL -->"
END_SHARED = "<!-- END SHARED OSCAL -->"
BEGIN_MARKER = "<!-- BEGIN PROJECT TABLES -->"
END_MARKER = "<!-- END PROJECT TABLES -->"

# landscape "maturity" value -> README section title (in display order)
SECTIONS = [
    ("graduated", "Graduated"),
    ("incubating", "Incubation"),
    ("sandbox", "Sandbox"),
]


def fetch_landscape_items():
    request = urllib.request.Request(
        LANDSCAPE_DATA_URL, headers={"User-Agent": "cncf-compliance-updater"}
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310 (fixed https URL)
        return json.load(response)["items"]


def primary_repo_url(item):
    repos = item.get("repositories") or []
    for repo in repos:
        if repo.get("primary"):
            return repo["url"]
    if repos:
        return repos[0]["url"]
    return item.get("homepage_url") or item.get("website") or ""


def load_projects():
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def load_existing():
    """Existing data/projects.json entries by id, so assessed fields survive a refresh."""
    return {p["id"]: p for p in load_projects()}


def build_projects(items, existing):
    wanted = {key for key, _ in SECTIONS}
    projects = []
    for item in items:
        maturity = item.get("maturity")
        if maturity not in wanted:
            continue
        previous = existing.get(item["id"], {})
        project = {
            "id": item["id"],
            "name": item["name"],
            "maturity": maturity,
            "logo": item.get("logo", ""),
            "repo_url": primary_repo_url(item),
            "cncf_controls_status": previous.get("cncf_controls_status", DEFAULT_STATUS),
        }
        if previous.get("cncf_controls_report"):
            project["cncf_controls_report"] = previous["cncf_controls_report"]
        projects.append(project)
    projects.sort(key=lambda p: (p["maturity"], p["name"].casefold(), p["id"]))
    return projects


def md_cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def render_oscal_docs(project):
    repo_url = project.get("repo_url", "")
    if not repo_url:
        return "-"
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", repo_url)
    path = m.group(1) if m else repo_url
    slug = re.sub(r"[^a-zA-Z0-9._-]", "--", path)

    catalog_rel   = "trestle.ws/catalogs/cncf-controls/catalog.json"
    profile_rel   = "trestle.ws/profiles/cncf-repo/profile.json"
    base_cd_rel   = "trestle.ws/component-definitions/cncf-repo/component-definition.json"
    comp_def_rel  = f"trestle.ws/component-definitions/{slug}/component-definition.json"
    ssp_rel       = f"trestle.ws/system-security-plans/{slug}/system-security-plan.json"
    ap_rel        = f"trestle.ws/assessment-plans/{slug}/assessment-plan.json"
    ar_rel        = f"trestle.ws/assessment-results/{slug}/assessment-results.json"

    # Only show dropdown if project has generated artifacts
    if not (ROOT / comp_def_rel).exists() and not (ROOT / ar_rel).exists():
        return "-"

    docs = []
    if (ROOT / catalog_rel).exists():
        docs.append(f'<a href="{catalog_rel}">Catalog</a>')
    if (ROOT / profile_rel).exists():
        docs.append(f'<a href="{profile_rel}">Profile</a>')
    if (ROOT / base_cd_rel).exists():
        docs.append(f'<a href="{base_cd_rel}">Base Component Definition</a>')
    if (ROOT / comp_def_rel).exists():
        docs.append(f'<a href="{comp_def_rel}">Component Definition</a>')
    if (ROOT / ssp_rel).exists():
        docs.append(f'<a href="{ssp_rel}">System Security Plan</a>')
    if (ROOT / ap_rel).exists():
        docs.append(f'<a href="{ap_rel}">Assessment Plan</a>')
    if (ROOT / ar_rel).exists():
        docs.append(f'<a href="{ar_rel}">Assessment Results</a>')

    if not docs:
        return "-"

    items = "".join(f"<li>{d}</li>" for d in docs)
    return f"<details><summary>OSCAL Docs</summary><ul>{items}</ul></details>"


def render_row(project):
    logo = ""
    if project["logo"]:
        logo_url = f"{LANDSCAPE_BASE}/{project['logo']}"
        logo = f'<img src="{logo_url}" alt="{md_cell(project["name"])} logo" width="48">'
    name = md_cell(project["name"])
    if project.get("repo_url"):
        repo_url = project["repo_url"]
        project_cell = f'[{name}]({repo_url} "{repo_url}")'
    else:
        project_cell = name

    status_text = project["cncf_controls_status"]
    tooltip = STATUS_TOOLTIPS.get(status_text, "")
    badge_path = STATUS_BADGES.get(status_text, STATUS_BADGES["TBD"])
    badge_img = f'<img src="{badge_path}" alt="{md_cell(status_text)}">'
    if tooltip:
        badge_img = f'<img src="{badge_path}" alt="{md_cell(status_text)}" title="{tooltip}">'
    if project.get("cncf_controls_report"):
        report_url = project["cncf_controls_report"]
        status = f'[{badge_img}]({report_url})<br>[report]({report_url})'
    else:
        status = badge_img
    oscal_docs = render_oscal_docs(project)
    return f"| {logo} | {project_cell} | {status} | {oscal_docs} |"


def render_shared_oscal():
    """Return a Markdown snippet linking the shared OSCAL artifacts (catalog, profile, base comp def)."""
    catalog_rel  = "trestle.ws/catalogs/cncf-controls/catalog.json"
    profile_rel  = "trestle.ws/profiles/cncf-repo/profile.json"
    base_cd_rel  = "trestle.ws/component-definitions/cncf-repo/component-definition.json"

    links = []
    if (ROOT / catalog_rel).exists():
        links.append(f"[Catalog]({catalog_rel})")
    if (ROOT / profile_rel).exists():
        links.append(f"[Profile]({profile_rel})")
    if (ROOT / base_cd_rel).exists():
        links.append(f"[Base Component Definition]({base_cd_rel})")

    if not links:
        return ""
    return "**Shared OSCAL artifacts:** " + " · ".join(links) + "\n"


def render_tables(projects):
    lines = []
    for key, title in SECTIONS:
        section = [p for p in projects if p["maturity"] == key]
        lines.append(f"### {title} ({len(section)})")
        lines.append("")
        lines.append("| Logo | Project | cncf-controls status | OSCAL documents |")
        lines.append("| --- | --- | --- | --- |")
        lines.extend(render_row(p) for p in section)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _replace_block(text, begin, end, content):
    block = f"{begin}\n{content}{end}"
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text)
    # Insert before the project tables block if present, otherwise append
    if BEGIN_MARKER in text:
        return text.replace(BEGIN_MARKER, block + "\n\n" + BEGIN_MARKER, 1)
    return text.rstrip("\n") + "\n\n" + block + "\n"


def update_readme(tables):
    text = README_FILE.read_text(encoding="utf-8")
    shared = render_shared_oscal()
    if shared:
        text = _replace_block(text, BEGIN_SHARED, END_SHARED, shared)
    text = _replace_block(text, BEGIN_MARKER, END_MARKER, tables)
    README_FILE.write_text(text, encoding="utf-8")


def main():
    items = fetch_landscape_items()
    projects = build_projects(items, load_existing())
    if not projects:
        print("No CNCF projects found in landscape data; aborting.", file=sys.stderr)
        return 1

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(projects, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_readme(render_tables(projects))
    print(f"Updated {len(projects)} projects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
