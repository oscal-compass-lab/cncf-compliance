package steps

import (
	"archive/tar"
	"compress/gzip"
	"context"
	"fmt"
	"io"
	"path"
	"sort"
	"strings"
	"time"

	"github.com/gemaraproj/go-gemara"
	"github.com/ossf/pvtr-github-repo-scanner/data"
	"github.com/zricethezav/gitleaks/v8/detect"
)

const (
	scanTimeout      = 5 * time.Minute
	maxArchiveBytes  = 200 << 20 // compressed download limit
	maxFileBytes     = 1 << 20   // larger files are skipped
	maxFindingsShown = 5
)

// secretFinding names a detected secret by location and rule only. The secret
// value is never kept.
type secretFinding struct {
	File   string
	RuleID string
}

// scanSummary is the outcome of scanning an archive.
type scanSummary struct {
	files    int
	skipped  int
	findings []secretFinding
}

func (s scanSummary) describe() string {
	if len(s.findings) == 0 {
		return fmt.Sprintf("Scanned %d files in the default branch with gitleaks; no secrets found (%d skipped as binary or too large)", s.files, s.skipped)
	}
	seen := map[string]bool{}
	var items []string
	for _, f := range s.findings {
		k := f.File + " (" + f.RuleID + ")"
		if !seen[k] {
			seen[k] = true
			items = append(items, k)
		}
	}
	sort.Strings(items)
	return fmt.Sprintf("Gitleaks found %d potential secrets in the default branch: %s", len(s.findings), strings.Join(firstN(items, maxFindingsShown), ", "))
}

// scanTarball scans every regular text file of a gzip-compressed tar archive.
func scanTarball(r io.Reader, ignored []string) (scanSummary, error) {
	detector, err := detect.NewDetectorDefaultConfig()
	if err != nil {
		return scanSummary{}, fmt.Errorf("gitleaks configuration: %w", err)
	}
	gz, err := gzip.NewReader(io.LimitReader(r, maxArchiveBytes))
	if err != nil {
		return scanSummary{}, fmt.Errorf("archive is not gzip: %w", err)
	}
	defer func() { _ = gz.Close() }()

	var out scanSummary
	tr := tar.NewReader(gz)
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return scanSummary{}, fmt.Errorf("reading archive: %w", err)
		}
		if hdr.Typeflag != tar.TypeReg {
			continue
		}
		// The first path element is the archive's root directory.
		name := hdr.Name
		if i := strings.Index(name, "/"); i >= 0 {
			name = name[i+1:]
		}
		if hdr.Size > maxFileBytes || pathIgnored(name, ignored) {
			out.skipped++
			continue
		}
		body, err := io.ReadAll(io.LimitReader(tr, maxFileBytes+1))
		if err != nil {
			return scanSummary{}, fmt.Errorf("reading %s: %w", name, err)
		}
		if looksBinary(body) {
			out.skipped++
			continue
		}
		out.files++
		for _, f := range detector.Detect(detect.Fragment{Raw: string(body), FilePath: name}) {
			out.findings = append(out.findings, secretFinding{File: name, RuleID: f.RuleID})
		}
	}
	return out, nil
}

func looksBinary(b []byte) bool {
	if len(b) > 8000 {
		b = b[:8000]
	}
	for _, c := range b {
		if c == 0 {
			return true
		}
	}
	return false
}

func pathIgnored(name string, patterns []string) bool {
	for _, pat := range patterns {
		if ok, _ := path.Match(pat, name); ok {
			return true
		}
		if strings.HasSuffix(pat, "/") && strings.HasPrefix(name, pat) {
			return true
		}
	}
	return false
}

// NoSecretsInDefaultBranch implements CNSC-184.01. It downloads the default
// branch as an archive and scans the files with gitleaks. Paths that hold
// intentional fixtures can be excluded with the secrets-scan-ignore-paths
// plugin variable (comma separated glob patterns or directory prefixes ending
// in "/"); skipped paths are counted in the result message.
func NoSecretsInDefaultBranch(p data.Payload) (gemara.Result, string, gemara.ConfidenceLevel) {
	branch := defaultBranch(p)
	if branch == "" {
		return gemara.NeedsReview, "Default branch is not known", gemara.Low
	}
	ctx, cancel := context.WithTimeout(context.Background(), scanTimeout)
	defer cancel()
	resp, err := request(ctx, p, repoPath(p, "tarball/%s", branch))
	if err != nil {
		return gemara.NeedsReview, "Default branch archive could not be downloaded: " + err.Error(), gemara.Low
	}
	defer func() { _ = resp.Body.Close() }()

	var ignored []string
	for _, pat := range strings.Split(p.Config.GetString("secrets-scan-ignore-paths"), ",") {
		if pat = strings.TrimSpace(pat); pat != "" {
			ignored = append(ignored, pat)
		}
	}
	summary, err := scanTarball(resp.Body, ignored)
	if err != nil {
		return gemara.NeedsReview, "Default branch could not be scanned: " + err.Error(), gemara.Low
	}
	if len(summary.findings) > 0 {
		return gemara.Failed, summary.describe(), gemara.Medium
	}
	return gemara.Passed, summary.describe(), gemara.Medium
}
