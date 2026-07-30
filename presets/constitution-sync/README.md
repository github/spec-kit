# Constitution Template Sync

An **opt-in** preset that restores the pre-0.14.4 `/constitution` behavior: after the
constitution is updated, it propagates the amended guidance into the project's dependent
templates and installed command files.

## Background

Through 0.14.3, `/constitution` performed a "consistency propagation checklist" — it read
`.specify/templates/plan-template.md`, `spec-template.md`, `tasks-template.md`, the installed
Spec Kit command files, and guidance docs, and updated them to match the amended principles.

[#3790](https://github.com/github/spec-kit/pull/3790) (shipped in 0.14.4) **removed** that
propagation from the core command. The default model is now **runtime resolution**: `plan`,
`tasks`, and `analyze` read `.specify/memory/constitution.md` live on every run, so the
templates only need to carry a pointer (`plan-template.md` ships
`[Gates determined based on constitution file]`) rather than a materialized copy. This avoids
duplicating the source of truth and avoids fighting the preset/override composition system.

## When to use this preset

Install it **only** if your team treats the materialized templates as **reviewed, committed
artifacts** — for example, if `plan-template.md`'s Constitution Check is read in PRs as "here are
our current gates" and is expected to stay in sync with the constitution.

If you rely on the default runtime-resolution model, you do **not** need this preset. Your
workflow is already correct without it: the live constitution is the single source of truth.

## What it does

This preset ships a single `wrap`-strategy override of `speckit.constitution`. It composes on top
of the current core command (via `{CORE_TEMPLATE}`), so it stays forward-compatible with core
changes, and appends a propagation pass that:

- Aligns `plan/spec/tasks-template.md` with the updated principles.
- Scans installed command files for stale agent-specific references.
- Updates guidance-doc references to changed principles.
- Extends the Sync Impact Report with the templates it touched.

It deliberately **does not** edit versioned preset- or extension-provided template files — those
are owned by their packages and recomposed on update.

## Interaction with the resolution stack (important limitation)

This preset and the preset resolution stack are built on **opposing philosophies**, and they can
bite each other:

- The resolution stack (the default model since #3790) treats templates and commands as
  **layered, package-owned artifacts that are recomposed on demand** — nothing is meant to be a
  frozen copy.
- Auto-propagation does the **opposite**: it **materializes** constitutional guidance *into*
  template files and freezes it there.

So if a template you propagate into is actually **provided by another preset or extension in your
stack**, the two mechanisms fight: your propagated gate text is clobbered the next time that
package is reconciled/updated, and your hand edits are lost. For the same reason the wrapper only
ever writes into the project's **own** `.specify/templates/` scaffolds and installed command files
— never into stack-owned template layers.

Practical guidance:

- This preset is safe and useful when your governed templates are **project-local scaffolds** you
  own and review.
- If your `plan/spec/tasks` templates come from **other presets or extensions**, propagation will
  not stick — keep the default runtime-resolution model instead, where the live constitution is
  read on every run and there is nothing to sync.

## Tradeoffs

- Re-introduces a materialized copy of constitutional guidance in the templates, which can drift
  if `/constitution` is not re-run. The default runtime model does not have this problem.
- Materializing concrete gates into `plan-template.md` replaces the runtime pointer; a pre-filled
  Constitution Check can bias the first `/plan` pass. Keep the pointer unless you specifically
  want committed gates.

## Installation

```bash
# constitution-sync is a bundled preset — no download needed
specify preset add constitution-sync
```

## Development

```bash
# Test from local directory
specify preset add --dev ./presets/constitution-sync

# Verify the wrapped command resolves
specify preset resolve speckit.constitution

# Remove when done
specify preset remove constitution-sync
```

## Migrating back to the default

If you decide to move to runtime resolution, reset each materialized
`## Constitution Check` section in `.specify/templates/plan-template.md` back to the pointer:

```text
## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]
```

Then remove this preset. See `docs/upgrade.md` for details.

## License

MIT
