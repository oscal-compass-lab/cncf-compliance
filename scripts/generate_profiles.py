#!/usr/bin/env python3
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cat_path = ROOT / "trestle.ws" / "catalogs" / "cncf-controls" / "catalog.json"
orig_prof_path = ROOT / "trestle.ws" / "profiles" / "cncf-repo" / "profile.json"

# Load catalog controls
cat_data = json.loads(cat_path.read_text(encoding="utf-8"))
cat_ctrls = []
def scan_group(g):
    for c in g.get("controls", []):
        cat_ctrls.append(c["id"])
        scan_group(c)
    for sg in g.get("groups", []):
        scan_group(sg)
scan_group(cat_data["catalog"])

# Load active controls from existing active profile (or original profile if active profile does not exist)
prof_active_path = ROOT / "trestle.ws" / "profiles" / "cncf-repo-active" / "profile.json"
prof_skip_path = ROOT / "trestle.ws" / "profiles" / "cncf-repo-skip" / "profile.json"

active_source_path = prof_active_path if prof_active_path.exists() else orig_prof_path
active_prof = json.loads(active_source_path.read_text(encoding="utf-8"))
active_ctrls = []
for imp in active_prof["profile"].get("imports", []):
    for inc in imp.get("include-controls", []):
        active_ctrls.extend(inc.get("with-ids", []))

skipped_ctrls = [c for c in cat_ctrls if c not in active_ctrls]

orig_prof = json.loads(orig_prof_path.read_text(encoding="utf-8"))
active_uuid = active_prof["profile"].get("uuid") if prof_active_path.exists() else str(uuid.uuid4())
skip_uuid = (
    json.loads(prof_skip_path.read_text(encoding="utf-8"))["profile"].get("uuid")
    if prof_skip_path.exists()
    else str(uuid.uuid4())
)

# Write Profile 1 (Active)
prof_active_path.parent.mkdir(parents=True, exist_ok=True)
prof_active_data = {
    "profile": {
        "uuid": active_uuid,
        "metadata": {
            "title": "CNCF Source Repository Profile - Profile 1 (Active)",
            "last-modified": "2026-10-15T00:00:00.000+00:00",
            "version": "1.0",
            "oscal-version": "1.2.1",
            "props": [
                {
                    "name": "description",
                    "value": "Profile 1 comprising the active set of controls that are evaluated for status."
                }
            ],
            "parties": orig_prof["profile"]["metadata"].get("parties", [])
        },
        "imports": [
            {
                "href": "trestle://catalogs/cncf-controls/catalog.json",
                "include-controls": [
                    {
                        "with-ids": active_ctrls
                    }
                ]
            }
        ]
    }
}
prof_active_path.write_text(json.dumps(prof_active_data, indent=2), encoding="utf-8")
print(f"Written Profile 1 (Active): {prof_active_path} with {len(active_ctrls)} controls")

# Write Profile 2 (Skip)
prof_skip_path.parent.mkdir(parents=True, exist_ok=True)
prof_skip_data = {
    "profile": {
        "uuid": skip_uuid,
        "metadata": {
            "title": "CNCF Source Repository Profile - Profile 2 (Skipped)",
            "last-modified": "2026-10-15T00:00:00.000+00:00",
            "version": "1.0",
            "oscal-version": "1.2.1",
            "props": [
                {
                    "name": "description",
                    "value": "Profile 2 comprising all other controls that were not included in Profile 1, which are skipped."
                }
            ],
            "parties": orig_prof["profile"]["metadata"].get("parties", [])
        },
        "imports": [
            {
                "href": "trestle://catalogs/cncf-controls/catalog.json",
                "include-controls": [
                    {
                        "with-ids": skipped_ctrls
                    }
                ]
            }
        ]
    }
}
prof_skip_path.write_text(json.dumps(prof_skip_data, indent=2), encoding="utf-8")
print(f"Written Profile 2 (Skipped): {prof_skip_path} with {len(skipped_ctrls)} controls")

# Write Master Profile (replacing cncf-repo/profile.json)
prof_master_data = {
    "profile": {
        "uuid": orig_prof["profile"]["uuid"], # keep original UUID for compatibility
        "metadata": {
            "title": "CNCF Source Repository Profile",
            "last-modified": "2026-10-15T00:00:00.000+00:00",
            "version": "1.0",
            "oscal-version": "1.2.1",
            "props": [
                {
                    "name": "description",
                    "value": "Master profile selecting all CNCF controls, combining Profile 1 (evaluated) and Profile 2 (skipped)."
                }
            ],
            "parties": orig_prof["profile"]["metadata"].get("parties", [])
        },
        "imports": [
            {
                "href": "trestle://profiles/cncf-repo-active/profile.json",
                "include-all": {}
            },
            {
                "href": "trestle://profiles/cncf-repo-skip/profile.json",
                "include-all": {}
            }
        ]
    }
}
orig_prof_path.write_text(json.dumps(prof_master_data, indent=2), encoding="utf-8")
print(f"Updated Master Profile: {orig_prof_path} importing both active and skipped profiles")
