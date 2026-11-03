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

- `docfx.json` - DocFX configuration file
- `index.md` - Main documentation homepage
- `toc.yml` - Table of contents configuration
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
- `how-to/spec-persistence.md` - Choosing a specification persistence model
- `how-to/evolving-specs.md` - Maintaining specifications after delivery
- `how-to/customization.md` - Adapting Spec Kit to your process
- `reference/catalogs.md` - Catalog discovery, trust, private sources, and precedence
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
- `community/extensions.md` - Community extension listing
- `integrations/index.md` - Integration directory and shared setup guidance
- `integrations/cli.md` - Shared integration management CLI reference
- `integrations/<key>.md` - Agent-specific setup, invocation, options, and limitations
- `integrations/catalog.md` - Catalog schema and external adapter metadata
- `integrations/contributing.md` - Integration and catalog contribution guide
- `reference/agentic-*.md` - Detailed process command references
- `_site/` - Generated documentation output (ignored by git)

## Deployment

Documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch. The workflow is defined in `.github/workflows/docs.yml`.
