# Upgrade Guide

> You have Spec Kit installed and want to upgrade to the latest version to get new features, bug fixes, or updated slash commands. This guide covers both upgrading the CLI tool and updating your project files.

---

## Quick Reference

| What to Upgrade | Command | When to Use |
|----------------|---------|-------------|
| **CLI Tool (recommended)** | `specify self upgrade` | Latest stable release, in place. Auto-detects whether you installed via `uv tool` or `pipx`. |
| **CLI Tool — pin a version** | `specify self upgrade --tag vX.Y.Z[suffix]` | Upgrade to a specific release tag instead of the latest stable. Suffixes are limited to dev, alpha/beta/rc, and/or build metadata forms. |
| **CLI Tool — manual fallback** | `uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git@vX.Y.Z` | When `specify self upgrade` isn't available (older installs) or when you want explicit control. |
| **CLI Tool — manual fallback (pipx)** | `pipx install --force git+https://github.com/github/spec-kit.git@vX.Y.Z` | Same as above, for pipx installs. |
| **Project Files** | Run `specify integration upgrade <key>`, then `specify extension update` | Refresh installed integration files and extensions in your project |
| **Both** | Run CLI upgrade, then project update | Recommended for major version updates |

---

## Part 1: Upgrade the CLI Tool

The CLI tool (`specify`) is separate from your project files. Upgrade it to get the latest features and bug fixes.

### Recommended: `specify self upgrade`

The CLI ships with two self-management commands that handle the common case automatically:

```bash
# Check whether a newer release is available (read-only — does not modify anything)
specify self check

# Preview what would run, without actually upgrading
specify self upgrade --dry-run

# Upgrade in place to the latest stable release (auto-detects uv tool vs pipx install)
specify self upgrade

# Or pin a specific release tag (replace vX.Y.Z[suffix] with the tag you want)
specify self upgrade --tag vX.Y.Z[suffix]
```

Bare `specify self upgrade` executes immediately, matching the no-prompt behavior of commands like `pip install -U` and `npm update`. The CLI classifies your runtime into one of: `uv tool`, `pipx`, `uvx (ephemeral)`, source checkout, or unsupported. Only `uv tool` and `pipx` are upgraded automatically; for `uv tool` installs, it runs `uv tool install specify-cli --force --from <git ref>` under the hood so pinned release tags work. The other paths print path-specific guidance and exit 0 without touching anything.

Pinned tags must start with `vMAJOR.MINOR.PATCH`. Optional suffixes are limited to dev, alpha/beta/rc, and/or build metadata forms such as `v1.0.0-rc1`, `v0.8.0.dev0`, `v0.8.0+build.42`, or the combination `v1.0.0-rc1+build.42`; branch names, hash refs, `latest`, and bare versions without `v` are rejected.

Set `SPECIFY_UPGRADE_TIMEOUT_SECS` to cap how long the installer subprocess may run (default: no timeout — interrupt with `Ctrl+C` if needed). If that internal timeout fires, `specify self upgrade` exits 124 and reports that it timed out while waiting for the installer subprocess, including the configured timeout and manual retry command. A real installer exit code 124 is propagated with `Upgrade failed. Installer exit code: 124.`, so scripts should treat exit 124 as ambiguous and inspect the message when they need to distinguish the two cases.

If your installed CLI is older than the release that introduced `specify self upgrade`, use the manual equivalents below. These commands are also useful when you want explicit control over the installer command.

### If you installed with `uv tool install`

Upgrade to a specific release (check [Releases](https://github.com/github/spec-kit/releases) for the latest tag):

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

### If you use one-shot `uvx` commands

Specify the desired release tag:

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init --here --integration copilot
```

`uvx` runs a temporary copy of Spec Kit for that single command. It does not update a persistent `specify` installed with `uv tool install`, `pipx`, or another tool manager. If a newer feature works through `uvx` but your local `specify` still reports an older version, upgrade the persistent CLI with the command that matches your install method.

### If you installed with `pipx`

Upgrade to a specific release:

```bash
pipx install --force git+https://github.com/github/spec-kit.git@vX.Y.Z
```

### Verify the upgrade

```bash
# Confirms the CLI is working and shows installed tools
specify check

# Confirms the installed version against the latest GitHub release
specify self check
```

`specify check` shows the surrounding tool environment; `specify self check` is read-only and tells you whether you're now on the latest release (`Up to date: X.Y.Z`) or if a newer one became available between releases.

---

## Part 2: Updating Project Files

When Spec Kit releases new features (like new slash commands, updated templates, or extension changes), you need to refresh the Spec Kit files that were installed into your project.

### What gets updated?

For existing Spec Kit projects, use the manifest-aware upgrade path first:

- ✅ **Integration command/skill files** (`.claude/skills/`, `.github/prompts/`, `.agents/skills/`, etc.)
- ✅ **Managed shared scripts and templates** (`.specify/scripts/`, `.specify/templates/`) when they are unchanged from the previous managed copy
- ✅ **Installed extensions** when you run `specify extension update`

The integration upgrade command uses the install manifest to detect local edits. If a managed integration file was modified after install, the command stops and asks you to inspect the change or rerun with `--force`.

### What stays safe?

These files are **never touched** by the manifest-aware integration/extension upgrade path:

- ✅ **Your specifications** (`specs/001-my-feature/spec.md`, etc.) - **CONFIRMED SAFE**
- ✅ **Your implementation plans** (`specs/001-my-feature/plan.md`, `tasks.md`, etc.) - **CONFIRMED SAFE**
- ✅ **Your constitution** (`.specify/memory/constitution.md`) when using `specify integration upgrade`
- ✅ **Your source code** - **CONFIRMED SAFE**
- ✅ **Your git history** - **CONFIRMED SAFE**

The `specs/` directory is completely excluded from template packages and will never be modified during upgrades.

### 1. Check installed integrations

Run this inside your project directory:

```bash
specify integration status
```

This reports the default integration, all installed integrations, and any modified or missing managed files. You can also inspect `.specify/integration.json`; installed integrations are listed under `installed_integrations`.

### 2. Upgrade each installed integration

Run this inside your project directory:

```bash
specify integration upgrade <key>
```

Replace `<key>` with an installed integration key such as `copilot`, `claude`, or `codex`. In projects with multiple installed integrations, run the command once per installed key.

**Example:**

```bash
specify integration upgrade claude
specify integration upgrade codex
```

See the [integration reference](reference/integrations.md#upgrade-an-integration) for options such as `--script`, `--integration-options`, and `--force`.

### 3. Update installed extensions

Run:

```bash
specify extension update
```

With no extension argument, this updates all installed extensions. Use `specify extension update <extension-id-or-name>` to update only one extension. See the [extensions reference](reference/extensions.md#update-extensions) for details.

### Fallback: re-run init

If a project predates manifests, has missing integration metadata, or needs a broader recovery, you can still re-run init:

```bash
specify init --here --force --integration <your-agent>
```

Use this as an escape hatch rather than the default project-file upgrade path. It refreshes the selected integration and shared project scaffolding, but it does not use the same per-integration manifest checks before overwriting files.

## ⚠️ Important Warnings

### 1. Constitution file and memory customizations

`specify integration upgrade <key>` does not update `.specify/memory/constitution.md`.

The fallback `specify init --here --force --integration <your-agent>` path also preserves an existing `.specify/memory/constitution.md`; if the file is missing, init creates it from the current constitution template. You do not need a constitution backup/restore step for the manifest-aware upgrade path.

As with any broad fallback refresh, commit or back up local customizations before using `init --here --force` so you can review the resulting diff.

### 2. Custom integration, script, or template modifications

`specify integration upgrade <key>` blocks when manifest-tracked integration files were modified locally, unless you pass `--force`.

Shared scripts and templates are refreshed when they still match the previously recorded managed copy. Local customizations are preserved unless you explicitly use a force/refresh option that overwrites them. If you customized files in `.specify/scripts/` or `.specify/templates/`, commit or back them up first:

```bash
# Back up custom templates and scripts
cp -r .specify/templates .specify/templates-backup
cp -r .specify/scripts .specify/scripts-backup

# After upgrade, merge your changes back manually
```

### 3. Duplicate slash commands (IDE-based agents)

Some IDE-based agents (like Kilo Code, Cline) may show **duplicate slash commands** after upgrading—both old and new versions appear.

**Solution:** Manually delete the old command files from your agent's folder.

**Example for Kilo Code:**

```bash
# Navigate to the agent's commands folder
cd .kilocode/workflows/

# List files and identify duplicates
ls -la

# Delete old versions (example filenames - yours may differ)
rm speckit.specify-old.md
rm speckit.plan-v1.md
```

Restart your IDE to refresh the command list.

---

## Common Scenarios

### Scenario 1: "I just want new slash commands"

```bash
# Upgrade CLI (auto-detects uv tool vs pipx install)
specify self upgrade

# Inspect installed integrations
specify integration status

# Update project files to get new commands
specify integration upgrade <key>
specify extension update
```

### Scenario 2: "I customized templates and constitution"

```bash
# 1. Commit or back up customizations
git status
cp -r .specify/templates /tmp/templates-backup

# 2. Upgrade CLI
specify self upgrade

# 3. Use the manifest-aware project update first
specify integration upgrade <key>
specify extension update

# 4. If the upgrade reports modified managed files, inspect the diff before using --force
```

### Scenario 3: "I see duplicate slash commands in my IDE"

This happens with IDE-based agents (Kilo Code, Cline, etc.).

```bash
# Find the agent folder (example: .kilocode/workflows/)
cd .kilocode/workflows/

# List all files
ls -la

# Delete old command files
rm speckit.old-command-name.md

# Restart your IDE
```

### Scenario 4: "I don't want the git extension"

The git extension is now opt-in, so upgrades do not install it unless you add it explicitly.

```bash
# Upgrade CLI
specify self upgrade

# Refresh integration files and installed extensions
specify integration upgrade <key>
specify extension update

# The git extension is not added unless you run `specify extension add git`
```

If you later decide you want the git extension's commands and hooks, install it explicitly:

```bash
specify extension add git
```

Projects that do not use Git can still work with Spec Kit by setting `SPECIFY_FEATURE_DIRECTORY` to the feature directory path before planning commands:

```bash
# Bash/Zsh
export SPECIFY_FEATURE_DIRECTORY="specs/001-my-feature"

# PowerShell
$env:SPECIFY_FEATURE_DIRECTORY = "specs/001-my-feature"
```

Alternatively, run the `/speckit.specify` command which creates `.specify/feature.json` automatically.

---

## Troubleshooting

### "Slash commands not showing up after upgrade"

**Cause:** Agent didn't reload the command files.

**Fix:**

1. **Restart your IDE/editor** completely (not just reload window)
2. **For CLI-based agents**, verify files exist:

   ```bash
   ls -la .claude/commands/      # Claude Code
   ls -la .gemini/commands/      # Gemini
   ls -la .cursor/skills/      # Cursor
   ls -la .pi/prompts/           # Pi Coding Agent
   ls -la .omp/commands/         # Oh My Pi
   ```

3. **Check agent-specific setup:**
   - Codex requires `CODEX_HOME` environment variable
   - Some agents need workspace restart or cache clearing

### "Will init overwrite my constitution customizations?"

Current `specify init --here --force` preserves an existing `.specify/memory/constitution.md`; it creates the file from the template only when it is missing.

If you previously lost constitution changes through an older workflow or manual replacement, restore from git or backup:

```bash
# If you committed the customized constitution
git restore .specify/memory/constitution.md

# If you backed up manually
cp /tmp/constitution-backup.md .specify/memory/constitution.md
```

**Prevention:** Use `specify integration upgrade <key>` for routine project-file updates. If you need the fallback `specify init --here --force` path, commit first so you can review the full diff afterward.

### "Warning: Current directory is not empty"

**Full warning message:**

```text
Warning: Current directory is not empty (25 items)
Template files will be merged with existing content and may overwrite existing files
Do you want to continue? [y/N]
```

**What this means:**

This warning appears when you run `specify init --here` (or `specify init .`) in a directory that already has files. It's telling you:

1. **The directory has existing content** - In the example, 25 files/folders
2. **Files will be merged** - New template files will be added alongside your existing files
3. **Some files may be overwritten** - If you already have Spec Kit files (`.claude/`, `.specify/`, etc.), they'll be replaced with the new versions

**What gets overwritten:**

Only Spec Kit infrastructure files:

- Agent command files (`.claude/commands/`, `.github/prompts/`, etc.)
- Scripts in `.specify/scripts/`
- Templates in `.specify/templates/`
- Missing memory files such as `.specify/memory/constitution.md` may be created from templates; an existing constitution is preserved

**What stays untouched:**

- Your `specs/` directory (specifications, plans, tasks)
- Your source code files
- Your `.git/` directory and git history
- Any other files not part of Spec Kit templates

**How to respond:**

- **Type `y` and press Enter** - Proceed with the merge when using the fallback init path
- **Type `n` and press Enter** - Cancel the operation
- **Use `--force` flag** - Skip this confirmation entirely:

  ```bash
  specify init --here --force --integration copilot
  ```

**When you see this warning:**

- ✅ **Expected** when using the fallback init path in an existing Spec Kit project
- ✅ **Expected** when adding Spec Kit to an existing codebase
- ⚠️ **Unexpected** if you thought you were creating a new project in an empty directory

**Prevention tip:** Before using the fallback init path, commit your current work so any refreshed files are easy to review or restore.

### "CLI upgrade doesn't seem to work"

If a command behaves like an older Spec Kit version, first ask the CLI itself:

```bash
# Read-only — prints "Up to date: X.Y.Z" or "Update available: X.Y.Z → vY.Z.W"
specify self check

# Preview the install method, current version, and target tag the upgrade would use
specify self upgrade --dry-run
```

`specify check` is an offline environment scan; `specify self check` is the CLI version lookup.

If `self check` shows the wrong version, verify the installation:

```bash
# Check installed tools
uv tool list

# Should show specify-cli

# Verify path
which specify

# Should point to the uv tool installation directory
```

If not found, reinstall:

```bash
uv tool uninstall specify-cli
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

### "Do I need to run specify every time I open my project?"

**Short answer:** No, you only run `specify init` once per project, or later as a fallback recovery path.

**Explanation:**

The `specify` CLI tool is used for:

- **Initial setup:** `specify init` to bootstrap Spec Kit in your project
- **Routine project-file upgrades:** `specify integration upgrade <key>` and `specify extension update`
- **Fallback recovery:** `specify init --here --force` when integration metadata is missing or the manifest-aware path cannot be used
- **Diagnostics:** `specify check` to verify tool installation

Once you've run `specify init`, the slash commands (like `/speckit.specify`, `/speckit.plan`, etc.) are **permanently installed** in your project's agent folder (`.claude/`, `.github/prompts/`, `.pi/prompts/`, `.omp/commands/`, etc.). Your AI coding agent reads these command files directly—no need to run `specify` again.

**If your agent isn't recognizing slash commands:**

1. **Verify command files exist:**

   ```bash
   # For GitHub Copilot
   ls -la .github/prompts/

   # For Claude
   ls -la .claude/commands/

   # For Pi
   ls -la .pi/prompts/

   # For Oh My Pi
   ls -la .omp/commands/
   ```

2. **Restart your IDE/editor completely** (not just reload window)

3. **Check you're in the correct directory** where you ran `specify init`

4. **For some agents**, you may need to reload the workspace or clear cache

**Related issue:** If Copilot can't open local files or uses PowerShell commands unexpectedly, this is typically an IDE context issue, not related to `specify`. Try:

- Restarting VS Code
- Checking file permissions
- Ensuring the workspace folder is properly opened

---

## Version Compatibility

Spec Kit follows semantic versioning for major releases. The CLI and project files are designed to be compatible within the same major version.

**Best practice:** Keep both CLI and project files in sync by upgrading both together during major version changes.

---

## Next Steps

After upgrading:

- **Test new slash commands:** Run `/speckit.constitution` or another command to verify everything works
- **Review release notes:** Check [GitHub Releases](https://github.com/github/spec-kit/releases) for new features and breaking changes
- **Update workflows:** If new commands were added, update your team's development workflows
- **Check documentation:** Visit [github.io/spec-kit](https://github.github.io/spec-kit/) for updated guides
