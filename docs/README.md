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
- `guides/bugfix.md` - Bug-fixing walkthrough
- `guides/assessment.md` - Idea assessment walkthrough
- `guides/customization.md` - Choosing and combining customization building blocks
- `reference/agentic-*.md` - Detailed process command references
- `_site/` - Generated documentation output (ignored by git)

## Deployment

Documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch. The workflow is defined in `.github/workflows/docs.yml`.
