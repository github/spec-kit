# Preset Publishing Guide

This guide explains how to publish your preset to the Spec Kit preset catalog, making it discoverable by `specify preset search`.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Prepare Your Preset](#prepare-your-preset)
3. [Submit to Catalog](#submit-to-catalog)
4. [Verification Process](#verification-process)
5. [Release Workflow](#release-workflow)
6. [Best Practices](#best-practices)

---

## Prerequisites

Before publishing a preset, ensure you have:

1. **Valid Preset**: A working preset with a valid `preset.yml` manifest
2. **Git Repository**: Preset hosted on GitHub (or other public git hosting)
3. **Documentation**: A preset-scoped README.md that explains how to use **this preset**, including a valid `specify preset add ...` install command (see [Usage README Requirements](#usage-readme-requirements))
4. **License**: Open source license file (MIT, Apache 2.0, etc.)
5. **Versioning**: Semantic versioning (e.g., 1.0.0)
6. **Testing**: Preset tested on real projects with `specify preset add --dev`

---

## Prepare Your Preset

### 1. Preset Structure

Ensure your preset follows the standard structure:

```text
your-preset/
├── preset.yml                 # Required: Preset manifest
├── README.md                  # Required: Documentation
├── LICENSE                    # Required: License file
├── CHANGELOG.md               # Recommended: Version history
│
├── templates/                 # Template overrides
│   ├── spec-template.md
│   ├── plan-template.md
│   └── ...
│
└── commands/                  # Command overrides (optional)
    └── speckit.specify.md
```

Start from the [scaffold](scaffold/) if you're creating a new preset.

### 2. preset.yml Validation

Verify your manifest is valid:

```yaml
schema_version: "1.0"

preset:
  id: "your-preset"               # Unique lowercase-hyphenated ID
  name: "Your Preset Name"        # Human-readable name
  version: "1.0.0"                # Semantic version
  description: "Brief description (one sentence)"
  author: "Your Name or Organization"
  repository: "https://github.com/your-org/spec-kit-preset-your-preset"
  license: "MIT"

requires:
  speckit_version: ">=0.1.0"      # Required spec-kit version

provides:
  templates:
    - type: "template"
      name: "spec-template"
      file: "templates/spec-template.md"
      description: "Custom spec template"
      replaces: "spec-template"

tags:                              # 2-5 relevant tags
  - "category"
  - "workflow"
```

**Validation Checklist**:

- ✅ `id` is lowercase with hyphens only (no underscores, spaces, or special characters)
- ✅ `version` follows semantic versioning (X.Y.Z)
- ✅ `description` is concise (under 200 characters)
- ✅ `repository` URL is valid and public
- ✅ All template and command files exist in the preset directory
- ✅ Template names are lowercase with hyphens only
- ✅ Command names use dot notation (e.g. `speckit.specify`)
- ✅ Tags are lowercase and descriptive

### 3. Test Locally

```bash
# Install from local directory
specify preset add --dev /path/to/your-preset

# Verify templates resolve from your preset
specify preset resolve spec-template

# Verify preset info
specify preset info your-preset

# List installed presets
specify preset list

# Remove when done testing
specify preset remove your-preset
```

If your preset includes command overrides, verify they appear in the agent directories:

```bash
# Check Claude commands (if using Claude)
ls .claude/commands/speckit.*.md

# Check Copilot commands (if using Copilot)
ls .github/agents/speckit.*.agent.md

# Check Gemini commands (if using Gemini)
ls .gemini/commands/speckit.*.toml
```

### 4. Create GitHub Release

Create a GitHub release for your preset version:

```bash
# Tag the release
git tag v1.0.0
git push origin v1.0.0
```

The release archive URL will be:

```text
https://github.com/your-org/spec-kit-preset-your-preset/archive/refs/tags/v1.0.0.zip
```

### 5. Test Installation from Archive

```bash
specify preset add --from https://github.com/your-org/spec-kit-preset-your-preset/archive/refs/tags/v1.0.0.zip
```

### Usage README Requirements

The catalog `documentation` field must point at a README that explains how to use
**this preset** — not a product pitch for a broader framework or a separate CLI.

The submission workflow **mechanically enforces** that the linked README is a GitHub-hosted
URL whose path ends with `README.md`, resolves to a readable file, and contains at least one
valid `specify preset add ...` command. The remaining items (preferring a preset-scoped README
in monorepos, covering the minimum structure) are expectations a human reviewer checks —
follow them so your submission isn't sent back for changes.

- **Point `documentation` at the preset-scoped README.** In a monorepo where the preset
  lives in a subdirectory (e.g. `presets/<id>/`), link the README inside that directory
  (`presets/<id>/README.md`) rather than the repository-root README. The root README is
  often a marketing/overview page; the catalog should surface preset usage instead. The key
  requirement is that this README is reachable at the `documentation` URL so users can read
  it *before* downloading the release artifact — it's fine for the same file to also ship
  inside the release ZIP.
- **Include a valid Spec Kit CLI install command** *(enforced)*. The linked README must
  contain at least one `specify preset add ...` invocation. Preferably use the
  catalog-install form whose URL matches your Download URL:

  ```bash
  # <download-url> is the same URL you submit as the catalog Download URL —
  # either the tag archive or a release asset, e.g.:
  specify preset add --from https://github.com/<org>/<repo>/archive/refs/tags/vX.Y.Z.zip
  specify preset add --from https://github.com/<org>/<repo>/releases/download/vX.Y.Z/<id>-X.Y.Z.zip
  ```

  `specify preset add <id>` and `specify preset add --dev <path>` are also accepted, but the
  `--from <download-url>` form is the clearest signal that the README documents this exact
  preset release.
- **Cover the minimum structure** so a reader can decide whether the preset fits:
  - What the preset does / what it provides
  - The install command using Spec Kit CLI syntax (above)
  - When to use it / when not to use it

A submission whose linked README lacks a valid `specify preset add ...` command **fails
validation** (workflow check 2d) and will not be added until corrected.

---

## Submit to Catalog

### Understanding the Catalogs

Spec Kit uses a dual-catalog system:

- **`catalog.json`** — Official, verified presets (install allowed by default)
- **`catalog.community.json`** — Community-contributed presets (discovery only by default)

All community presets should be submitted to `catalog.community.json`.

### 1. Fork the spec-kit Repository

```bash
git clone https://github.com/YOUR-USERNAME/spec-kit.git
cd spec-kit
```

### 2. Add Preset to Community Catalog

Edit `presets/catalog.community.json` and add your preset.

> **⚠️ Entries must be sorted alphabetically by preset ID.** Insert your preset in the correct position within the `"presets"` object.

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-03-10T00:00:00Z",
  "catalog_url": "https://raw.githubusercontent.com/github/spec-kit/main/presets/catalog.community.json",
  "presets": {
    "your-preset": {
      "name": "Your Preset Name",
      "id": "your-preset",
      "description": "Brief description of what your preset provides",
      "author": "Your Name",
      "version": "1.0.0",
      "download_url": "https://github.com/your-org/spec-kit-preset-your-preset/archive/refs/tags/v1.0.0.zip",
      "sha256": "OPTIONAL: SHA-256 hex digest of the archive above; verified before install",
      "repository": "https://github.com/your-org/spec-kit-preset-your-preset",
      "documentation": "https://github.com/your-org/spec-kit-preset-your-preset/blob/main/README.md",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=0.1.0"
      },
      "provides": {
        "templates": 3,
        "commands": 1
      },
      "tags": [
        "category",
        "workflow"
      ],
      "created_at": "2026-03-10T00:00:00Z",
      "updated_at": "2026-03-10T00:00:00Z"
    }
  }
}
```

### 3. Update Community Presets Table

Add your preset to the Community Presets table on the docs site at `docs/community/presets.md`:

```markdown
| Your Preset Name | Brief description of what your preset does | N templates, M commands[, P scripts] | — | [repo-name](https://github.com/your-org/spec-kit-preset-your-preset) |
```

Insert your row in alphabetical order by preset **name** (the first column of the table).

### 4. Submit Pull Request

```bash
git checkout -b add-your-preset
git add presets/catalog.community.json docs/community/presets.md
git commit -m "Add your-preset to community catalog

- Preset ID: your-preset
- Version: 1.0.0
- Author: Your Name
- Description: Brief description
"
git push origin add-your-preset
```

**Pull Request Checklist**:

```markdown
## Preset Submission

**Preset Name**: Your Preset Name
**Preset ID**: your-preset
**Version**: 1.0.0
**Repository**: https://github.com/your-org/spec-kit-preset-your-preset

### Checklist
- [ ] Valid preset.yml manifest
- [ ] Usage README with a valid `specify preset add ...` command, linked from `documentation` (preset-scoped README recommended for monorepos)
- [ ] LICENSE file included
- [ ] GitHub release created
- [ ] Preset tested with `specify preset add --dev`
- [ ] Templates resolve correctly (`specify preset resolve`)
- [ ] Commands register to agent directories (if applicable)
- [ ] Commands match template sections (command + template are coherent)
- [ ] Added to presets/catalog.community.json
- [ ] Added row to docs/community/presets.md table
```

---

## Verification Process

After submission, maintainers will review:

1. **Manifest validation** — valid `preset.yml`, all files exist
2. **Template quality** — templates are useful and well-structured
3. **Command coherence** — commands reference sections that exist in templates
4. **Security** — no malicious content, safe file operations
5. **Documentation** — the README linked from `documentation` explains how to use *this* preset and contains a valid `specify preset add ...` command

> **Reviewer note:** the workflow can mechanically check *structure* (the linked README
> resolves and contains a valid `specify preset add ...` snippet; when that snippet uses the
> `--from <url>` form, its URL must match the submitted download URL exactly — other accepted
> forms like `specify preset add <id>` don't reference the download URL at all). Whether the
> README genuinely documents *this* preset is partly a content judgment, so a human reviewer
> should still confirm the linked doc isn't just a funnel to a separate product or CLI before
> approving.

Once verified, `verified: true` is set and the preset appears in `specify preset search`.

---

## Release Workflow

When releasing a new version:

1. Update `version` in `preset.yml`
2. Update CHANGELOG.md
3. Tag and push: `git tag v1.1.0 && git push origin v1.1.0`
4. Submit PR to update `version` and `download_url` in `presets/catalog.community.json`

---

## Best Practices

### Template Design

- **Keep sections clear** — use headings and placeholder text the LLM can replace
- **Match commands to templates** — if your preset overrides a command, make sure it references the sections in your template
- **Document customization points** — use HTML comments to guide users on what to change

### Naming

- Preset IDs should be descriptive: `healthcare-compliance`, `enterprise-safe`, `startup-lean`
- Avoid generic names: `my-preset`, `custom`, `test`

### Stacking

- Design presets to work well when stacked with others
- Only override templates you need to change
- Document which templates and commands your preset modifies

### Command Overrides

- Only override commands when the workflow needs to change, not just the output format
- If you only need different template sections, a template override is sufficient
- Test command overrides with multiple agents (Claude, Gemini, Copilot)
