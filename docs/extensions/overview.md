# Extensions Overview

Guide for using Spec Kit extensions to add commands, external tool integrations,
quality gates, and other capabilities beyond the built-in Spec-Driven
Development process.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Finding Extensions](#finding-extensions)
4. [Installing Extensions](#installing-extensions)
5. [Using Extensions](#using-extensions)
6. [Managing Extensions](#managing-extensions)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Introduction

### What are Extensions?

Extensions are modular packages that add new commands and functionality to Spec Kit without bloating the core framework. They allow you to:

- **Integrate** with external tools (Jira, Linear, GitHub, etc.)
- **Automate** repetitive tasks with hooks
- **Customize** workflows for your team
- **Share** solutions across projects

### Why Use Extensions?

- **Clean Core**: Keeps spec-kit lightweight and focused
- **Optional Features**: Only install what you need
- **Community Driven**: Anyone can create and share extensions
- **Version Controlled**: Extensions are versioned independently

### Specification artifact maintenance

An extension can define commands or hooks that reconcile `spec.md`, `plan.md`,
and `tasks.md` during or after feature delivery. Any such edits follow the
extension's documented behavior and the project's governance; they are not
performed by, or added to the responsibilities of, the core Spec Kit commands.
The team's persistence model separately determines how artifacts are maintained
after delivery.

---

## Getting Started

### Prerequisites

- A current Spec Kit release compatible with the extension's
  `requires.speckit_version` constraint
- A project initialized with `specify init` (directory with `.specify/` folder)

### Check Your Version

```bash
specify version
```

### First Extension

Start with the bundled GitHub extension:

```bash
# 1. Search for the extension
specify extension search github

# 2. Get detailed information
specify extension info github

# 3. Install it
specify extension add github
```

The extension requires Git and a configured GitHub MCP server. Once those are
available, invoke `/speckit-github-taskstoissues` in GitHub Copilot chat to
convert a feature's `tasks.md` into GitHub issues. This is a chat command, not
a terminal command.

The Jira examples below illustrate a separately vetted third-party extension.
They assume you have installed it from a reviewed archive or configured your own
trusted catalog; Jira is discovery-only in the built-in community catalog.

---

## Finding Extensions

`specify extension search` searches **all active catalogs** simultaneously, including the community catalog by default. Results are annotated with their source catalog and install status.

The community catalog is discovery-only. Vet a release before installing it
directly or adding it to your own trusted catalog; see the
[catalog trust model](catalogs.md#trust-model-discovery-only-vs-install-sources).

### Browse All Extensions

```bash
specify extension search
```

Shows all extensions across all active catalogs (default and community by default).

### Search by Keyword

```bash
# Search for "jira"
specify extension search jira

# Search for "issue tracking"
specify extension search issue
```

### Filter by Tag

```bash
# Find all issue-tracking extensions
specify extension search --tag issue-tracking

# Find all Atlassian tools
specify extension search --tag atlassian
```

### Filter by Author

```bash
# Extensions by Stats Perform
specify extension search --author "Stats Perform"
```

### Show Verified Only

```bash
# Only show verified extensions
specify extension search --verified
```

### Get Extension Details

```bash
# Detailed information
specify extension info jira
```

Shows:

- Description
- Requirements
- Commands provided
- Hooks available
- Links (documentation, repository, changelog)
- Installation status

---

## Installing Extensions

### Install from Catalog

```bash
# Install a bundled extension by name
specify extension add github
```

For an extension advertised by an install-enabled catalog, installation will:

1. Download the advertised archive (bundled extensions use the shipped copy)
2. Validate the manifest
3. Check compatibility with your spec-kit version
4. Install to `.specify/extensions/<extension-id>/`
5. Register commands with your coding agent
6. Scaffold any declared configuration templates without overwriting existing
   configuration

After vetting Jira, a catalog you control can advertise it as installable:

```bash
specify extension add jira
```

### Install from URL

```bash
# From GitHub release
specify extension add <extension-name> --from https://github.com/org/spec-kit-ext/archive/refs/tags/v1.0.0.zip
```

### Install from Local Directory (Development)

```bash
# For testing or development
specify extension add --dev /path/to/extension
```

### Install a specific catalog version

```bash
specify extension info jira --versions
specify extension add jira --version <version>
```

The requested version must be advertised by the winning install-enabled
catalog entry. See the [CLI reference](cli.md#install-an-extension) for
selection rules and option restrictions.

### Installation Output

Illustrative output for a Jira release installed from a vetted source:

```text
✓ Extension installed successfully!

Jira Integration (v1.0.0)
  Create Jira Epics, Stories, and Issues from spec-kit artifacts

Provided commands:
  • speckit-jira-specstoissues - Create Jira hierarchy from spec and tasks
  • speckit-jira-discover-fields - Discover Jira custom fields for configuration
  • speckit-jira-sync-status - Sync task completion status to Jira

⚠  Configuration may be required
   Check: .specify/extensions/jira/
```

---

## Using Extensions

### Using Extension Commands

Extensions add skills that appear in GitHub Copilot:

```text
# In GitHub Copilot
> /speckit-jira-specstoissues
```

### Extension Configuration

Most extensions require configuration:

```bash
# 1. Find the config file
ls .specify/extensions/jira/

# 2. Copy template to config
cp .specify/extensions/jira/jira-config.template.yml \
   .specify/extensions/jira/jira-config.yml

# 3. Edit configuration
vim .specify/extensions/jira/jira-config.yml

# 4. Use the extension
# (Commands will now work with your config)
```

### Extension Hooks

Some extensions provide hooks that execute after core commands:

**Example**: Jira extension hooks into `/speckit-tasks`

```text
# Run core command
> /speckit-tasks

# Output includes:
## Extension Hooks

**Optional Hook**: jira
Command: `/speckit-jira-specstoissues`
Description: Automatically create Jira hierarchy after task generation

Prompt: Create Jira issues from tasks?
To execute: `/speckit-jira-specstoissues`
```

You can then choose to run the hook or skip it.

Mandatory hooks are surfaced as automatic commands. Current command templates
use configured YAML order, skip disabled hooks and hooks with non-empty
conditions, and do not consult the reserved `auto_execute_hooks` setting.
See the [hook configuration contract](api.md#hook-configuration) for details.

Extensions can also react to coding-agent lifecycle events, such as session
start or tool use. Unlike hooks, runtime events execute scripts directly rather
than sending Markdown instructions to the coding agent. See
[Extension runtime events](api.md#extension-runtime-events).

---

## Managing Extensions

### List Installed Extensions

```bash
specify extension list
```

Output:

```text
Installed Extensions:

  ✓ Jira Integration (v1.0.0)
     Create Jira Epics, Stories, and Issues from spec-kit artifacts
     Commands: 3 | Hooks: 1 | Status: Enabled
```

### Update Extensions

```bash
# Check for updates (all extensions)
specify extension update

# Update specific extension
specify extension update jira
```

Output:

```text
🔄 Checking for updates...

Updates available:

  • jira: 1.0.0 → 1.1.0

Update these extensions? [y/N]:
```

### Disable Extension Temporarily

```bash
# Disable without removing
specify extension disable jira
```

Declarative hooks are marked disabled in `.specify/extensions.yml`. Native
runtime-event configuration is then refreshed on a best-effort basis. A refresh
failure produces a warning but can leave a stale native hook active and able to
execute. Retry the affected integration with `specify integration upgrade <key>`.
Re-enable the extension with `specify extension enable jira`.

For the generic integration, disabling also removes owned command or skill
files. Other integrations can retain generated files that remain invocable
until an integration switch, uninstall, or reconciliation removes them.
Disabled extensions are excluded from registry-driven artifact resolution and
future integration registration; disabling is not a universal file-removal or
execution-blocking mechanism.

### Re-enable Extension

```bash
specify extension enable jira

✓ Extension 'jira' enabled
```

### Remove Extension

```bash
# Remove extension (with confirmation)
specify extension remove jira

# Keep configuration when removing
specify extension remove jira --keep-config

# Force removal (no confirmation)
specify extension remove jira --force
```

---

## Configuration

### Configuration Files

Extensions can have multiple configuration files:

```text
.specify/extensions/jira/
├── jira-config.yml           # Main config (version controlled)
├── local-config.yml         # Local overrides (gitignored)
└── jira-config.template.yml  # Template (reference)
```

### Configuration Layers

Configuration is merged in this order (highest priority last):

1. **Extension defaults** (top-level `defaults` merged with `config.defaults`,
   with `config.defaults` winning on conflicts)
2. **Project config** (`jira-config.yml`)
3. **Local overrides** (`local-config.yml`)
4. **Environment variables** (`SPECKIT_JIRA_*`)

### Example: Jira Configuration

**Project config** (`.specify/extensions/jira/jira-config.yml`):

```yaml
project:
  key: "MSATS"

defaults:
  epic:
    labels: ["spec-driven"]
```

**Local override** (`.specify/extensions/jira/local-config.yml`):

```yaml
project:
  key: "MYTEST"  # Override for local development
```

**Environment variable**:

```bash
export SPECKIT_JIRA_PROJECT_KEY="DEVTEST"
```

When the extension uses `ConfigManager` or equivalent loading, the final
resolved config uses `DEVTEST` from the environment variable. Spec Kit does not
automatically inject merged configuration into arbitrary commands or scripts;
the extension must load it. YAML `${...}` strings are not interpolated by
`ConfigManager`. See [Config loading](developing.md#config-loading).

### Project-Wide Extension Settings

File: `.specify/extensions.yml`

```yaml
# Extensions installed in this project
installed:
  - jira
  - linear

# Global settings
settings:
  auto_execute_hooks: true  # Reserved; currently not consulted

# Hook configuration
# Available events: before_specify, after_specify, before_plan, after_plan,
#                   before_tasks, after_tasks, before_implement, after_implement,
#                   before_analyze, after_analyze, before_checklist, after_checklist,
#                   before_clarify, after_clarify, before_constitution, after_constitution,
# Bundled bug extension events (when installed):
#                   before_bug_assess, after_bug_assess, before_bug_fix, after_bug_fix,
#                   before_bug_test, after_bug_test
hooks:
  after_tasks:
    - extension: jira
      command: speckit.jira.specstoissues
      enabled: true
      optional: true
      prompt: "Create Jira issues from tasks?"
```

See the [hook configuration contract](api.md#hook-configuration) for all fields
and current execution limitations.

---

## Troubleshooting

### Extension Not Found

**Error**: `Extension 'jira' not found in catalog`

**Solutions**:

1. Check spelling: `specify extension search jira`
2. Inspect the active catalogs: `specify extension catalog list`
3. Check internet connection
4. Extension may not be published yet

`specify extension search --help` displays help; it does not refresh cached
catalog data. Catalog caches normally expire after one hour. Python callers can
explicitly clear them with `ExtensionCatalog.clear_cache()`.

### Configuration Not Found

**Error**: `Jira configuration not found`

**Solutions**:

1. Check if extension is installed: `specify extension list`
2. Create config from template:

   ```bash
   cp .specify/extensions/jira/jira-config.template.yml \
      .specify/extensions/jira/jira-config.yml
   ```

3. Reinstall extension: `specify extension remove jira && specify extension add jira`

### Command Not Available

**Issue**: Extension command not appearing in coding agent

**Solutions**:

1. Check extension is enabled: `specify extension list`
2. Restart GitHub Copilot
3. Check the skill file exists:

   ```bash
   ls .github/skills/speckit-jira-*/SKILL.md
   ```

4. Reinstall extension

### Incompatible Version

**Error**: `Extension requires spec-kit >=0.2.0, but you have 0.1.0`

**Solutions**:

1. Upgrade spec-kit:

   ```bash
   uv tool upgrade specify-cli
   ```

2. Install older version of extension:

   ```bash
   specify extension add <extension-name> --from https://github.com/org/ext/archive/v1.0.0.zip
   ```

### MCP Tool Not Available

**Error**: `Tool 'jira-mcp-server/epic_create' not found`

**Solutions**:

1. Check MCP server is installed
2. Check coding agent MCP configuration
3. Restart coding agent
4. Check extension requirements: `specify extension info jira`

### Permission Denied

**Error**: `Permission denied` when accessing Jira

**Solutions**:

1. Check Jira credentials in MCP server config
2. Verify project permissions in Jira
3. Test MCP server connection independently

---

## Best Practices

### 1. Version Control

**Do commit**:

- `.specify/extensions.yml` (project extension config)
- `.specify/extensions/*/jira-config.yml` (project config)

**Don't commit**:

- `.specify/extensions/.cache/` (catalog cache)
- `.specify/extensions/.backup/` (config backups)
- `.specify/extensions/*/local-config.yml` (local overrides)
- `.specify/extensions/.registry` (installation state)

Add to `.gitignore`:

```gitignore
.specify/extensions/.cache/
.specify/extensions/.backup/
.specify/extensions/*/local-config.yml
.specify/extensions/.registry
```

### 2. Team Workflows

**For teams**:

1. Agree on which extensions to use
2. Commit extension configuration
3. Document extension usage in README
4. Keep extensions updated together

**Example README section**:

```markdown
## Extensions

This project uses:
- **jira** (v1.0.0) - Jira integration
  - Config: `.specify/extensions/jira/jira-config.yml`
  - Requires: jira-mcp-server

To install: `specify extension add jira`
```

### 3. Local Development

Use local config for development:

```yaml
# .specify/extensions/jira/local-config.yml
project:
  key: "DEVTEST"  # Your test project

defaults:
  task:
    custom_fields:
      customfield_10002: 1  # Lower story points for testing
```

### 4. Environment-Specific Config

Use environment variables for CI/CD:

```bash
# .github/workflows/deploy.yml
env:
  SPECKIT_JIRA_PROJECT_KEY: ${{ secrets.JIRA_PROJECT }}

- name: Create Jira Issues
  run: specify extension add jira && ...
```

### 5. Extension Updates

**Check for updates regularly**:

```bash
# Weekly or before major releases
specify extension update
```

**Select exact catalog versions for reproducible installation**:

```bash
specify extension add jira --version 1.0.0
```

Record the installation command for your team. The `installed` list in
`.specify/extensions.yml` is not a version-lock mechanism; explicitly running
`update` can install a newer version.

### 6. Minimal Extensions

Only install extensions you actively use:

- Reduces complexity
- Faster command loading
- Less configuration

### 7. Documentation

Document extension usage in your project:

```markdown
# PROJECT.md

## Working with Jira

After creating tasks, sync to Jira:
1. Run `/speckit-tasks` to generate tasks
2. Run `/speckit-jira-specstoissues` to create Jira issues
3. Run `/speckit-jira-sync-status` to update status
```

---

## FAQ

### Q: Can I use multiple extensions at once?

**A**: Yes! Extensions are designed to work together. Install as many as you need.

### Q: Do extensions slow down spec-kit?

**A**: Extension metadata is read during operations such as listing,
installation, and artifact resolution. Hooks can add work around Spec Kit
commands, and runtime events can run scripts during coding-agent lifecycle
events. Their cost depends on the installed extensions and configured behavior.

### Q: Can I create private extensions?

**A**: Yes. Install with `--dev` or `--from` and keep private. Public catalog submission is optional.

### Q: How do I know if an extension is safe?

**A**: A verified badge is not a code-audit guarantee. Spec Kit maintainers do
not review, audit, endorse, or support independently maintained extension code.
You must vet the source and release archive before installing; use extensions at
your own discretion.

### Q: Can extensions modify spec-kit core?

**A**: Extensions contribute commands, templates, scripts, hooks, and runtime
events without changing Spec Kit's source code. Their commands and hooks can
edit project files under their documented behavior and the project's governance;
see [Specification artifact maintenance](#specification-artifact-maintenance).

### Q: What happens if two extensions have the same command name?

**A**: Namespaced commands (`speckit.{extension}.{command}`) reduce conflicts.
Installation rejects exact command-name or alias collisions with installed
extensions, and normalized output-name collisions with core commands.
Resolution priority determines precedence for contributed artifacts such as
templates; it does not allow conflicting command names to be installed.
Use [`specify extension set-priority`](cli.md#set-extension-priority) to change
artifact resolution priority.

### Q: Can I contribute to existing extensions?

**A**: Yes! Most extensions are open source. Check the repository link in `specify extension info {extension}`.

### Q: How do I report extension bugs?

**A**: Go to the extension's repository (shown in `specify extension info`) and create an issue.

### Q: Can extensions work offline?

**A**: Once installed, extensions work offline. However, some extensions may require internet for their functionality (e.g., Jira requires Jira API access).

### Q: How do I backup my extension configuration?

**A**: Extension configs are in `.specify/extensions/{extension}/`. Back up this directory or commit configs to git.

---

## Support

- **Extension Issues**: Report to extension repository (see `specify extension info`)
- **Spec Kit Issues**: <https://github.com/github/spec-kit/issues>
- **Extension Catalog**: <https://github.com/github/spec-kit/tree/main/extensions>
- **Documentation**: See [Developing extensions](developing.md) and [Extension Publishing Guide](publishing.md)

---

*Last Updated: 2026-01-28*
*Spec Kit Version: 0.1.0*

> Agent invocation examples on this page use GitHub Copilot's default skills syntax (`/speckit-*`). For other integrations and modes, see [Command invocation](../integrations/cli.md#command-invocation).

## See also

- [Extension CLI reference](cli.md)
- [Extension catalogs](catalogs.md)
- [Community extensions](../community/extensions.md)
- [Developing extensions](developing.md)
- [Extension API reference](api.md)
- [Publishing extensions](publishing.md)
- [Spec persistence models](../concepts/spec-persistence.md)
