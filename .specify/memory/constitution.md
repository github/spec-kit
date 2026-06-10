<!--
SYNC IMPACT REPORT
==================
Version change: [unfilled template] → 1.0.0
Rationale: Initial ratification. First concrete constitution for Spec Kit,
distilled from AGENTS.md (integration architecture) and CONTRIBUTING.md
(development workflow, testing, and contribution standards).

Principles defined:
  1. Integration Registry Is the Single Source of Truth
  2. Cross-Platform Script Parity (NON-NEGOTIABLE)
  3. Test-Backed Changes
  4. Spec-Driven Dogfooding
  5. Focused, Conventional Contributions

Added sections:
  - Core Principles (5 principles)
  - Additional Constraints (Architecture & Compatibility)
  - Development Workflow & Quality Gates
  - Governance

Removed sections: none (replaced unfilled template placeholders)

Templates requiring updates:
  ✅ .specify/templates/plan-template.md — "Constitution Check" gate is generic
     and references the constitution file; no edit required.
  ✅ .specify/templates/spec-template.md — no constitution-specific content; OK.
  ✅ .specify/templates/tasks-template.md — no constitution-specific content; OK.
  ✅ .specify/templates/commands/*.md — reference the constitution generically
     (e.g. analyze.md treats constitution conflicts as CRITICAL); no edit required.

Follow-up TODOs: none. RATIFICATION_DATE set to initial adoption date (2026-06-10).
-->

# Spec Kit Constitution

## Core Principles

### I. Integration Registry Is the Single Source of Truth

Every supported coding-agent integration MUST be a self-contained subpackage under
`src/specify_cli/integrations/<key>/` that subclasses an integration base class and
declares all of its metadata (`key`, `config`, `registrar_config`, `context_file`).
Each integration MUST be added to the global `INTEGRATION_REGISTRY` via
`_register_builtins()`. Agent capabilities, directories, formats, and command output
behavior MUST be derived from these classes — never hard-coded or duplicated in
unrelated modules. For CLI-based integrations (`requires_cli: True`), the `key` MUST
match the actual executable name so tool checks resolve without special cases.

**Rationale**: A single, declarative registry keeps the matrix of supported agents
consistent, discoverable, and testable. Scattered or duplicated agent metadata is the
primary source of drift between the CLI, the templates, and the context-update scripts.

### II. Cross-Platform Script Parity (NON-NEGOTIABLE)

Every shell capability MUST ship in both Bash (`scripts/bash/*.sh`) and PowerShell
(`scripts/powershell/*.ps1`) with equivalent behavior and outputs. This includes
per-integration wrapper scripts and the shared dispatchers (e.g.
`update-agent-context`, `check-prerequisites`). A change to one variant MUST be
mirrored in the other within the same change set. Scripts MUST NOT hard-depend on
optional tooling (e.g. `jq`) or on a git repository where a documented fallback is
expected; they MUST degrade gracefully.

**Rationale**: Spec Kit supports contributors and users on macOS, Linux, and Windows.
Parity is the contract that lets any user run the workflow regardless of shell.

### III. Test-Backed Changes

New functionality MUST be accompanied by tests. Every integration MUST have a dedicated
test file at `tests/integrations/test_integration_<key>.py` (hyphens in the key become
underscores). Any change to agent metadata, integration wiring, or context-update
scripts MUST keep `tests/test_agent_config_consistency.py` passing. A change that alters
the canonical core-command set MUST update every place that enumerates it (registries,
integration tests, and documentation) in the same change set.

**Rationale**: The integration surface is wide and highly repetitive; automated checks
are the only scalable defense against regressions in agent wiring and command coverage.

### IV. Spec-Driven Dogfooding

Spec Kit MUST be developed using its own Spec-Driven Development workflow. Features that
add or change behavior begin as a specification and proceed through plan and tasks before
implementation. Any change that affects a slash command's behavior MUST be manually
validated through a coding agent and the results reported with the change. Prerequisite
commands MUST be exercised in order (specify → plan → tasks → implement).

**Rationale**: The product is the workflow. Using it to build itself is both the most
honest validation and the fastest way to discover gaps in the experience.

### V. Focused, Conventional Contributions

Each change MUST stay as focused as possible; independent changes SHOULD be submitted
separately. Large or materially impactful changes (new templates, arguments, or
structural changes) MUST be discussed and agreed with maintainers before implementation.
Changes MUST follow existing coding conventions and MUST update user-facing documentation
(`README.md`, `spec-driven.md`, and the `docs/` reference) when they affect user-facing
behavior.

**Rationale**: Small, conventional, well-documented changes are reviewable and
reversible; unscoped changes are the ones that break the wide compatibility matrix.

## Additional Constraints (Architecture & Compatibility)

- **Adding an integration** MUST follow the documented procedure in `AGENTS.md`: choose a
  base class, create the subpackage, register it, add both script wrappers, update the
  shared context-update dispatchers, and add a dedicated test.
- **Command file formats** MUST conform to the agent's declared format (Markdown, TOML, or
  YAML) and use the correct argument placeholder for that format (`$ARGUMENTS` for
  Markdown, `{{args}}` for TOML/YAML, or the integration's documented override).
- **Placeholders** such as `{SCRIPT}`, `__AGENT__`, and `__SPECKIT_COMMAND_*__` MUST be
  left intact in source templates and resolved only through the established processing
  pipeline — never pre-expanded by hand.
- **Backward compatibility**: changes MUST NOT silently break existing initialized
  projects, the public CLI surface, or installed integrations.

## Development Workflow & Quality Gates

- Use `uv` for dependency management; the CLI MUST run from a clean `uv sync --extra test`
  environment.
- Run focused automated checks before manual workflow tests; at minimum,
  `tests/test_agent_config_consistency.py` MUST pass for agent/wiring changes.
- Slash-command behavior changes MUST include manual test results (agent, OS/shell, and
  pass/fail per command exercised).
- Documentation MUST be updated in the same change set as the behavior it describes.

## Governance

This constitution supersedes ad-hoc practices for the areas it covers. All pull requests
and reviews MUST verify compliance with these principles; deviations MUST be justified in
the change description or resolved before merge. Complexity that conflicts with a principle
MUST be justified against a concrete need or removed.

Amendments MUST be made by updating this document with a clear rationale, a version bump
per the policy below, and corresponding updates to any dependent templates and
documentation. Versioning follows semantic rules: **MAJOR** for backward-incompatible
governance or principle removals/redefinitions, **MINOR** for a new principle or materially
expanded guidance, **PATCH** for clarifications and non-semantic refinements.

**Version**: 1.0.0 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-06-10
