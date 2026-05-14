# Coding Agent Context Extension

This bundled extension manages the **coding agent context/instruction file** (e.g. `CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md`, `GEMINI.md`, …) for the active integration.

It owns the lifecycle of the managed section delimited by the configurable start/end markers (defaults: `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->`).

## Why an extension?

Not every Spec Kit user wants Spec Kit to write into the coding agent's context file. Extracting this behavior into a dedicated extension lets users:

- **Opt out** entirely with `specify extension disable agent-context` — Spec Kit will then never create or modify the agent context file.
- **Customize the markers** by editing `.specify/extensions/agent-context/agent-context-config.yml` — both the Python layer and the bundled scripts honor the same `context_markers` value.
- **Refresh on demand** with `/speckit.agent-context.update`, or automatically through the hooks declared in `extension.yml` (`after_specify`, `after_plan`).

## Commands

| Command | Description |
|---------|-------------|
| `speckit.agent-context.update` | Refresh the managed section in the agent context file with the current plan path. |

## Configuration

All configuration flows through the extension's own config file at
`.specify/extensions/agent-context/agent-context-config.yml`:

```yaml
# Path to the coding agent context file managed by this extension
context_file: CLAUDE.md

# Delimiters for the managed Spec Kit section
context_markers:
  start: "<!-- SPECKIT START -->"
  end: "<!-- SPECKIT END -->"
```

- `context_file` — the project-relative path to the coding agent context file, written by `specify init` and `specify integration install`.
- `context_markers.start` / `.end` — the delimiters around the managed section. Edit these to use custom markers.
- Runtime note: the bundled update scripts require Python 3 for YAML/upsert processing (PowerShell can also use `ConvertFrom-Yaml` when available).

## Disable

```bash
specify extension disable agent-context
```

When disabled, Spec Kit skips context file creation, updates, and removal (the gates are inside `upsert_context_section()` and `remove_context_section()`).
