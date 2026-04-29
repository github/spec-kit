# AGENTS.md

## About Spec Kit and Specify

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework. It sets up the necessary directory structures, templates, and AI agent integrations to support the Spec-Driven Development workflow.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## Integration Architecture

Each AI agent is a self-contained **integration subpackage** under `src/specify_cli/integrations/<key>/`. The subpackage exposes a single class that declares all metadata and inherits setup/teardown logic from a base class. Built-in integrations are then instantiated and added to the global `INTEGRATION_REGISTRY` by `src/specify_cli/integrations/__init__.py` via `_register_builtins()`.

```
src/specify_cli/integrations/
├── __init__.py            # INTEGRATION_REGISTRY + _register_builtins()
├── base.py                # IntegrationBase, MarkdownIntegration, TomlIntegration, YamlIntegration, SkillsIntegration
├── manifest.py            # IntegrationManifest (file tracking)
├── claude/                # Example: SkillsIntegration subclass
│   ├── __init__.py        #   ClaudeIntegration class
│   └── scripts/           #   Thin wrapper scripts
│       ├── update-context.sh
│       └── update-context.ps1
├── gemini/                # Example: TomlIntegration subclass
│   ├── __init__.py
│   └── scripts/
├── windsurf/              # Example: MarkdownIntegration subclass
│   ├── __init__.py
│   └── scripts/
├── copilot/               # Example: IntegrationBase subclass (custom setup)
│   ├── __init__.py
│   └── scripts/
└── ...                    # One subpackage per supported agent
```

The registry is the **single source of truth for Python integration metadata**. Supported agents, their directories, formats, and capabilities are derived from the integration classes for the Python integration layer. However, context-update behavior still requires explicit cases in the shared dispatcher scripts (`scripts/bash/update-agent-context.sh` and `scripts/powershell/update-agent-context.ps1`), which currently maintain their own supported-agent lists and agent-key→context-file mappings until they are migrated to registry-based dispatch.

---

## Adding a New Integration

### 1. Choose a base class

| Your agent needs… | Subclass |
|---|---|
| Standard markdown commands (`.md`) | `MarkdownIntegration` |
| TOML-format commands (`.toml`) | `TomlIntegration` |
| YAML recipe files (`.yaml`) | `YamlIntegration` |
| Skill directories (`speckit-<name>/SKILL.md`) | `SkillsIntegration` |
| Fully custom output (companion files, settings merge, etc.) | `IntegrationBase` directly |

Most agents only need `MarkdownIntegration` — a minimal subclass with zero method overrides.

### 2. Create the subpackage

Create `src/specify_cli/integrations/<package_dir>/__init__.py`, where `<package_dir>` is the Python-safe directory name derived from `<key>`: use the key as-is when it contains no hyphens (e.g., key `"gemini"` → `gemini/`), or replace hyphens with underscores when it does (e.g., key `"kiro-cli"` → `kiro_cli/`). The `IntegrationBase.key` class attribute always retains the original hyphenated value, since that is what the CLI and registry use. For CLI-based integrations (`requires_cli: True`), the `key` should match the actual CLI tool name (the executable users install and run) so CLI checks can resolve it correctly. For IDE-based integrations (`requires_cli: False`), use the canonical integration identifier instead.

**Minimal example — Markdown agent (Windsurf):**

```python
"""Windsurf IDE integration."""

from ..base import MarkdownIntegration


class WindsurfIntegration(MarkdownIntegration):
    key = "windsurf"
    config = {
        "name": "Windsurf",
        "folder": ".windsurf/",
        "commands_subdir": "workflows",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".windsurf/workflows",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = ".windsurf/rules/specify-rules.md"
```

**TOML agent (Gemini):**

```python
"""Gemini CLI integration."""

from ..base import TomlIntegration


class GeminiIntegration(TomlIntegration):
    key = "gemini"
    config = {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".gemini/commands",
        "format": "toml",
        "args": "{{args}}",
        "extension": ".toml",
    }
    context_file = "GEMINI.md"
```

**Skills agent (Codex):**

```python
"""Codex CLI integration — skills-based agent."""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class CodexIntegration(SkillsIntegration):
    key = "codex"
    config = {
        "name": "Codex CLI",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Codex)",
            ),
        ]
```

#### Required fields

| Field | Location | Purpose |
|---|---|---|
| `key` | Class attribute | Unique identifier; for CLI-based integrations (`requires_cli: True`), must match the CLI executable name |
| `config` | Class attribute (dict) | Agent metadata: `name`, `folder`, `commands_subdir`, `install_url`, `requires_cli` |
| `registrar_config` | Class attribute (dict) | Command output config: `dir`, `format`, `args` placeholder, file `extension` |
| `context_file` | Class attribute (str or None) | Path to agent context/instructions file (e.g., `"CLAUDE.md"`, `".github/copilot-instructions.md"`) |

**Key design rule:** For CLI-based integrations (`requires_cli: True`), `key` must be the actual executable name (e.g., `"cursor-agent"` not `"cursor"`). This ensures `shutil.which(key)` works for CLI-tool checks without special-case mappings. IDE-based integrations (`requires_cli: False`) should use their canonical identifier (e.g., `"windsurf"`, `"copilot"`).

### 3. Register it

In `src/specify_cli/integrations/__init__.py`, add one import and one `_register()` call inside `_register_builtins()`. Both lists are alphabetical:

```python
def _register_builtins() -> None:
    # -- Imports (alphabetical) -------------------------------------------
    from .claude import ClaudeIntegration
    # ...
    from .newagent import NewAgentIntegration   # ← add import
    # ...

    # -- Registration (alphabetical) --------------------------------------
    _register(ClaudeIntegration())
    # ...
    _register(NewAgentIntegration())            # ← add registration
    # ...
```

### 4. Add scripts

Create two thin wrapper scripts in `src/specify_cli/integrations/<package_dir>/scripts/` that delegate to the shared context-update scripts. Each is ~25 lines of boilerplate.

> **Note on `<package_dir>` vs `<key>`:** `<package_dir>` is the Python-safe directory name for your integration — it matches `<key>` exactly when the key contains no hyphens (e.g., key `"gemini"` → `gemini/`), but uses underscores when it does (e.g., key `"kiro-cli"` → `kiro_cli/`). The `IntegrationBase.key` class attribute always retains the original hyphenated value (e.g., `key = "kiro-cli"`), since that is what the CLI and registry use.

**`update-context.sh`:**

```bash
#!/usr/bin/env bash
# update-context.sh — <Agent Name> integration: create/update <context_file>
set -euo pipefail

_script_dir="$(cd "$(dirname "$0")" && pwd)"
_root="$_script_dir"
while [ "$_root" != "/" ] && [ ! -d "$_root/.specify" ]; do _root="$(dirname "$_root")"; done
if [ -z "${REPO_ROOT:-}" ]; then
  if [ -d "$_root/.specify" ]; then
    REPO_ROOT="$_root"
  else
    git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [ -n "$git_root" ] && [ -d "$git_root/.specify" ]; then
      REPO_ROOT="$git_root"
    else
      REPO_ROOT="$_root"
    fi
  fi
fi

exec "$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh" <key>
```

**`update-context.ps1`:**

```powershell
# update-context.ps1 — <Agent Name> integration: create/update <context_file>
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = try { git rev-parse --show-toplevel 2>$null } catch { $null }
if (-not $repoRoot -or -not (Test-Path (Join-Path $repoRoot '.specify'))) {
    $repoRoot = $scriptDir
    $fsRoot = [System.IO.Path]::GetPathRoot($repoRoot)
    while ($repoRoot -and $repoRoot -ne $fsRoot -and -not (Test-Path (Join-Path $repoRoot '.specify'))) {
        $repoRoot = Split-Path -Parent $repoRoot
    }
}

& "$repoRoot/.specify/scripts/powershell/update-agent-context.ps1" -AgentType <key>
```

Replace `<key>` with your integration key and `<Agent Name>` / `<context_file>` with the appropriate values.

You must also add the agent to the shared context-update scripts so the shared dispatcher recognises the new key:

- **`scripts/bash/update-agent-context.sh`** — add a file-path variable and a case in `update_specific_agent()`.
- **`scripts/powershell/update-agent-context.ps1`** — add a file-path variable, add the new key to the `AgentType` parameter's `[ValidateSet(...)]`, add a switch case in `Update-SpecificAgent`, and add an entry in `Update-AllExistingAgents`.

### 5. Test it

```bash
# Install into a test project
specify init my-project --integration <key>

# Verify files were created in the commands directory configured by
# config["folder"] + config["commands_subdir"] (for example, .windsurf/workflows/)
ls -R my-project/.windsurf/workflows/

# Uninstall cleanly
cd my-project && specify integration uninstall <key>
```

Each integration also has a dedicated test file at `tests/integrations/test_integration_<key>.py`. Note that hyphens in the key are replaced with underscores in the filename (e.g., key `cursor-agent` → `test_integration_cursor_agent.py`, key `kiro-cli` → `test_integration_kiro_cli.py`). Run it with:

```bash
pytest tests/integrations/test_integration_<key_with_underscores>.py -v
```

### 6. Optional overrides

The base classes handle most work automatically. Override only when the agent deviates from standard patterns:

| Override | When to use | Example |
|---|---|---|
| `command_filename(template_name)` | Custom file naming or extension | Copilot → `speckit.{name}.agent.md` |
| `options()` | Integration-specific CLI flags via `--integration-options` | Codex → `--skills` flag, Copilot → `--skills` flag |
| `setup()` | Custom install logic (companion files, settings merge) | Copilot → `.agent.md` + `.prompt.md` + `.vscode/settings.json` (default) or `speckit-<name>/SKILL.md` (skills mode) |
| `teardown()` | Custom uninstall logic | Rarely needed; base handles manifest-tracked files |

**Example — Copilot (fully custom `setup`):**

Copilot extends `IntegrationBase` directly because it creates `.agent.md` commands, companion `.prompt.md` files, and merges `.vscode/settings.json`. It also supports a `--skills` mode that scaffolds `speckit-<name>/SKILL.md` under `.github/skills/` using composition with an internal `_CopilotSkillsHelper`. See `src/specify_cli/integrations/copilot/__init__.py` for the full implementation.

### 7. Update Devcontainer files (Optional)

For agents that have VS Code extensions or require CLI installation, update the devcontainer configuration files:

#### VS Code Extension-based Agents

For agents available as VS Code extensions, add them to `.devcontainer/devcontainer.json`:

```jsonc
{
  "customizations": {
    "vscode": {
      "extensions": [
        // ... existing extensions ...
        "[New Agent Extension ID]"
      ]
    }
  }
}
```

#### CLI-based Agents

For agents that require CLI tools, add installation commands to `.devcontainer/post-create.sh`:

```bash
#!/bin/bash

# Existing installations...

echo -e "\n🤖 Installing [New Agent Name] CLI..."
# run_command "npm install -g [agent-cli-package]@latest"
echo "✅ Done"
```

---

## Command File Formats

### Markdown Format

**Standard format:**

```markdown
---
description: "Command description"
---

Command content with {SCRIPT} and $ARGUMENTS placeholders.
```

**GitHub Copilot Chat Mode format:**

```markdown
---
description: "Command description"
mode: speckit.command-name
---

Command content with {SCRIPT} and $ARGUMENTS placeholders.
```

### TOML Format

```toml
description = "Command description"

prompt = """
Command content with {SCRIPT} and {{args}} placeholders.
"""
```

### YAML Format

Used by: Goose

```yaml
version: 1.0.0
title: "Command Title"
description: "Command description"
author:
  contact: spec-kit
extensions:
  - type: builtin
    name: developer
activities:
  - Spec-Driven Development
prompt: |
  Command content with {SCRIPT} and {{args}} placeholders.
```

## Argument Patterns

Different agents use different argument placeholders. The placeholder used in command files is always taken from `registrar_config["args"]` for each integration — check there first when in doubt:

- **Markdown/prompt-based**: `$ARGUMENTS` (default for most markdown agents)
- **TOML-based**: `{{args}}` (e.g., Gemini)
- **YAML-based**: `{{args}}` (e.g., Goose)
- **Custom**: some agents override the default (e.g., Forge uses `{{parameters}}`)
- **Script placeholders**: `{SCRIPT}` (replaced with actual script path)
- **Agent placeholders**: `__AGENT__` (replaced with agent name)

## Special Processing Requirements

Some agents require custom processing beyond the standard template transformations:

### Copilot Integration

GitHub Copilot has unique requirements:
- Commands use `.agent.md` extension (not `.md`)
- Each command gets a companion `.prompt.md` file in `.github/prompts/`
- Installs `.vscode/settings.json` with prompt file recommendations
- Context file lives at `.github/copilot-instructions.md`

Implementation: Extends `IntegrationBase` with custom `setup()` method that:
1. Processes templates with `process_template()`
2. Generates companion `.prompt.md` files
3. Merges VS Code settings

**Skills mode (`--skills`):** Copilot also supports an alternative skills-based layout
via `--integration-options="--skills"`. When enabled:
- Commands are scaffolded as `speckit-<name>/SKILL.md` under `.github/skills/`
- No companion `.prompt.md` files are generated
- No `.vscode/settings.json` merge
- `post_process_skill_content()` injects a `mode: speckit.<stem>` frontmatter field
- `build_command_invocation()` returns `/speckit-<stem>` instead of bare args

The two modes are mutually exclusive — a project uses one or the other:

```bash
# Default mode: .agent.md agents + .prompt.md companions + settings merge
specify init my-project --integration copilot

# Skills mode: speckit-<name>/SKILL.md under .github/skills/
specify init my-project --integration copilot --integration-options="--skills"
```

### Forge Integration

Forge has special frontmatter and argument requirements:
- Uses `{{parameters}}` instead of `$ARGUMENTS`
- Strips `handoffs` frontmatter key (Forge-specific collaboration feature)
- Injects `name` field into frontmatter when missing

Implementation: Extends `MarkdownIntegration` with custom `setup()` method that:
1. Inherits standard template processing from `MarkdownIntegration`
2. Adds extra `$ARGUMENTS` → `{{parameters}}` replacement after template processing
3. Applies Forge-specific transformations via `_apply_forge_transformations()`
4. Strips `handoffs` frontmatter key
5. Injects missing `name` fields
6. Ensures the shared `update-agent-context.*` scripts include a `forge` case that maps context updates to `AGENTS.md` and lists `forge` in their usage/help text

### Goose Integration

Goose is a YAML-format agent using Block's recipe system:
- Uses `.goose/recipes/` directory for YAML recipe files
- Uses `{{args}}` argument placeholder
- Produces YAML with `prompt: |` block scalar for command content

Implementation: Extends `YamlIntegration` (parallel to `TomlIntegration`):
1. Processes templates through the standard placeholder pipeline
2. Extracts title and description from frontmatter
3. Renders output as Goose recipe YAML (version, title, description, author, extensions, activities, prompt)
4. Uses `yaml.safe_dump()` for header fields to ensure proper escaping
5. Context updates map to `AGENTS.md` (shared with opencode/codex/pi/forge)

## Common Pitfalls

1. **Using shorthand keys for CLI-based integrations**: For CLI-based integrations (`requires_cli: True`), the `key` must match the executable name (e.g., `"cursor-agent"` not `"cursor"`). `shutil.which(key)` is used for CLI tool checks — mismatches require special-case mappings. IDE-based integrations (`requires_cli: False`) are not subject to this constraint.
2. **Forgetting update scripts**: Both bash and PowerShell thin wrappers and the shared context-update scripts must be updated.
3. **Incorrect `requires_cli` value**: Set to `True` only for agents that have a CLI tool; set to `False` for IDE-based agents.
4. **Wrong argument format**: Use `$ARGUMENTS` for Markdown agents, `{{args}}` for TOML agents.
5. **Skipping registration**: The import and `_register()` call in `_register_builtins()` must both be added.

---

*This documentation should be updated whenever new integrations are added to maintain accuracy and completeness.*
