# Documentation

This folder contains the documentation source files for Spec Kit, built using [DocFX](https://dotnet.github.io/docfx/).

## Building Locally

To build the documentation locally:

1. Install DocFX:

   ```bash
   dotnet tool install -g docfx
   ```

2. Build the documentation:

   ```bash
   cd docs
   docfx docfx.json --serve
   ```

3. Open your browser to `http://localhost:8080` to view the documentation.

## Structure

The table of contents groups project background and shared CLI reference under
**Overview**. **Getting Started** pairs each process walkthrough with its command
reference. **How to** covers project practices, authentication, and local
development of Spec Kit itself. Integrations, extensions, presets, workflows,
workflow steps, bundles, and community resources retain their own sections.

Overview's supporting pages live under `overview/`, while `index.md` remains
the site homepage. Process command references and authentication remain under
`reference/`, and the local development guide lives under `how-to/`.

- `docfx.json` - DocFX configuration file
- `index.md` - Main documentation homepage
- `overview/history.md` - Project history and stewardship
- `toc.yml` - Table of contents configuration
- `overview/core.md` - Core CLI commands and shared project configuration
- `overview/mcp.md` - Experimental local stdio MCP server
- `overview/artifacts.md` - Artifact inventory and composition reference
- `reference/authentication.md` - Authentication configuration guide and reference
- `how-to/local-development.md` - Developing and checking Spec Kit locally
- `installation.md` - Installation guide
- `quickstart.md` - Spec-Driven Development walkthrough
- `guides/agentic-sdlc.md` - How Spec Kit applies agentic and conventional SDLC practices to itself
- `guides/bugfix.md` - Bug-fixing walkthrough
- `guides/assessment.md` - Idea assessment walkthrough
- `how-to/index.md` - How-to guide directory
- `how-to/sdd.md` - Understanding Spec-Driven Development
- `how-to/existing-projects.md` - Adopting Spec Kit in an existing project
- `how-to/monorepo.md` - Working in a monorepo
- `how-to/contract-driven-development.md` - Defining and evolving component contracts
- `how-to/complex-features.md` - Implementing complex features in bounded runs
- `how-to/spec-of-specs.md` - Breaking large features into smaller specifications
- `how-to/persisting-specs.md` - Persisting specifications after delivery
- `how-to/evolving-specs.md` - Evolving specifications for subsequent changes
- `how-to/customization.md` - Adapting Spec Kit to your process
- `overview/catalogs.md` - Catalog discovery, trust, private sources, and precedence
- `extensions/overview.md` - Extension user guide
- `extensions/cli.md` - Extension management CLI reference
- `extensions/catalogs.md` - Extension catalog configuration, trust, and release schema
- `extensions/developing.md` - Extension authoring guide
- `extensions/api.md` - Extension manifest, API, hook, and runtime event contracts
- `extensions/publishing.md` - Extension publishing and catalog submission guide
- `presets/overview.md` - Preset user guide
- `presets/cli.md` - Preset management CLI reference
- `presets/developing.md` - Preset authoring and local testing guide
- `presets/api.md` - Manifest, composition, and lifecycle reference
- `presets/catalogs.md` - Preset catalog configuration, schemas, and trust
- `presets/publishing.md` - Preset publishing and catalog submission guide
- `workflows/overview.md` - Workflow user guide and run/review/resume walkthrough
- `workflows/cli.md` - Workflow, overlay, and workflow catalog CLI reference
- `workflows/developing.md` - Workflow authoring guide
- `workflows/api.md` - YAML, execution, and persisted-state contracts
- `workflows/expressions.md` - Expression language, runtime context, and shell safety
- `workflows/overlays.md` - Workflow composition through overlays and slots
- `workflows/catalogs.md` - Workflow catalogs, releases, and trust
- `workflows/publishing.md` - Workflow publishing and catalog submission guide
- `workflow-steps/overview.md` - Built-in and custom workflow step overview
- `workflow-steps/cli.md` - Custom step and step catalog management CLI
- `workflow-steps/developing.md` - Step package authoring and validation
- `workflow-steps/api.md` - Python extension API, registry, and loader contracts
- `workflow-steps/types.md` - Built-in step configuration and outputs
- `workflow-steps/catalogs.md` - Step catalogs, releases, and trust
- `workflow-steps/publishing.md` - Step release and submission guidance
- `bundles/overview.md` - Bundle user guide and first-party setups
- `bundles/cli.md` - Bundle management CLI reference
- `bundles/developing.md` - Bundle authoring and installation testing guide
- `bundles/api.md` - Manifest, reference expansion, and installed-record contracts
- `bundles/catalogs.md` - Bundle catalogs, policies, and release history
- `bundles/publishing.md` - Bundle publishing and catalog submission guide
- `community/extensions.md` - Community extension listing
- `community/integrations.md` - Community integration discovery and contribution
- `community/workflows.md` - Community workflow listing and contribution
- `community/workflow-steps.md` - Community step listing and submission contract
- `integrations/index.md` - Integration directory and shared setup guidance
- `integrations/cli.md` - Shared integration management CLI reference
- `integrations/api.md` - Public Python adapter and file ownership contracts
- `integrations/<key>.md` - Agent-specific setup, invocation, options, and limitations
- `integrations/catalog.md` - Catalog schema and external adapter metadata
- `integrations/contributing.md` - Integration and catalog contribution guide
- `reference/agentic-*.md` - Detailed process command references
- `_site/` - Generated documentation output (ignored by git)

## Deployment

Documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch. The workflow is defined in `.github/workflows/docs.yml`.
