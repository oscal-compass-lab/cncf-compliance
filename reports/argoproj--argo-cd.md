# CNCF controls report: argoproj/argo-cd

![cncf-controls: Fail](../badges/fail.svg)

- **Repository:** [https://github.com/argoproj/argo-cd](https://github.com/argoproj/argo-cd)
- **Commit assessed:** `0c62671`
- **Assessed at:** 2026-10-14 13:13 UTC
- **Level:** **Fail**. MUST controls not satisfied: CNSC-184, CNSC-198
- **Totals:** 42 satisfied, 12 failed, 5 not automated (of 59 controls)

Levels: *Fail* if any MUST control is not satisfied; otherwise *Baseline Pass Only* at 50%, *Bronze* at 60%, *Silver* at 75%, *Gold* at 90% of automated SHOULD controls. MUST controls: CNSC-182, CNSC-184, CNSC-190, CNSC-198, CNSC-199. Manual and non-assessable controls (N/A) are excluded from the percentage and never count as passes.

## Results by control

| Control | Priority | Result | Requirement | Evidence |
| --- | --- | --- | --- | --- |
| CNSC-65 | SHOULD | PASS | Early Vulnerability Scanning: Vulnerability and configuration scanning must be integrated at the pull-request or CI stage. | Found CI vulnerability/security scanning workflow: .github/workflows/auto-assign-pr-author.yaml |
| CNSC-67 | SHOULD | PASS | Business-Critical Code Testing: Tests must exist for business-critical code paths. | Found: test |
| CNSC-68 | SHOULD | PASS | Infrastructure Code Testing: Tests must exist for business-critical infrastructure. | Found: test |
| CNSC-69 | SHOULD | PASS | Local Test Execution: Test suites must be runnable locally without external dependencies. | Target 'test' found in Makefile |
| CNSC-71 | SHOULD | PASS | Two Non-Author Reviewers Approval: At least two non-author reviewers must approve before merging. | Branch 'master' protected=True |
| CNSC-72 | SHOULD | PASS | Clean Pipeline-as-Code: Code must be clean and well commented. | Found: Makefile |
| CNSC-73 | SHOULD | PASS | Full Infrastructure Tests: Full infrastructure tests must be present. | Found: test |
| CNSC-74 | SHOULD | PASS | Regression Testing: Regression tests must be present. | Found: test |
| CNSC-75 | SHOULD | PASS | Emerging Threat Test Updates: Test suites must be updated against new and emerging threats. | Found: test |
| CNSC-78 | SHOULD | FAIL | Threat Model Driven Testing Priorities: Threat model results must be used to determine test development priorities. | Missing: THREAT_MODEL.md |
| CNSC-195 | SHOULD | PASS | Secure Configuration Default State: Secure configuration must be the default state of the system. | Found: SECURITY.md |
| CNSC-259 | SHOULD | PASS | IDE and CI Vulnerability Scanning: Vulnerability and configuration scanning must be integrated in both IDE and CI pipeline. | Found CI vulnerability/security scanning workflow: .github/workflows/auto-assign-pr-author.yaml |
| CNSC-265 | SHOULD | PASS | Single Non-Author Reviewer Approval: At least one non-author reviewer must approve before merging. | Branch 'master' protected=True |
| CNSC-82 | SHOULD | PASS | Static Application Security Testing (SAST): Static application security testing (SAST) must be performed. | Found CI SAST workflow: .github/workflows/ci-build.yaml |
| CNSC-85 | SHOULD | PASS | Manifest and Workflow Scanning: Application, workflow, and deployment manifests must be scanned and validated in the CI pipeline. | Found CI manifest scanning workflow: .github/workflows/ci-build.yaml |
| CNSC-150 | SHOULD | PASS | Build Environment and Dependency Declaration: Build environments and dependencies must be validated before use. | Found: go.mod |
| CNSC-152 | SHOULD | PASS | Reproducible Builds Dependency Lock: Build artifacts must be reproducible; a dependency lock file must be present. | Found: go.sum |
| CNSC-153 | SHOULD | FAIL | External Requirements Hash Pinning: External requirements must be locked and verified with hash pinning. | Pattern '--require-hashes' not found in Makefile |
| CNSC-154 | SHOULD | PASS | Non-Determinism Elimination via Lock File: Sources of non-determinism must be eliminated; a lock file must be present. | Found: go.sum |
| CNSC-155 | SHOULD | PASS | Build Environment Recording: The build environment must be recorded. | Found: go.sum |
| CNSC-156 | SHOULD | FAIL | Automated Build Environment Creation: Creation of the build environment must be automated. | Target 'venv' not found in Makefile |
| CNSC-158 | SHOULD | PASS | Pipeline-as-Code Automation: Build and CI/CD steps must be automated through pipeline-as-code. | Found: Makefile |
| CNSC-159 | SHOULD | PASS | Standardized Single Pipeline Entry Point: Pipelines must be standardized across projects using a single entry point. | Target 'all' found in Makefile |
| CNSC-165 | SHOULD | FAIL | Secured Pipeline Output Storage: Pipeline output must be written to a separate secured storage location. | Missing: dist |
| CNSC-166 | SHOULD | PASS | Branch Protected Pipeline Modification: Pipeline modification must only be allowed through pipeline-as-code with branch protection. | Branch 'master' protected=True |
| CNSC-167 | SHOULD | PASS | Repository User Roles Definition: User roles must be defined for the repository. | Found: CODEOWNERS |
| CNSC-168 | SHOULD | PASS | Root-of-Trust Establishment Procedure: A root-of-trust establishment procedure must be documented. | Found: SECURITY.md |
| CNSC-173 | SHOULD | PASS | Third-Party Artifact Declaration & Verification: Third-party artifacts and open source libraries must be declared and verified. | Found: go.mod |
| CNSC-174 | SHOULD | FAIL | Supplier SBOM Requirement: An SBOM must be required from third-party suppliers. | Missing: sbom.json |
| CNSC-175 | SHOULD | PASS | Open Source Component Dependency Tracking: Dependencies between open source components must be tracked. | Found: go.mod |
| CNSC-177 | SHOULD | FAIL | Trusted Package Managers and Repositories: Only trusted package managers and repositories must be used. | Pattern 'go get' not found in Makefile |
| CNSC-178 | SHOULD | FAIL | Immutable Code SBOM Generation: An immutable SBOM of the code must be generated. | Target 'generate-sbom' not found in Makefile |
| CNSC-179 | SHOULD | PASS | Known Vulnerability Scanning: Software must be scanned for known vulnerabilities. | Found CI vulnerability/security scanning workflow: .github/workflows/auto-assign-pr-author.yaml |
| CNSC-180 | SHOULD | FAIL | License Compliance Scanning: Software must be scanned for license compliance. | Target 'license-check' not found in Makefile |
| CNSC-181 | SHOULD | FAIL | Software Composition Analysis (SCA): Software composition analysis must be run on ingested software. | Target 'sca' not found in Makefile |
| CNSC-182 | MUST | PASS | Cryptographic Commit and Tag Signing: All commits and tags must carry a valid GPG or SSH cryptographic signature, with exemption for automated release bot commits. | 10/10 recent commits carry a signature |
| CNSC-183 | SHOULD | PASS | Default Branch Full Attestation and Verification: Full attestation and verification must be enforced for the default branch. | Branch 'master' protected=True |
| CNSC-184 | MUST | FAIL | No Unencrypted Secrets in Repository: No unencrypted secrets must be committed to the repository. | Potential hardcoded secrets in: hack/start-redis-with-password.sh, resource_customizations/operator.victoriametrics.com/_/health_test.yaml, resource_customizations/operator.victoriametrics.com/_/testdata/degraded.yaml |
| CNSC-185 | SHOULD | PASS | Explicit Repository Write Access Definition: Individuals or teams with write access must be explicitly defined. | Found: CODEOWNERS |
| CNSC-186 | SHOULD | PASS | Automated Pipeline Security Scanning: Software security scanning and testing must be automated in the pipeline. | Found CI SAST workflow: .github/workflows/ci-build.yaml |
| CNSC-187 | SHOULD | PASS | Documented Contribution Policies: Contribution policies must be established and documented. | Found: CONTRIBUTING.md |
| CNSC-188 | SHOULD | PASS | Functional Role Alignment: Roles must be defined and aligned to functional responsibilities. | Found: CODEOWNERS |
| CNSC-189 | SHOULD | PASS | Four-Eyes Principle Branch Protection: An independent four-eyes principle must be enforced via branch protection. | Branch 'master' protected=True |
| CNSC-190 | MUST | PASS | Default Branch Protection Rules Enabled: Branch protection rules must be enabled on the default branch. | Branch 'master' protected=True |
| CNSC-191 | SHOULD | N/A | MFA Enforced for Repository Access: MFA must be enforced for accessing source code repositories. | Manual check - requires human review; not automated. |
| CNSC-192 | SHOULD | N/A | SSH Key Developer Access: SSH keys must be used to provide developer access to source code repositories. | Not assessable against a clone of the repository. |
| CNSC-193 | SHOULD | PASS | Documented Key Rotation Policy: A key rotation policy must be documented. | Found: SECURITY.md |
| CNSC-194 | SHOULD | PASS | Ephemeral Credentials for Automated Access: Short-lived or ephemeral credentials must be used for machine and service access. | Found: SECURITY.md |
| CNSC-121 | SHOULD | FAIL | Documented Code and Infrastructure Threat Model: A threat model for code and infrastructure must be documented. | Missing: THREAT_MODEL.md |
| CNSC-196 | SHOULD | PASS | Supply Chain Security Best Practices: Supply chain security best practices must be adhered to (SBOM, lock file, SCA). | Found: go.sum |
| CNSC-197 | SHOULD | PASS | Restricted Repository and Branch Access: Access to repository and branches must be restricted via branch protection and CODEOWNERS. | Branch 'master' protected=True |
| CNSC-198 | MUST | FAIL | Prohibition of Unencrypted Stored Credentials: Unencrypted credentials or secrets must never be stored in the repository. | Potential hardcoded secrets in: hack/start-redis-with-password.sh, resource_customizations/operator.victoriametrics.com/_/health_test.yaml, resource_customizations/operator.victoriametrics.com/_/testdata/degraded.yaml |
| CNSC-199 | MUST | PASS | Strong Identity Enforcement with Signed Commits: Strong identity must be enforced with GPG-signed commits, with exemption for automated release bot commits. | 10/10 recent commits carry a signature |
| CNSC-200 | SHOULD | PASS | Linear History and Force-Push Disallowed: Linear history must be enforced; force-push must be disallowed. | Branch 'master' protected=True |
| CNSC-201 | SHOULD | PASS | Enforced Branching and Code Review Policy: Branching policy must be enforced with main branch protection and code review. | Branch 'master' protected=True |
| CNSC-202 | SHOULD | N/A | Git and GitOps Tool Vulnerability Monitoring: Git and GitOps tools must be monitored for vulnerabilities and kept up to date. | Manual check - requires human review; not automated. |
| CNSC-203 | SHOULD | PASS | Regular SSH Key and PAT Rotation: SSH keys and Personal Access Tokens must be rotated regularly. | Found: SECURITY.md |
| CNSC-204 | SHOULD | N/A | Dedicated Technical Accounts for Automation: Dedicated non-user technical accounts must be used for automated access. | Manual check - requires human review; not automated. |
| CNSC-205 | SHOULD | N/A | Limited Permission Escalation Authority: Users who can escalate permissions must be limited to a pre-approved set. | Manual check - requires human review; not automated. |

Generated by `scripts/assess_project.py`. Machine-readable results are in the OSCAL assessment-results file for this project.
