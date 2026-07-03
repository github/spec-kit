# EARS Requirements Syntax Extension

Author, lint, and convert requirements using **EARS (Easy Approach to Requirements Syntax)** - the five industry-standard sentence patterns for writing unambiguous, testable requirements. Each command reads and writes Markdown under `.specify/ears/<slug>/`, keeping EARS work self-contained and optional.

## Overview

EARS was developed at Rolls-Royce to remove ambiguity from natural-language requirements and is widely used in aerospace, automotive, and other safety-critical domains. It constrains each requirement to one of five patterns built around the mandatory modal **shall**:

| Pattern | Template |
|---------|----------|
| **Ubiquitous** | The `<system>` shall `<response>`. |
| **Event-Driven** | When `<trigger>`, the `<system>` shall `<response>`. |
| **State-Driven** | While `<state>`, the `<system>` shall `<response>`. |
| **Unwanted Behavior** | If `<condition>`, then the `<system>` shall `<response>`. |
| **Optional Feature** | Where `<feature>`, the `<system>` shall `<response>`. |

This extension delivers three commands that any AI coding agent can drive:

1. **Author** - turn a feature idea into a fresh EARS requirements set.
2. **Lint** - audit existing requirements for EARS conformance and ambiguity (read-only).
3. **Convert** - rewrite free-form requirements into EARS with a traceability matrix.

The commands communicate through Markdown files in a single per-topic directory:

```
.specify/ears/<slug>/
├── requirements.md   # written by speckit.ears.author and speckit.ears.convert
└── lint-report.md    # written by speckit.ears.lint
```

## Commands

| Command | Description | Output |
|---------|-------------|--------|
| `speckit.ears.author` | Drafts requirements for a feature directly in EARS format, classified by pattern. | `.specify/ears/<slug>/requirements.md` |
| `speckit.ears.lint` | Audits existing requirements for EARS conformance and ambiguity, with suggested rewrites. | `.specify/ears/<slug>/lint-report.md` |
| `speckit.ears.convert` | Rewrites free-form requirements into EARS and records original-to-EARS traceability. | `.specify/ears/<slug>/requirements.md` |

## Slug Conventions

A *slug* is the per-topic directory name under `.specify/ears/`. It is the handle the three commands share.

- **User-provided**: any shape the user wants, normalized to lowercase kebab-case (e.g. `task-board`, `checkout-flow`, `auth-service`). The slug is preserved verbatim after normalization.
- **Asked for**: in interactive use, `speckit.ears.author` asks for a slug when none is supplied, suggesting a kebab-case default derived from the feature summary.
- **Automated**: when no human is available to answer, the agent generates a slug itself. A generated slug **MUST** produce a unique directory for new work - if `.specify/ears/<slug>/` already exists, the agent appends the shortest disambiguating suffix needed (`-2`, `-3`, …) or a short date (`-20260605`). Existing directories are never overwritten without confirmation.

## Installation

```bash
# Install the bundled EARS extension (no network required)
specify extension add ears
```

## Disabling

```bash
# Disable the EARS extension
specify extension disable ears

# Re-enable it
specify extension enable ears
```

## Typical Flow

```bash
# 1. Author EARS requirements from a feature idea
/speckit.ears.author "A kanban task board where users drag tasks between columns" slug=task-board

# 2. Audit an existing spec's requirements for EARS conformance
/speckit.ears.lint .specify/specs/001-task-board/spec.md slug=task-board

# 3. Convert free-form requirements into EARS with traceability
/speckit.ears.convert slug=task-board
```

EARS work is additive: it produces reference artifacts under `.specify/ears/` and never changes the default Spec Kit workflow. Fold the results into a spec and continue with `/speckit.plan` when you are ready.

## Guardrails

- `speckit.ears.lint` is **read-only**. It never modifies the source requirements, `spec.md`, or any file other than its own `lint-report.md`; all rewrites are suggestions.
- `speckit.ears.author` and `speckit.ears.convert` write only inside `.specify/ears/<slug>/`. They may offer to insert a generated block into an existing spec, but only apply it after explicit confirmation.
- None of the commands overwrite an existing report without confirmation; in automated mode they refuse and pick a new unique slug instead.
- Conformance is never over-claimed: an honest audit of largely non-conformant requirements is the point, and statements too ambiguous to rewrite safely are flagged `[NEEDS CLARIFICATION]` rather than guessed.

## Hooks

This extension registers no hooks. The three commands are always invoked explicitly by the user.
