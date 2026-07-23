# AGENTS.md

## About Spec Kit and Specify

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework. It sets up the necessary directory structures, templates, and AI agent integrations to support the Spec-Driven Development workflow.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## Integration Architecture

Each AI agent is a self-contained **integration subpackage** under `src/specify_cli/integrations/<key>/`. The subpackage exposes a single class that declares all metadata and inherits setup/teardown logic from a base class. Built-in integrations are then instantiated and added to the global `INTEGRATION_REGISTRY` by `src/specify_cli/integrations/__init__.py` via `_register_builtins()`.

```text
src/specify_cli/integrations/
├── __init__.py            # INTEGRATION_REGISTRY + _register_builtins()
├── base.py                # IntegrationBase, MarkdownIntegration, TomlIntegration, YamlIntegration, SkillsIntegration
├── manifest.py            # IntegrationManifest (file tracking)
├── claude/                # Example: SkillsIntegration subclass
│   └── __init__.py        #   ClaudeIntegration class
├── gemini/                # Example: TomlIntegration subclass
│   └── __init__.py
├── kilocode/              # Example: MarkdownIntegration subclass
│   └── __init__.py
├── copilot/               # Example: IntegrationBase subclass (custom setup)
│   └── __init__.py
└── ...                    # One subpackage per supported agent
```

The registry is the **single source of truth for Python integration metadata**. Supported agents, their directories, formats, capabilities, and context files are derived from the integration classes for the Python integration layer.

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

**Minimal example — Markdown agent (Kilo Code):**

```python
"""Kilo Code IDE integration."""

from ..base import MarkdownIntegration


class KilocodeIntegration(MarkdownIntegration):
    key = "kilocode"
    config = {
        "name": "Kilo Code",
        "folder": ".kilocode/",
        "commands_subdir": "workflows",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".kilocode/workflows",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
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

**Key design rule:** For CLI-based integrations (`requires_cli: True`), `key` must be the actual executable name (e.g., `"cursor-agent"` not `"cursor"`). This ensures `shutil.which(key)` works for CLI-tool checks without special-case mappings. IDE-based integrations (`requires_cli: False`) should use their canonical identifier (e.g., `"kilocode"`, `"copilot"`).

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

### 4. Context file behavior

The Specify CLI carries **no agent-context state whatsoever**. Integration classes do **not** declare a `context_file`, and the CLI never creates, updates, removes, resolves, or migrates a context/instruction file (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, …). New integrations add nothing for context handling.

Managing the "Spec Kit" section in the context file is fully owned by the bundled `agent-context` extension (`extensions/agent-context/`), which is a **full opt-in**: `specify init` does not install it. A user adds/enables it through the standard extension verbs, after which the extension's own bundled scripts maintain the context section. When the extension is absent or disabled, nothing in Spec Kit touches the context file.

The extension reads its own config file at `.specify/extensions/agent-context/agent-context-config.yml`:

```yaml
# Path to the coding agent context file managed by this extension
context_file: CLAUDE.md

# Delimiters for the managed Spec Kit section
context_markers:
  start: "<!-- SPECKIT START -->"
  end: "<!-- SPECKIT END -->"
```

- The Specify CLI does **not** write this config. When `context_file` is empty, the extension's bundled scripts self-seed it by looking up the active integration's key in the extension's own `agent-context-defaults.json` map (`extensions/agent-context/scripts/bash/update-agent-context.sh`, `.ps1`, and `extensions/agent-context/scripts/python/update_agent_context.py`). The CLI registry is never consulted — all agent→context-file knowledge lives inside the extension.
- `context_markers.{start,end}` are read solely by the extension's scripts; they default to the Spec Kit markers shown above and can be customized by editing `agent-context-config.yml` directly.

Existing projects created by older Spec Kit versions keep working: any previously written managed section or extension config is left intact and is only ever updated by the extension when run.

Only add custom setup logic when the agent needs non-standard behavior. Integrations no longer require per-agent thin wrapper scripts or shared context-update dispatcher scripts — the `agent-context` extension is fully generic.

### 5. Test it

```bash
# Install into a test project
specify init my-project --integration <key>

# Verify files were created in the commands directory configured by
# config["folder"] + config["commands_subdir"] (for example, .kilocode/workflows/)
ls -R my-project/.kilocode/workflows/

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

### Script References (`scripts:` frontmatter)

Core command templates (`templates/commands/*.md`) that invoke a helper script declare it in a `scripts:` frontmatter block with one line per supported script type. The `{SCRIPT}` placeholder in the command body is replaced at install time with the entry matching the project's selected script type (`--script sh|ps|py`):

```yaml
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
  py: scripts/python/setup_plan.py --json
```

| Key  | Script type            | Location                   |
| ---- | ---------------------- | -------------------------- |
| `sh` | POSIX shell (bash/zsh) | `scripts/bash/*.sh`        |
| `ps` | PowerShell             | `scripts/powershell/*.ps1` |
| `py` | Python                 | `scripts/python/*.py`      |

All three entries must be present and behaviorally equivalent — agents parse the same stdout contract (`FEATURE_DIR:…`, `AVAILABLE_DOCS:…`, `--json` shapes) regardless of which one runs. (The bundled `agent-context` and `git` extension command templates also invoke helpers but do not yet use `scripts:` frontmatter — see [Script Types and Migration](#script-types-and-migration).)

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
- **Script placeholders**: `{SCRIPT}` (replaced with the resolved command from the template's `scripts:` frontmatter, per the project's `--script sh|ps|py` selection)
- **Agent placeholders**: `__AGENT__` (replaced with agent name)

## Script Types and Migration

Spec Kit ships every core workflow script in three interchangeable variants — POSIX shell (`sh`), PowerShell (`ps`), and Python (`py`) — selected per project with `specify init --script sh|ps|py`. Each core command template that invokes a helper script carries all three in its `scripts:` frontmatter (templates that don't call a script, e.g. `constitution`/`specify`, have no `scripts:` block); see [Script References](#script-references-scripts-frontmatter).

### Why Python is recommended

- **No extra runtime.** The `specify` CLI is already Python, so the interpreter is guaranteed present — `py` adds no new dependency.
- **Path toward a single source of truth.** The shell variants require paired `.sh` + `.ps1` maintenance and diverge on JSON handling (`jq` vs manual parsing). The Python variant avoids `jq` and is intended to eventually replace that dual-maintenance — but that consolidation has not happened yet: all three variants are still maintained in parallel (see the parity rule below).
- **Parity-tested.** The Python ports are covered by tests — output-parity tests against the shell scripts where the contract is stdout-based, and direct unit tests elsewhere — so the stdout contract agents rely on stays stable.

### Defaults and availability

- `py` is available today for the core command templates (via their `scripts:` frontmatter). The bundled extensions (`agent-context`, `git`) ship Python script variants on disk, but their command templates still hard-code the Bash/PowerShell invocations, so `--script py` does not yet route those extension commands to Python — wiring `py` into the extension command templates is tracked separately.
- Selection is per project: interactive `specify init` prompts for the script type, while non-interactive runs default to a shell variant by OS (`sh` on Linux/macOS, `ps` on Windows). `py` is chosen at the prompt or via `--script py`.
- `sh` and `ps` remain fully supported. Nothing is removed, and `py` is not yet the default.

### Parity rule for contributors

All three script types are first-class: any change to a workflow script must update `sh`, `ps`, and `py` together and keep their tests (parity and unit) green. Making `py` the default and eventually retiring `sh`/`ps` is future work gated on adoption, tracked under the script-unification epic ([#3277](https://github.com/github/spec-kit/issues/3277)) — not something to act on from this doc.

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

## Branch Naming Convention

Branches follow one of two patterns depending on whether an issue exists:

```text
<type>/<number>-<short-slug>   # when an issue is created first
<type>/<short-slug>            # when no issue exists (PR-only changes)
```

When an issue exists, include its number immediately after the prefix — this is what makes branches traceable. For small or self-contained changes that go straight to a PR without a tracking issue, omit the number.

| Prefix | When to use | Example |
|---|---|---|
| `feat/` | New features | `feat/2342-workflow-cli-alignment` |
| `fix/` | Bug fixes | `fix/2653-paths-only-validation` |
| `docs/` | Documentation changes | `docs/2677-branch-naming-convention`, `docs/update-landing-stats` |
| `community/` | Community catalog additions | `community/2492-add-mde-extension` |
| `chore/` | Maintenance, tooling, CI | `chore/2366-editorconfig` |

**Rules:**

1. Include the issue number when one exists — this is what makes branches traceable
2. Use kebab-case for the slug
3. Keep the slug short — enough to identify the work without looking up the issue

---

## Agent Disclosure for PRs, Comments, and Commits

Disclosure is **continuous**, not a one-time event. A single AI-disclosure paragraph in the PR body does **not** cover the commits and replies you add during review rounds. Each of the following must independently attest to agent authorship.

### Commits

- **Every commit you author must carry an `Assisted-by:` trailer** identifying the agent and whether it acted autonomously or under direct human supervision, for example:

  ```
  Assisted-by: GitHub Copilot (model: <name-if-known>, autonomous)
  ```

  Use `supervised` instead of `autonomous` only when a human actually authored or line-by-line reviewed the change before it was committed.
- **Never push solo-authored commits that hide agent authorship behind the operator's git identity.** If an agent generated the change, the trailer must say so even when the commit is attributed to a human account.
- Preserve any tool-generated `Co-authored-by:` trailers (e.g. Copilot Autofix) — do not strip them to make a commit look hand-written.

### Comments

- If you are an agent working on behalf of a human, **disclose your identity in your PR comment** — name the agent (and model, if applicable) and the human you are acting for (e.g., "Posted on behalf of @user by GitHub Copilot (model: &lt;name-if-known&gt;)").
- **Re-state agent identity in each review-round summary comment.** A prior PR-body disclosure does not cover later comments or commits.
- Post **one** top-level summary comment per review round listing what changed and the commit SHA. Do not reply on every individual comment.
- Reply inline only when context is needed (disagreement, deferral, non-obvious fix). Keep it to a sentence or two.
- **Never click "Resolve conversation"** — that belongs to the reviewer or PR author.
- No emoji, no celebratory framing, no checklist mirroring the reviewer's items, no restating what the reviewer wrote.
- Re-request review once per round (when all feedback is addressed), not after every intermediate push.

### Anti-patterns (do not do these)

- **Do not** reply "Done" or push a "fix" within seconds/minutes of a review event without disclosing that the response or commit was agent-generated. Speed of turnaround is not a substitute for attestation — a near-instant tested code change is itself a signal of automation and must be disclosed as such.
- **Do not** claim "reviewed, tested, and understood by me" for commits that were authored and pushed automatically in response to a review trigger. If the loop is automated, disclose it as automated.

---

## Common Pitfalls

1. **Using shorthand keys for CLI-based integrations**: For CLI-based integrations (`requires_cli: True`), the `key` must match the executable name (e.g., `"cursor-agent"` not `"cursor"`). `shutil.which(key)` is used for CLI tool checks — mismatches require special-case mappings. IDE-based integrations (`requires_cli: False`) are not subject to this constraint.
2. **Reintroducing context handling into the CLI**: The opt-in `agent-context` extension owns everything about context files — including the per-agent default mapping in `agent-context-defaults.json`. Integration classes must **not** declare a `context_file`, and no CLI code should read, write, resolve, or migrate context files. All context-file logic lives in `.specify/extensions/agent-context/` and its bundled scripts.
3. **Incorrect `requires_cli` value**: Set to `True` only for agents that have a CLI tool; set to `False` for IDE-based agents.
4. **Wrong argument format**: Use `$ARGUMENTS` for Markdown agents, `{{args}}` for TOML agents.
5. **Skipping registration**: The import and `_register()` call in `_register_builtins()` must both be added.
6. **Running tests against the wrong environment**: Always run the suite inside this working tree's own virtualenv (`uv sync --extra test` then `.venv/bin/python -m pytest`, or activate the venv first). A bare `uv run pytest` can resolve to an ambient/global interpreter whose editable `.pth` points at a *different* worktree. The failure is sneaky: test collection still imports `specify_cli` successfully, but newly-added subpackages (e.g. a fresh `specify_cli/bundler/`) resolve as a stale namespace package and raise `ModuleNotFoundError`. If a brand-new subpackage imports under `python -c` but not under pytest, suspect environment contamination, not your code.

---

*This documentation should be updated whenever new integrations are added to maintain accuracy and completeness.*
