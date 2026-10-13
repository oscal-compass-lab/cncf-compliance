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

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "projects.json"
README_FILE = ROOT / "README.md"

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


def render_row(project):
    logo = ""
    if project["logo"]:
        logo_url = f"{LANDSCAPE_BASE}/{project['logo']}"
        logo = f'<img src="{logo_url}" alt="{md_cell(project["name"])} logo" width="48">'
    repo = f"[{md_cell(project['repo_url'])}]({project['repo_url']})" if project["repo_url"] else ""
    status = md_cell(project["cncf_controls_status"])
    if project.get("cncf_controls_report"):
        status = f"[{status}]({project['cncf_controls_report']})"
    return f"| {logo} | {md_cell(project['name'])} | {repo} | {status} |"


def render_tables(projects):
    lines = []
    for key, title in SECTIONS:
        section = [p for p in projects if p["maturity"] == key]
        lines.append(f"### {title} ({len(section)})")
        lines.append("")
        lines.append("| Logo | Project | Repository | cncf-controls status |")
        lines.append("| --- | --- | --- | --- |")
        lines.extend(render_row(p) for p in section)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def update_readme(tables):
    text = README_FILE.read_text(encoding="utf-8")
    block = f"{BEGIN_MARKER}\n{tables}{END_MARKER}"
    pattern = re.compile(re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if pattern.search(text):
        text = pattern.sub(lambda _: block, text)
    else:
        text = text.rstrip("\n") + "\n\n## CNCF Projects\n\n" + block + "\n"
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
