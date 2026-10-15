package steps

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"encoding/json"
	"errors"
	"strings"
	"testing"

	"github.com/gemaraproj/go-gemara"
	"github.com/ossf/pvtr-github-repo-scanner/data"
	"github.com/privateerproj/privateer-sdk/config"
)

func payload(vars map[string]interface{}) data.Payload {
	if vars == nil {
		vars = map[string]interface{}{}
	}
	vars["owner"], vars["repo"] = "_", "_"
	p := data.Payload{
		GraphqlRepoData: &data.GraphqlRepoData{},
		Config:          &config.Config{Vars: vars},
	}
	p.Repository.DefaultBranchRef.Name = "main"
	return p
}

// fakeGet serves canned JSON by path prefix.
func fakeGet(responses map[string]any) getter {
	return func(path string, out any) error {
		for prefix, v := range responses {
			if strings.HasPrefix(path, prefix) {
				if err, ok := v.(error); ok {
					return err
				}
				b, _ := json.Marshal(v)
				return json.Unmarshal(b, out)
			}
		}
		return errors.New("unexpected path " + path)
	}
}

func commit(sha, author, login, typ string, verified bool) map[string]any {
	c := map[string]any{
		"sha": sha,
		"commit": map[string]any{
			"author":       map[string]any{"name": author},
			"committer":    map[string]any{"name": author},
			"verification": map[string]any{"verified": verified, "reason": "x"},
		},
	}
	if login != "" {
		c["author"] = map[string]any{"login": login, "type": typ}
	}
	return c
}

func TestCommitsSigned(t *testing.T) {
	p := payload(nil)
	auto := releaseAutomation(p)
	cases := []struct {
		name     string
		commits  []map[string]any
		wantOK   bool
		excused  int
		unsigned int
	}{
		{"all signed", []map[string]any{commit("aaaaaaaa", "A", "a", "User", true)}, true, 0, 0},
		{"unsigned human", []map[string]any{commit("bbbbbbbb", "B", "b", "User", false)}, false, 0, 1},
		{"unsigned bot", []map[string]any{commit("cccccccc", "dependabot", "dependabot[bot]", "Bot", false)}, true, 1, 0},
		{"unsigned release tool, no account", []map[string]any{commit("dddddddd", "semantic-release", "", "", false)}, true, 1, 0},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			r, err := checkCommits(fakeGet(map[string]any{"/repos/": c.commits}), p, "main", 20, auto)
			if err != nil {
				t.Fatal(err)
			}
			if r.ok() != c.wantOK || r.excused != c.excused || len(r.unsigned) != c.unsigned {
				t.Fatalf("got %+v", r)
			}
		})
	}
}

func TestTags(t *testing.T) {
	p := payload(nil)
	get := fakeGet(map[string]any{
		"/repos/_/_/tags":            []map[string]any{{"name": "v1"}, {"name": "v2"}, {"name": "v3"}},
		"/repos/_/_/git/ref/tags/v1": map[string]any{"object": map[string]any{"type": "tag", "sha": "s1"}},
		"/repos/_/_/git/ref/tags/v2": map[string]any{"object": map[string]any{"type": "commit", "sha": "s2"}},
		"/repos/_/_/git/ref/tags/v3": map[string]any{"object": map[string]any{"type": "tag", "sha": "s3"}},
		"/repos/_/_/git/tags/s1":     map[string]any{"tagger": map[string]any{"name": "Dev"}, "verification": map[string]any{"verified": true}},
		"/repos/_/_/git/tags/s3":     map[string]any{"tagger": map[string]any{"name": "semantic-release"}, "verification": map[string]any{"verified": false}},
	})
	r, err := checkTags(get, p, 10, releaseAutomation(p))
	if err != nil {
		t.Fatal(err)
	}
	if r.signed != 1 || r.excused != 1 || len(r.unsigned) != 1 || !strings.Contains(r.unsigned[0], "v2") {
		t.Fatalf("got %+v", r)
	}
}

func TestCommitsAndTagsSignedUnreadable(t *testing.T) {
	p := payload(nil)
	res, _, _ := commitsAndTagsSigned(fakeGet(map[string]any{"/repos/": errors.New("boom")}), p)
	if res != gemara.NeedsReview {
		t.Fatalf("got %v", res)
	}
}

func TestSignedCommitsEnforced(t *testing.T) {
	signed := []map[string]any{commit("aaaaaaaa", "A", "a", "User", true)}
	t.Run("ruleset requires signatures", func(t *testing.T) {
		get := fakeGet(map[string]any{
			"/repos/_/_/commits":             signed,
			"/repos/_/_/rules/branches/main": []map[string]any{{"type": "required_signatures"}},
		})
		if res, _, _ := signedCommitsEnforced(get, payload(nil)); res != gemara.Passed {
			t.Fatalf("got %v", res)
		}
	})
	t.Run("classic protection requires signatures", func(t *testing.T) {
		p := payload(nil)
		p.Repository.DefaultBranchRef.BranchProtectionRule.RequiresCommitSignatures = true
		get := fakeGet(map[string]any{"/repos/_/_/commits": signed, "/repos/_/_/rules/": []map[string]any{}})
		if res, _, _ := signedCommitsEnforced(get, p); res != gemara.Passed {
			t.Fatalf("got %v", res)
		}
	})
	t.Run("not enforced, not admin", func(t *testing.T) {
		get := fakeGet(map[string]any{"/repos/_/_/commits": signed, "/repos/_/_/rules/": []map[string]any{}})
		if res, _, _ := signedCommitsEnforced(get, payload(nil)); res != gemara.NeedsReview {
			t.Fatalf("got %v", res)
		}
	})
	t.Run("unsigned human commit fails", func(t *testing.T) {
		get := fakeGet(map[string]any{
			"/repos/_/_/commits": []map[string]any{commit("bbbbbbbb", "B", "b", "User", false)},
			"/repos/_/_/rules/":  []map[string]any{{"type": "required_signatures"}},
		})
		if res, _, _ := signedCommitsEnforced(get, payload(nil)); res != gemara.Failed {
			t.Fatalf("got %v", res)
		}
	})
}

func tarball(t *testing.T, files map[string]string) *bytes.Buffer {
	t.Helper()
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gz)
	for name, body := range files {
		if err := tw.WriteHeader(&tar.Header{Name: "repo-abc/" + name, Mode: 0o644, Size: int64(len(body)), Typeflag: tar.TypeReg}); err != nil {
			t.Fatal(err)
		}
		_, _ = tw.Write([]byte(body))
	}
	_ = tw.Close()
	_ = gz.Close()
	return &buf
}

func TestScanTarball(t *testing.T) {
	// Assembled at run time so this source file holds no token-shaped literal.
	secret := "ghp_" + strings.Repeat("aB3dE5gH7j", 3) + "aB3dE5"
	files := map[string]string{
		"README.md":      "hello\n",
		"deploy/env.txt": "GITHUB_TOKEN=" + secret + "\n",
		"fixtures/k.txt": "GITHUB_TOKEN=" + secret + "\n",
		"bin.dat":        "\x00\x01\x02",
	}
	t.Run("detects and names only file and rule", func(t *testing.T) {
		s, err := scanTarball(tarball(t, files), []string{"fixtures/"})
		if err != nil {
			t.Fatal(err)
		}
		if len(s.findings) == 0 || s.findings[0].File != "deploy/env.txt" || s.skipped != 2 {
			t.Fatalf("got %+v", s)
		}
		if strings.Contains(s.describe(), secret) {
			t.Fatal("description leaks the secret")
		}
	})
	t.Run("clean", func(t *testing.T) {
		s, err := scanTarball(tarball(t, map[string]string{"a.txt": "nothing here\n"}), nil)
		if err != nil || len(s.findings) != 0 || s.files != 1 {
			t.Fatalf("got %+v, %v", s, err)
		}
	})
	t.Run("not gzip", func(t *testing.T) {
		if _, err := scanTarball(strings.NewReader("plain"), nil); err == nil {
			t.Fatal("expected error")
		}
	})
}
