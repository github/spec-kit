# Copilot instructions for this repository

These notes orient AI coding agents to be productive quickly in this codebase. Keep advice concrete and specific to this repo.

## Big picture
- Purpose: Spec Kit provides the Specify CLI and scaffolding for Spec‑Driven Development (SDD). This repo is the toolkit and CLI, not an app template itself.
- Core deliverable: a CLI named `specify` that bootstraps SDD projects with agent workflows, templates, and scripts.
- Key modules:
  - `src/specify_cli/__init__.py`: Typer-based CLI entry point, most logic lives here (banner, tool checks, init flow, download/resolve templates, UX rendering with Rich).
  - `src/specify_cli/paths.py`: Single source of truth for file/folder locations (e.g., `get_specs_root`, `get_specify_root`, `specify_templates_dir`). Avoid hardcoding paths—use these helpers.
- Templates live in `templates/` and docs in `docs/` (DocFX sources). Agent integration rules in `AGENTS.md`; product overview and CLI reference in `README.md`.

## How things fit together
- CLI flow (high level):
  1) Parse args with Typer → 2) Optional tool checks (Claude, Cursor, etc.) → 3) Resolve template source (release ZIP, local dir via `--template-path`, or `SPEC_KIT_TEMPLATE_PATH`) → 4) Extract to project → 5) Write agent-specific command files and helper scripts.
- Declarative layout (in scaffolded projects): `.specs/.specify/layout.yaml` defines `spec_roots`, `folder_strategy` (flat/epic/product), and canonical filenames (`design.md`, `fprd.md`, `pprd.md`, `tasks.md`). Scripts read this at runtime—do not assume filenames or fixed directories.
- Template resolution prefers overrides at `.specs/.specify/templates/assets/*-template.md` before built-ins under `.specs/.specify/templates/`.

## Developer workflows (this repo)
- Run without install:
  - `python -m src.specify_cli --help`
  - `python -m src.specify_cli init demo --ai claude --ignore-agent-tools --script sh`
- Using uv:
  - Editable install: `uv venv && source .venv/bin/activate && uv pip install -e . && specify --help`
  - Local run w/o install: `uvx --from . specify init demo --ai copilot --ignore-agent-tools --script ps`
  - Build a wheel: `uv build`
- Docs (DocFX): `cd docs && docfx docfx.json --serve` then open http://localhost:8080.
- Policy: If you change `src/specify_cli/__init__.py`, bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry (see `AGENTS.md`).

## Project conventions
- Entry point: `[project.scripts] specify = "specify_cli:main"` in `pyproject.toml`. Keep help text and README examples in sync with CLI behavior.
- Supported agents: enumerated in `AI_CHOICES` (`__init__.py`). Adding agents requires code + docs + release script updates; follow `AGENTS.md` (directory names, file formats, argument placeholders differ by agent).
- IDE vs CLI agents:
  - IDE: Copilot (`.github/prompts/`), Windsurf (`.windsurf/workflows/`).
  - CLI: Claude (`.claude/commands/`), Cursor (`.cursor/commands/`), Gemini/Qwen (TOML in `.gemini/.qwen`), opencode, etc. Placeholders: `$ARGUMENTS` (md) vs `{{args}}` (toml).
- Environment variables:
  - `SPEC_KIT_TEMPLATE_REPO` / `SPEC_KIT_TEMPLATE_PATH` to override template source.
  - `SPECIFY_FEATURE`, `SPECIFY_PRODUCT`, `SPECIFY_EPIC` guide feature routing when using product/epic strategies.
  - `GH_TOKEN`/`GITHUB_TOKEN` improve GitHub API rate limits.
- Filenames used in scaffolded projects: plan → `design.md` (not `plan.md`); feature PRD → `fprd.md`; a legacy `spec.md` stub may be written for compatibility.

## What to reuse
- Paths: use `get_specs_root`, `get_specify_root`, `specify_templates_dir` from `src/specify_cli/paths.py` (don’t hardcode `.specs` paths).
- Tool checks and progress: reuse `check_tool`, `check_tool_for_tracker`, and `StepTracker` from `__init__.py` for consistent UX.
- Scripts: keep bash and PowerShell parity under `scripts/bash/` and `scripts/powershell/`; wire into templates as needed.

## Quick examples
- Local run via uvx: `uvx --from . specify init myproj --ai cursor --ignore-agent-tools --script sh`
- Direct module call: `python -m src.specify_cli check`

Key refs: `README.md`, `AGENTS.md`, `docs/local-development.md`, `src/specify_cli/__init__.py`, `src/specify_cli/paths.py`.

If anything here seems out of date with the code, note it and I’ll update this file.

## Workflow policies

- PR-only merges: Do not push directly to `main`. Always open a pull request so changes are reviewed and tracked.
- Quick check-and-PR helper: `scripts/bash/verify-and-pr.sh <branch>` will delete a redundant branch (no unique commits) or push and open a PR if it has unique commits.
- Versioning: When changing `src/specify_cli/__init__.py`, bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry. Tagging is done after merges to `main`.

### Non-interactive GitHub CLI (gh)

When invoking GitHub CLI commands from automations or agents, ensure they never require interactive prompts. Use these practices so commands return without human intervention:

- Always pass `--repo <owner>/<repo>` (or `-R`) to avoid selection prompts.
- Disable prompts globally in the environment: set `GH_PROMPT=disabled`.
- Prefer explicit confirmation flags:
  - `gh pr merge --squash --auto --delete-branch` (adds `--auto` to avoid confirmation)
  - `gh release create <tag> <assets...> --title "..." --notes "..." --latest` (no editor)
  - `gh workflow run <name-or-id> --ref main` (no follow-up prompts)
- Avoid opening editors: supply `--title/--body/--notes/--notes-file` instead of relying on `$EDITOR`.
- Non-interactive auth: rely on `GITHUB_TOKEN` (Actions) or a preconfigured `gh auth login`—do not trigger login flows during runs.
- Optional: set `GH_NO_UPDATE_NOTIFIER=1` to suppress update notices in CI logs.

If a command is known to prompt, add the appropriate `--yes/--confirm/--auto` flag or refactor the flow to avoid the prompt.
