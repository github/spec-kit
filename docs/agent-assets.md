# Agent Asset Packaging

This guide explains how Spec Kit assembles the command prompts and supporting files that ship with each AI agent bundle. Use it when you need to trace where the prompts come from, verify the new `.specs/.specify` layout, or build custom packages for downstream consumers.

## Overview

Each agent receives a curated slice of the repository that includes:

- **Command prompts** sourced from `templates/commands/*.md`, rewritten into the agent-specific format (`.md`, `.prompt.md`, or `.toml`).
- **Shared templates** (`spec-template.md`, `plan-template.md` -> writes `design.md`, `tasks-template.md`, `pprd-template.md`, `agent-file-template.md`) and supporting documentation copied into `.specs/.specify/templates/` and `.specs/.specify/docs/`.
- **Automation scripts** copied into `.specs/.specify/scripts/<shell>/`, matching the `--script` variant selected during packaging (Bash or PowerShell).
- **Project memory and supporting assets** relocated under `.specs/.specify/` to keep non-agent files together.
 - **Layout configuration** copied to `.specs/.specify/layout.yaml` describing canonical roots, folder strategy, and file names.

The packaging workflow guarantees that every generated archive adheres to the consolidated `.specs/.specify` directory structure introduced in v0.0.18.

## Source of Agent Templates

| Asset type                    | Source path (repo)                | Destination in package                |
|-------------------------------|-----------------------------------|---------------------------------------|
| Command prompts               | `templates/commands/*.md`         | `.<agent>/commands/` (format dependent)|
| Agent context template        | `templates/agent-file-template.md`| `.specs/.specify/templates/`          |
| Spec/plan/tasks/PPRD layouts  | `templates/*.md`                  | `.specs/.specify/templates/`          |
| Template overrides (assets)   | `templates/assets/*-template.md`  | `.specs/.specify/templates/assets/`   |
| Layout configuration          | `templates/layout.yaml`           | `.specs/.specify/layout.yaml`         |
| Automation scripts            | `scripts/bash/`, `scripts/powershell/` | `.specs/.specify/scripts/bash/` or `.specs/.specify/scripts/powershell/` |
| Constitution (memory)         | `memory/constitution.md`          | `.specs/.specify/memory/constitution.md` |
| Docs                          | `docs/`                           | `.specs/.specify/docs/`               |

The original prompt templates still reference placeholder paths such as `scripts/bash/...` or `/memory/constitution.md`. During packaging these references are rewritten to `.specs/.specify/...` so the generated projects align with the new hierarchy without modifying the authoring files in-place.

In addition, generated projects resolve layout files dynamically at runtime using helper scripts:

- `.specs/.specify/scripts/bash/resolve-template.sh` (and PowerShell variant) selects template bodies, preferring `templates/assets/*-template.md` overrides when present.
- `.specs/.specify/scripts/bash/read-layout.sh` and `spec-root.sh` (and PowerShell variants) read `.specs/.specify/layout.yaml` to determine roots, folder strategy, and canonical file names (e.g., `design.md`, `fprd.md`, `pprd.md`).

## Packaging Workflow

The script `.github/workflows/scripts/create-release-packages.sh` drives asset creation for every supported agent. Key steps:

1. **Determine agent/script variants** – reads `ALL_AGENTS` and `ALL_SCRIPTS`, optionally filtered by the `AGENTS` or `SCRIPTS` environment variables.
2. **Copy shared assets** – creates `.specs/.specify/` inside the build directory and copies docs, memory, scripts, and templates.
3. **Normalize paths** – runs `rewrite_paths()` to replace legacy references (`memory/`, `scripts/`, `templates/`) with `.specs/.specify/...` inside each command prompt so the generated instructions point at the relocated files.
4. **Generate prompts** – `generate_commands()` converts every file in `templates/commands/` into the agent’s preferred format (Markdown, `prompt.md`, or TOML) and drops them into `.<agent>/commands/` (or equivalent).
5. **Zip the package** – produces archives named `spec-kit-template-<agent>-<script>-<version>.zip` inside `.genreleases/`.

The same script is invoked locally or by CI workflows. Because it produces a plain directory before zipping, you can inspect the build output (for example `.genreleases/sdd-claude-package-sh/`) prior to compression.

## Using Packaged Templates

The `specify` CLI downloads these archives by default from the `Jrakru/spec-kit` releases. You can direct the CLI to alternate sources using:

- `--template-repo owner/repo` or `SPEC_KIT_TEMPLATE_REPO` to pull from a forked release.
- `--template-path /path/to/template.zip` or `SPEC_KIT_TEMPLATE_PATH` to scaffold from a local archive or directory (handy when testing output from `.genreleases/`).

Regardless of the source, the CLI relocates any legacy `.specify/` content into `.specs/.specify/` and ensures scripts are executable, so existing customized archives remain compatible.

## Verifying a Package Locally

To confirm an archive produces the expected structure:

```bash
AGENTS=claude SCRIPTS=sh bash .github/workflows/scripts/create-release-packages.sh v0.0.19
uv run specify init tmp/claude-demo \
  --ai claude \
  --script sh \
  --template-path .genreleases/spec-kit-template-claude-sh-v0.0.19.zip \
  --no-git
```

Inspect `tmp/claude-demo/.specs/.specify/` and `tmp/claude-demo/.claude/commands/` to ensure prompts reference the new paths. Confirm that:

- `layout.yaml` exists under `.specs/.specify/` and lists `spec_roots`, `folder_strategy`, and `files` keys.
- `templates/assets/` contains overrides you expect (e.g., `PPRD-template.md`).
- Scripts under `.specs/.specify/scripts/<shell>/` include `resolve-template.sh`, `read-layout.sh`, and `spec-root.sh`.

## Adding or Updating Agents

When bringing a new agent online (or modifying an existing one):

1. Update `templates/commands/*.md` with any agent-specific guidance.
2. Extend the packaging script’s `ALL_AGENTS` list and case statement to define the target directory (for example `.windsurf/workflows/`).
3. Regenerate a package and run `specify init` with `--template-path` to validate the resulting scaffold.
4. Publish the new archive via the release workflow or distribute it internally.

See `AGENTS.md` for a complete checklist when integrating additional agents into the toolkit.
