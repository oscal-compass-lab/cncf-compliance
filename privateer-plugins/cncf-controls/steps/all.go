package steps

import (
	"github.com/ossf/pvtr-github-repo-scanner/evaluation_plans/osps/access_control"
	"github.com/ossf/pvtr-github-repo-scanner/evaluation_plans/osps/build_release"
)

// All maps assessment requirement ids of the cncf-controls catalog to
// their steps. Steps of one requirement run in order; the first failure ends
// the requirement.
var All = map[string][]Step{
	"CNSC-182.01": {CommitsAndTagsSigned},
	"CNSC-184.01": {NoSecretsInDefaultBranch},
	"CNSC-190.01": {access_control.BranchProtectionRestrictsPushes},
	"CNSC-198.01": {build_release.SecretScanningInUse, NoSecretsInDefaultBranch},
	"CNSC-199.01": {SignedCommitsEnforced},
}
