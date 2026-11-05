# CNCF controls report: meshery/meshery

![cncf-controls: Assessment Incomplete](../badges/assessment-incomplete.svg)

- **Repository:** [https://github.com/meshery/meshery](https://github.com/meshery/meshery)
- **Commit assessed:** `52d205d`
- **Assessed at:** 2026-11-04 15:50 UTC
- **Level:** **Assessment Incomplete**. No controls had a decisive result
- **Totals:** 0 satisfied, 0 failed, 25 no result, 30 no check (of 55 controls in scope)

The level depends on the percentage of controls with a decisive result (PASS or FAIL) that passed. All controls count equally.

| Level | Conditions |
| --- | --- |
| **Gold** | ≥ 90% of controls with a decisive result satisfied |
| **Silver** | ≥ 75% satisfied |
| **Bronze** | ≥ 60% satisfied |
| **Baseline Pass Only** | ≥ 50% satisfied |
| **Fail** | < 50% satisfied |

| Result | Meaning | Counted? |
| --- | --- | --- |
| PASS | Check ran and passed | Yes |
| FAIL | Check ran and failed | Yes |
| NO-RESULT | Check ran but gave no decisive answer (e.g. Privateer "Needs Review") | No |
| NO-CHECK | Control is in scope but no Privateer check was found, native or plugin | No |

## Results by control

| Control | Result | Requirement | Evidence |
| --- | --- | --- | --- |
| CNSC-65 | NO-RESULT | Vulnerability and configuration scanning is integrated in the IDE or at the pull request | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-67 | NO-RESULT | Tests are built for business-critical code | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-68 | NO-CHECK | Tests are built for business-critical infrastructure | <span title="No Privateer check found, native or plugin. OSPS-QA-06.01 only checks that CI ran an automated test suite; it does not distinguish infrastructure tests.">No Privateer check found</span> |
| CNSC-69 | NO-RESULT | Test suites are able to be run locally | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-71 | NO-CHECK | Two non-author reviewers or approvers are required prior to merging | <span title="No Privateer check found, native or plugin. OSPS-QA-07.01 requires one non-author approval, not two. A pass would overstate this control.">No Privateer check found</span> |
| CNSC-72 | NO-CHECK | Code is clean and well commented | <span title="No Privateer check found, native or plugin. Code cleanliness and commenting are not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-73 | NO-CHECK | Full infrastructure tests are used | <span title="No Privateer check found, native or plugin. OSPS-QA-06.01 only checks that CI ran an automated test suite; it does not distinguish full infrastructure tests.">No Privateer check found</span> |
| CNSC-74 | NO-CHECK | Regression tests are used | <span title="No Privateer check found, native or plugin. OSPS-QA-06.01 only checks that CI ran an automated test suite; it does not identify regression tests.">No Privateer check found</span> |
| CNSC-75 | NO-CHECK | Test suites are updated against new and emerging threats and developed into security regression tests | <span title="No Privateer check found, native or plugin. OSPS-QA-06.03 covers a policy to update tests with changes, not security regression tests driven by emerging threats.">No Privateer check found</span> |
| CNSC-78 | NO-CHECK | Threat model results are used to determine ROI for test development | <span title="No Privateer check found, native or plugin. OSPS-SA-03.02 checks that a threat model exists (CNSC-121), not that it drives test priorities.">No Privateer check found</span> |
| CNSC-82 | NO-RESULT | Static application security testing (SAST) is performed | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-85 | NO-CHECK | Application manifests are scanned in CI pipeline | <span title="No Privateer check found, native or plugin. The Baseline analyses workflows for risks (OSPS-BR-01.x) but does not check that manifests are scanned in CI.">No Privateer check found</span> |
| CNSC-121 | NO-RESULT | Threat model code and infrastructure | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-150 | NO-CHECK | Environments and dependencies are validated before usage | <span title="No Privateer check found, native or plugin. Checksum and signature validation of dependencies is not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-152 | NO-CHECK | Build artefacts are validated through verifiably reproducible builds | <span title="No Privateer check found, native or plugin. Reproducible builds are not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-153 | NO-CHECK | External requirements from the build process are locked and verified | <span title="No Privateer check found, native or plugin. Hash pinning and locking of external requirements are not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-154 | NO-CHECK | Sources of non-determinism are found and eliminated | <span title="No Privateer check found, native or plugin. Build determinism is not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-155 | NO-RESULT | The build environment is recorded | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-156 | NO-CHECK | Creation of the build environment is automated | <span title="No Privateer check found, native or plugin. OSPS-DO-07.01 detects build documentation or automation but not automated creation of the build environment.">No Privateer check found</span> |
| CNSC-158 | NO-CHECK | Build and related CI/CD steps are automated through a pipeline delivered as code | <span title="No Privateer check found, native or plugin. The Baseline does not check that build and CI/CD steps are defined as code.">No Privateer check found</span> |
| CNSC-159 | NO-CHECK | Pipelines are standardized across projects | <span title="No Privateer check found, native or plugin. Pipeline standardization across projects is not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-165 | NO-CHECK | Output is written to a separate secured storage repo | <span title="No Privateer check found, native or plugin. Separate secured storage for pipeline output is not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-166 | NO-CHECK | Pipeline modification is only allowed through pipeline as code | <span title="No Privateer check found, native or plugin. Immutability of pipeline configuration is not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-167 | NO-RESULT | User roles are defined | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-168 | NO-CHECK | Established practices are followed for establishing a root of trust from an offline source | <span title="No Privateer check found, native or plugin. Root-of-trust establishment from an offline source is not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-173 | NO-CHECK | Third party artefacts and open source libraries are verified | <span title="No Privateer check found, native or plugin. Verification of third-party artifacts is not evaluated by the OSPS Baseline.">No Privateer check found</span> |
| CNSC-174 | NO-CHECK | SBOM is required from third party suppliers | <span title="No Privateer check found, native or plugin. OSPS-QA-02.02 covers the project&#x27;s own SBOM (CNSC-178), not SBOMs required from suppliers.">No Privateer check found</span> |
| CNSC-175 | NO-RESULT | Dependencies between open source components are tracked | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-177 | NO-RESULT | Trusted package managers and repositories are defined and prioritized | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-178 | NO-RESULT | An immutable SBOM of the code is generated | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-179 | NO-RESULT | Software is scanned for vulnerabilities | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-180 | NO-CHECK | Software is scanned for license implications | <span title="No Privateer check found, native or plugin. License scanning of dependencies is not evaluated by the OSPS Baseline. OSPS-LE-02.01 checks the project&#x27;s own license.">No Privateer check found</span> |
| CNSC-181 | NO-RESULT | Software composition analysis is run on ingested software | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-182 | NO-RESULT | Commits and tags are signed | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-183 | NO-RESULT | Full attestation and verification is enforced for protected branches | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-184 | NO-RESULT | Secrets are not committed to the source code repository unless encrypted | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-185 | NO-RESULT | Individuals or teams with write access to a repository are defined | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-186 | NO-CHECK | Software security scanning and testing is automated | <span title="No Privateer check found, native or plugin. OSPS-VM-06.02 covers SAST only. The control also asks for DAST, which is not evaluated.">No Privateer check found</span> |
| CNSC-187 | NO-RESULT | Contribution policies are established and adhered to | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-188 | NO-RESULT | Roles are defined and aligned to functional responsibilities | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-189 | NO-CHECK | An independent four-eyes principle is enforced | <span title="No Privateer check found, native or plugin. OSPS-QA-07.01 requires one non-author approval, not the two reviewers the control asks for. A pass would overstate this control.">No Privateer check found</span> |
| CNSC-190 | NO-RESULT | Branch protection rules are used | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-191 | NO-RESULT | MFA is enforced for accessing source code repositories | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-193 | NO-RESULT | A key rotation policy is maintained | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-195 | NO-CHECK | Secure configuration is implemented as the default state of the system | <span title="No Privateer check found, native or plugin. Secure defaults of the software are not evaluated by the repository-level OSPS Baseline.">No Privateer check found</span> |
| CNSC-196 | NO-CHECK | Supply chain security best practices are adhered to | <span title="No Privateer check found, native or plugin. This umbrella control has no single OSPS equivalent. Related practices are covered by CNSC-175, CNSC-177 and CNSC-178.">No Privateer check found</span> |
| CNSC-197 | NO-CHECK | Access to repository and branches is restricted | <span title="No Privateer check found, native or plugin. OSPS-AC-03.01 covers the primary branch only, not access to the repository. OSPS-AC-02.01 is enforced by GitHub for every project, so it would pass unconditionally.">No Privateer check found</span> |
| CNSC-198 | NO-RESULT | Unencrypted credentials or secrets are never stored in the Git repository and sensitive data is blocked from being pushed | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-199 | NO-RESULT | Strong identity is enforced with GPG Signed Commits for accountability and traceability | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-200 | NO-CHECK | Linear history is required and commit history is maintained by disallowing force pushes | <span title="No Privateer check found, native or plugin. Linear history and force-push protection are not evaluated by the OSPS Baseline. OSPS-AC-03.02 covers branch deletion only.">No Privateer check found</span> |
| CNSC-201 | NO-CHECK | Branching policy is enforced with main branch protection and code review required before merging | <span title="No Privateer check found, native or plugin. The control needs both branch protection (OSPS-AC-03.01) and required code review (OSPS-QA-07.01). Each control maps to one requirement, and neither covers both.">No Privateer check found</span> |
| CNSC-202 | NO-CHECK | Vulnerabilities are monitored and Git and GitOps tools are kept up to date | <span title="No Privateer check found, native or plugin. Monitoring and updating of Git and GitOps tooling is not observable from the repository.">No Privateer check found</span> |
| CNSC-205 | NO-RESULT | Users who can elevate permissions to remove security features are limited to prevent deletion of audit trails and silencing of alerts | Privateer unavailable: pvtr run timed out after 240s |
| CNSC-259 | NO-CHECK | Integrate vulnerability and configuration scanning in both the IDE and at the CI system during pull request | <span title="No Privateer check found, native or plugin. OSPS-VM-05.03 covers scanning in CI during pull requests. The control also asks for IDE scanning, so a pass would overstate it.">No Privateer check found</span> |
| CNSC-265 | NO-RESULT | Implement at least one other non-author reviewer/approver prior to merging | Privateer unavailable: pvtr run timed out after 240s |

Generated by `scripts/assess_project.py`. Machine-readable results are in the OSCAL assessment-results file for this project.
