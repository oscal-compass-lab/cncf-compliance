# Parameter overrides

Each subdirectory in this directory holds the parameter overrides for one project.
The assessment pipeline merges these values into the auto-probed parameter set
before writing OSCAL artifacts.

---

## Directory structure

```
data/param-overrides/
  <slug>/
    overrides.json
```

The subdirectory name is the project **slug** derived from the GitHub URL:

```
github.com/<org>/<repo>  →  <org>--<repo>
```

Examples:

| GitHub URL | Override directory |
|---|---|
| `https://github.com/argoproj/argo-cd` | `argoproj--argo-cd/` |
| `https://github.com/oscal-compass/compliance-trestle` | `oscal-compass--compliance-trestle/` |
| `https://github.com/cncf/tag-security` | `cncf--tag-security/` |

To add overrides for a new project, create the directory and file:

```
data/param-overrides/<slug>/overrides.json
```

---

## File format

`overrides.json` is a flat JSON object — **param ID as key, string value as value**.

```json
{
  "param-id-one": "value",
  "param-id-two": "value"
}
```

- Include **none, one, or all** params — only the params listed are overridden.
- Omitted params use the auto-probed value if available, otherwise the shared default.
- The override file is applied last and always wins.

---

## Examples

### Override one param

Exclude extra directories from secrets scanning:

```json
{
  "secrets-scan-exclude-paths": ".venv,trestle.ws,.git,dist,hack,vendor"
}
```

### Override several params

A Go project with a non-standard branch name, test directory, and workflow keywords:

```json
{
  "default-branch": "master",
  "test-dir": "e2e/tests",
  "vuln-scan-workflows": "codeql,trivy,govulncheck"
}
```

### Override all params for a project

A project with non-standard tooling across the board:

```json
{
  "default-branch": "develop",
  "pipeline-file": "Taskfile.yml",
  "dependency-file": "pyproject.toml",
  "lock-file": "poetry.lock",
  "test-dir": "src/tests",
  "test-target": "pytest",
  "sast-target": "lint-security",
  "sast-workflows": "semgrep,bandit",
  "vuln-scan-workflows": "snyk,trivy",
  "manifest-scan-workflows": "checkov,yamllint",
  "secrets-scan-exclude-paths": ".venv,.git,dist,fixtures",
  "signed-commits-exempt-pattern": "^release:",
  "min-reviewers": "1"
}
```

---

## Where overrides appear in the OSCAL output

Running `python scripts/build_project_compliance.py project <repo-url>` writes two
OSCAL files that both reflect the merged (probed + override) parameter values.

### 1. Component Definition — the delta

`trestle.ws/component-definitions/<slug>/component-definition.json`

Contains only params that **differ from the shared base default**.
Each override appears as a `set-parameters` entry inside the component's
`control-implementations`:

```json
{
  "component-definition": {
    "components": [
      {
        "control-implementations": [
          {
            "set-parameters": [
              {
                "param-id": "secrets-scan-exclude-paths",
                "values": [
                  ".venv,trestle.ws,.git,dist,hack,resource_customizations"
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 2. System Security Plan — the full picture

`trestle.ws/system-security-plans/<slug>/system-security-plan.json`

Contains **all** params for every control — probed values and overrides merged
together. Each control's entry in `implemented-requirements` carries its own
`set-parameters` block with the final resolved values:

```json
{
  "system-security-plan": {
    "control-implementation": {
      "implemented-requirements": [
        {
          "control-id": "CNSC-184",
          "set-parameters": [
            {
              "param-id": "secrets-scan-extensions",
              "values": ["py,sh,yaml,yml,env,cfg,ini"]
            },
            {
              "param-id": "secrets-scan-exclude-paths",
              "values": [".venv,trestle.ws,.git,dist,hack,resource_customizations"]
            }
          ]
        }
      ]
    }
  }
}
```

The SSP is the authoritative record of every parameter value used during
assessment for a specific project.

---

## All available param IDs

| Param ID | Default value | What it controls |
|---|---|---|
| `default-branch` | `main` | Branch name checked for protection rules and used by commit-signing checks |
| `min-reviewers` | `2` | Minimum required non-author reviewers for branch protection |
| `pipeline-file` | `Makefile` | Pipeline-as-code file searched for named targets (`Makefile`, `Taskfile.yml`, `Justfile`, etc.) |
| `test-dir` | `tests` | Directory that must exist to satisfy test-suite controls |
| `test-target` | `test` | Pipeline target that runs the test suite locally |
| `all-target` | `all` | Top-level pipeline entry point target |
| `env-setup-target` | `venv` | Pipeline target that creates the build environment |
| `sast-target` | `sast` | Pipeline target that runs SAST |
| `sast-workflows` | `codeql,scorecard,sonar,sast,gosec,bandit,semgrep,ruff` | Keywords matched against CI workflow filenames/content for SAST |
| `sast-tool` | `bandit` | SAST tool name (informational, used in evidence) |
| `pipeline-vuln-scan-target` | `audit-deps` | Pipeline target that runs vulnerability scanning |
| `vuln-scan-workflows` | `codeql,scorecard,trivy,snyk,sonar,vuln,audit,security,actionlint` | Keywords matched against CI workflow filenames/content for vulnerability scanning |
| `vulnerability-scanner` | `pip-audit` | Vulnerability scanner tool name (informational) |
| `manifest-scan-target` | `act-lint` | Pipeline target that validates/lints manifests |
| `manifest-scan-workflows` | `actionlint,kube-linter,yamllint,checkov,trivy,lint` | Keywords matched against CI workflow filenames/content for manifest scanning |
| `dependency-file` | `requirements.txt` | Dependency declaration file (`go.mod`, `pyproject.toml`, `package.json`, etc.) |
| `lock-file` | `requirements.lock` | Dependency lock file (`go.sum`, `poetry.lock`, `package-lock.json`, etc.) |
| `hash-pin-pattern` | `--require-hashes` | Pattern in the pipeline file that activates dependency hash verification |
| `trusted-registry-pattern` | `pip install` | Pattern in the pipeline file confirming use of a trusted package manager |
| `codeowners-file` | `CODEOWNERS` | Path to the CODEOWNERS file |
| `contributing-file` | `CONTRIBUTING.md` | Path to the contribution policy document |
| `security-policy-file` | `SECURITY.md` | Path to the security policy document |
| `threat-model-file` | `THREAT_MODEL.md` | Path to the threat model document |
| `sbom-output-path` | `sbom.json` | Path to the generated SBOM file |
| `sbom-target` | `generate-sbom` | Pipeline target that generates the SBOM |
| `license-scan-target` | `license-check` | Pipeline target that runs license compliance scanning |
| `license-scanner` | `pip-licenses` | License scanner tool name (informational) |
| `sca-target` | `sca` | Pipeline target that runs software composition analysis |
| `output-artifact-path` | `dist` | Path to the primary pipeline output artifact or directory |
| `signed-commits-lookback` | `10` | Number of recent commits to verify for cryptographic signatures |
| `signed-commits-exempt-pattern` | `^chore: Merge back.*\|^\d+\.\d+\.\d+` | Regex matching release-bot commit messages exempt from the signing requirement |
| `mfa-enforcement-scope` | `organization` | Scope at which MFA is enforced (manual control — not auto-checked) |
| `git-config-file` | `.git/config` | Path to the git configuration file |
| `ssh-remote-pattern` | `git@github\.com` | Regex pattern confirming SSH remote URL in git config |
