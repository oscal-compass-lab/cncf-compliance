#!/usr/bin/env python3
"""Write the cncf-repo profile: the catalog controls in scope for git repositories.

The in-scope controls are those in privateer_mapping.py (MAPPED, which have a
Privateer check, and UNMAPPED, which have none). Every other control in the
catalog is out of scope for git repositories and is not in the profile.

Usage: python scripts/generate_profile.py
"""
import json
import sys
from pathlib import Path

from privateer_mapping import MAPPED, UNMAPPED, load_catalog

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "trestle.ws" / "profiles" / "cncf-repo" / "profile.json"


def _natural(cid: str) -> int:
    return int(cid.split("-")[1])


def main() -> int:
    catalog = load_catalog()
    in_scope = sorted(set(MAPPED) | set(UNMAPPED), key=_natural)
    unknown = [c for c in in_scope if c not in catalog]
    if unknown:
        print(f"Controls not in the catalog: {', '.join(unknown)}", file=sys.stderr)
        return 1

    existing = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))["profile"]
    profile = {
        "profile": {
            "uuid": existing["uuid"],
            "metadata": {
                "title": "CNCF Source Repository Profile",
                "last-modified": existing["metadata"]["last-modified"],
                "version": "1.0",
                "oscal-version": "1.2.1",
                "props": [
                    {
                        "name": "description",
                        "value": "The CNCF controls that are in scope for git repositories. "
                                 "All other catalog controls are out of scope.",
                    }
                ],
                "parties": existing["metadata"].get("parties", []),
            },
            "imports": [
                {
                    "href": "trestle://catalogs/cncf-controls/catalog.json",
                    "include-controls": [{"with-ids": in_scope}],
                }
            ],
        }
    }
    PROFILE_PATH.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(f"Written: {PROFILE_PATH} with {len(in_scope)} controls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
