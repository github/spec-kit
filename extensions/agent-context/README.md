# Coding Agent Context Extension

This bundled extension manages the **coding agent context/instruction file** (e.g. `CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md`, `GEMINI.md`, …) for the active integration.

It owns the lifecycle of the managed section delimited by the configurable start/end markers (defaults: `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->`).

## Why an extension?

Not every Spec Kit user wants Spec Kit to write into the coding agent's context file. Keeping this behavior in a dedicated, **opt-in** extension lets users:

- **Choose whether to install it at all** — `specify init` does not install it. Add it explicitly when you want Spec Kit to manage the agent context file; if it is absent or disabled, Spec Kit never creates or modifies that file.
- **Customize the markers** by editing `.specify/extensions/agent-context/agent-context-config.yml` — the bundled scripts honor the `context_markers` value.
- **Synchronize multiple agent anchors** by setting `context_files` when a project intentionally uses more than one coding agent context file, such as `AGENTS.md` and `CLAUDE.md`.
- **Refresh on demand** by running the `speckit.agent-context.update` command in your agent, or automatically through the hooks declared in `extension.yml` (`after_specify`, `after_plan`). Invoke it using your agent's slash-command separator — `/speckit.agent-context.update` for dot-separator agents or `/speckit-agent-context-update` for hyphen-separator agents (e.g. Forge, Cline).

## Commands

The command ID below is canonical. When invoking it as a slash command, use your agent's separator: `/speckit.agent-context.update` for dot-separator agents or `/speckit-agent-context-update` for hyphen-separator agents (e.g. Forge, Cline).

| Command | Description |
|---------|-------------|
| `speckit.agent-context.update` | Refresh the managed section in the agent context file with the current plan path. |

## Configuration

All configuration flows through the extension's own config file at
`.specify/extensions/agent-context/agent-context-config.yml`:

```yaml
# Path to the coding agent context file managed by this extension
context_file: CLAUDE.md

# Optional list of coding agent context files to manage together.
# When non-empty, this takes precedence over context_file.
context_files:
  - AGENTS.md
  - CLAUDE.md

# Delimiters for the managed Spec Kit section
context_markers:
  start: "<!-- SPECKIT START -->"
  end: "<!-- SPECKIT END -->"
```

- `context_file` — the project-relative path to the coding agent context file. When empty, the bundled update scripts self-seed it by looking up the active integration's key in this extension's own `agent-context-defaults.json` map. The Specify CLI is never consulted.
- `context_files` — optional project-relative paths to multiple coding agent context files. When non-empty, the list takes precedence over `context_file`. Absolute paths, backslash separators, and `..` path segments are rejected.
- `context_markers.start` / `.end` — the delimiters around the managed section. Edit these to use custom markers.

## Requirements

The bundled update scripts require **Python 3** with **PyYAML** for YAML/upsert processing (PowerShell can also use `ConvertFrom-Yaml` when available).

PyYAML ships with the `specify` CLI and is normally available via the same `python3` interpreter. If a hook reports *"PyYAML is required … not available in the current Python environment"*, it means the system `python3` differs from the one used to install Spec Kit. To resolve, run:

```bash
pip install pyyaml
# or target the specific interpreter Spec Kit uses:
/path/to/speckit-python -m pip install pyyaml
```

## Disable

```bash
specify extension disable agent-context
```

When disabled (or never installed), Spec Kit performs no agent context file creation, updates, or removal — the extension's bundled scripts are the only code that ever touches the managed section. The Specify CLI carries no agent-context state at all: it never reads this config, never resolves a context file, and the `__CONTEXT_FILE__` placeholder (if present in any template) is left untouched. All context-file knowledge — including the per-agent default mapping in `agent-context-defaults.json` — lives entirely within this extension, so disabling it is a complete opt-out.
