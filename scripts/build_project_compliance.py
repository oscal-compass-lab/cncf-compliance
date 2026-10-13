#!/usr/bin/env python3
"""Build OSCAL compliance artifacts for CNCF projects.

Two sub-commands:

  base
      Write the shared cncf-repo Component Definition into the trestle
      workspace.  Contains all rules, check types, and parameter defaults.
      Run once, or whenever the catalog/profile changes.

  project <repo-url>
      Shallow-clone the target repository, probe it for actual parameter
      values, diff those values against the shared defaults, and write:

        component-definitions/<slug>/component-definition.json
            Per-project comp def — imports the base, overrides only the
            parameters that differ from the defaults.

        system-security-plans/<slug>/system-security-plan.json
            SSP — binds the per-project comp def to the cncf-repo profile,
            records the probed parameter values.

        assessment-plans/<slug>/assessment-plan.json
            Assessment Plan — references the SSP, selects all profile
            controls for assessment.

Usage
-----
  python scripts/build_project_compliance.py base [--trestle-ws PATH]

  python scripts/build_project_compliance.py project <repo-url>
      [--trestle-ws PATH] [--clone-dir PATH]

Defaults
--------
  --trestle-ws   trestle.ws
  --clone-dir    /tmp/cncf-compliance-clones
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from trestle.oscal import OSCAL_VERSION
from trestle.oscal import component as comp
from trestle.oscal import ssp as ssp_mod
from trestle.oscal import assessment_plan as ap_mod
from trestle.oscal import common


# ---------------------------------------------------------------------------
# Control requirements table
# Rule + check type + parameter defaults — shared across all projects.
# ---------------------------------------------------------------------------

REQUIREMENTS = [
    # ---- Develop -----------------------------------------------------------
    {
        "control_id": "CNSC-65",
        "rule": "Vulnerability and configuration scanning must be integrated at the pull-request or CI stage.",
        "check": "ci-vuln-scan | param: pipeline-vuln-scan-target; vuln-scan-workflows",
        "params": [
            {"id": "pipeline-vuln-scan-target", "default": "audit-deps",
             "description": "Pipeline target that runs vulnerability scanning."},
            {"id": "vuln-scan-workflows", "default": "codeql,scorecard,trivy,snyk,sonar,vuln,audit,security,actionlint",
             "description": "Comma-separated keywords or filenames for CI vulnerability/configuration scanning workflows."},
        ],
    },
    {
        "control_id": "CNSC-67",
        "rule": "Tests must exist for business-critical code paths.",
        "check": "file-exists | param: test-dir",
        "params": [
            {"id": "test-dir", "default": "tests",
             "description": "Directory containing test suites."},
        ],
    },
    {
        "control_id": "CNSC-68",
        "rule": "Tests must exist for business-critical infrastructure.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-69",
        "rule": "Test suites must be runnable locally without external dependencies.",
        "check": "makefile-target | param: test-target",
        "params": [
            {"id": "test-target", "default": "test",
             "description": "Pipeline target that runs tests locally."},
        ],
    },
    {
        "control_id": "CNSC-71",
        "rule": "At least two non-author reviewers must approve before merging.",
        "check": "git-branch-protected | param: default-branch; min-reviewers",
        "params": [
            {"id": "default-branch", "default": "main",
             "description": "The repository default branch name."},
            {"id": "min-reviewers", "default": "2",
             "description": "Minimum number of required non-author reviewers."},
        ],
    },
    {
        "control_id": "CNSC-72",
        "rule": "Code must be clean and well commented.",
        "check": "file-exists | param: pipeline-file",
        "params": [
            {"id": "pipeline-file", "default": "Makefile",
             "description": "The pipeline-as-code file (Makefile, Taskfile.yml, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-73",
        "rule": "Full infrastructure tests must be present.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-74",
        "rule": "Regression tests must be present.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-75",
        "rule": "Test suites must be updated against new and emerging threats.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-78",
        "rule": "Threat model results must be used to determine test development priorities.",
        "check": "file-exists | param: threat-model-file",
        "params": [
            {"id": "threat-model-file", "default": "THREAT_MODEL.md",
             "description": "Path to the threat model document."},
        ],
    },
    {
        "control_id": "CNSC-195",
        "rule": "Secure configuration must be the default state of the system.",
        "check": "file-exists | param: security-policy-file",
        "params": [
            {"id": "security-policy-file", "default": "SECURITY.md",
             "description": "Path to the security policy document."},
        ],
    },
    {
        "control_id": "CNSC-259",
        "rule": "Vulnerability and configuration scanning must be integrated in both IDE and CI pipeline.",
        "check": "ci-vuln-scan | param: pipeline-vuln-scan-target; vuln-scan-workflows",
        "params": [],
    },
    {
        "control_id": "CNSC-265",
        "rule": "At least one non-author reviewer must approve before merging.",
        "check": "git-branch-protected | param: default-branch; min-reviewers",
        "params": [],
    },
    # ---- Distribute --------------------------------------------------------
    {
        "control_id": "CNSC-82",
        "rule": "Static application security testing (SAST) must be performed.",
        "check": "ci-sast | param: sast-target; sast-workflows",
        "params": [
            {"id": "sast-target", "default": "sast",
             "description": "Pipeline target that runs SAST."},
            {"id": "sast-workflows", "default": "codeql,scorecard,sonar,sast,gosec,bandit,semgrep,ruff",
             "description": "Comma-separated keywords or filenames for CI SAST workflows."},
            {"id": "sast-tool", "default": "bandit",
             "description": "SAST tool (bandit, semgrep, gosec, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-85",
        "rule": "Application manifests and OSCAL artifacts must be validated in the pipeline.",
        "check": "makefile-target | param: validate-target",
        "params": [
            {"id": "validate-target", "default": "validate-catalog",
             "description": "Pipeline target that validates manifests/artifacts."},
        ],
    },
    # ---- Securing Build Pipelines ------------------------------------------
    {
        "control_id": "CNSC-150",
        "rule": "Build environments and dependencies must be validated before use.",
        "check": "file-exists | param: dependency-file",
        "params": [
            {"id": "dependency-file", "default": "requirements.txt",
             "description": "Dependency declaration file (requirements.txt, go.mod, package.json, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-152",
        "rule": "Build artifacts must be reproducible; a dependency lock file must be present.",
        "check": "file-exists | param: lock-file",
        "params": [
            {"id": "lock-file", "default": "requirements.lock",
             "description": "Dependency lock file (requirements.lock, go.sum, package-lock.json, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-153",
        "rule": "External requirements must be locked and verified with hash pinning.",
        "check": "file-contains | param: pipeline-file; hash-pin-pattern",
        "params": [
            {"id": "hash-pin-pattern", "default": "--require-hashes",
             "description": "Pattern in the pipeline file that activates hash verification."},
        ],
    },
    {
        "control_id": "CNSC-154",
        "rule": "Sources of non-determinism must be eliminated; a lock file must be present.",
        "check": "file-exists | param: lock-file",
        "params": [],
    },
    {
        "control_id": "CNSC-155",
        "rule": "The build environment must be recorded.",
        "check": "file-exists | param: lock-file",
        "params": [],
    },
    {
        "control_id": "CNSC-156",
        "rule": "Creation of the build environment must be automated.",
        "check": "makefile-target | param: env-setup-target",
        "params": [
            {"id": "env-setup-target", "default": "venv",
             "description": "Pipeline target that creates the build environment."},
        ],
    },
    {
        "control_id": "CNSC-158",
        "rule": "Build and CI/CD steps must be automated through pipeline-as-code.",
        "check": "file-exists | param: pipeline-file",
        "params": [],
    },
    {
        "control_id": "CNSC-159",
        "rule": "Pipelines must be standardized across projects using a single entry point.",
        "check": "makefile-target | param: all-target",
        "params": [
            {"id": "all-target", "default": "all",
             "description": "The single top-level pipeline entry point target."},
        ],
    },
    {
        "control_id": "CNSC-165",
        "rule": "Pipeline output must be written to a separate secured storage location.",
        "check": "file-exists | param: output-artifact-path",
        "params": [
            {"id": "output-artifact-path", "default": "dist",
             "description": "Path to the primary secured pipeline output artifact or directory."},
        ],
    },
    {
        "control_id": "CNSC-166",
        "rule": "Pipeline modification must only be allowed through pipeline-as-code with branch protection.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-167",
        "rule": "User roles must be defined for the repository.",
        "check": "file-exists | param: codeowners-file",
        "params": [
            {"id": "codeowners-file", "default": "CODEOWNERS",
             "description": "Path to the CODEOWNERS file."},
        ],
    },
    {
        "control_id": "CNSC-168",
        "rule": "A root-of-trust establishment procedure must be documented.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    # ---- Securing Materials ------------------------------------------------
    {
        "control_id": "CNSC-173",
        "rule": "Third-party artifacts and open source libraries must be declared and verified.",
        "check": "file-exists | param: dependency-file",
        "params": [],
    },
    {
        "control_id": "CNSC-174",
        "rule": "An SBOM must be required from third-party suppliers.",
        "check": "file-exists | param: sbom-output-path",
        "params": [
            {"id": "sbom-output-path", "default": "sbom.json",
             "description": "Path to the generated SBOM file."},
        ],
    },
    {
        "control_id": "CNSC-175",
        "rule": "Dependencies between open source components must be tracked.",
        "check": "file-exists | param: dependency-file",
        "params": [],
    },
    {
        "control_id": "CNSC-177",
        "rule": "Only trusted package managers and repositories must be used.",
        "check": "file-contains | param: pipeline-file; trusted-registry-pattern",
        "params": [
            {"id": "trusted-registry-pattern", "default": "pip install",
             "description": "Pattern confirming use of a trusted package manager in the pipeline file."},
        ],
    },
    {
        "control_id": "CNSC-178",
        "rule": "An immutable SBOM of the code must be generated.",
        "check": "makefile-target | param: sbom-target",
        "params": [
            {"id": "sbom-target", "default": "generate-sbom",
             "description": "Pipeline target that generates the SBOM."},
        ],
    },
    {
        "control_id": "CNSC-179",
        "rule": "Software must be scanned for known vulnerabilities.",
        "check": "ci-vuln-scan | param: pipeline-vuln-scan-target; vuln-scan-workflows",
        "params": [
            {"id": "vulnerability-scanner", "default": "pip-audit",
             "description": "Vulnerability scanner tool (pip-audit, trivy, grype, govulncheck, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-180",
        "rule": "Software must be scanned for license compliance.",
        "check": "makefile-target | param: license-scan-target",
        "params": [
            {"id": "license-scan-target", "default": "license-check",
             "description": "Pipeline target that runs license compliance scanning."},
            {"id": "license-scanner", "default": "pip-licenses",
             "description": "License scanner tool (pip-licenses, golicense, license-checker, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-181",
        "rule": "Software composition analysis must be run on ingested software.",
        "check": "makefile-target | param: sca-target",
        "params": [
            {"id": "sca-target", "default": "sca",
             "description": "Pipeline target that runs software composition analysis."},
        ],
    },
    # ---- Securing the Source Code ------------------------------------------
    {
        "control_id": "CNSC-182",
        "rule": "All commits and tags must carry a valid GPG or SSH cryptographic signature, with exemption for automated release bot commits.",
        "check": "git-commits-signed | param: signed-commits-lookback; signed-commits-exempt-pattern",
        "params": [
            {"id": "signed-commits-lookback", "default": "10",
             "description": "Number of recent commits to verify for signatures."},
            {"id": "signed-commits-exempt-pattern", "default": r"^chore: Merge back.*|^\d+\.\d+\.\d+",
             "description": "Regex pattern matching allowable unsigned release automation commits."},
        ],
    },
    {
        "control_id": "CNSC-183",
        "rule": "Full attestation and verification must be enforced for the default branch.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-184",
        "rule": "No unencrypted secrets must be committed to the repository.",
        "check": "no-secrets-in-files | param: secrets-scan-extensions; secrets-scan-exclude-paths",
        "params": [
            {"id": "secrets-scan-extensions", "default": "py,sh,yaml,yml,env,cfg,ini",
             "description": "Comma-separated file extensions to scan for hardcoded secrets."},
            {"id": "secrets-scan-exclude-paths", "default": ".venv,trestle.ws,.git,dist",
             "description": "Comma-separated directory names to exclude from secrets scanning."},
        ],
    },
    {
        "control_id": "CNSC-185",
        "rule": "Individuals or teams with write access must be explicitly defined.",
        "check": "file-exists | param: codeowners-file",
        "params": [],
    },
    {
        "control_id": "CNSC-186",
        "rule": "Software security scanning and testing must be automated in the pipeline.",
        "check": "ci-sast | param: sast-target; sast-workflows",
        "params": [],
    },
    {
        "control_id": "CNSC-187",
        "rule": "Contribution policies must be established and documented.",
        "check": "file-exists | param: contributing-file",
        "params": [
            {"id": "contributing-file", "default": "CONTRIBUTING.md",
             "description": "Path to the contribution policy document."},
        ],
    },
    {
        "control_id": "CNSC-188",
        "rule": "Roles must be defined and aligned to functional responsibilities.",
        "check": "file-exists | param: codeowners-file",
        "params": [],
    },
    {
        "control_id": "CNSC-189",
        "rule": "An independent four-eyes principle must be enforced via branch protection.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-190",
        "rule": "Branch protection rules must be enabled on the default branch.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-191",
        "rule": "MFA must be enforced for accessing source code repositories.",
        "check": "manual | param: mfa-enforcement-scope",
        "params": [
            {"id": "mfa-enforcement-scope", "default": "organization",
             "description": "Scope at which MFA is enforced (organization, team, repository)."},
        ],
    },
    {
        "control_id": "CNSC-192",
        "rule": "SSH keys must be used to provide developer access to source code repositories.",
        "check": "file-contains | param: git-config-file; ssh-remote-pattern",
        "params": [
            {"id": "git-config-file", "default": ".git/config",
             "description": "Path to the git configuration file."},
            {"id": "ssh-remote-pattern", "default": "git@github\\.com",
             "description": "Pattern confirming SSH remote URL in git config."},
        ],
    },
    {
        "control_id": "CNSC-193",
        "rule": "A key rotation policy must be documented.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-194",
        "rule": "Short-lived or ephemeral credentials must be used for machine and service access.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    # ---- Security Assurance ------------------------------------------------
    {
        "control_id": "CNSC-121",
        "rule": "A threat model for code and infrastructure must be documented.",
        "check": "file-exists | param: threat-model-file",
        "params": [],
    },
    {
        "control_id": "CNSC-196",
        "rule": "Supply chain security best practices must be adhered to (SBOM, lock file, SCA).",
        "check": "file-exists | param: lock-file",
        "params": [],
    },
    {
        "control_id": "CNSC-197",
        "rule": "Access to repository and branches must be restricted via branch protection and CODEOWNERS.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-198",
        "rule": "Unencrypted credentials or secrets must never be stored in the repository.",
        "check": "no-secrets-in-files | param: secrets-scan-extensions; secrets-scan-exclude-paths",
        "params": [],
    },
    {
        "control_id": "CNSC-199",
        "rule": "Strong identity must be enforced with GPG-signed commits, with exemption for automated release bot commits.",
        "check": "git-commits-signed | param: signed-commits-lookback; signed-commits-exempt-pattern",
        "params": [],
    },
    {
        "control_id": "CNSC-200",
        "rule": "Linear history must be enforced; force-push must be disallowed.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-201",
        "rule": "Branching policy must be enforced with main branch protection and code review.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-202",
        "rule": "Git and GitOps tools must be monitored for vulnerabilities and kept up to date.",
        "check": "manual | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-203",
        "rule": "SSH keys and Personal Access Tokens must be rotated regularly.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-204",
        "rule": "Dedicated non-user technical accounts must be used for automated access.",
        "check": "manual | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-205",
        "rule": "Users who can escalate permissions must be limited to a pre-approved set.",
        "check": "manual | param: security-policy-file",
        "params": [],
    },
]

# Flat map of all default param values, derived from REQUIREMENTS.
# First declaration of each param-id wins (matches comp-def behaviour).
DEFAULT_PARAMS: dict[str, str] = {}
for _req in REQUIREMENTS:
    for _p in _req.get("params", []):
        DEFAULT_PARAMS.setdefault(_p["id"], _p["default"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sp(param_id: str, value: str, remarks: str | None = None) -> common.SetParameter:
    return common.SetParameter(
        **{"param-id": param_id},
        values=[value],
        remarks=remarks,
    )


def _slug(repo_url: str) -> str:
    """Turn a GitHub URL into a filesystem-safe slug, e.g. oscal-compass--compliance-trestle."""
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", repo_url)
    path = m.group(1) if m else repo_url
    return re.sub(r"[^a-zA-Z0-9._-]", "--", path)


def _repo_name(repo_url: str) -> str:
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", repo_url)
    return m.group(1) if m else repo_url


def _git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=cwd, timeout=30)
    return r.stdout.strip()


# ---------------------------------------------------------------------------
# Repo cloning and probing
# ---------------------------------------------------------------------------

def clone_repo(repo_url: str, clone_base: Path) -> Path:
    slug = _slug(repo_url)
    dest = clone_base / slug
    if dest.exists():
        print(f"  Updating existing clone: {dest}")
        subprocess.run(["git", "pull", "--ff-only"], cwd=dest, check=False, capture_output=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  Cloning {repo_url} → {dest}")
        subprocess.run(
            ["git", "clone", "--depth=20", repo_url, str(dest)],
            check=True,
            capture_output=True,
        )
    return dest


def _first_existing(root: Path, candidates: list[str]) -> str | None:
    for c in candidates:
        if (root / c).exists():
            return c
    return None


def probe_params(repo_root: Path) -> dict[str, str]:
    """Probe the repo and return a complete param-id → value dict."""
    p: dict[str, str] = {}

    branch = _git(["symbolic-ref", "--short", "HEAD"], repo_root)
    p["default-branch"] = branch or "main"

    p["pipeline-file"] = _first_existing(repo_root, [
        "Makefile", "Taskfile.yml", "Taskfile.yaml",
        ".github/workflows/ci.yml", ".github/workflows/build.yml",
        "Justfile",
    ]) or "Makefile"

    p["dependency-file"] = _first_existing(repo_root, [
        "go.mod", "pyproject.toml", "requirements.txt",
        "package.json", "Cargo.toml", "Pipfile",
    ]) or "requirements.txt"

    p["lock-file"] = _first_existing(repo_root, [
        "go.sum", "poetry.lock", "package-lock.json",
        "yarn.lock", "requirements.lock", "Pipfile.lock", "Cargo.lock",
    ]) or "requirements.lock"

    p["codeowners-file"] = _first_existing(repo_root, [
        ".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS",
    ]) or "CODEOWNERS"

    p["contributing-file"] = _first_existing(repo_root, [
        "CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md",
    ]) or "CONTRIBUTING.md"

    p["security-policy-file"] = _first_existing(repo_root, [
        "SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md",
    ]) or "SECURITY.md"

    p["threat-model-file"] = _first_existing(repo_root, [
        "THREAT_MODEL.md", "THREAT-MODEL.md", "docs/THREAT_MODEL.md",
    ]) or "THREAT_MODEL.md"

    p["sbom-output-path"] = _first_existing(repo_root, [
        "sbom.json", "sbom.cdx.json", "dist/sbom.json",
    ]) or "sbom.json"

    p["output-artifact-path"] = _first_existing(repo_root, [
        "trestle.ws/catalogs/cncf-controls/catalog.json", "dist", "build",
    ]) or "dist"

    p["test-dir"] = _first_existing(repo_root, [
        "tests", "test", "spec", "__tests__",
    ]) or "tests"

    # Detect ecosystem-specific tooling from dependency-file
    dep = p["dependency-file"]
    if dep in ("go.mod",):
        p.setdefault("sast-tool", "gosec")
        p.setdefault("vulnerability-scanner", "govulncheck")
        p.setdefault("license-scanner", "golicense")
        p.setdefault("trusted-registry-pattern", "go get")
    elif dep in ("package.json",):
        p.setdefault("sast-tool", "eslint")
        p.setdefault("vulnerability-scanner", "npm audit")
        p.setdefault("license-scanner", "license-checker")
        p.setdefault("trusted-registry-pattern", "npm install")
    else:
        p.setdefault("sast-tool", "bandit")
        p.setdefault("vulnerability-scanner", "pip-audit")
        p.setdefault("license-scanner", "pip-licenses")
        p.setdefault("trusted-registry-pattern", "pip install")

    # Anything not detected falls back to the shared base default
    for k, v in DEFAULT_PARAMS.items():
        p.setdefault(k, v)

    return p


def diff_params(probed: dict[str, str]) -> dict[str, str]:
    """Return only the params whose probed value differs from the base default."""
    return {
        k: v for k, v in probed.items()
        if DEFAULT_PARAMS.get(k) != v
    }


# ---------------------------------------------------------------------------
# Base component definition builder
# ---------------------------------------------------------------------------

def build_base_comp_def() -> comp.Model:
    now = datetime.now(tz=timezone.utc)
    profile_href = "trestle://profiles/cncf-repo/profile.json"

    # Global set-parameters: deduplicated by first declaration
    global_params: dict[str, common.SetParameter] = {}
    for req in REQUIREMENTS:
        for p in req["params"]:
            if p["id"] not in global_params:
                global_params[p["id"]] = _sp(p["id"], p["default"], p["description"])

    implemented = []
    for req in REQUIREMENTS:
        cid = req["control_id"]
        props = [
            common.Property(name="rule",  value=req["rule"]),
            common.Property(name="check", value=req["check"]),
        ]
        set_params = [
            _sp(p["id"], p["default"], p["description"])
            for p in req["params"]
        ] or None
        ir_kwargs: dict = {
            "uuid": str(uuid.uuid4()),
            "control-id": cid,
            "description": req["rule"],
            "props": props,
            "statements": [
                comp.Statement(
                    **{"statement-id": f"{cid}_smt"},
                    uuid=str(uuid.uuid4()),
                    description=f"Rule: {req['rule']} | Check: {req['check']}",
                )
            ],
        }
        if set_params:
            ir_kwargs["set-parameters"] = set_params
        implemented.append(comp.ImplementedRequirement(**ir_kwargs))

    control_impl = comp.ControlImplementation(
        uuid=str(uuid.uuid4()),
        source=profile_href,
        description="Shared implementation of cncf-repo profile controls for all CNCF source repositories.",
        **{"set-parameters": list(global_params.values())},
        **{"implemented-requirements": implemented},
    )

    component = comp.DefinedComponent(
        uuid=str(uuid.uuid4()),
        type="software",
        title="CNCF Source Repository",
        description=(
            "Shared component representing any CNCF source repository. "
            "Defines rules, check types, and default parameter values for all "
            "controls selected by the cncf-repo profile. "
            "Per-project component definitions import this base and override "
            "only the parameters that differ from these defaults."
        ),
        purpose="Provide a reusable compliance baseline for CNCF source repositories.",
        **{"control-implementations": [control_impl]},
    )

    metadata = common.Metadata(
        title="CNCF Source Repository — Shared Base Component Definition",
        **{"last-modified": now},
        version="1.0",
        **{"oscal-version": OSCAL_VERSION},
        parties=[
            common.Parties(
                uuid=str(uuid.uuid4()),
                type="organization",
                name="CNCF TAG Security and Compliance",
            )
        ],
    )

    return comp.Model(**{
        "component-definition": comp.ComponentDefinition(
            uuid=str(uuid.uuid4()),
            metadata=metadata,
            components=[component],
        )
    })


# ---------------------------------------------------------------------------
# Per-project component definition builder
# ---------------------------------------------------------------------------

def build_project_comp_def(repo_url: str, repo_name: str, overrides: dict[str, str]) -> comp.Model:
    now = datetime.now(tz=timezone.utc)
    profile_href = "trestle://profiles/cncf-repo/profile.json"
    base_href = "trestle://component-definitions/cncf-repo/component-definition.json"

    set_params = [_sp(k, v) for k, v in sorted(overrides.items())] or None

    ci_kwargs: dict = {
        "uuid": str(uuid.uuid4()),
        "source": profile_href,
        "description": f"Parameter overrides for {repo_name} relative to the shared cncf-repo base.",
    }
    if set_params:
        ci_kwargs["set-parameters"] = set_params
    # At least one implemented-requirement is required by OSCAL schema;
    # we declare a single placeholder that defers all rules to the base.
    ci_kwargs["implemented-requirements"] = [
        comp.ImplementedRequirement(
            uuid=str(uuid.uuid4()),
            **{"control-id": "CNSC-71"},
            description=(
                "All control implementations are inherited from the shared base "
                "component definition. Only parameter overrides are declared here."
            ),
        )
    ]

    component = comp.DefinedComponent(
        uuid=str(uuid.uuid4()),
        type="software",
        title=repo_name,
        description=f"Source code repository at {repo_url}.",
        purpose="CNCF project source repository assessed against the cncf-repo profile.",
        links=[common.Link(href=repo_url, rel="reference")],
        **{"control-implementations": [comp.ControlImplementation(**ci_kwargs)]},
    )

    metadata = common.Metadata(
        title=f"Component Definition — {repo_name}",
        **{"last-modified": now},
        version="1.0",
        **{"oscal-version": OSCAL_VERSION},
        parties=[
            common.Parties(
                uuid=str(uuid.uuid4()),
                type="organization",
                name=repo_name,
                links=[common.Link(href=repo_url, rel="canonical")],
            )
        ],
    )

    return comp.Model(**{
        "component-definition": comp.ComponentDefinition(
            uuid=str(uuid.uuid4()),
            metadata=metadata,
            **{"import-component-definitions": [
                comp.ImportComponentDefinition(href=base_href)
            ]},
            components=[component],
        )
    })


# ---------------------------------------------------------------------------
# SSP builder
# ---------------------------------------------------------------------------

def build_ssp(
    repo_url: str,
    repo_name: str,
    slug: str,
    probed: dict[str, str],
) -> ssp_mod.Model:
    now = datetime.now(tz=timezone.utc)
    profile_href = "trestle://profiles/cncf-repo/profile.json"
    comp_def_href = f"trestle://component-definitions/{slug}/component-definition.json"
    comp_uuid = str(uuid.uuid4())

    # One implemented-requirement per control, with all probed param values
    ctrl_param_map: dict[str, list[str]] = {}
    for req in REQUIREMENTS:
        pids = [p["id"] for p in req["params"]]
        ctrl_param_map.setdefault(req["control_id"], [])
        ctrl_param_map[req["control_id"]].extend(pids)

    implemented = []
    seen_controls: set[str] = set()
    for req in REQUIREMENTS:
        cid = req["control_id"]
        if cid in seen_controls:
            continue
        seen_controls.add(cid)

        all_pids = list(dict.fromkeys(ctrl_param_map.get(cid, [])))
        set_params = [
            common.SetParameter(**{"param-id": pid}, values=[probed[pid]])
            for pid in all_pids
            if pid in probed
        ] or None

        ir_kwargs: dict = {
            "uuid": str(uuid.uuid4()),
            "control-id": cid,
            "by-components": [
                ssp_mod.ByComponent(
                    **{"component-uuid": comp_uuid},
                    uuid=str(uuid.uuid4()),
                    description=f"Repository component implements {cid}.",
                )
            ],
        }
        if set_params:
            ir_kwargs["set-parameters"] = set_params

        implemented.append(ssp_mod.ImplementedRequirement(**ir_kwargs))

    ssp = ssp_mod.SystemSecurityPlan(
        uuid=str(uuid.uuid4()),
        metadata=common.Metadata(
            title=f"System Security Plan — {repo_name}",
            **{"last-modified": now},
            version="1.0",
            **{"oscal-version": OSCAL_VERSION},
            parties=[
                common.Parties(
                    uuid=str(uuid.uuid4()),
                    type="organization",
                    name=repo_name,
                    links=[common.Link(href=repo_url, rel="canonical")],
                )
            ],
        ),
        **{"import-profile": ssp_mod.ImportProfile(href=profile_href)},
        **{"system-characteristics": ssp_mod.SystemCharacteristics(
            **{
                "system-ids": [common.SystemId(
                    **{"identifier-type": "https://github.com"}, id=repo_url
                )],
                "system-name": repo_name,
                "description": (
                    f"Source code repository at {repo_url}, "
                    "assessed against the CNCF cncf-repo profile."
                ),
                "status": ssp_mod.Status1(
                    state=ssp_mod.OperationalStateValidValues.operational
                ),
                "authorization-boundary": ssp_mod.AuthorizationBoundary(
                    description=(
                        "The source code repository, its build pipeline, "
                        "dependency declarations, branch protection settings, "
                        "and committed artifacts."
                    )
                ),
                "system-information": ssp_mod.SystemInformation(
                    **{"information-types": [
                        ssp_mod.InformationType(
                            uuid=str(uuid.uuid4()),
                            title="Source Code and Build Artifacts",
                            description=(
                                "Source code, scripts, configuration files, "
                                "dependency declarations, and generated OSCAL artifacts."
                            ),
                        )
                    ]}
                ),
            }
        )},
        **{"system-implementation": ssp_mod.SystemImplementation(
            components=[
                common.SystemComponent(
                    uuid=comp_uuid,
                    type="software",
                    title=repo_name,
                    description=f"Source repository: {repo_url}",
                    status=common.Status(
                        state=common.SystemComponentOperationalStateValidValues.operational
                    ),
                    links=[common.Link(href=repo_url, rel="reference")],
                    props=[common.Property(
                        name="component-definition-href",
                        value=comp_def_href,
                    )],
                )
            ],
            users=[
                common.SystemUser(
                    uuid=str(uuid.uuid4()),
                    title="Repository Contributor",
                    **{"short-name": "contributor"},
                    description="Developer with commit access to the repository.",
                    **{"role-ids": ["developer"]},
                )
            ],
        )},
        **{"control-implementation": ssp_mod.ControlImplementation(
            description=(
                "Implementation of cncf-repo profile controls. "
                "Parameter values are specific to this repository."
            ),
            **{"implemented-requirements": implemented},
        )},
    )

    return ssp_mod.Model(**{"system-security-plan": ssp})


# ---------------------------------------------------------------------------
# Assessment plan builder
# ---------------------------------------------------------------------------

def build_ap(repo_name: str, slug: str) -> ap_mod.Model:
    now = datetime.now(tz=timezone.utc)
    ssp_href = f"trestle://system-security-plans/{slug}/system-security-plan.json"
    control_ids = list(dict.fromkeys(r["control_id"] for r in REQUIREMENTS))

    ap = ap_mod.AssessmentPlan(
        uuid=str(uuid.uuid4()),
        metadata=common.Metadata(
            title=f"Assessment Plan — {repo_name}",
            **{"last-modified": now},
            version="1.0",
            **{"oscal-version": OSCAL_VERSION},
        ),
        **{"import-ssp": common.ImportSsp(href=ssp_href)},
        **{"reviewed-controls": common.ReviewedControls(
            description="All controls selected by the cncf-repo profile.",
            **{"control-selections": [
                common.ControlSelections(
                    **{"include-controls": [
                        common.SelectControlById(**{"control-id": cid})
                        for cid in control_ids
                    ]}
                )
            ]},
        )},
        **{"assessment-subjects": [
            common.AssessmentSubjectAll(
                type="component",
                description="The source code repository component.",
                **{"include-all": common.IncludeAll()},
            )
        ]},
    )

    return ap_mod.Model(**{"assessment-plan": ap})


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


def cmd_project(repo_url: str, trestle_ws: Path, clone_base: Path) -> int:
    slug = _slug(repo_url)
    repo_name = _repo_name(repo_url)
    print(f"Project : {repo_name}")
    print(f"Slug    : {slug}")

    # 1. Clone / update
    repo_root = clone_repo(repo_url, clone_base)

    # 2. Probe
    print("  Probing repository...")
    probed = probe_params(repo_root)
    overrides = diff_params(probed)
    print(f"  Probed {len(probed)} params; {len(overrides)} differ from base defaults:")
    for k, v in sorted(overrides.items()):
        print(f"    {k}: {DEFAULT_PARAMS.get(k)!r} → {v!r}")

    # 3. Per-project comp def
    cd_model = build_project_comp_def(repo_url, repo_name, overrides)
    cd_dir = trestle_ws / "component-definitions" / slug
    cd_dir.mkdir(parents=True, exist_ok=True)
    cd_path = cd_dir / "component-definition.json"
    cd_path.write_text(
        cd_model.model_dump_json(indent=2, exclude_none=True, by_alias=True),
        encoding="utf-8",
    )
    print(f"  Written: {cd_path}")

    # 4. SSP
    ssp_model = build_ssp(repo_url, repo_name, slug, probed)
    ssp_dir = trestle_ws / "system-security-plans" / slug
    ssp_dir.mkdir(parents=True, exist_ok=True)
    ssp_path = ssp_dir / "system-security-plan.json"
    ssp_path.write_text(
        ssp_model.model_dump_json(indent=2, exclude_none=True, by_alias=True),
        encoding="utf-8",
    )
    print(f"  Written: {ssp_path}")

    # 5. Assessment plan
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
    p_proj.add_argument(
        "--clone-dir", default="/tmp/cncf-compliance-clones",
        help="Directory for shallow clones (default: /tmp/cncf-compliance-clones)",
    )

    args = parser.parse_args()
    trestle_ws = Path(args.trestle_ws)

    if args.cmd == "base":
        return cmd_base(trestle_ws)
    if args.cmd == "project":
        return cmd_project(args.repo_url, trestle_ws, Path(args.clone_dir))
    return 1


if __name__ == "__main__":
    sys.exit(main())
