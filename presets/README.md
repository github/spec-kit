# Presets

Presets are stackable, priority-ordered collections of template and command overrides for Spec Kit. They let you customize both the artifacts produced by the Spec-Driven Development workflow (specs, plans, tasks, checklists, constitutions) and the commands that guide the LLM in creating them — without forking or modifying core files.

## How It Works

When Spec Kit needs a template (e.g. `spec-template`), it walks a resolution stack:

1. `.specify/templates/overrides/` — project-local one-off overrides
2. `.specify/presets/<preset-id>/templates/` — installed presets (sorted by priority)
3. `.specify/extensions/<ext-id>/templates/` — extension-provided templates
4. `.specify/templates/` — core templates shipped with Spec Kit

If no preset is installed, core templates are used — exactly the same behavior as before presets existed.

Template resolution happens **at runtime** — although preset files are copied into `.specify/presets/<id>/` during installation, Spec Kit walks the resolution stack on every template lookup rather than merging templates into a single location.

For detailed resolution and command registration flows, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Command Overrides

Presets can also override the commands that guide the SDD workflow. Templates define *what* gets produced (specs, plans, constitutions); commands define *how* the LLM produces them (the step-by-step instructions).

Unlike templates, command overrides are applied **at install time**. When a preset includes `type: "command"` entries, the commands are registered into all detected agent directories (`.claude/commands/`, `.gemini/commands/`, etc.) in the correct format (Markdown or TOML with appropriate argument placeholders). When the preset is removed, the registered commands are cleaned up.

## Quick Start

```bash
# Search available presets
specify preset search

# Install a preset from the catalog
specify preset add healthcare-compliance

# Install from a local directory (for development)
specify preset add --dev ./my-preset

# Install with a specific priority (lower = higher precedence)
specify preset add healthcare-compliance --priority 5

# List installed presets
specify preset list

# See which template a name resolves to
specify preset resolve spec-template

# Get detailed info about a preset
specify preset info healthcare-compliance

# Remove a preset
specify preset remove healthcare-compliance
```

## Stacking Presets

Multiple presets can be installed simultaneously. The `--priority` flag controls which one wins when two presets provide the same template (lower number = higher precedence):

```bash
specify preset add enterprise-safe --priority 10      # base layer
specify preset add healthcare-compliance --priority 5  # overrides enterprise-safe
specify preset add pm-workflow --priority 1            # overrides everything
```

Presets **override**, they don't merge. If two presets both provide `spec-template`, the one with the lowest priority number wins entirely.

## Catalog Management

Presets are discovered through catalogs. By default, Spec Kit uses the official and community catalogs:

> [!NOTE]
> Community presets are independently created and maintained by their respective authors. GitHub and the Spec Kit maintainers may review pull requests that add entries to the community catalog for formatting, catalog structure, or policy compliance, but they do **not review, audit, endorse, or support the preset code itself**. Review preset source code before installation and use at your own discretion.

```bash
# List active catalogs
specify preset catalog list

# Add a custom catalog
specify preset catalog add https://example.com/catalog.json --name my-org --install-allowed

# Remove a catalog
specify preset catalog remove my-org
```

## Creating a Preset

See [scaffold/](scaffold/) for a scaffold you can copy to create your own preset.

1. Copy `scaffold/` to a new directory
2. Edit `preset.yml` with your preset's metadata
3. Add or replace templates in `templates/`
4. Test locally with `specify preset add --dev .`
5. Verify with `specify preset resolve spec-template`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SPECKIT_PRESET_CATALOG_URL` | Override the full catalog stack with a single URL (replaces all defaults) | Built-in default stack |
| `GH_TOKEN` / `GITHUB_TOKEN` | GitHub token for authenticated requests to GitHub-hosted URLs (`raw.githubusercontent.com`, `github.com`, `api.github.com`). Required when your catalog JSON or preset ZIPs are hosted in a private GitHub repository. | None |

#### Example: Using a private GitHub-hosted catalog

```bash
# Authenticate with a token (gh CLI, PAT, or GITHUB_TOKEN in CI)
export GITHUB_TOKEN=$(gh auth token)

# Search a private catalog added via `specify preset catalog add`
specify preset search my-template

# Install from a private catalog
specify preset add my-template
```

The token is attached automatically to requests targeting GitHub domains. Non-GitHub catalog URLs are always fetched without credentials.

## Configuration Files

| File | Scope | Description |
|------|-------|-------------|
| `.specify/preset-catalogs.yml` | Project | Custom catalog stack for this project |
| `~/.specify/preset-catalogs.yml` | User | Custom catalog stack for all projects |

## Future Considerations

The following enhancements are under consideration for future releases:

- **Composition strategies** — Allow presets to declare a `strategy` per template instead of the default `replace`:

  | Type | `replace` | `prepend` | `append` | `wrap` |
  |------|-----------|-----------|----------|--------|
  | **template** | ✓ (default) | ✓ | ✓ | ✓ |
  | **command** | ✓ (default) | ✓ | ✓ | ✓ |
  | **script** | ✓ (default) | — | — | ✓ |

  For artifacts and commands (which are LLM directives), `wrap` would inject preset content before and after the core template using a `{CORE_TEMPLATE}` placeholder. For scripts, `wrap` would run custom logic before/after the core script via a `$CORE_SCRIPT` variable.
- **Script overrides** — Enable presets to provide alternative versions of core scripts (e.g. `create-new-feature.sh`) for workflow customization. A `strategy: "wrap"` option could allow presets to run custom logic before/after the core script without fully replacing it.
