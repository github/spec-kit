# AGENTS.md

## About InfraKit

**InfraKit** is [spec-kit](https://github.com/github/spec-kit) for infrastructure-as-code, with a multi-persona pipeline layered on top. It captures the spec for an IaC change first, routes it through four specialized personas (Cloud Solutions Engineer → Cloud Architect → Cloud Security Engineer → IaC Engineer), and then generates Crossplane YAML or Terraform HCL — with the full audit trail committed to git alongside the code.

**InfraKit CLI** is the command-line interface that bootstraps projects with the InfraKit framework. It sets up the necessary directory structures, templates, and AI agent integrations to support the spec-driven workflow.

Five AI coding agents are supported: **Claude Code**, **Codex CLI**, **Gemini CLI**, **GitHub Copilot**, plus a **generic** fallback for bring-your-own-agent setups. The set was deliberately scoped down from a much larger list — fewer agents, deeper testing, plus subagent invocation on the agents that support it (currently Claude only).

---

## General practices

- Any changes to `__init__.py` for the InfraKit CLI require a version rev in `pyproject.toml` and addition of entries to `CHANGELOG.md`.

## Adding New Agent Support

This section explains how to add support for new AI agents/assistants to the InfraKit CLI. Use this guide as a reference when integrating new AI tools into the spec-driven workflow.

### Overview

InfraKit supports multiple AI agents by generating agent-specific command files and directory structures when initializing projects. Each agent has its own conventions for:

- **Command file formats** (Markdown, TOML, etc.)
- **Directory structures** (`.claude/commands/`, `.windsurf/workflows/`, etc.)
- **Command invocation patterns** (slash commands, CLI tools, etc.)
- **Argument passing conventions** (`$ARGUMENTS`, `{{args}}`, etc.)

### Current Supported Agents

| Agent              | Directory             | Format   | CLI Tool        | Subagents | Notes                                                        |
| ------------------ | --------------------- | -------- | --------------- | --------- | ------------------------------------------------------------ |
| **Claude Code**    | `.claude/commands/`   | Markdown | `claude`        | ✅        | Anthropic's Claude Code CLI; uses `Task` for review phases.  |
| **Codex CLI**      | `.codex/prompts/`     | Markdown | `codex`         | —         | OpenAI's Codex CLI.                                          |
| **Gemini CLI**     | `.gemini/commands/`   | TOML     | `gemini`        | —         | Google's Gemini CLI.                                         |
| **GitHub Copilot** | `.github/agents/`     | `.agent.md` + `.prompt.md` pair | N/A (IDE-based) | —         | Auto-emits prompt + agent files; configures `.vscode/settings.json`. |
| **Generic**        | `.infrakit/commands/` | Markdown | N/A             | —         | Bring-your-own; use `--ai-commands-dir <path>` to place files. |

### Why the set is intentionally small

InfraKit historically supported 19 agents. Each new agent meant another
folder layout, another command-format quirk, another MCP-install convention,
and a per-agent zip in the release matrix. The maintenance cost was high,
the per-agent testing was shallow, and the per-agent prompt quality drifted
because no one was running the workflow end-to-end on 19 different harnesses.

In v0.2 the supported set was scoped down to five agents that are actively
tested end-to-end on every release:

- **Claude Code** — the reference target. Multi-persona review phases use
  the native Task tool for subagent isolation.
- **Codex CLI** — OpenAI's reference CLI.
- **Gemini CLI** — Google's reference CLI.
- **GitHub Copilot** — covers the IDE-based agent surface.
- **Generic** — covers everything else via --ai-commands-dir.

If you need first-class support for another agent, please open an issue
describing the use case. We won't add agents speculatively, but we do
take a real workflow + a contributor willing to maintain it seriously.

## Internal: how the per-agent layout is rendered

For maintainers: the per-agent transformation (folder placement, command file extension, TOML wrapping for Gemini, Copilot's prompt-pair generation, VS Code settings deep-merge) lives in `src/infrakit_cli/template_renderer.py`. Each agent's layout is declared as data in `AGENT_CONFIG` (in `src/infrakit_cli/agent_config.py`); the renderer reads that data and produces the on-disk layout at `infrakit init` time.

To add a new agent:

1. Add an entry to `AGENT_CONFIG` declaring its `folder`, `commands_subdir`, `command_format`, `command_extension`, `command_args` token, and `supports_subagents` flag.
2. If the agent needs post-render hooks (e.g. Copilot's prompt+agent file pair), add an `extras` list and implement the hook in `template_renderer.materialize_project`.
3. Add the agent to the `--ai` help string in `src/infrakit_cli/cli.py` and to the supported-agents tables in `README.md` and this file.
4. Add a parametrized test row to `tests/test_template_renderer.py` covering both `terraform` and `crossplane` IaC tools.
5. End-to-end verify: `uv build && pip install dist/*.whl && infrakit init demo --ai <new-agent> --iac terraform --no-git` produces the expected directory layout.

No changes to release tooling are required — the per-agent rendering all happens at `infrakit init` time, not at release time.
