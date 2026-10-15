// Package steps holds the assessment steps of the cncf-controls plugin.
package steps

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/gemaraproj/go-gemara"
	"github.com/ossf/pvtr-github-repo-scanner/data"
)

const (
	apiBase    = "https://api.github.com"
	apiTimeout = 30 * time.Second
)

// Step is the signature of every assessment step in this plugin. It matches
// the github-repo plugin's step type so steps can be shared between the two.
type Step func(data.Payload) (gemara.Result, string, gemara.ConfidenceLevel)

// defaultReleaseAutomation names commit authors and tag taggers that publish
// releases without a signature. Extend it with the release-automation-authors
// plugin variable (comma separated, case-insensitive).
const defaultReleaseAutomation = "semantic-release"

func owner(p data.Payload) string { return p.Config.GetString("owner") }
func repo(p data.Payload) string  { return p.Config.GetString("repo") }

// defaultBranch is the repository's default branch name.
func defaultBranch(p data.Payload) string {
	if p.GraphqlRepoData == nil {
		return ""
	}
	return p.Repository.DefaultBranchRef.Name
}

// intVar reads a positive integer plugin variable, or returns def.
func intVar(p data.Payload, name string, def int) int {
	if n, err := strconv.Atoi(strings.TrimSpace(p.Config.GetString(name))); err == nil && n > 0 {
		return n
	}
	return def
}

// releaseAutomation returns the lower-cased names of unsigned release automation.
func releaseAutomation(p data.Payload) map[string]bool {
	out := map[string]bool{}
	list := defaultReleaseAutomation + "," + p.Config.GetString("release-automation-authors")
	for _, n := range strings.Split(list, ",") {
		if n = strings.ToLower(strings.TrimSpace(n)); n != "" {
			out[n] = true
		}
	}
	return out
}

// request performs an authenticated GET against the GitHub API through the
// scanner's counted HTTP client. The caller closes the body.
func request(ctx context.Context, p data.Payload, path string) (*http.Response, error) {
	if p.RestData == nil || p.HttpClient == nil {
		return nil, errors.New("GitHub client is not available")
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, apiBase+path, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("Authorization", "Bearer "+p.Config.GetString("token"))
	resp, err := p.HttpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("GitHub request failed: %w", err)
	}
	if resp.StatusCode != http.StatusOK {
		_ = resp.Body.Close()
		return nil, fmt.Errorf("GitHub API returned %s", resp.Status)
	}
	return resp, nil
}

// getJSON decodes a GitHub API response into out.
func getJSON(p data.Payload, path string, out any) error {
	ctx, cancel := context.WithTimeout(context.Background(), apiTimeout)
	defer cancel()
	resp, err := request(ctx, p, path)
	if err != nil {
		return err
	}
	defer func() { _ = resp.Body.Close() }()
	return json.NewDecoder(resp.Body).Decode(out)
}

func repoPath(p data.Payload, format string, args ...any) string {
	escaped := make([]any, len(args))
	for i, a := range args {
		escaped[i] = url.PathEscape(fmt.Sprint(a))
	}
	return fmt.Sprintf("/repos/%s/%s/", url.PathEscape(owner(p)), url.PathEscape(repo(p))) +
		fmt.Sprintf(format, escaped...)
}
