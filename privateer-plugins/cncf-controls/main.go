// Command cncf-controls is a Privateer plugin that evaluates the CNCF security
// controls (CNSC) that the OSPS Baseline plugin (github-repo) does not cover.
//
// It reuses the github-repo plugin's data loader, so one GitHub payload feeds
// both the reused OSPS steps and the steps defined here.
package main

import (
	"embed"
	"fmt"
	"os"
	"path/filepath"

	"github.com/gemaraproj/go-gemara"
	"github.com/ossf/pvtr-github-repo-scanner/data"

	"github.com/oscal-compass-lab/pvtr-cncf-controls/steps"
	"github.com/privateerproj/privateer-sdk/command"
	"github.com/privateerproj/privateer-sdk/config"
	"github.com/privateerproj/privateer-sdk/pluginkit"
	"github.com/privateerproj/privateer-sdk/shared"
)

var (
	// Version is replaced at build time by the release tag.
	Version = "0.0.0"
	// VersionPostfix marks the version, such as "dev".
	VersionPostfix = "dev"
	// GitCommitHash is the commit at build time.
	GitCommitHash = ""
	// BuiltAt is the build datetime.
	BuiltAt = ""

	PluginName   = "cncf-controls"
	RequiredVars = []string{"owner", "repo", "token"}

	//go:embed data/catalogs
	files   embed.FS
	dataDir = filepath.Join("data", "catalogs")
)

func main() {
	if VersionPostfix != "" {
		Version = fmt.Sprintf("%s-%s", Version, VersionPostfix)
	}

	orchestrator, err := newOrchestrator()
	if err != nil {
		fmt.Printf("%v\n", err)
		os.Exit(shared.InternalError)
	}

	runCmd := command.NewPluginCommands(PluginName, Version, GitCommitHash, BuiltAt, orchestrator)
	if err := runCmd.Execute(); err != nil {
		os.Exit(shared.InternalError)
	}
}

func newOrchestrator() (*pluginkit.EvaluationOrchestrator, error) {
	orchestrator := &pluginkit.EvaluationOrchestrator{
		PluginName:    PluginName,
		PluginVersion: Version,
		PluginUri:     "https://github.com/oscal-compass-lab/cncf-compliance",
		Publisher:     "oscal-compass-lab",
		License:       "Apache-2.0",
	}
	orchestrator.AddLoader(data.Loader)
	orchestrator.AddTargetBuilder(func(c *config.Config) gemara.Resource {
		slug := fmt.Sprintf("%s/%s", c.GetString("owner"), c.GetString("repo"))
		return gemara.Resource{
			Id:   fmt.Sprintf("github.com/%s", slug),
			Name: slug,
			Type: gemara.Software,
			Uri:  fmt.Sprintf("https://github.com/%s", slug),
		}
	})

	if err := orchestrator.AddReferenceCatalogs(dataDir, files); err != nil {
		return nil, fmt.Errorf("error loading catalog: %w", err)
	}
	orchestrator.AddRequiredVars(RequiredVars)

	if err := pluginkit.AddEvaluationSuiteTypedForAllCatalogs(orchestrator, nil, steps.All); err != nil {
		return nil, fmt.Errorf("error adding evaluation suites: %w", err)
	}
	return orchestrator, nil
}
