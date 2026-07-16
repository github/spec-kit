# Coding Agent Context Extension

This bundled extension manages the **coding agent context/instruction file** (e.g. `CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md`, `GEMINI.md`, …) for the active integration.

It owns the lifecycle of the managed section delimited by the configurable start/end markers (defaults: `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->`). Everything else is untouched.

> NOTE: Spec Kit itself never touches your agent context file. This extension is the only thing that does, and it's opt-in: install it if you want the block kept in sync, skip it if you'd rather manage that file yourself.

## Why an extension?

Not every Spec Kit user wants Spec Kit to write into the coding agent's context file. Keeping this behavior in a dedicated, **opt-in** extension lets users:

- **Choose whether to install it at all** - `specify init` does **NOT** install it. Add it explicitly when you want Spec Kit to manage the agent context file; if it is absent or disabled, Spec Kit never creates or modifies that file (the AI context file).
- **Customize the markers** by editing `.specify/extensions/agent-context/agent-context-config.yml` ([agent-context-config.yml](./agent-context-config.yml) in this repo) - the bundled scripts honor the `context_markers` value.
- **Synchronize multiple agent anchors** by setting `context_files` when a project intentionally uses more than one coding agent context file, such as `AGENTS.md` and `CLAUDE.md`.
- **Refresh on demand** by running the `speckit.agent-context.update` command in your agent, or automatically through the hooks declared in [extension.yml](./extension.yml) (`after_specify`, `after_plan`).

## Installation

To install the extension, from the root of an initialized Spec Kit project, run:

```bash
specify extension add agent-context
```

## Disabling

```bash
specify extension disable agent-context

# Re-enable it
specify extension enable agent-context
```

While this extension is disabled (or not installed), nothing in Spec Kit creates, updates, or removes the managed block - the `__CONTEXT_FILE__` placeholder in any template is left as-is, and the extension's own config is never read.

## Commands

| Command                        | Description                                                                       |
| ------------------------------ | --------------------------------------------------------------------------------- |
| `speckit.agent-context.update` | Refresh the managed section in the agent context file with the current plan path. |

> NOTE: The command ID above is canonical. When invoking it as a slash command, use your agent's separator: `/speckit.agent-context.update` for dot-separator agents or `/speckit-agent-context-update` for hyphen-separator agents (e.g. Forge, Cline).

## Configuration

All configuration flows through the extension's own config file at `.specify/extensions/agent-context/agent-context-config.yml` ([agent-context-config.yml](./agent-context-config.yml) in the repo).

## Requirements

The bundled update scripts require **Python 3** with **PyYAML** for YAML/upsert processing (PowerShell can also use `ConvertFrom-Yaml` when available).

PyYAML ships with the `specify` CLI and is normally available via the same `python3` interpreter. If a hook reports _"PyYAML is required … not available in the current Python environment"_, it means the system `python3` differs from the one used to install Spec Kit. To resolve, run:

```bash
pip install pyyaml
# or target the specific interpreter Spec Kit uses:
/path/to/speckit-python -m pip install pyyaml
```

## Issues

For any other issues, please create an issue in the [official GitHub repo](https://github.com/github/spec-kit/issues).
