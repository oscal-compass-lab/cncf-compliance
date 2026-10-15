# CNCF controls report: oscal-compass/compliance-trestle

![cncf-controls: Fail](../badges/fail.svg)

- **Repository:** [https://github.com/oscal-compass/compliance-trestle](https://github.com/oscal-compass/compliance-trestle)
- **Commit assessed:** `a92c595`
- **Assessed at:** 2026-10-15 18:44 UTC
- **Level:** **Fail**. MUST controls not satisfied: CNSC-198, CNSC-199
- **Totals:** 13 satisfied, 4 failed, 5 no result, 33 no check, 159 skipped (of 214 controls)

Levels: *Fail* if any MUST control fails; MUST controls without a decisive result do not fail a project but are listed in the level detail. Otherwise *Baseline Pass Only* at 50%, *Bronze* at 60%, *Silver* at 75%, *Gold* at 90% of automated SHOULD controls. MUST controls: CNSC-182, CNSC-184, CNSC-190, CNSC-198, CNSC-199. Result labels: PASS and FAIL are decisive. NO-RESULT means a check ran but gave no decisive answer (for example Privateer "Needs Review"). NO-CHECK means the control is in scope but has no unique check. SKIP means the control is out of scope by design. NO-RESULT, NO-CHECK and SKIP controls are excluded from the percentage and never count as passes.

## Results by control

| Control | Priority | Result | Requirement | Evidence |
| --- | --- | --- | --- | --- |
| CNSC-1 | SHOULD | SKIP | Secrets are injected at runtime | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-2 | SHOULD | SKIP | Applications and workloads are explicitly authorized to communicate with each other using mutual authentication | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-3 | SHOULD | SKIP | Keys are rotated frequently | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-4 | SHOULD | SKIP | Key lifespan is short | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-5 | SHOULD | SKIP | Credentials and keys protecting sensitive workloads (health/finance/etc) are generated and managed independent of a cloud service provider | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-6 | SHOULD | SKIP | Authentication and authorization are determined independently | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-7 | SHOULD | SKIP | Authentication and authorization are enforced independently | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-8 | SHOULD | SKIP | Access control and file permissions are updated in real-time | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-9 | SHOULD | SKIP | Authorization for workloads is granted based on attributes and roles/permissions previously assigned | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-10 | SHOULD | SKIP | ABAC and RBAC are used | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-11 | SHOULD | SKIP | End user identity is capable of being accepted, consumed, and forwarded on for contextual or dynamic authorization | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-12 | SHOULD | SKIP | All cluster and workloads operators are authenticated | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-13 | SHOULD | SKIP | Cluster and workloads operate actions are evaluated against access control policies governing context, purpose, and output | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-14 | SHOULD | SKIP | Identity federation uses multi-factor authentication | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-15 | SHOULD | SKIP | HSMs are used to physically protect cryptographic secrets with an encryption key residing in the HSM | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-16 | SHOULD | SKIP | Secrets should have a short expiration period or time to live | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-17 | SHOULD | SKIP | Time to live and expiration period on secrets is verified to prevent reuse | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-18 | SHOULD | SKIP | Secrets management systems are highly available | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-19 | SHOULD | SKIP | Long-lived secrets adhere to periodic rotation and revocation | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-20 | SHOULD | SKIP | Secrets are distributed through secured communication channels protected commensurate with the level of access or data they are protecting | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-21 | SHOULD | SKIP | Secrets injected at runtime are masked or dropped from logs, audit, or system dumps | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-22 | SHOULD | SKIP | Bootstrapping is employed to verify correct physical and logical location of compute | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-23 | SHOULD | SKIP | Disparate data sensitive workloads are not run on the same host OS kernel | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-24 | SHOULD | SKIP | Monitor and detect any changes to the initial configurations made in runtime | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-25 | SHOULD | SKIP | API auditing is enabled with a filter for a specific set of API Groups or verbs | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-26 | SHOULD | SKIP | Container specific operating systems are in use | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-27 | SHOULD | SKIP | The hardware root of trust is based in a Trusted Platform Module (TPM) or virtual TPM (vTPM) | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-28 | SHOULD | SKIP | Minimize administrative access to the control plane | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-29 | SHOULD | SKIP | Object level and resource requests and limits are controlled through cgroups | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-30 | SHOULD | SKIP | Systems processing alerts are periodically tuned for false positives | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-31 | SHOULD | SKIP | All orchestrator control plane components are configured to communicate via mutual authentication and certificate validation with a periodically rotated certificate | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-32 | SHOULD | SKIP | Only sanctioned capabilities and system calls (e.g. seccomp filters), are allowed to execute or be invoked in a container by the host operating system | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-33 | SHOULD | SKIP | Changes to critical mount points and files are prevented, monitored, and alerted | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-34 | SHOULD | SKIP | Runtime configuration control prevents changes to binaries, certificates, and remote access configurations | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-35 | SHOULD | SKIP | Runtime configuration prevents ingress and egress network access for containers to only what is required to operate | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-36 | SHOULD | SKIP | Policies are defined that restrict communications to only occur between sanctioned microservice pairs | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-37 | SHOULD | SKIP | Use a policy agent to control and enforce authorized, signed container images | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-38 | SHOULD | SKIP | Use a policy agent to control provenance assurance for operational workloads | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-39 | SHOULD | SKIP | Use a service mesh that eliminates implicit trust through data-in-motion encryption (data in transit) | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-40 | SHOULD | SKIP | Use components that detect, track, aggregate and report system calls and network traffic from a container | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-41 | SHOULD | SKIP | Workloads should be dynamically scanned to detect malicious or insidious behavior for which no known occurrence yet exists | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-42 | SHOULD | SKIP | Environments are continuously scanned to detect new vulnerabilities in workloads | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-43 | SHOULD | SKIP | Actionable audit events are generated that correlate/contextualize data from logs into "information" that can drive decision trees/incident response | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-44 | SHOULD | SKIP | Segregation of duties and the principle of least privilege is enforced | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-45 | SHOULD | SKIP | Non-compliant violations are detected based on a pre-configured set of rules defined by the organization's policies | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-46 | SHOULD | SKIP | Native secret stores encrypt with keys from an external Key Management Store (KMS) | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-47 | SHOULD | SKIP | Native secret stores are not configured for base64 encoding or stored in clear-text in the key-value store by default | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-48 | SHOULD | SKIP | Network traffic to malicious domains is detected and denied | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-49 | SHOULD | SKIP | Use encrypted containers for sensitive sources, methods, and data | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-50 | SHOULD | SKIP | Use SBOMs to identify current deployments of vulnerable libraries, dependencies, and packages | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-51 | SHOULD | SKIP | Processes must execute only functions explicitly defined in an allow list | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-52 | SHOULD | SKIP | Functions are not be allowed to make changes to critical file system mount points | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-53 | SHOULD | SKIP | Function access is only permitted to sanctioned services | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-54 | SHOULD | SKIP | Egress network connection is monitored to detect and prevent access to C&C (command and control) and other malicious network domains | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-55 | SHOULD | SKIP | Ingress network inspection is employed detect and remove malicious payloads and commands | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-56 | SHOULD | SKIP | Serverless functions are run in tenant-based resource or performance isolation for similar data classifications | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-57 | SHOULD | SKIP | Trust confirmation verifies the image has a valid signature from an authorized source | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-58 | SHOULD | SKIP | Image runtime policies are enforced prior to deployment | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-59 | SHOULD | SKIP | Image integrity and signature are verified prior to deployment | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-60 | SHOULD | SKIP | Applications provide logs regarding authentication, authorization, actions, and failures | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-61 | SHOULD | SKIP | Forensics capabilities are integrated into an incident response plan and procedures | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-62 | SHOULD | SKIP | AI, ML, or statistical modeling are used for behavioural and heuristic environment analysis to detect unwanted activities | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-63 | SHOULD | SKIP | A dedicated production environment is established | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-64 | SHOULD | SKIP | Dynamic deployments are leveraged for safer releases | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-65 | SHOULD | NO-RESULT | Vulnerability and configuration scanning is integrated in the IDE or at the pull request | Privateer github-repo 0.32.3 OSPS-VM-05.03: Needs Review (Low confidence). Workflow, documentation, or Security Insights inspection was incomplete, so end-to-end SCA enforcement could not be determined |
| CNSC-66 | SHOULD | SKIP | Dedicated development, testing, and production environments are established | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-67 | SHOULD | PASS | Tests are built for business-critical code | Privateer github-repo 0.32.3 OSPS-QA-06.01: Passed. 18 status checks were run |
| CNSC-68 | SHOULD | NO-CHECK | Tests are built for business-critical infrastructure | No unique Privateer check. The only OSPS test requirement (OSPS-QA-06.01) is used by CNSC-67 and does not distinguish infrastructure tests. |
| CNSC-69 | SHOULD | NO-RESULT | Test suites are able to be run locally | Privateer github-repo 0.32.3 OSPS-QA-06.02: Needs Review (Low confidence). Review project documentation to ensure it explains when and how tests are run |
| CNSC-70 | SHOULD | SKIP | Test suites are available to run in a shared environment | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-71 | SHOULD | NO-CHECK | Two non-author reviewers or approvers are required prior to merging | No unique Privateer check. OSPS-QA-07.01 requires one approval, not two, and is used by CNSC-265. A pass would overstate this control. |
| CNSC-72 | SHOULD | NO-CHECK | Code is clean and well commented | No unique Privateer check. Code cleanliness and commenting are not evaluated by the OSPS Baseline. |
| CNSC-73 | SHOULD | NO-CHECK | Full infrastructure tests are used | No unique Privateer check. The only OSPS test requirement (OSPS-QA-06.01) is used by CNSC-67 and does not distinguish full infrastructure tests. |
| CNSC-74 | SHOULD | NO-CHECK | Regression tests are used | No unique Privateer check. The only OSPS test requirement (OSPS-QA-06.01) is used by CNSC-67 and does not identify regression tests. |
| CNSC-75 | SHOULD | NO-CHECK | Test suites are updated against new and emerging threats and developed into security regression tests | No unique Privateer check. OSPS-QA-06.03 covers a policy to update tests with changes, not security regression tests driven by emerging threats. |
| CNSC-76 | SHOULD | SKIP | A dedicated testing environment is established | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-77 | SHOULD | SKIP | Continuous integration server is isolated | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-78 | SHOULD | NO-CHECK | Threat model results are used to determine ROI for test development | No unique Privateer check. OSPS-SA-03.02 checks that a threat model exists (CNSC-121), not that it drives test priorities. |
| CNSC-79 | SHOULD | SKIP | Trust is verified | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-80 | SHOULD | SKIP | Artifacts ready for deployment are managed in a staging or pre-prod registry | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-81 | SHOULD | SKIP | Container images are hardened following best practices | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-82 | SHOULD | NO-RESULT | Static application security testing (SAST) is performed | Privateer github-repo 0.32.3 OSPS-VM-06.02: Needs Review (Medium confidence). A SAST tool runs in CI and required status checks are configured on the default branch, but none could be matched to the SAST tool; confirm the SAST check must pass before merging |
| CNSC-83 | SHOULD | SKIP | Test suites follow the test pyramid | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-84 | SHOULD | SKIP | Artifacts undergoing active development are held in a private registry | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-85 | SHOULD | NO-CHECK | Application manifests are scanned in CI pipeline | No unique Privateer check. The Baseline analyses workflows for risks (OSPS-BR-01.x) but does not check that manifests are scanned in CI. |
| CNSC-86 | SHOULD | SKIP | CI servers for sensitive workloads are isolated from other workloads | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-87 | SHOULD | SKIP | Builds requiring elevated privileges run on dedicated servers | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-88 | SHOULD | SKIP | Build policies are enforced on the CI pipeline | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-89 | SHOULD | SKIP | Pipeline metadata is signed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-90 | SHOULD | SKIP | Build stages are verified prior to the next stage executing | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-91 | SHOULD | SKIP | Images are scanned within the CI pipeline | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-92 | SHOULD | SKIP | Vulnerability scans are coupled with pipeline compliance rules | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-93 | SHOULD | SKIP | Dynamic application security testing (DAST) is performed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-94 | SHOULD | SKIP | Application instrumentation is employed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-95 | SHOULD | SKIP | Automated test results map back to requirements | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-96 | SHOULD | SKIP | Infrastructure security tests are employed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-97 | SHOULD | SKIP | Tests to verify security health are executed at build and deploy time | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-98 | SHOULD | SKIP | Infrastructure as Code is subject to the same pipeline policy controls as application code | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-99 | SHOULD | SKIP | Security testing is automated | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-100 | SHOULD | SKIP | Registries require mutually authenticated TLS for all registry connections | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-101 | SHOULD | SKIP | Image and metadata are signed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-102 | SHOULD | SKIP | Configuration is signed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-103 | SHOULD | SKIP | Package is signed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-104 | SHOULD | SKIP | Integrity of images is validated | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-105 | SHOULD | SKIP | Images are scanned for vulnerabilities and malware | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-106 | SHOULD | SKIP | Image signing key revocation is enabled in the event of compromise | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-107 | SHOULD | SKIP | Security updates are prioritized | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-108 | SHOULD | SKIP | HSMs or credential managers are used for protecting credentials | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-109 | SHOULD | SKIP | Container image scanning findings are acted upon | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-110 | SHOULD | SKIP | Organizational compliance rules are enforced | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-111 | SHOULD | SKIP | Incremental hardening of the infrastructure is employed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-112 | SHOULD | SKIP | Pulls from public registries are controlled and only from authorized engineers or internal registries | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-113 | SHOULD | SKIP | Image encryption is coupled with key management attestation and/or authorization and credential distribution | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-114 | SHOULD | SKIP | At-risk applications are prioritized for remediation by exploit maturity and vulnerable path presence in addition to the CVSS score | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-115 | SHOULD | SKIP | Network policies enforce east-west network communication within the container deployment is limited to only that which is authorized for access | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-116 | SHOULD | SKIP | Incident response considers cloud native workloads | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-117 | SHOULD | SKIP | Incident response accounts for appropriate evidence handling and collection of cloud native workloads | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-118 | SHOULD | SKIP | Rootless builds are employed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-119 | SHOULD | SKIP | Cgroups and system groups are used to isolate workloads and deployments | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-120 | SHOULD | SKIP | MAC implementations are employed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-121 | SHOULD | FAIL | Threat model code and infrastructure | Privateer github-repo 0.32.3 OSPS-SA-03.02: Failed (Medium confidence). Project has published releases but no threat modeling or attack surface analysis was found in Security Insights |
| CNSC-122 | SHOULD | SKIP | Entities are able to independently authenticate other identities | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-123 | SHOULD | SKIP | Each entity can create proof of who the identity is | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-124 | SHOULD | SKIP | Orchestrator is running on a trusted OS, BIOS, etc | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-125 | SHOULD | SKIP | Orchestrator verifies the claims of a container | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-126 | SHOULD | SKIP | Orchestrator network policies are used in conjunction with a service mesh | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-127 | SHOULD | SKIP | Storage control plane management interface requires mutual authentication and TLS for connections | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-128 | SHOULD | SKIP | Data availability is achieved through parity or mirroring, erasure coding or replicas | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-129 | SHOULD | SKIP | Hashing and checksums are added to blocks, objects or files | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-130 | SHOULD | SKIP | Data backup storage locations employ like access controls and security policies to that of the data storage source | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-131 | SHOULD | SKIP | Secure erasure adhering to OPAL standards is employed for returned or non-functional devices | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-132 | SHOULD | SKIP | Encryption at rest considers data path, size, and frequency of access when determining additional security protections and cryptographic algorithms to employ | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-133 | SHOULD | SKIP | Caching is considered for determining encryption requirements in architectures | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-134 | SHOULD | SKIP | Namespaces have defined trust boundaries to cordon access to volumes | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-135 | SHOULD | SKIP | Security policies are used to prevent containers from accessing volume mounts on worker nodes | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-136 | SHOULD | SKIP | Security policies are used enforce authorized worker node access to volumes | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-137 | SHOULD | SKIP | Volume UID and GID are inaccessible to containers | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-138 | SHOULD | SKIP | Artifact registry supports OCI artifacts | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-139 | SHOULD | SKIP | Artifact registry supports signed artifacts | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-140 | SHOULD | SKIP | Artifact registry verifies artifacts against organizational policies | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-141 | SHOULD | SKIP | Every step in the build process is signed and attested for process integrity | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-142 | SHOULD | SKIP | Every step in the build process verifies previously generated signatures | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-143 | SHOULD | SKIP | A framework is used to manage signing of artefacts | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-144 | SHOULD | SKIP | A store is used to manage attestations | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-145 | SHOULD | SKIP | Artefacts any given party is authorized to certify are limited | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-146 | SHOULD | SKIP | Rotation and revocation of private keys is supported | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-147 | SHOULD | SKIP | A container registry that supports OCI image-spec images is used | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-148 | SHOULD | SKIP | Artefacts are encrypted before distribution and only authorized platforms have decryption capabilities | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-149 | SHOULD | SKIP | Policy adherence is cryptographically guaranteed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-150 | SHOULD | NO-CHECK | Environments and dependencies are validated before usage | No unique Privateer check. Checksum and signature validation of dependencies is not evaluated by the OSPS Baseline. |
| CNSC-151 | SHOULD | SKIP | Runtime security of build workers is validated | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-152 | SHOULD | NO-CHECK | Build artefacts are validated through verifiably reproducible builds | No unique Privateer check. Reproducible builds are not evaluated by the OSPS Baseline. |
| CNSC-153 | SHOULD | NO-CHECK | External requirements from the build process are locked and verified | No unique Privateer check. Hash pinning and locking of external requirements are not evaluated by the OSPS Baseline. |
| CNSC-154 | SHOULD | NO-CHECK | Sources of non-determinism are found and eliminated | No unique Privateer check. Build determinism is not evaluated by the OSPS Baseline. |
| CNSC-155 | SHOULD | PASS | The build environment is recorded | Privateer github-repo 0.32.3 OSPS-DO-07.01: Passed. Build-from-source instructions were found (build automation file or a build section in the README or CONTRIBUTING guide) |
| CNSC-156 | SHOULD | NO-CHECK | Creation of the build environment is automated | No unique Privateer check. OSPS-DO-07.01 (used by CNSC-155) detects build documentation or automation but not automated creation of the build environment. |
| CNSC-157 | SHOULD | SKIP | Builds are distributed across different infrastructure | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-158 | SHOULD | NO-CHECK | Build and related CI/CD steps are automated through a pipeline delivered as code | No unique Privateer check. The Baseline does not check that build and CI/CD steps are defined as code. |
| CNSC-159 | SHOULD | NO-CHECK | Pipelines are standardized across projects | No unique Privateer check. Pipeline standardization across projects is not evaluated by the OSPS Baseline. |
| CNSC-160 | SHOULD | SKIP | A secured orchestration platform is provisioned to host the software factory | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-161 | SHOULD | SKIP | Build workers are single use | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-162 | SHOULD | SKIP | Software factory has minimal network connectivity | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-163 | SHOULD | SKIP | Duties of each build worker are segregated | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-164 | SHOULD | SKIP | Build worker environment and commands are passed in | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-165 | SHOULD | NO-CHECK | Output is written to a separate secured storage repo | No unique Privateer check. Separate secured storage for pipeline output is not evaluated by the OSPS Baseline. |
| CNSC-166 | SHOULD | NO-CHECK | Pipeline modification is only allowed through pipeline as code | No unique Privateer check. Immutability of pipeline configuration is not evaluated by the OSPS Baseline. |
| CNSC-167 | SHOULD | NO-CHECK | User roles are defined | No unique Privateer check. The only related OSPS requirement (OSPS-GV-01.02) is used by CNSC-188, which states it more precisely. |
| CNSC-168 | SHOULD | NO-CHECK | Established practices are followed for establishing a root of trust from an offline source | No unique Privateer check. Root-of-trust establishment from an offline source is not evaluated by the OSPS Baseline. |
| CNSC-169 | SHOULD | SKIP | Short-lived workload certificates are used | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-170 | SHOULD | SKIP | Clients can perform verification of artefacts and associated metadata | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-171 | SHOULD | SKIP | Clients can verify the freshness of files | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-172 | SHOULD | SKIP | A framework is used for managing software updates | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-173 | SHOULD | NO-CHECK | Third party artefacts and open source libraries are verified | No unique Privateer check. Verification of third-party artifacts is not evaluated by the OSPS Baseline. |
| CNSC-174 | SHOULD | NO-CHECK | SBOM is required from third party suppliers | No unique Privateer check. OSPS-QA-02.02 covers the project's own SBOM (CNSC-178), not SBOMs required from suppliers. |
| CNSC-175 | SHOULD | PASS | Dependencies between open source components are tracked | Privateer github-repo 0.32.3 OSPS-QA-02.01: Passed (High confidence). Found 12 dependency manifests from GitHub API |
| CNSC-176 | SHOULD | SKIP | Libraries are built based upon source code | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-177 | SHOULD | PASS | Trusted package managers and repositories are defined and prioritized | Privateer github-repo 0.32.3 OSPS-BR-05.01: Passed. Found 12 dependency manifest(s) in the GitHub dependency graph, indicating dependencies are ingested via standardized tooling |
| CNSC-178 | SHOULD | NO-RESULT | An immutable SBOM of the code is generated | Privateer github-repo 0.32.3 OSPS-QA-02.02: Needs Review (Low confidence). No SBOM was found among the GitHub assets for release(s) publishing compiled or archived software: v5.2.0, v5.1.0, v5.0.0, v3.12.4, v4.2.0, v4.1.0, v3.12.3, v4.0.3, v4.0.2, v4.0.1, v4.0.0, v3.12.0, v3.11.0, v3.10.4, v3.10.2, v3.9.3, v3.9.2, v3.9.1, v3.9.0, v3.8.1, v3.8.0, v3.7.0, v3.6.0, v3.5.0, v3.4.0, v3.3.0, v3.2.0, v3.1.0, v3.0.1, v2.6.1, v2.6.0, v2.5.1, v2.5.0, v2.4.0, v2.3.1, v2.3.0, v2.2.1, v2.2.0, v2.1.1, v2.1.0, v2.0.0, v1.2.0, v1.1.0, v1.0.2, v1.0.1, v1.0.0, v0.37.0, v1.0.0-rc.0, v0.36.0, v0.35.0, v0.34.0, v0.33.0, v0.32.1, v0.32.0, v0.31.0, v0.30.0, v0.29.0, v0.28.1, v0.28.0, v0.27.2, v0.27.1, v0.27.0, v0.26.0, v0.25.1, v0.25.0, v0.24.0, v0.23.0, v0.22.1, v0.22.0, v0.21.0, v0.20.0, v0.19.0, v0.18.1, v0.18.0, v0.17.0, v0.16.0, v0.15.1, v0.15.0, v0.14.4, v0.14.3, v0.14.2, v0.14.1, v0.14.0, v0.13.1, v0.13.0, v0.12.0, v0.11.0, v0.10.0, v0.9.0, v0.8.1, v0.8.0, v0.7.2, v0.7.1, v0.7.0, v0.6.2, v0.6.1, v0.6.0, v0.5.0, v0.4.0, v0.3.0, v0.2.2, v0.2.1, v0.2.0, v0.1.1, v0.1.0, v0.0.3, v0.0.2. Review publisher evidence because an SBOM may be retained privately or distributed through another channel |
| CNSC-179 | SHOULD | NO-CHECK | Software is scanned for vulnerabilities | No unique Privateer check. The only OSPS requirement for automated vulnerability evaluation (OSPS-VM-05.03) is used by CNSC-65. |
| CNSC-180 | SHOULD | NO-CHECK | Software is scanned for license implications | No unique Privateer check. License scanning of dependencies is not evaluated by the OSPS Baseline. OSPS-LE-02.01 checks the project's own license. |
| CNSC-181 | SHOULD | NO-CHECK | Software composition analysis is run on ingested software | No unique Privateer check. The only OSPS requirement for automated dependency evaluation (OSPS-VM-05.03) is used by CNSC-65. |
| CNSC-182 | MUST | PASS | Commits and tags are signed | Privateer cncf-controls 0.0.0 CNSC-182.01: Passed (High confidence). 18 of 20 recent commits are signed (2 unsigned by release automation excused); 0 of 10 recent tags are signed (10 unsigned by release automation excused) |
| CNSC-183 | SHOULD | FAIL | Full attestation and verification is enforced for protected branches | Privateer github-repo 0.32.3 OSPS-QA-03.01: Failed. Some executed status checks are not mandatory but all should be: Analyze (python), Atheris fuzz – OSCAL Catalog loader, set-versions, test-with-codegen (ubuntu-latest, 3.14), CodeQL (NOTE: Not continuing to evaluate branch protection: combining requirements in rulesets and branch protection is not recommended) |
| CNSC-184 | MUST | PASS | Secrets are not committed to the source code repository unless encrypted | Privateer cncf-controls 0.0.0 CNSC-184.01: Passed (Medium confidence). Scanned 1515 files in the default branch with gitleaks; no secrets found (56 skipped as binary or too large) |
| CNSC-185 | SHOULD | PASS | Individuals or teams with write access to a repository are defined | Privateer github-repo 0.32.3 OSPS-GV-01.01: Passed (High confidence). Project admins were specified in Security Insights data |
| CNSC-186 | SHOULD | NO-CHECK | Software security scanning and testing is automated | No unique Privateer check. The only OSPS requirement for automated security scanning (OSPS-VM-06.02) is used by CNSC-82. DAST is not evaluated. |
| CNSC-187 | SHOULD | PASS | Contribution policies are established and adhered to | Privateer github-repo 0.32.3 OSPS-GV-03.01: Passed (High confidence). Contributing guide specified in Security Insights data (Bonus: code of conduct location also specified) |
| CNSC-188 | SHOULD | PASS | Roles are defined and aligned to functional responsibilities | Privateer github-repo 0.32.3 OSPS-GV-01.02: Passed (Medium confidence). Governance/maintainers documentation found via GitHub (MAINTAINERS.md) |
| CNSC-189 | SHOULD | NO-CHECK | An independent four-eyes principle is enforced | No unique Privateer check. OSPS-QA-07.01 is used by CNSC-265. It does not test that the author differs from the approver or that there are two reviewers. |
| CNSC-190 | MUST | PASS | Branch protection rules are used | Privateer cncf-controls 0.0.0 CNSC-190.01: Passed (High confidence). Branch rule requires approving reviews |
| CNSC-191 | SHOULD | PASS | MFA is enforced for accessing source code repositories | Privateer github-repo 0.32.3 OSPS-AC-01.01: Passed. This control is enforced by GitHub for all projects |
| CNSC-192 | SHOULD | SKIP | SSH keys are used to provide developers access to source code repositories | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-193 | SHOULD | NO-RESULT | A key rotation policy is maintained | Privateer github-repo 0.32.3 OSPS-BR-07.02: Needs Review (Low confidence). No documented policy for managing secrets and credentials was found in the repository's security policy; manual review is required to confirm one exists elsewhere |
| CNSC-194 | SHOULD | SKIP | Short-lived or ephemeral credentials are used for machine and service access | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-195 | SHOULD | NO-CHECK | Secure configuration is implemented as the default state of the system | No unique Privateer check. Secure defaults of the software are not evaluated by the repository-level OSPS Baseline. |
| CNSC-196 | SHOULD | NO-CHECK | Supply chain security best practices are adhered to | No unique Privateer check. This umbrella control has no single OSPS equivalent. Related practices are covered by CNSC-175, CNSC-177 and CNSC-178. |
| CNSC-197 | SHOULD | NO-CHECK | Access to repository and branches is restricted | No unique Privateer check. The OSPS requirement for restricting branch access (OSPS-AC-03.01) is used by CNSC-190. OSPS-AC-02.01 is enforced by GitHub for every project, so it would pass unconditionally. |
| CNSC-198 | MUST | FAIL | Unencrypted credentials or secrets are never stored in the Git repository and sensitive data is blocked from being pushed | Privateer cncf-controls 0.0.0 CNSC-198.01: Failed (Medium confidence). GitHub reports secret scanning and push protection are both disabled |
| CNSC-199 | MUST | FAIL | Strong identity is enforced with GPG Signed Commits for accountability and traceability | Privateer cncf-controls 0.0.0 CNSC-199.01: Failed (High confidence). 18 of 20 recent commits are signed (2 unsigned by release automation excused); neither branch protection nor a ruleset requires signed commits |
| CNSC-200 | SHOULD | NO-CHECK | Linear history is required and commit history is maintained by disallowing force pushes | No unique Privateer check. Linear history and force-push protection are not evaluated by the OSPS Baseline. OSPS-AC-03.02 covers branch deletion only. |
| CNSC-201 | SHOULD | NO-CHECK | Branching policy is enforced with main branch protection and code review required before merging | No unique Privateer check. The related OSPS requirements (OSPS-AC-03.01, OSPS-QA-07.01) are used by CNSC-190 and CNSC-265. |
| CNSC-202 | SHOULD | NO-CHECK | Vulnerabilities are monitored and Git and GitOps tools are kept up to date | No unique Privateer check. Monitoring and updating of Git and GitOps tooling is not observable from the repository. |
| CNSC-203 | SHOULD | SKIP | SSH keys and Personal Access Tokens are rotated and unauthorized access to Git repositories is blocked | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-204 | SHOULD | SKIP | Dedicated non-user technical accounts are used for access with frequently rotated short-lived credentials | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-205 | SHOULD | PASS | Users who can elevate permissions to remove security features are limited to prevent deletion of audit trails and silencing of alerts | Privateer github-repo 0.32.3 OSPS-GV-04.01: Passed (Medium confidence). Documentation requires code collaborators to be reviewed before receiving escalated permissions (docs/contributing/github_actions_setup.md) |
| CNSC-208 | SHOULD | SKIP | Identity federation uses multi-factor authentication for human users | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-233 | SHOULD | SKIP | Use a service mesh that eliminates implicit trust through data-in-motion protection (i.e. confidentiality, integrity, authentication, authorization) | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-259 | SHOULD | NO-CHECK | Integrate vulnerability and configuration scanning in both the IDE and at the CI system during pull request | No unique Privateer check. The only OSPS requirement for automated vulnerability evaluation (OSPS-VM-05.03) is used by CNSC-65, which this control duplicates. |
| CNSC-265 | SHOULD | PASS | Implement at least one other non-author reviewer/approver prior to merging | Privateer github-repo 0.32.3 OSPS-QA-07.01: Passed (Medium confidence). The default branch requires 1 approving review(s), and commits pushed after an approval cannot merge unreviewed |
| CNSC-271 | SHOULD | SKIP | Continuous integration server is isolated and hardened | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-274 | SHOULD | SKIP | Should software artifacts become untrusted due to compromise or other incident, teams should revoke signing keys to ensure repudiation | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-297 | SHOULD | SKIP | Workload-related configuration is signed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-298 | SHOULD | SKIP | Workload-related package is signed | Skipped: This control is out-of-scope for static source repository assessments. |
| CNSC-303 | SHOULD | SKIP | HSMs or credential managers should be used for protecting credentials. If this is not possible, software-based credential managers should be used. | Skipped: This control is out-of-scope for static source repository assessments. |

Generated by `scripts/assess_project.py`. Machine-readable results are in the OSCAL assessment-results file for this project.
