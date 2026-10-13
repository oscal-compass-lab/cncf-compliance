# CNCF controls report: oscal-compass/compliance-trestle

- **Repository:** [https://github.com/oscal-compass/compliance-trestle](https://github.com/oscal-compass/compliance-trestle)
- **Commit assessed:** `ecccc7c`
- **Assessed at:** 2026-10-13 18:27 UTC
- **Level:** **Bronze**. 34/49 automated SHOULD controls satisfied (69%)
- **Totals:** 39 satisfied, 15 failed, 5 not automated (of 59 controls)

Levels: *Fail* if any MUST control is not satisfied; otherwise *Baseline Pass Only* at 50%, *Bronze* at 60%, *Silver* at 75%, *Gold* at 90% of automated SHOULD controls. MUST controls: CNSC-182, CNSC-184, CNSC-190, CNSC-198, CNSC-199. Manual and non-assessable controls (N/A) are excluded from the percentage and never count as passes.

## Results by control

| Control | Priority | Result | Requirement | Evidence |
| --- | --- | --- | --- | --- |
| CNSC-65 | SHOULD | PASS | Vulnerability and configuration scanning must be integrated at the pull-request or CI stage. | Found CI vulnerability/security scanning workflow: .github/workflows/act-test.yml |
| CNSC-67 | SHOULD | PASS | Tests must exist for business-critical code paths. | Found: tests |
| CNSC-68 | SHOULD | PASS | Tests must exist for business-critical infrastructure. | Found: tests |
| CNSC-69 | SHOULD | PASS | Test suites must be runnable locally without external dependencies. | Target 'test' found in Makefile |
| CNSC-71 | SHOULD | PASS | At least two non-author reviewers must approve before merging. | Branch 'develop' protected=True |
| CNSC-72 | SHOULD | PASS | Code must be clean and well commented. | Found: Makefile |
| CNSC-73 | SHOULD | PASS | Full infrastructure tests must be present. | Found: tests |
| CNSC-74 | SHOULD | PASS | Regression tests must be present. | Found: tests |
| CNSC-75 | SHOULD | PASS | Test suites must be updated against new and emerging threats. | Found: tests |
| CNSC-78 | SHOULD | FAIL | Threat model results must be used to determine test development priorities. | Missing: THREAT_MODEL.md |
| CNSC-195 | SHOULD | PASS | Secure configuration must be the default state of the system. | Found: SECURITY.md |
| CNSC-259 | SHOULD | PASS | Vulnerability and configuration scanning must be integrated in both IDE and CI pipeline. | Found CI vulnerability/security scanning workflow: .github/workflows/act-test.yml |
| CNSC-265 | SHOULD | PASS | At least one non-author reviewer must approve before merging. | Branch 'develop' protected=True |
| CNSC-82 | SHOULD | PASS | Static application security testing (SAST) must be performed. | Found CI SAST workflow: .github/workflows/codeql-analysis.yml |
| CNSC-85 | SHOULD | FAIL | Application manifests and OSCAL artifacts must be validated in the pipeline. | Target 'validate-catalog' not found in Makefile |
| CNSC-150 | SHOULD | PASS | Build environments and dependencies must be validated before use. | Found: pyproject.toml |
| CNSC-152 | SHOULD | FAIL | Build artifacts must be reproducible; a dependency lock file must be present. | Missing: requirements.lock |
| CNSC-153 | SHOULD | FAIL | External requirements must be locked and verified with hash pinning. | Pattern '--require-hashes' not found in Makefile |
| CNSC-154 | SHOULD | FAIL | Sources of non-determinism must be eliminated; a lock file must be present. | Missing: requirements.lock |
| CNSC-155 | SHOULD | FAIL | The build environment must be recorded. | Missing: requirements.lock |
| CNSC-156 | SHOULD | FAIL | Creation of the build environment must be automated. | Target 'venv' not found in Makefile |
| CNSC-158 | SHOULD | PASS | Build and CI/CD steps must be automated through pipeline-as-code. | Found: Makefile |
| CNSC-159 | SHOULD | FAIL | Pipelines must be standardized across projects using a single entry point. | Target 'all' not found in Makefile |
| CNSC-165 | SHOULD | FAIL | Pipeline output must be written to a separate secured storage location. | Missing: dist |
| CNSC-166 | SHOULD | PASS | Pipeline modification must only be allowed through pipeline-as-code with branch protection. | Branch 'develop' protected=True |
| CNSC-167 | SHOULD | PASS | User roles must be defined for the repository. | Found: .github/CODEOWNERS |
| CNSC-168 | SHOULD | PASS | A root-of-trust establishment procedure must be documented. | Found: SECURITY.md |
| CNSC-173 | SHOULD | PASS | Third-party artifacts and open source libraries must be declared and verified. | Found: pyproject.toml |
| CNSC-174 | SHOULD | FAIL | An SBOM must be required from third-party suppliers. | Missing: sbom.json |
| CNSC-175 | SHOULD | PASS | Dependencies between open source components must be tracked. | Found: pyproject.toml |
| CNSC-177 | SHOULD | PASS | Only trusted package managers and repositories must be used. | Pattern 'pip install' found in Makefile |
| CNSC-178 | SHOULD | FAIL | An immutable SBOM of the code must be generated. | Target 'generate-sbom' not found in Makefile |
| CNSC-179 | SHOULD | PASS | Software must be scanned for known vulnerabilities. | Found CI vulnerability/security scanning workflow: .github/workflows/act-test.yml |
| CNSC-180 | SHOULD | FAIL | Software must be scanned for license compliance. | Target 'license-check' not found in Makefile |
| CNSC-181 | SHOULD | FAIL | Software composition analysis must be run on ingested software. | Target 'sca' not found in Makefile |
| CNSC-182 | MUST | PASS | All commits and tags must carry a valid GPG or SSH cryptographic signature, with exemption for automated release bot commits. | 8/8 recent commits carry a signature (2 release bot commits excused) |
| CNSC-183 | SHOULD | PASS | Full attestation and verification must be enforced for the default branch. | Branch 'develop' protected=True |
| CNSC-184 | MUST | PASS | No unencrypted secrets must be committed to the repository. | No hardcoded secrets detected |
| CNSC-185 | SHOULD | PASS | Individuals or teams with write access must be explicitly defined. | Found: .github/CODEOWNERS |
| CNSC-186 | SHOULD | PASS | Software security scanning and testing must be automated in the pipeline. | Found CI SAST workflow: .github/workflows/codeql-analysis.yml |
| CNSC-187 | SHOULD | PASS | Contribution policies must be established and documented. | Found: CONTRIBUTING.md |
| CNSC-188 | SHOULD | PASS | Roles must be defined and aligned to functional responsibilities. | Found: .github/CODEOWNERS |
| CNSC-189 | SHOULD | PASS | An independent four-eyes principle must be enforced via branch protection. | Branch 'develop' protected=True |
| CNSC-190 | MUST | PASS | Branch protection rules must be enabled on the default branch. | Branch 'develop' protected=True |
| CNSC-191 | SHOULD | N/A | MFA must be enforced for accessing source code repositories. | Manual check - requires human review; not automated. |
| CNSC-192 | SHOULD | N/A | SSH keys must be used to provide developer access to source code repositories. | Not assessable against a clone of the repository. |
| CNSC-193 | SHOULD | PASS | A key rotation policy must be documented. | Found: SECURITY.md |
| CNSC-194 | SHOULD | PASS | Short-lived or ephemeral credentials must be used for machine and service access. | Found: SECURITY.md |
| CNSC-121 | SHOULD | FAIL | A threat model for code and infrastructure must be documented. | Missing: THREAT_MODEL.md |
| CNSC-196 | SHOULD | FAIL | Supply chain security best practices must be adhered to (SBOM, lock file, SCA). | Missing: requirements.lock |
| CNSC-197 | SHOULD | PASS | Access to repository and branches must be restricted via branch protection and CODEOWNERS. | Branch 'develop' protected=True |
| CNSC-198 | MUST | PASS | Unencrypted credentials or secrets must never be stored in the repository. | No hardcoded secrets detected |
| CNSC-199 | MUST | PASS | Strong identity must be enforced with GPG-signed commits, with exemption for automated release bot commits. | 8/8 recent commits carry a signature (2 release bot commits excused) |
| CNSC-200 | SHOULD | PASS | Linear history must be enforced; force-push must be disallowed. | Branch 'develop' protected=True |
| CNSC-201 | SHOULD | PASS | Branching policy must be enforced with main branch protection and code review. | Branch 'develop' protected=True |
| CNSC-202 | SHOULD | N/A | Git and GitOps tools must be monitored for vulnerabilities and kept up to date. | Manual check - requires human review; not automated. |
| CNSC-203 | SHOULD | PASS | SSH keys and Personal Access Tokens must be rotated regularly. | Found: SECURITY.md |
| CNSC-204 | SHOULD | N/A | Dedicated non-user technical accounts must be used for automated access. | Manual check - requires human review; not automated. |
| CNSC-205 | SHOULD | N/A | Users who can escalate permissions must be limited to a pre-approved set. | Manual check - requires human review; not automated. |

Generated by `scripts/assess_project.py`. Machine-readable results are in the OSCAL assessment-results file for this project.
