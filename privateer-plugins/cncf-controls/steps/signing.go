package steps

import (
	"fmt"
	"net/url"
	"strings"

	"github.com/gemaraproj/go-gemara"
	"github.com/ossf/pvtr-github-repo-scanner/data"
)

const (
	defaultCommitCount = 20
	defaultTagCount    = 10
)

// getter fetches and decodes one GitHub API path. Steps use apiGetter; tests
// substitute a fake.
type getter func(path string, out any) error

func apiGetter(p data.Payload) getter {
	return func(path string, out any) error { return getJSON(p, path, out) }
}

type actor struct {
	Login string `json:"login"`
	Type  string `json:"type"`
}

type verification struct {
	Verified bool   `json:"verified"`
	Reason   string `json:"reason"`
}

type commitItem struct {
	SHA    string `json:"sha"`
	Author *actor `json:"author"`
	Commit struct {
		Author       struct{ Name string } `json:"author"`
		Committer    struct{ Name string } `json:"committer"`
		Verification verification          `json:"verification"`
	} `json:"commit"`
	Committer *actor `json:"committer"`
}

type tagListItem struct {
	Name string `json:"name"`
}

type tagRef struct {
	Object struct {
		Type string `json:"type"`
		SHA  string `json:"sha"`
	} `json:"object"`
}

type tagObject struct {
	Tagger       struct{ Name string } `json:"tagger"`
	Verification verification          `json:"verification"`
}

// signingReport summarizes the signature state of recent commits or tags.
type signingReport struct {
	checked  int
	signed   int
	excused  int
	unsigned []string // short names of unsigned items that are not excused
}

func (r signingReport) ok() bool { return len(r.unsigned) == 0 }

func (r signingReport) describe(kind string) string {
	s := fmt.Sprintf("%d of %d recent %s are signed", r.signed, r.checked, kind)
	if r.excused > 0 {
		s += fmt.Sprintf(" (%d unsigned by release automation excused)", r.excused)
	}
	if len(r.unsigned) > 0 {
		s += fmt.Sprintf("; unsigned: %s", strings.Join(firstN(r.unsigned, 5), ", "))
	}
	return s
}

func firstN(in []string, n int) []string {
	if len(in) <= n {
		return in
	}
	return append(append([]string{}, in[:n]...), fmt.Sprintf("and %d more", len(in)-n))
}

func short(sha string) string {
	if len(sha) > 7 {
		return sha[:7]
	}
	return sha
}

// isAutomation reports whether any name is a bot account or one of the named
// release automations. Names are matched case-insensitively as substrings, so
// "semantic-release" matches "semantic-release-bot".
func isAutomation(automation map[string]bool, a *actor, names ...string) bool {
	if a != nil && (a.Type == "Bot" || strings.HasSuffix(strings.ToLower(a.Login), "[bot]")) {
		return true
	}
	if a != nil {
		names = append(names, a.Login)
	}
	for _, n := range names {
		n = strings.ToLower(strings.TrimSpace(n))
		if n == "" {
			continue
		}
		for known := range automation {
			if strings.Contains(n, known) {
				return true
			}
		}
	}
	return false
}

// checkCommits verifies the signatures of the latest commits on branch.
func checkCommits(get getter, p data.Payload, branch string, count int, automation map[string]bool) (signingReport, error) {
	var commits []commitItem
	path := repoPath(p, "commits") + fmt.Sprintf("?sha=%s&per_page=%d", url.QueryEscape(branch), count)
	if err := get(path, &commits); err != nil {
		return signingReport{}, err
	}
	var r signingReport
	for _, c := range commits {
		r.checked++
		switch {
		case c.Commit.Verification.Verified:
			r.signed++
		case isAutomation(automation, c.Author, c.Commit.Author.Name) ||
			isAutomation(automation, c.Committer, c.Commit.Committer.Name):
			r.excused++
		default:
			r.unsigned = append(r.unsigned, short(c.SHA))
		}
	}
	return r, nil
}

// checkTags verifies the signatures of the most recently listed tags.
// Lightweight tags carry no signature and count as unsigned.
func checkTags(get getter, p data.Payload, count int, automation map[string]bool) (signingReport, error) {
	var tags []tagListItem
	if err := get(repoPath(p, "tags")+fmt.Sprintf("?per_page=%d", count), &tags); err != nil {
		return signingReport{}, err
	}
	var r signingReport
	for _, t := range tags {
		r.checked++
		var ref tagRef
		if err := get(repoPath(p, "git/ref/tags/%s", t.Name), &ref); err != nil {
			return signingReport{}, err
		}
		if ref.Object.Type != "tag" {
			r.unsigned = append(r.unsigned, t.Name+" (lightweight)")
			continue
		}
		var obj tagObject
		if err := get(repoPath(p, "git/tags/%s", ref.Object.SHA), &obj); err != nil {
			return signingReport{}, err
		}
		switch {
		case obj.Verification.Verified:
			r.signed++
		case isAutomation(automation, nil, obj.Tagger.Name):
			r.excused++
		default:
			r.unsigned = append(r.unsigned, t.Name)
		}
	}
	return r, nil
}

// CommitsAndTagsSigned implements CNSC-182.01.
func CommitsAndTagsSigned(p data.Payload) (gemara.Result, string, gemara.ConfidenceLevel) {
	return commitsAndTagsSigned(apiGetter(p), p)
}

func commitsAndTagsSigned(get getter, p data.Payload) (gemara.Result, string, gemara.ConfidenceLevel) {
	branch := defaultBranch(p)
	if branch == "" {
		return gemara.NeedsReview, "Default branch is not known", gemara.Low
	}
	automation := releaseAutomation(p)
	commits, err := checkCommits(get, p, branch, intVar(p, "signature-commit-count", defaultCommitCount), automation)
	if err != nil {
		return gemara.NeedsReview, "Commit signatures could not be read: " + err.Error(), gemara.Low
	}
	tags, err := checkTags(get, p, intVar(p, "signature-tag-count", defaultTagCount), automation)
	if err != nil {
		return gemara.NeedsReview, "Tag signatures could not be read: " + err.Error(), gemara.Low
	}
	msg := commits.describe("commits") + "; " + tags.describe("tags")
	if commits.ok() && tags.ok() {
		return gemara.Passed, msg, gemara.High
	}
	return gemara.Failed, msg, gemara.High
}

// requiresSignedCommits reports whether the default branch enforces signed
// commits through classic branch protection or a ruleset. The second result
// is false when the answer is not observable with the current token.
func requiresSignedCommits(get getter, p data.Payload, branch string) (enforced, observable bool) {
	if p.Repository.DefaultBranchRef.BranchProtectionRule.RequiresCommitSignatures {
		return true, true
	}
	var rules []struct {
		Type string `json:"type"`
	}
	if err := get(repoPath(p, "rules/branches/%s", branch), &rules); err != nil {
		return false, false
	}
	for _, r := range rules {
		if r.Type == "required_signatures" {
			return true, true
		}
	}
	// Classic protection settings are visible to admins only; rulesets are
	// visible to anyone, so with no admin the negative is only half-observed.
	return false, p.RepositoryMetadata != nil && p.RepositoryMetadata.ViewerCanAdminister()
}

// SignedCommitsEnforced implements CNSC-199.01.
func SignedCommitsEnforced(p data.Payload) (gemara.Result, string, gemara.ConfidenceLevel) {
	return signedCommitsEnforced(apiGetter(p), p)
}

func signedCommitsEnforced(get getter, p data.Payload) (gemara.Result, string, gemara.ConfidenceLevel) {
	branch := defaultBranch(p)
	if branch == "" {
		return gemara.NeedsReview, "Default branch is not known", gemara.Low
	}
	commits, err := checkCommits(get, p, branch, intVar(p, "signature-commit-count", defaultCommitCount), releaseAutomation(p))
	if err != nil {
		return gemara.NeedsReview, "Commit signatures could not be read: " + err.Error(), gemara.Low
	}
	enforced, observable := requiresSignedCommits(get, p, branch)
	msg := commits.describe("commits")
	switch {
	case !commits.ok():
		return gemara.Failed, msg, gemara.High
	case enforced:
		return gemara.Passed, msg + "; branch requires signed commits", gemara.High
	case observable:
		return gemara.Failed, msg + "; neither branch protection nor a ruleset requires signed commits", gemara.High
	default:
		return gemara.NeedsReview, msg + "; enforcement of signed commits is not observable with the current token", gemara.Low
	}
}
