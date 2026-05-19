# AGENTS.md

## About Spec Kit and Specify

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) — a methodology that requires writing clear, structured specifications *before* any implementation begins. The toolkit provides templates, scripts, and workflows that guide development teams through a consistent, repeatable process for building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework. It sets up directory structures, installs command templates, and wires up AI agent integrations so that every project starts from a well-defined, consistent foundation.

The toolkit is designed to be agent-agnostic: teams can use their preferred AI coding assistant (Claude, Copilot, Gemini, Codex, Windsurf, and others) while maintaining a shared project structure and development workflow.

---

## Quickstart — Add a New Integration in 5 Steps

If you are new to the codebase and want to add support for a new AI agent, here is the shortest path from zero to a working integration:

1. **Choose a base class** — most agents only need `MarkdownIntegration`. See the [Base Class Reference](#base-class-reference) section for guidance.
2. **Create a subpackage** — add `src/specify_cli/integrations/<your_agent>/__init__.py` with the required fields.
3. **Register it** — add one import and one `_register()` call in `src/specify_cli/integrations/__init__.py`.
4. **Write a test file** — create `tests/integrations/test_integration_<your_agent>.py`.
5. **Run and verify** — use `specify init` to test the full install/uninstall cycle.

The sections below cover each step in detail. A complete, end-to-end example is also provided in [Full Example: Adding `mycli`](#full-example-adding-mycli).

---

## Integration Architecture

Each AI agent is a self-contained **integration subpackage** under `src/specify_cli/integrations/<key>/`. The subpackage exposes a single class that declares all metadata and inherits setup/teardown logic from a shared base class. All built-in integrations are then instantiated and added to the global `INTEGRATION_REGISTRY` via `_register_builtins()` in `src/specify_cli/integrations/__init__.py`.

```
src/specify_cli/integrations/
├── __init__.py            # INTEGRATION_REGISTRY + _register_builtins()
├── base.py                # IntegrationBase, MarkdownIntegration, TomlIntegration, YamlIntegration, SkillsIntegration
├── manifest.py            # IntegrationManifest (file tracking for clean uninstall)
├── claude/
│   └── __init__.py        # ClaudeIntegration — SkillsIntegration subclass
├── gemini/
│   └── __init__.py        # GeminiIntegration — TomlIntegration subclass
├── windsurf/
│   └── __init__.py        # WindsurfIntegration — MarkdownIntegration subclass
├── copilot/
│   └── __init__.py        # CopilotIntegration — IntegrationBase subclass (custom setup)
└── ...                    # One subpackage per supported agent
```

The `INTEGRATION_REGISTRY` is the **single source of truth** for all Python integration metadata. Supported agents, their output directories, file formats, capabilities, and context file paths are all derived from the integration class definitions.

---

## Base Class Reference

Choosing the right base class is the most important decision when adding a new integration. The table below summarizes each option and when to use it.

| Base Class | File Format | When to Use |
|---|---|---|
| `MarkdownIntegration` | `.md` | Standard agents that read Markdown command files. The default choice for most agents. |
| `TomlIntegration` | `.toml` | Agents that use TOML-format command definitions (e.g., Gemini CLI). |
| `YamlIntegration` | `.yaml` | Agents that use YAML recipe files (e.g., Goose). |
| `SkillsIntegration` | `SKILL.md` | Agents that organize capabilities as named skill directories (e.g., Claude, Codex). |
| `IntegrationBase` | Custom | Agents with fully custom output (companion files, settings merges, non-standard layouts). Extend this only when none of the above fit. |

### Method Reference

Each base class provides the following methods. You only need to override a method when the agent deviates from the standard behavior.

| Method | Default Behavior | Override When |
|---|---|---|
| `setup()` | Processes templates, writes command files, updates the context file | The agent needs companion files, settings merges, or non-standard file layouts |
| `teardown()` | Removes all files tracked by the integration manifest | The agent created files outside the standard manifest (rare) |
| `command_filename(template_name)` | Returns `<template_name><extension>` | The agent uses a different naming convention (e.g., Copilot uses `speckit.<name>.agent.md`) |
| `options()` | Returns an empty list (no extra CLI flags) | The agent supports integration-specific install options (e.g., `--skills` for Codex) |
| `process_template(content)` | Replaces `{SCRIPT}`, `$ARGUMENTS`, and `__AGENT__` placeholders | The agent uses non-standard placeholders (e.g., Forge uses `{{parameters}}`) |

> **Rule of thumb:** Start with `MarkdownIntegration` and zero overrides. Only add custom logic when a specific behavior cannot be achieved with the defaults.

---

## IntegrationManifest — File Tracking

`manifest.py` provides the `IntegrationManifest` class, which tracks every file created during `setup()`. This record is what makes `teardown()` reliable and safe.

### How it works

When `setup()` installs files, it registers each file path with the manifest:

```python
self.manifest.add("path/to/command.md")
self.manifest.add("path/to/context.md")
```

The manifest is persisted to a hidden file inside the integration's folder (e.g., `.windsurf/.specify-manifest.json`). When the user runs `specify integration uninstall <key>`, `teardown()` reads the manifest and removes only the files that belong to this integration. Files that the user created manually are never touched.

### Why this matters

Without the manifest, uninstall would either:
- Remove files it should not (destructive), or
- Leave files behind (messy)

The manifest solves both problems. If you are writing a custom `setup()` method, always register every file you create with `self.manifest.add(path)`.

---

## Adding a New Integration

### Step 1 — Choose a base class

Refer to the [Base Class Reference](#base-class-reference) table above.

### Step 2 — Create the subpackage

Create `src/specify_cli/integrations/<package_dir>/__init__.py`.

**Naming rules:**
- If the key has no hyphens, use it directly as the directory name: key `"gemini"` → `gemini/`
- If the key contains hyphens, replace them with underscores: key `"kiro-cli"` → `kiro_cli/`
- The `key` class attribute always retains the original value (including hyphens), because the CLI and registry use it directly.

#### Required fields

Every integration class must define the following:

| Field | Type | Purpose |
|---|---|---|
| `key` | `str` | Unique identifier. For CLI-based integrations, must match the executable name (used by `shutil.which()`). |
| `config` | `dict` | Agent metadata: `name`, `folder`, `commands_subdir`, `install_url`, `requires_cli`. |
| `registrar_config` | `dict` | Output configuration: `dir`, `format`, `args` placeholder, `extension`. |
| `context_file` | `str` or `None` | Path to the agent's context/instructions file (e.g., `"CLAUDE.md"`). |

#### Example — Standard Markdown agent (Windsurf)

Use this as your starting template for most agents. No method overrides required.

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
        "requires_cli": False,    # IDE plugin, not a CLI tool
    }
    registrar_config = {
        "dir": ".windsurf/workflows",
        "format": "markdown",
        "args": "$ARGUMENTS",     # Standard placeholder for markdown agents
        "extension": ".md",
    }
    context_file = ".windsurf/rules/specify-rules.md"
```

#### Example — TOML agent (Gemini CLI)

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
        "requires_cli": True,     # Installed as a CLI tool; key must match executable name
    }
    registrar_config = {
        "dir": ".gemini/commands",
        "format": "toml",
        "args": "{{args}}",       # TOML agents use double-brace syntax
        "extension": ".toml",
    }
    context_file = "GEMINI.md"
```

#### Example — Skills agent (Codex)

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
        "extension": "/SKILL.md",  # Each skill is a directory with a SKILL.md file
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

### Step 3 — Register the integration

Open `src/specify_cli/integrations/__init__.py` and add your integration in two places. Both lists are kept in **alphabetical order**.

```python
def _register_builtins() -> None:
    # -- Imports (alphabetical) -------------------------------------------
    from .claude import ClaudeIntegration
    from .codex import CodexIntegration
    from .gemini import GeminiIntegration
    from .mycli import MycliIntegration       # ← add your import here
    from .windsurf import WindsurfIntegration

    # -- Registration (alphabetical) --------------------------------------
    _register(ClaudeIntegration())
    _register(CodexIntegration())
    _register(GeminiIntegration())
    _register(MycliIntegration())             # ← add your registration here
    _register(WindsurfIntegration())
```

> Skipping either the import or the `_register()` call means the integration silently does not appear in the registry. Always add both.

### Step 4 — Context file behavior

Set `context_file` to the path where the agent reads its instructions (e.g., `"CLAUDE.md"`, `"AGENTS.md"`, `".github/copilot-instructions.md"`). The base class automatically handles:

- **On install:** Creates the file if it does not exist, or appends a managed Spec Kit section if it does.
- **On uninstall:** Removes the managed section. If the file becomes empty after removal, the file itself is deleted.

The managed section is clearly delimited so it does not interfere with content the user has written manually:

```markdown
<!-- spec-kit:start -->
<!-- This section is managed by Specify CLI. Do not edit manually. -->

... Spec Kit instructions ...

<!-- spec-kit:end -->
```

Only add custom context-file logic if the agent requires a non-standard format.

### Step 5 — Write a test file

Create `tests/integrations/test_integration_<key>.py`. Use underscores in the filename, not hyphens (e.g., key `kiro-cli` → `test_integration_kiro_cli.py`).

A well-structured test file should cover:

| Test | What to assert |
|---|---|
| Install creates expected files | All files in `registrar_config["dir"]` exist after `setup()` |
| Context file is created or updated | `context_file` exists and contains the managed section |
| Uninstall removes all managed files | No integration files remain after `teardown()` |
| Uninstall preserves user files | Files not in the manifest are untouched |
| Command files use correct format | File extension and argument placeholder match `registrar_config` |

**Minimal test structure:**

```python
import pytest
from pathlib import Path
from specify_cli.integrations.mycli import MycliIntegration


def test_setup_creates_command_files(tmp_path):
    integration = MycliIntegration()
    integration.setup(project_dir=tmp_path)

    commands_dir = tmp_path / ".mycli" / "commands"
    assert commands_dir.exists()
    assert any(commands_dir.iterdir()), "Expected at least one command file"


def test_setup_creates_context_file(tmp_path):
    integration = MycliIntegration()
    integration.setup(project_dir=tmp_path)

    context = tmp_path / "MYCLI.md"
    assert context.exists()
    assert "spec-kit:start" in context.read_text()


def test_teardown_removes_managed_files(tmp_path):
    integration = MycliIntegration()
    integration.setup(project_dir=tmp_path)
    integration.teardown(project_dir=tmp_path)

    commands_dir = tmp_path / ".mycli" / "commands"
    assert not commands_dir.exists() or not any(commands_dir.iterdir())


def test_teardown_preserves_user_files(tmp_path):
    integration = MycliIntegration()
    integration.setup(project_dir=tmp_path)

    user_file = tmp_path / "MYCLI.md"
    user_file.write_text("# My custom notes\n\n" + user_file.read_text())

    integration.teardown(project_dir=tmp_path)

    # User content above the managed section should survive
    assert "My custom notes" in user_file.read_text()
```

Run with:

```bash
pytest tests/integrations/test_integration_mycli.py -v
```

---

## Full Example: Adding `mycli`

This section walks through adding a fictional CLI tool called `mycli` from start to finish.

**Scenario:** `mycli` reads Markdown command files from `.mycli/commands/`, uses `$ARGUMENTS` as the placeholder, and expects a `MYCLI.md` context file in the project root.

### 1. Create the subpackage

```
src/specify_cli/integrations/mycli/__init__.py
```

```python
"""mycli integration."""

from ..base import MarkdownIntegration


class MycliIntegration(MarkdownIntegration):
    key = "mycli"                  # Must match the CLI executable name
    config = {
        "name": "My CLI",
        "folder": ".mycli/",
        "commands_subdir": "commands",
        "install_url": "https://example.com/mycli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".mycli/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "MYCLI.md"
```

### 2. Register it

In `src/specify_cli/integrations/__init__.py`:

```python
from .mycli import MycliIntegration   # Add import (alphabetical)

_register(MycliIntegration())          # Add registration (alphabetical)
```

### 3. Test the install

```bash
specify init test-project --integration mycli
ls test-project/.mycli/commands/
cat test-project/MYCLI.md
```

Expected output:

```
test-project/.mycli/commands/
├── spec.md
├── implement.md
└── review.md

MYCLI.md — contains the managed Spec Kit section
```

### 4. Test the uninstall

```bash
cd test-project
specify integration uninstall mycli
ls .mycli/commands/   # Should be empty or removed
```

### 5. Run the test suite

```bash
pytest tests/integrations/test_integration_mycli.py -v
```

---

## Command File Formats

### Markdown

Used by most agents, including Windsurf, Forge, Claude, and Copilot.

```markdown
---
description: "Generate a specification for the given feature"
---

You are a specification writer. Given $ARGUMENTS, produce a clear,
structured feature specification using the Spec Kit template at {SCRIPT}.
```

### TOML

Used by Gemini CLI.

```toml
description = "Generate a specification for the given feature"

prompt = """
You are a specification writer. Given {{args}}, produce a clear,
structured feature specification using the Spec Kit template at {SCRIPT}.
"""
```

### YAML

Used by Goose.

```yaml
version: 1.0.0
title: "Generate Specification"
description: "Generate a specification for the given feature"
author:
  contact: spec-kit
extensions:
  - type: builtin
    name: developer
activities:
  - Spec-Driven Development
prompt: |
  You are a specification writer. Given {{args}}, produce a clear,
  structured feature specification using the Spec Kit template at {SCRIPT}.
```

### Argument and Script Placeholders

| Placeholder | Replaced With | Used By |
|---|---|---|
| `$ARGUMENTS` | User-supplied arguments at runtime | Most Markdown agents |
| `{{args}}` | User-supplied arguments at runtime | TOML and YAML agents (Gemini, Goose) |
| `{{parameters}}` | User-supplied arguments at runtime | Forge |
| `{SCRIPT}` | Absolute path to the spec script | All agents |
| `__AGENT__` | Name of the current agent | All agents |

Always check `registrar_config["args"]` for the correct placeholder before writing command templates for a new integration.

---

## Special Processing — Built-in Integrations

Some integrations require logic beyond standard template substitution. These are documented here for reference and as patterns you can follow.

### GitHub Copilot

Copilot's command format differs from other Markdown agents in three ways:

- Command files use `.agent.md` instead of `.md`
- Each command gets a companion `.prompt.md` file in `.github/prompts/`
- A `.vscode/settings.json` file is created (or merged) to register the prompt files with VS Code

Copilot extends `IntegrationBase` directly and overrides `setup()` to handle all three requirements.

**Skills mode** is also supported via `--integration-options="--skills"`. In this mode:
- Commands are scaffolded as `speckit-<name>/SKILL.md` under `.github/skills/`
- No companion `.prompt.md` files are generated
- No `.vscode/settings.json` merge occurs

The two modes are mutually exclusive per project:

```bash
# Default: .agent.md + .prompt.md companions + .vscode/settings.json
specify init my-project --integration copilot

# Skills mode: speckit-<name>/SKILL.md only
specify init my-project --integration copilot --integration-options="--skills"
```

### Forge

Forge uses `{{parameters}}` instead of `$ARGUMENTS`, strips a Forge-specific `handoffs` frontmatter key, and injects a `name` field if it is missing from frontmatter. This is handled by `_apply_forge_transformations()` inside the custom `setup()` method.

### Goose

Goose uses Block's YAML recipe format. The integration extends `YamlIntegration`, extracts the `title` and `description` from template frontmatter, and renders a valid Goose recipe using `yaml.safe_dump()` for proper escaping.

---

## Error Handling and Debugging

### Common Errors and Fixes

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Integration 'mycli' not found` | Missing `_register()` call | Add `_register(MycliIntegration())` to `_register_builtins()` |
| `Integration 'mycli' not found` (still) | Missing import | Add `from .mycli import MycliIntegration` in `_register_builtins()` |
| CLI check fails for `requires_cli: True` agent | `key` does not match executable name | Set `key` to the exact name users type in the terminal (verified by `shutil.which(key)`) |
| Command files have wrong argument syntax | Wrong `args` value in `registrar_config` | Use `$ARGUMENTS` for Markdown agents, `{{args}}` for TOML/YAML agents |
| Context file not created or updated | `context_file` is `None` or points to wrong path | Set `context_file` to the exact relative path the agent reads |
| Uninstall leaves files behind | Files created in `setup()` not registered with manifest | Call `self.manifest.add(path)` for every file created in a custom `setup()` |
| Black background in table cells (docx output) | `ShadingType.SOLID` used instead of `ShadingType.CLEAR` | Use `ShadingType.CLEAR` for all cell shading |

### Debugging Tips

**Inspect the manifest file** to see what files are tracked for an integration:

```bash
cat .mycli/.specify-manifest.json
```

**Run with verbose output** to trace what Specify CLI is doing during install:

```bash
specify init my-project --integration mycli --verbose
```

**Check if a CLI tool is detected** before debugging further:

```bash
which mycli        # Should print the path if installed
```

**Manually verify the output structure** after install:

```bash
find my-project/.mycli -type f
cat my-project/MYCLI.md
```

---

## Updating Devcontainer Configuration

For agents distributed as VS Code extensions or CLI tools, update the devcontainer files so the environment is pre-configured for new contributors.

### VS Code Extension-Based Agents

Add the extension ID to `.devcontainer/devcontainer.json`:

```jsonc
{
  "customizations": {
    "vscode": {
      "extensions": [
        "existing.extension-one",
        "your-publisher.mycli-extension"   // ← add here
      ]
    }
  }
}
```

### CLI-Based Agents

Add an install command to `.devcontainer/post-create.sh`:

```bash
echo -e "\n🤖 Installing mycli..."
run_command "npm install -g mycli@latest"
echo "✅ Done"
```

---

## Contribution Checklist

Use this checklist before submitting a pull request for a new integration.

- [ ] Subpackage created at `src/specify_cli/integrations/<key>/__init__.py`
- [ ] All required fields defined: `key`, `config`, `registrar_config`, `context_file`
- [ ] `requires_cli` set correctly (`True` for CLI tools, `False` for IDE plugins)
- [ ] `key` matches the CLI executable name when `requires_cli` is `True`
- [ ] Argument placeholder in `registrar_config["args"]` matches the agent's expected format
- [ ] Integration imported and registered (alphabetically) in `_register_builtins()`
- [ ] Test file created at `tests/integrations/test_integration_<key>.py`
- [ ] All tests pass: `pytest tests/integrations/test_integration_<key>.py -v`
- [ ] Full install/uninstall cycle verified manually with `specify init` and `specify integration uninstall`
- [ ] Devcontainer files updated if the agent has a VS Code extension or requires a CLI install
- [ ] This `AGENTS.md` updated if new patterns, formats, or base class behaviors were introduced

---

