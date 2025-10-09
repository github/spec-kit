# Spec Kit PR Guidelines (Working Playbook)

This guide distills practical rules and checklists from recent PR work to help contributors ship changes that are spec‑first, technology‑neutral, reproducible, and easy to review. It consolidates prior notes from both English and Chinese guides into one canonical document.

## Before You Start: Why + Definition of Done

- State the Why in one sentence (bug, compatibility, maintainability, UX, perf, compliance, etc.).
- Define verifiable acceptance criteria (e.g., all agent×script packages build; docs compile; CLI examples run on Windows and Linux).
- Break work down into small tasks (e.g., update CLI help → update README → patch packaging script → local verify).

## Purpose

- Strengthen Spec‑Driven Development (SDD) by turning ideas into structured, machine‑readable specs.
- Keep changes agent‑agnostic and framework‑agnostic.
- Prevent silent failures; make success/failure observable and reproducible.

## Core Principles

- Spec‑First: Prefer structured artifacts (tokens, component APIs, flows, HTML skeletons, BDD, data contracts) over prose.
- Technology‑Neutral: Default to semantic HTML + ARIA and JSON Schema; avoid binding to specific frameworks.
- Reproducible Paths: Always use absolute file paths emitted by scripts; never guess or hard‑code template locations in commands.
- Fail‑Fast: If prerequisites/templates are missing, exit with a clear error (no silent empty files).
- Idempotent Packaging: Path rewriting must not produce double prefixes (e.g., `.specify.specify/`).
- Minimal Scope: Keep each PR focused; only touch files relevant to the change.

## Agent Integration and CLI Core Changes

- If you modify `src/specify_cli/__init__.py`:
  - Bump the version in `pyproject.toml` and add a `CHANGELOG.md` entry (per AGENTS.md).
- Adding or changing agent support:
  - Update `AI_CHOICES` and help text in `src/specify_cli/__init__.py`.
  - Update Supported Agents table in `README.md`.
  - Update `.github/workflows/scripts/create-release-packages.sh` (ALL_AGENTS, directory cases, placeholder replacements).
  - If release artifacts change, update `.github/workflows/scripts/create-github-release.sh` accordingly.
  - Keep agent context updaters in sync: `scripts/bash/update-agent-context.sh` and `scripts/powershell/update-agent-context.ps1`.

## Branching & Environment

- Use feature branches like `001-some-feature`.
- For non‑Git environments, set `SPECIFY_FEATURE` to select the feature folder.
- Common helpers already warn but allow non‑Git flows; prefer branches when possible.

## Files, Paths, and Scripts

- Command templates (e.g., `/speckit.*`):
  - Rely only on JSON keys printed by setup scripts (e.g., `README_FILE`, `TOKENS_FILE`, `COMPONENTS_SPEC`, `FLOWS_FILE`, `HTML_SKELETON`, `BDD_FILE`, `TYPES_SCHEMA`/`TYPES_TS`).
  - Do not infer or reconstruct paths inside command text.
- Setup scripts (Bash + PowerShell):
  - Resolve template root from `.specify/templates/<area>` (packaged projects) or `templates/<area>` (repo checkout).
  - Emit absolute paths via JSON once and reuse them.
  - Fail if any required template is missing; include actionable guidance in errors.
- Do not commit generated artifacts under `specs/` in PRs unless explicitly requested.

### Cross‑Agent Conventions (placeholders)

- Directory layout by agent: `.claude/commands/`, `.gemini/commands/`, `.cursor/commands/`, `.windsurf/workflows/`, `.github/prompts/` (Copilot), etc.
- Argument placeholders by format:
  - Markdown/Prompt: `$ARGUMENTS`
  - TOML: `{{args}}`
  - Script path placeholder: `{SCRIPT}`
  - Agent name placeholder: `__AGENT__`

## Packaging & Release

- Packager script: `.github/workflows/scripts/create-release-packages.sh`
  - Rewrites `memory/`, `scripts/`, and `templates/` into `.specify/*`.
  - Include an idempotency guard to collapse accidental double prefixes (e.g., `.specify/.specify/`).
- Do not modify CLI core (`src/specify_cli/__init__.py`) unless necessary. If you do:
  - Bump version in `pyproject.toml` and add a `CHANGELOG.md` entry (per AGENTS.md).

### Workflow Triggers

- Release workflow (`.github/workflows/release.yml`) is triggered on changes under `memory/**`, `scripts/**`, `templates/**`, and `.github/workflows/**`.
- Docs workflow (`.github/workflows/docs.yml`) builds and publishes docs when `docs/**` changes.

### Docs Build (DocFX)

- Docs use DocFX. If you modify DocFX config/structure, verify locally before pushing (requires .NET + DocFX).

## CI Smoke Tests

- Add/update a workflow that:
  - Builds packages for supported agents and script variants (sh/ps).
  - Verifies no `.specify.specify/` strings in packaged commands.
  - Runs `create-new-feature` and your setup script; validates JSON keys exist; asserts files are non‑empty.
  - Validates JSON with `jq` (Linux). Add light static analysis (`shellcheck`, `PSScriptAnalyzer`)—warnings may be non‑blocking initially.

## Documentation & Help Text

- README: Add commands and minimal usage notes (branch vs `SPECIFY_FEATURE`, “use JSON keys only”, and default to JSON Schema).
- Template README: Document conventions (tokens‑only styling, accessibility, neutrality, path usage via JSON keys).
- Keep examples concise and technology‑neutral; add framework mapping notes as comments when helpful.

## Local Verification (quick references)

- Using uv (no global install required):
  - `uv sync`
  - `uv run specify --help`
  - `uv run specify check`
  - Example: `uv run specify init demo --ai claude --script sh --ignore-agent-tools`
- Global Specify (optional):
  - `specify --help`
  - `specify check`
- Packaging dry‑run:
  - `bash .github/workflows/scripts/create-release-packages.sh v0.0.0`

## Data Contracts

- Prefer JSON Schema (`types.schema.json`) for neutrality.
- TypeScript interfaces (`types.ts`) are optional developer aids.
- Ensure contracts align with events/results implied by flows and components.

## Accessibility & Tokens

- Put all visual primitives in `tokens.json` (colors, spacing, radius, shadows, typography; optional: breakpoints, zIndex, opacity, motion).
- Encourage rem‑based sizing guidance in docs (e.g., 16px body → 1rem).
- Preserve roles/labels/`aria-live`; plan focus management.

## AI Disclosure

- Include a short note in PRs if AI assisted drafting or code generation, and confirm manual review/verification.

## Review Checklist

- [ ] Command uses only script JSON keys (no hard‑coded paths).
- [ ] Scripts resolve both packaged and repo roots; missing templates fail with guidance.
- [ ] No silent file creation; all artifacts are real and non‑empty.
- [ ] Packaging contains `.specify/templates/<area>/*` and no `.specify.specify/`.
- [ ] Tokens‑only styling outside of `tokens.json` (no raw hex/px in other files).
- [ ] Components referenced in `skeleton.html` exist in `components.md`.
- [ ] Flows and BDD align on state names and transitions.
- [ ] Data contracts present; JSON Schema preferred.
- [ ] README/Template docs updated; include branch/SPECIFY_FEATURE guidance.
- [ ] CI smoke tests pass on Ubuntu + Windows.
- [ ] If CLI core changed: version bump + changelog entry present.

## Quick Commands (examples)

- Local (no init):
  ```bash
  export SPECIFY_FEATURE=001-ui-feature
  bash scripts/bash/setup-ui.sh | tee /tmp/ui.json
  jq -r '.README_FILE,.TOKENS_FILE,.COMPONENTS_SPEC,.FLOWS_FILE,.HTML_SKELETON,.BDD_FILE,.TYPES_SCHEMA,.TYPES_TS' /tmp/ui.json
  ```
- Packaged (Linux):
  ```bash
  bash .github/workflows/scripts/create-release-packages.sh vX.Y.Z
  unzip -q .genreleases/spec-kit-template-claude-sh-vX.Y.Z.zip -d /tmp/p
  cd /tmp/p
  .specify/scripts/bash/create-new-feature.sh --json 'UI smoke'
  .specify/scripts/bash/setup-ui.sh | jq .
  ```

## Anti‑Patterns

- Hard‑coding template paths in commands.
- Creating empty placeholder files on failure.
- Binding artifacts to a specific UI framework by default.
- Mixing unrelated changes (workflows, docs, and features) without clear rationale.

---
Keep this guide updated as the process evolves.
