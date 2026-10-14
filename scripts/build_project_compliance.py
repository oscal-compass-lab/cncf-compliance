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
from pathlib import Path

import oscal_factory as factory
from trestle.oscal import component as comp
from trestle.oscal import ssp as ssp_mod
from trestle.oscal import common

# Re-export so callers that import CNCF_OSCAL_NS from here still work.
CNCF_OSCAL_NS = factory.CNCF_OSCAL_NS


# ---------------------------------------------------------------------------
# Control requirements table
# Rule + check type + parameter defaults — shared across all projects.
# ---------------------------------------------------------------------------

REQUIREMENTS = [
    # ---- Develop -----------------------------------------------------------
    {
        "control_id": "CNSC-65",
        "rule_id": "RULE-01",
        "rule_title": "Early Vulnerability Scanning",
        "check_id": "CHECK-01",
        "check_title": "CI Vulnerability & Configuration Scanning Probe",
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
        "rule_id": "RULE-02",
        "rule_title": "Business-Critical Code Testing",
        "check_id": "CHECK-02",
        "check_title": "Test Suite Directory Verification",
        "rule": "Tests must exist for business-critical code paths.",
        "check": "file-exists | param: test-dir",
        "params": [
            {"id": "test-dir", "default": "tests",
             "description": "Directory containing test suites."},
        ],
    },
    {
        "control_id": "CNSC-68",
        "rule_id": "RULE-03",
        "rule_title": "Infrastructure Code Testing",
        "check_id": "CHECK-03",
        "check_title": "Infrastructure Test Directory Verification",
        "rule": "Tests must exist for business-critical infrastructure.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-69",
        "rule_id": "RULE-04",
        "rule_title": "Local Test Execution",
        "check_id": "CHECK-04",
        "check_title": "Local Test Pipeline Target Verification",
        "rule": "Test suites must be runnable locally without external dependencies.",
        "check": "makefile-target | param: test-target",
        "params": [
            {"id": "test-target", "default": "test",
             "description": "Pipeline target that runs tests locally."},
        ],
    },
    {
        "control_id": "CNSC-71",
        "rule_id": "RULE-05",
        "rule_title": "Two Non-Author Reviewers Approval",
        "check_id": "CHECK-05",
        "check_title": "Branch Protection Multi-Reviewer Probe",
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
        "rule_id": "RULE-06",
        "rule_title": "Clean Pipeline-as-Code",
        "check_id": "CHECK-06",
        "check_title": "Pipeline Definition File Verification",
        "rule": "Code must be clean and well commented.",
        "check": "file-exists | param: pipeline-file",
        "params": [
            {"id": "pipeline-file", "default": "Makefile",
             "description": "The pipeline-as-code file (Makefile, Taskfile.yml, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-73",
        "rule_id": "RULE-07",
        "rule_title": "Full Infrastructure Tests",
        "check_id": "CHECK-07",
        "check_title": "Full Infrastructure Test Suite Verification",
        "rule": "Full infrastructure tests must be present.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-74",
        "rule_id": "RULE-08",
        "rule_title": "Regression Testing",
        "check_id": "CHECK-08",
        "check_title": "Regression Test Suite Verification",
        "rule": "Regression tests must be present.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-75",
        "rule_id": "RULE-09",
        "rule_title": "Emerging Threat Test Updates",
        "check_id": "CHECK-09",
        "check_title": "Threat Test Coverage Verification",
        "rule": "Test suites must be updated against new and emerging threats.",
        "check": "file-exists | param: test-dir",
        "params": [],
    },
    {
        "control_id": "CNSC-78",
        "rule_id": "RULE-10",
        "rule_title": "Threat Model Driven Testing Priorities",
        "check_id": "CHECK-10",
        "check_title": "Threat Model Document Verification",
        "rule": "Threat model results must be used to determine test development priorities.",
        "check": "file-exists | param: threat-model-file",
        "params": [
            {"id": "threat-model-file", "default": "THREAT_MODEL.md",
             "description": "Path to the threat model document."},
        ],
    },
    {
        "control_id": "CNSC-195",
        "rule_id": "RULE-11",
        "rule_title": "Secure Configuration Default State",
        "check_id": "CHECK-11",
        "check_title": "Security Policy Document Verification",
        "rule": "Secure configuration must be the default state of the system.",
        "check": "file-exists | param: security-policy-file",
        "params": [
            {"id": "security-policy-file", "default": "SECURITY.md",
             "description": "Path to the security policy document."},
        ],
    },
    {
        "control_id": "CNSC-259",
        "rule_id": "RULE-12",
        "rule_title": "IDE and CI Vulnerability Scanning",
        "check_id": "CHECK-12",
        "check_title": "IDE/CI Vulnerability Scanning Probe",
        "rule": "Vulnerability and configuration scanning must be integrated in both IDE and CI pipeline.",
        "check": "ci-vuln-scan | param: pipeline-vuln-scan-target; vuln-scan-workflows",
        "params": [],
    },
    {
        "control_id": "CNSC-265",
        "rule_id": "RULE-13",
        "rule_title": "Single Non-Author Reviewer Approval",
        "check_id": "CHECK-13",
        "check_title": "Branch Protection Single-Reviewer Probe",
        "rule": "At least one non-author reviewer must approve before merging.",
        "check": "git-branch-protected | param: default-branch; min-reviewers",
        "params": [],
    },
    # ---- Distribute --------------------------------------------------------
    {
        "control_id": "CNSC-82",
        "rule_id": "RULE-14",
        "rule_title": "Static Application Security Testing (SAST)",
        "check_id": "CHECK-14",
        "check_title": "SAST Pipeline and Workflow Probe",
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
        "rule_id": "RULE-15",
        "rule_title": "Manifest and Workflow Scanning",
        "check_id": "CHECK-15",
        "check_title": "CI Manifest & Workflow Linter Probe",
        "rule": "Application, workflow, and deployment manifests must be scanned and validated in the CI pipeline.",
        "check": "ci-manifest-scan | param: manifest-scan-target; manifest-scan-workflows",
        "params": [
            {"id": "manifest-scan-target", "default": "act-lint",
             "description": "Pipeline target that validates/lints manifests."},
            {"id": "manifest-scan-workflows", "default": "actionlint,kube-linter,yamllint,checkov,trivy,lint",
             "description": "Keywords for CI manifest scanning workflows."},
        ],
    },
    # ---- Securing Build Pipelines ------------------------------------------
    {
        "control_id": "CNSC-150",
        "rule_id": "RULE-16",
        "rule_title": "Build Environment and Dependency Declaration",
        "check_id": "CHECK-16",
        "check_title": "Dependency Manifest File Verification",
        "rule": "Build environments and dependencies must be validated before use.",
        "check": "file-exists | param: dependency-file",
        "params": [
            {"id": "dependency-file", "default": "requirements.txt",
             "description": "Dependency declaration file (requirements.txt, go.mod, package.json, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-152",
        "rule_id": "RULE-17",
        "rule_title": "Reproducible Builds Dependency Lock",
        "check_id": "CHECK-17",
        "check_title": "Dependency Lock File Verification",
        "rule": "Build artifacts must be reproducible; a dependency lock file must be present.",
        "check": "file-exists | param: lock-file",
        "params": [
            {"id": "lock-file", "default": "requirements.lock",
             "description": "Dependency lock file (requirements.lock, go.sum, package-lock.json, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-153",
        "rule_id": "RULE-18",
        "rule_title": "External Requirements Hash Pinning",
        "check_id": "CHECK-18",
        "check_title": "Pipeline Hash Pinning Pattern Probe",
        "rule": "External requirements must be locked and verified with hash pinning.",
        "check": "file-contains | param: pipeline-file; hash-pin-pattern",
        "params": [
            {"id": "hash-pin-pattern", "default": "--require-hashes",
             "description": "Pattern in the pipeline file that activates hash verification."},
        ],
    },
    {
        "control_id": "CNSC-154",
        "rule_id": "RULE-19",
        "rule_title": "Non-Determinism Elimination via Lock File",
        "check_id": "CHECK-19",
        "check_title": "Deterministic Build Lock File Verification",
        "rule": "Sources of non-determinism must be eliminated; a lock file must be present.",
        "check": "file-exists | param: lock-file",
        "params": [],
    },
    {
        "control_id": "CNSC-155",
        "rule_id": "RULE-20",
        "rule_title": "Build Environment Recording",
        "check_id": "CHECK-20",
        "check_title": "Build Environment Record Verification",
        "rule": "The build environment must be recorded.",
        "check": "file-exists | param: lock-file",
        "params": [],
    },
    {
        "control_id": "CNSC-156",
        "rule_id": "RULE-21",
        "rule_title": "Automated Build Environment Creation",
        "check_id": "CHECK-21",
        "check_title": "Build Environment Setup Target Verification",
        "rule": "Creation of the build environment must be automated.",
        "check": "makefile-target | param: env-setup-target",
        "params": [
            {"id": "env-setup-target", "default": "venv",
             "description": "Pipeline target that creates the build environment."},
        ],
    },
    {
        "control_id": "CNSC-158",
        "rule_id": "RULE-22",
        "rule_title": "Pipeline-as-Code Automation",
        "check_id": "CHECK-22",
        "check_title": "Pipeline-as-Code File Verification",
        "rule": "Build and CI/CD steps must be automated through pipeline-as-code.",
        "check": "file-exists | param: pipeline-file",
        "params": [],
    },
    {
        "control_id": "CNSC-159",
        "rule_id": "RULE-23",
        "rule_title": "Standardized Single Pipeline Entry Point",
        "check_id": "CHECK-23",
        "check_title": "Top-Level Pipeline Entry Point Target Verification",
        "rule": "Pipelines must be standardized across projects using a single entry point.",
        "check": "makefile-target | param: all-target",
        "params": [
            {"id": "all-target", "default": "all",
             "description": "The single top-level pipeline entry point target."},
        ],
    },
    {
        "control_id": "CNSC-165",
        "rule_id": "RULE-24",
        "rule_title": "Secured Pipeline Output Storage",
        "check_id": "CHECK-24",
        "check_title": "Pipeline Output Artifact Path Verification",
        "rule": "Pipeline output must be written to a separate secured storage location.",
        "check": "file-exists | param: output-artifact-path",
        "params": [
            {"id": "output-artifact-path", "default": "dist",
             "description": "Path to the primary secured pipeline output artifact or directory."},
        ],
    },
    {
        "control_id": "CNSC-166",
        "rule_id": "RULE-25",
        "rule_title": "Branch Protected Pipeline Modification",
        "check_id": "CHECK-25",
        "check_title": "Pipeline Branch Protection Verification",
        "rule": "Pipeline modification must only be allowed through pipeline-as-code with branch protection.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-167",
        "rule_id": "RULE-26",
        "rule_title": "Repository User Roles Definition",
        "check_id": "CHECK-26",
        "check_title": "CODEOWNERS Roles File Verification",
        "rule": "User roles must be defined for the repository.",
        "check": "file-exists | param: codeowners-file",
        "params": [
            {"id": "codeowners-file", "default": "CODEOWNERS",
             "description": "Path to the CODEOWNERS file."},
        ],
    },
    {
        "control_id": "CNSC-168",
        "rule_id": "RULE-27",
        "rule_title": "Root-of-Trust Establishment Procedure",
        "check_id": "CHECK-27",
        "check_title": "Security Policy Root-of-Trust Verification",
        "rule": "A root-of-trust establishment procedure must be documented.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    # ---- Securing Materials ------------------------------------------------
    {
        "control_id": "CNSC-173",
        "rule_id": "RULE-28",
        "rule_title": "Third-Party Artifact Declaration & Verification",
        "check_id": "CHECK-28",
        "check_title": "Declared Dependencies Verification",
        "rule": "Third-party artifacts and open source libraries must be declared and verified.",
        "check": "file-exists | param: dependency-file",
        "params": [],
    },
    {
        "control_id": "CNSC-174",
        "rule_id": "RULE-29",
        "rule_title": "Supplier SBOM Requirement",
        "check_id": "CHECK-29",
        "check_title": "Supplier SBOM File Verification",
        "rule": "An SBOM must be required from third-party suppliers.",
        "check": "file-exists | param: sbom-output-path",
        "params": [
            {"id": "sbom-output-path", "default": "sbom.json",
             "description": "Path to the generated SBOM file."},
        ],
    },
    {
        "control_id": "CNSC-175",
        "rule_id": "RULE-30",
        "rule_title": "Open Source Component Dependency Tracking",
        "check_id": "CHECK-30",
        "check_title": "Component Dependency Manifest Verification",
        "rule": "Dependencies between open source components must be tracked.",
        "check": "file-exists | param: dependency-file",
        "params": [],
    },
    {
        "control_id": "CNSC-177",
        "rule_id": "RULE-31",
        "rule_title": "Trusted Package Managers and Repositories",
        "check_id": "CHECK-31",
        "check_title": "Trusted Registry Pattern Probe",
        "rule": "Only trusted package managers and repositories must be used.",
        "check": "file-contains | param: pipeline-file; trusted-registry-pattern",
        "params": [
            {"id": "trusted-registry-pattern", "default": "pip install",
             "description": "Pattern confirming use of a trusted package manager in the pipeline file."},
        ],
    },
    {
        "control_id": "CNSC-178",
        "rule_id": "RULE-32",
        "rule_title": "Immutable Code SBOM Generation",
        "check_id": "CHECK-32",
        "check_title": "SBOM Generation Pipeline Target Verification",
        "rule": "An immutable SBOM of the code must be generated.",
        "check": "makefile-target | param: sbom-target",
        "params": [
            {"id": "sbom-target", "default": "generate-sbom",
             "description": "Pipeline target that generates the SBOM."},
        ],
    },
    {
        "control_id": "CNSC-179",
        "rule_id": "RULE-33",
        "rule_title": "Known Vulnerability Scanning",
        "check_id": "CHECK-33",
        "check_title": "Vulnerability Scanning Probe",
        "rule": "Software must be scanned for known vulnerabilities.",
        "check": "ci-vuln-scan | param: pipeline-vuln-scan-target; vuln-scan-workflows",
        "params": [
            {"id": "vulnerability-scanner", "default": "pip-audit",
             "description": "Vulnerability scanner tool (pip-audit, trivy, grype, govulncheck, etc.)."},
        ],
    },
    {
        "control_id": "CNSC-180",
        "rule_id": "RULE-34",
        "rule_title": "License Compliance Scanning",
        "check_id": "CHECK-34",
        "check_title": "License Compliance Pipeline Target Verification",
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
        "rule_id": "RULE-35",
        "rule_title": "Software Composition Analysis (SCA)",
        "check_id": "CHECK-35",
        "check_title": "SCA Pipeline Target Verification",
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
        "rule_id": "RULE-36",
        "rule_title": "Cryptographic Commit and Tag Signing",
        "check_id": "CHECK-36",
        "check_title": "Git Commit Cryptographic Signature Probe",
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
        "rule_id": "RULE-37",
        "rule_title": "Default Branch Full Attestation and Verification",
        "check_id": "CHECK-37",
        "check_title": "Default Branch Protection Attestation Probe",
        "rule": "Full attestation and verification must be enforced for the default branch.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-184",
        "rule_id": "RULE-38",
        "rule_title": "No Unencrypted Secrets in Repository",
        "check_id": "CHECK-38",
        "check_title": "Unencrypted Secrets File Scanner Probe",
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
        "rule_id": "RULE-39",
        "rule_title": "Explicit Repository Write Access Definition",
        "check_id": "CHECK-39",
        "check_title": "CODEOWNERS Write Access Verification",
        "rule": "Individuals or teams with write access must be explicitly defined.",
        "check": "file-exists | param: codeowners-file",
        "params": [],
    },
    {
        "control_id": "CNSC-186",
        "rule_id": "RULE-40",
        "rule_title": "Automated Pipeline Security Scanning",
        "check_id": "CHECK-40",
        "check_title": "Automated Security Scanning Probe",
        "rule": "Software security scanning and testing must be automated in the pipeline.",
        "check": "ci-sast | param: sast-target; sast-workflows",
        "params": [],
    },
    {
        "control_id": "CNSC-187",
        "rule_id": "RULE-41",
        "rule_title": "Documented Contribution Policies",
        "check_id": "CHECK-41",
        "check_title": "CONTRIBUTING Document Verification",
        "rule": "Contribution policies must be established and documented.",
        "check": "file-exists | param: contributing-file",
        "params": [
            {"id": "contributing-file", "default": "CONTRIBUTING.md",
             "description": "Path to the contribution policy document."},
        ],
    },
    {
        "control_id": "CNSC-188",
        "rule_id": "RULE-42",
        "rule_title": "Functional Role Alignment",
        "check_id": "CHECK-42",
        "check_title": "CODEOWNERS Functional Role Verification",
        "rule": "Roles must be defined and aligned to functional responsibilities.",
        "check": "file-exists | param: codeowners-file",
        "params": [],
    },
    {
        "control_id": "CNSC-189",
        "rule_id": "RULE-43",
        "rule_title": "Four-Eyes Principle Branch Protection",
        "check_id": "CHECK-43",
        "check_title": "Four-Eyes Branch Protection Probe",
        "rule": "An independent four-eyes principle must be enforced via branch protection.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-190",
        "rule_id": "RULE-44",
        "rule_title": "Default Branch Protection Rules Enabled",
        "check_id": "CHECK-44",
        "check_title": "Default Branch Protection Enabled Probe",
        "rule": "Branch protection rules must be enabled on the default branch.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-191",
        "rule_id": "RULE-45",
        "rule_title": "MFA Enforced for Repository Access",
        "check_id": "CHECK-45",
        "check_title": "MFA Enforcement Scope Review",
        "rule": "MFA must be enforced for accessing source code repositories.",
        "check": "manual | param: mfa-enforcement-scope",
        "params": [
            {"id": "mfa-enforcement-scope", "default": "organization",
             "description": "Scope at which MFA is enforced (organization, team, repository)."},
        ],
    },
    {
        "control_id": "CNSC-192",
        "rule_id": "RULE-46",
        "rule_title": "SSH Key Developer Access",
        "check_id": "CHECK-46",
        "check_title": "Git Remote SSH Configuration Probe",
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
        "rule_id": "RULE-47",
        "rule_title": "Documented Key Rotation Policy",
        "check_id": "CHECK-47",
        "check_title": "Security Policy Key Rotation Verification",
        "rule": "A key rotation policy must be documented.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-194",
        "rule_id": "RULE-48",
        "rule_title": "Ephemeral Credentials for Automated Access",
        "check_id": "CHECK-48",
        "check_title": "Security Policy Ephemeral Credentials Verification",
        "rule": "Short-lived or ephemeral credentials must be used for machine and service access.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    # ---- Security Assurance ------------------------------------------------
    {
        "control_id": "CNSC-121",
        "rule_id": "RULE-49",
        "rule_title": "Documented Code and Infrastructure Threat Model",
        "check_id": "CHECK-49",
        "check_title": "Threat Model File Verification",
        "rule": "A threat model for code and infrastructure must be documented.",
        "check": "file-exists | param: threat-model-file",
        "params": [],
    },
    {
        "control_id": "CNSC-196",
        "rule_id": "RULE-50",
        "rule_title": "Supply Chain Security Best Practices",
        "check_id": "CHECK-50",
        "check_title": "Supply Chain Lock File Verification",
        "rule": "Supply chain security best practices must be adhered to (SBOM, lock file, SCA).",
        "check": "file-exists | param: lock-file",
        "params": [],
    },
    {
        "control_id": "CNSC-197",
        "rule_id": "RULE-51",
        "rule_title": "Restricted Repository and Branch Access",
        "check_id": "CHECK-51",
        "check_title": "Restricted Branch Access Probe",
        "rule": "Access to repository and branches must be restricted via branch protection and CODEOWNERS.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-198",
        "rule_id": "RULE-52",
        "rule_title": "Prohibition of Unencrypted Stored Credentials",
        "check_id": "CHECK-52",
        "check_title": "Unencrypted Credentials File Scanner Probe",
        "rule": "Unencrypted credentials or secrets must never be stored in the repository.",
        "check": "no-secrets-in-files | param: secrets-scan-extensions; secrets-scan-exclude-paths",
        "params": [],
    },
    {
        "control_id": "CNSC-199",
        "rule_id": "RULE-53",
        "rule_title": "Strong Identity Enforcement with Signed Commits",
        "check_id": "CHECK-53",
        "check_title": "GPG Signed Commits Identity Probe",
        "rule": "Strong identity must be enforced with GPG-signed commits, with exemption for automated release bot commits.",
        "check": "git-commits-signed | param: signed-commits-lookback; signed-commits-exempt-pattern",
        "params": [],
    },
    {
        "control_id": "CNSC-200",
        "rule_id": "RULE-54",
        "rule_title": "Linear History and Force-Push Disallowed",
        "check_id": "CHECK-54",
        "check_title": "Linear History Branch Protection Probe",
        "rule": "Linear history must be enforced; force-push must be disallowed.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-201",
        "rule_id": "RULE-55",
        "rule_title": "Enforced Branching and Code Review Policy",
        "check_id": "CHECK-55",
        "check_title": "Branching Policy Protection Probe",
        "rule": "Branching policy must be enforced with main branch protection and code review.",
        "check": "git-branch-protected | param: default-branch",
        "params": [],
    },
    {
        "control_id": "CNSC-202",
        "rule_id": "RULE-56",
        "rule_title": "Git and GitOps Tool Vulnerability Monitoring",
        "check_id": "CHECK-56",
        "check_title": "GitOps Tool Monitoring Manual Review",
        "rule": "Git and GitOps tools must be monitored for vulnerabilities and kept up to date.",
        "check": "manual | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-203",
        "rule_id": "RULE-57",
        "rule_title": "Regular SSH Key and PAT Rotation",
        "check_id": "CHECK-57",
        "check_title": "Key and PAT Rotation Policy Verification",
        "rule": "SSH keys and Personal Access Tokens must be rotated regularly.",
        "check": "file-exists | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-204",
        "rule_id": "RULE-58",
        "rule_title": "Dedicated Technical Accounts for Automation",
        "check_id": "CHECK-58",
        "check_title": "Technical Accounts Policy Manual Review",
        "rule": "Dedicated non-user technical accounts must be used for automated access.",
        "check": "manual | param: security-policy-file",
        "params": [],
    },
    {
        "control_id": "CNSC-205",
        "rule_id": "RULE-59",
        "rule_title": "Limited Permission Escalation Authority",
        "check_id": "CHECK-59",
        "check_title": "Privilege Escalation Policy Manual Review",
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
    return factory.set_parameter(param_id, value, remarks)


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

    # 2. Validation Component — Rule_Id / Check_Id / Check_Description /
    #    Target_Component props, one group per requirement.
    val_props = []
    for i, req in enumerate(REQUIREMENTS):
        remarks = f"check_set_{i:02d}"
        val_props.extend([
            factory.cncf_prop("Rule_Id", req["rule_id"], remarks),
            factory.cncf_prop("Check_Id", req["check_id"], remarks),
            factory.cncf_prop("Check_Description", req["check"], remarks),
            factory.cncf_prop("Target_Component", "CNCF Source Repository", remarks),
        ])

    val_component = factory.validation_component(
        title="CNCF Compliance Validation Engine",
        description=(
            "Automated check probes and validation engine evaluating repository "
            "compliance against software rules."
        ),
        purpose="Execute automated checks and parameter verification for CNCF controls.",
        val_props=val_props,
    )

    md = factory.org_metadata(
        "CNCF Source Repository — Shared Base Component Definition",
        org_name="CNCF TAG Security and Compliance",
    )

    return factory.component_definition(md=md, components=[sw_component, val_component])


# ---------------------------------------------------------------------------
# Per-project component definition builder
# ---------------------------------------------------------------------------

def build_project_comp_def(repo_url: str, repo_name: str,
                            overrides: dict[str, str]) -> comp.Model:
    profile_href = "trestle://profiles/cncf-repo/profile.json"
    base_href = "trestle://component-definitions/cncf-repo/component-definition.json"

    set_params = [_sp(k, v) for k, v in sorted(overrides.items())] or None

    ci_kwargs: dict = {
        "uuid": factory.new_uuid(),
        "source": profile_href,
        "description": (
            f"Parameter overrides for {repo_name} relative to the shared cncf-repo base."
        ),
    }
    if set_params:
        ci_kwargs["set-parameters"] = set_params
    # At least one implemented-requirement is required by OSCAL schema;
    # we declare a single placeholder that defers all rules to the base.
    ci_kwargs["implemented-requirements"] = [
        comp.ImplementedRequirement(
            uuid=factory.new_uuid(),
            **{"control-id": "CNSC-71"},
            description=(
                "All control implementations are inherited from the shared base "
                "component definition. Only parameter overrides are declared here."
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
    probed: dict[str, str],
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
    # One implemented-requirement per control, with all probed params.    #
    # ------------------------------------------------------------------ #
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
            factory.set_parameter(pid, probed[pid])
            for pid in all_pids
            if pid in probed
        ] or None

        ir_kwargs: dict = {
            "uuid": factory.new_uuid(),
            "control-id": cid,
            "by-components": [
                ssp_mod.ByComponent(
                    **{"component-uuid": proj_sw_uuid},
                    uuid=factory.new_uuid(),
                    description=f"Repository component implements {cid}.",
                )
            ],
        }
        if set_params:
            ir_kwargs["set-parameters"] = set_params

        implemented.append(ssp_mod.ImplementedRequirement(**ir_kwargs))

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

    # 3. Apply any hand-managed param overrides (never overwritten by this script).
    # Lives in data/param-overrides/<slug>/overrides.json — outside the trestle workspace so
    # that trestle validate --all is not affected by a missing SSP.
    overrides_path = Path(__file__).resolve().parent.parent / "data" / "param-overrides" / slug / "overrides.json"
    if overrides_path.exists():
        manual = json.loads(overrides_path.read_text(encoding="utf-8"))
        print(f"  Applying {len(manual)} manual param override(s) from {overrides_path.name}:")
        for k, v in manual.items():
            print(f"    {k}: {probed.get(k)!r} → {v!r}")
        probed.update(manual)

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
    ssp_model = build_ssp(repo_url, repo_name, slug, probed, trestle_ws)
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
