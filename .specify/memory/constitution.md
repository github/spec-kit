<!--
SYNC IMPACT REPORT
==================
Version change: (template/unratified) → 1.0.0
Bump rationale: Initial ratification of a concrete constitution for the brownfield
  Spec Kit / specify-cli codebase, derived from an exhaustive multi-pass analysis of
  the source tree, test suite, CI pipelines, and project conventions (AGENTS.md,
  CONTRIBUTING.md, DEVELOPMENT.md). MAJOR baseline because it establishes binding
  governance where none previously existed.

Principles defined:
  I.   Code Quality & Architectural Discipline
  II.  Test-Backed Change (NON-NEGOTIABLE)
  III. CLI & User-Experience Consistency
  IV.  Offline-First Performance & Resource Discipline
  V.   Minimal Dependencies & Safe, Idempotent File Operations

Added sections:
  - Security & Cross-Platform Constraints
  - Development Workflow & Quality Gates
  - Governance

Templates reviewed for alignment:
  ✅ .specify/templates/plan-template.md — generic "Constitution Check" gate (line 39)
       remains valid; gates are now concretely populated by Principles I–V at plan time.
  ✅ .specify/templates/spec-template.md — no constitution-specific tokens; no change needed.
  ✅ .specify/templates/tasks-template.md — task categories (setup/foundational/story/polish)
       already accommodate testing + performance + UX tasks mandated here; no change needed.
  ✅ .github/agents/speckit.*.agent.md — command guidance is agent-agnostic; no change needed.

Follow-up TODOs: none. RATIFICATION_DATE set to first adoption date below.
-->

# Spec Kit Constitution

Spec Kit (the `specify-cli` package and its bundled assets) is a local, offline-capable
developer CLI that bootstraps and operates Spec-Driven Development workflows for AI coding
agents. These principles are derived from the patterns the codebase already enforces. They
are binding on all changes — including the `specify bundle` subcommand and any future
command group, integration, extension, preset, or workflow.

## Core Principles

### I. Code Quality & Architectural Discipline

The codebase follows a strict, registry-driven, layered architecture, and all changes MUST
preserve it.

- **Separate the CLI surface from importable logic.** User-facing commands live in Typer
  sub-apps (e.g. `commands/`, `*/_commands.py`); business logic lives in plain, importable
  modules with no `@app.command()` decorators. New features MUST keep orchestration logic
  testable independently of Typer.
- **Use the established extension pattern.** New agents/integrations MUST subclass one of the
  standard base classes (`MarkdownIntegration`, `TomlIntegration`, `YamlIntegration`,
  `SkillsIntegration`) and declare the required class attributes (`key`, `config`,
  `registrar_config`, and `context_file` where applicable). Extending `IntegrationBase`
  directly is permitted only when no base class fits, and the deviation MUST be justified.
- **Honor the single source of truth.** Built-ins are wired through the relevant registry
  (e.g. `INTEGRATION_REGISTRY` via `_register_builtins()`), with imports and registrations
  kept in alphabetical order. Duplicate keys MUST fail loudly rather than silently override.
- **Naming and typing are not optional.** Private modules/functions are `_`-prefixed and MUST
  NOT be imported across package boundaries. Every new module begins with
  `from __future__ import annotations` and uses modern type syntax (`dict[str, Any]`,
  `str | None`); legacy `Dict`/`List`/`Optional` forms are rejected.
- **Package directories use underscores; keys keep their canonical (often hyphenated) form**
  (e.g. package `kiro_cli/`, `key = "kiro-cli"`). For CLI-backed integrations the `key` MUST
  match the executable name so `shutil.which(key)` resolves.

**Rationale:** A registry-plus-base-class architecture is what lets dozens of integrations,
extensions, and workflows coexist with minimal coupling. Drift here multiplies maintenance
cost and breaks the "add one subclass, register once, ship a test" contract.

### II. Test-Backed Change (NON-NEGOTIABLE)

Every behavioral change MUST be accompanied by automated tests, and the suite is a hard gate.

- **Tests gate merges.** CI runs `pytest` across a matrix of ubuntu + windows × Python 3.11,
  3.12, and 3.13. Changes MUST pass on every cell of that matrix.
- **Parity invariants MUST hold.** Every integration MUST be present in the registry, have a
  `CommandRegistrar` config entry where required, and ship a dedicated
  `tests/integrations/test_integration_<key>.py` (hyphens in the key become underscores in the
  filename). These are enforced by parametrized tests (e.g. `test_registry.py`) and MUST NOT
  be weakened.
- **Follow pytest conventions.** Test modules/classes/functions use the `test_*` / `Test*`
  naming the project configures, run under `--strict-markers`, and isolate state with
  `tmp_path`, `monkeypatch`, and the autouse auth-isolation fixture. Platform-specific tests
  MUST be guarded (e.g. `@requires_bash`) rather than left to fail.
- **Security and idempotency tests are mandatory categories.** Path-traversal rejection,
  manifest hash integrity/symlink safety, and no-overwrite idempotency are covered by existing
  suites; changes touching file writes, path handling, or setup scripts MUST extend (never
  reduce) that coverage.
- **Network is mocked.** No test may make a real outbound network call; HTTP MUST be stubbed
  so the suite is deterministic and offline-runnable.

**Rationale:** The breadth of supported agents and the offline/air-gapped guarantees can only
be sustained by exhaustive, parametrized tests. The parity and security suites are what stop a
single new integration from regressing the whole matrix.

### III. CLI & User-Experience Consistency

The CLI presents one coherent surface; every command group MUST feel like the others.

- **Reuse the shared verb vocabulary.** Consumer-facing groups use the established verbs —
  `list`, `add`/`install`, `remove`, `search`, `info`, `update`, plus `enable`/`disable` and
  `set-priority` where relevant. New verbs MUST NOT be invented when an existing one fits, and
  any genuinely new verb MUST be justified.
- **Mirror the catalog-stack model.** Catalog-backed groups MUST expose
  `<group> catalog list|add|remove`, back it with a priority-ordered source stack (lower number
  = higher precedence) plus per-source install policy (`install-allowed` vs `discovery-only`),
  and fall back to a built-in default stack when no project config is present.
- **Register sub-apps the standard way.** Command groups are `typer.Typer(...)` instances
  attached via `app.add_typer(child, name="...")`, preferably through a modular
  `register(app)` function imported in `__init__.py`. Nesting MUST stay within ~2–3 levels.
- **Output is consistent and machine-friendly.** Human output uses the shared Rich
  conventions (e.g. `[green]✓[/green]` success, `[red]Error:[/red]` + non-zero exit on
  failure, actionable remediation in messages). Where a `--json` flag is offered, valid JSON
  goes to stdout and all other logging is redirected to stderr.
- **Interactions are safe and idempotent.** Destructive actions show what will change before
  confirming; "already installed / already present" outcomes succeed (exit 0) rather than
  error. User-facing command groups MUST be documented under `docs/reference/`.

**Rationale:** Predictability is the product. Users learn one set of verbs, one catalog model,
and one output grammar, then apply them to every group — including `specify bundle`.

### IV. Offline-First Performance & Resource Discipline

Spec Kit is a local CLI; responsiveness, offline operability, and graceful degradation are the
performance contract.

- **`specify init` and core scaffolding MUST work fully offline** using bundled `core_pack`
  assets. Asset resolution MUST prefer bundled assets, then a source checkout, before ever
  reaching the network.
- **Network use is lazy, bounded, and degradable.** Network calls happen only on explicit
  user commands, MUST set timeouts, MUST cache catalog results (1-hour TTL) and fall back to
  stale cache on failure, and MUST surface offline/rate-limit conditions as clear messages
  without crashing.
- **Keep startup cheap.** Avoid adding heavyweight work to import time. New optional
  subsystems SHOULD prefer lazy loading over unconditional eager imports so that unrelated
  commands (including `--help`) stay fast.
- **Filesystem writes are minimal and idempotent.** Installs MUST track files (SHA-256
  manifests), avoid clobbering user-modified content, only uninstall files whose hash still
  matches, and never follow symlinks out of the project root.

**Rationale:** Developers run this tool in air-gapped, enterprise, and flaky-network
environments. Offline-first behavior and idempotent, hash-tracked file operations are what
make it safe and fast to run repeatedly.

### V. Minimal Dependencies & Safe, Idempotent File Operations

The project guards its dependency surface and its on-disk footprint deliberately.

- **Zero new runtime dependencies by default.** The runtime dependency set is intentionally
  small and pinned to a minimum major version. Adding a dependency requires maintainer
  agreement and a justification that existing deps (typer, click, rich, pyyaml, packaging,
  platformdirs, pathspec, json5, readchar) cannot serve the need. New subsystems SHOULD reuse
  existing primitive machinery in-process rather than re-implementing or re-shipping it.
- **All paths are validated.** Any project-relative path derived from user/manifest/catalog
  input MUST be confined to the project root (`Path.relative_to` checks) and reject traversal
  payloads; symlink escapes MUST be refused.
- **Errors are explicit and chained.** Validate inputs up front, raise with actionable context
  (offending field/value plus a hint), and use `raise ... from exc` to preserve causes. I/O
  that can legitimately fail MUST degrade gracefully rather than emit a raw traceback.
- **Versioning follows SemVer.** User-visible and packaged behavior changes follow
  MAJOR.MINOR.PATCH semantics; backward-incompatible changes MUST be called out and justified.

**Rationale:** A lean, pinned dependency set and hardened, idempotent file handling are what
keep the tool trustworthy in enterprise and air-gapped contexts and cheap to maintain.

## Security & Cross-Platform Constraints

- **Cross-platform parity is required.** Code MUST run on Linux, macOS, and Windows and on
  Python 3.11–3.13. Windows specifics (UTF-8 stream reconfiguration, bash-dependent tests
  auto-skipping) MUST be respected; do not introduce POSIX-only assumptions without a guarded
  fallback.
- **Security tooling is a gate.** CodeQL and the project's security test suites
  (path-traversal, manifest/symlink hardening) MUST remain green. Network access MUST default
  to off in tests and be opt-in, timeout-bounded, and credential-isolated at runtime.
- **Formatting is enforced.** `.editorconfig` rules (LF endings, final newline, no trailing
  whitespace, 4-space Python / 2-space YAML-JSON-Markdown), `ruff check src/`, and
  `markdownlint-cli2` MUST pass.

## Development Workflow & Quality Gates

- **Branch naming** follows `<type>/<number>-<short-slug>` (or `<type>/<short-slug>` with no
  issue), with `<type>` ∈ {feat, fix, docs, community, chore}.
- **PRs are focused** and MUST: pass `ruff`, `pytest` (full matrix), markdown lint, and CodeQL;
  add/extend tests for new behavior; update user-facing docs (`README.md`, `docs/`,
  `spec-driven.md`) when behavior changes; and disclose any AI assistance used.
- **Slash-command-affecting changes** MUST be manually exercised through a coding agent and the
  results reported in the PR, per CONTRIBUTING.md.
- **Large or cross-cutting changes** (new templates, arguments, command groups) MUST be agreed
  with maintainers before implementation.

## Governance

This constitution supersedes ad-hoc convention where they conflict; the existing codebase
patterns it codifies remain authoritative references.

- **Authority.** Principles I–V are binding gates. The `## Constitution Check` section of the
  plan template MUST be evaluated against these principles, and `/speckit.analyze` treats
  conflicts with a MUST as CRITICAL. Violations are resolved by changing the spec, plan, or
  tasks — not by diluting a principle.
- **Amendments.** Changes to this document require a PR with rationale, maintainer approval,
  and a version bump per the policy below. Any amendment MUST propagate to dependent templates
  and command guidance in the same change, recorded in the Sync Impact Report at the top of
  this file.
- **Versioning policy (SemVer for governance).** MAJOR = backward-incompatible governance or
  principle removal/redefinition; MINOR = a new principle/section or materially expanded
  guidance; PATCH = clarifications and non-semantic refinements.
- **Compliance review.** Every PR and review MUST verify compliance with these principles.
  Added complexity or any deviation MUST be justified in-PR (and, for plans, in the plan's
  Complexity Tracking section). Unjustified violations block merge.

**Version**: 1.0.0 | **Ratified**: 2026-06-19 | **Last Amended**: 2026-06-19
