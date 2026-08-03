# Constitution Template Sync

An **opt-in** preset that restores `/constitution`'s ability to propagate amended guidance into your
project's own templates and command files. After you update the constitution, it aligns
`plan-template.md`, `spec-template.md`, `tasks-template.md`, project-local command files, and
guidance docs so they reflect the current principles.

This propagation used to be built into `/constitution`; it was dropped when the command moved to the
preset model. Installing this preset opts you back into it: you get the guidance materialized into
reviewed, committed artifacts instead of relying on runtime resolution alone.

> **What you're opting into.** Propagation was removed deliberately — it duplicates the constitution
> as the source of truth and can fight the composition stack (materialized edits get shadowed or
> clobbered on the next recompose). This preset knowingly **reintroduces** that behavior, and those
> tradeoffs, for teams that want it. Read the [caveats](#caveats-you-take-on) before installing.

For most projects the default composable stack is the **recommended** approach, and at organization
scale it is usually the stronger governance model. Runtime resolution keeps the live constitution as
the single source of truth (nothing to re-sync, so nothing drifts), and the stack composes the
**entire** Spec Kit ecosystem — not just the SDD commands, but every command, template, script and
extension — with explicit priority levels, strategies, and independent versioning. It is a
capability, not automatic governance: a core team authors its own organizational presets and
extensions, then owns, versions, and audits that policy in one place and rolls it across many
repositories, instead of scattering frozen, per-repo copies no central team can see. This preset is
a supported escape hatch for teams whose workflow depends on reviewing materialized artifacts
directly — useful as a bridge, though for org-wide policy the better long-term path is usually a
versioned preset a core team maintains.

## What it does

Ships a single `wrap`-strategy override of `speckit.constitution`. It composes on top of the
current core command (via `{CORE_TEMPLATE}`), so it stays forward-compatible with core changes, and
appends a propagation pass that, after the constitution is written:

- Aligns `plan/spec/tasks-template.md` in `.specify/templates/` with the updated principles.
- Updates **project-local** command files and guidance docs to correct stale references.
- Extends the Sync Impact Report in `.specify/memory/constitution.md` with the files it touched.

## What it does not do

- It does **not** change behavior for anyone who does not install it — the default runtime
  resolution model is untouched.
- It does **not** disable runtime resolution. `plan`, `tasks`, and `analyze` still read the live
  constitution every run; this preset adds materialized copies on top — it does not replace the
  source of truth.
- It does **not** edit versioned, package-owned files — templates or command files provided or
  wrapped by another preset or extension. Those are recomposed from the resolution stack, so it
  only ever writes into your project's own `.specify/templates/` scaffolds and command files that
  are not managed by a preset/extension.

## When to use it

Install it **only** if your team treats the materialized templates and commands as
**reviewed, committed artifacts** — for example, if `plan-template.md`'s Constitution Check is
read in PRs as "here are our current gates" and is expected to track the constitution.

If you rely on the default runtime-resolution model, you do **not** need this preset: the live
constitution is already the single source of truth and there is nothing to sync.

## Caveats you take on

The preset resolution stack is how Spec Kit composes templates and commands going forward: they are
**layered, package-owned artifacts recomposed on demand**, not frozen files you edit in place.
Propagation is the opposite idea — it **materializes** guidance into files and freezes it. That
tension is the main thing to understand before installing:

- **Materialized copies can drift.** Anything propagated is a snapshot; if you amend the
  constitution and do not re-run `/constitution`, the copies fall out of sync. The default runtime
  model has no drift because it reads the live constitution every run.

- **Edits to composed files do not survive reconciliation.** If the rest of your SDD flow is
  preset/extension-managed, the commands it materializes (`speckit.plan`, `speckit.specify`,
  `speckit.tasks`, `speckit.analyze`, `speckit.implement`, …) are recomputed from the stack. Any
  guidance propagated into them is clobbered the next time the stack reconciles — on
  `specify integration use <key>` / `switch`, `specify integration upgrade`, or any preset/extension
  install or remove. The same applies to templates owned by another preset/extension. This is why
  the preset restricts itself to project-local files; propagation is reliable **only** for
  artifacts you own outright.

- **A pre-filled Constitution Check can bias `/plan`.** Materializing concrete gates into
  `plan-template.md` replaces the runtime pointer, so the first `/plan` pass may anchor on the
  frozen text. Keep the pointer unless you specifically want committed gates.

**Bottom line:** this preset fits projects whose governed templates and commands are project-local
artifacts they review, with the rest of the SDD flow on the plain bundled core. If your
`plan`/`specify`/`tasks`/`analyze` commands or templates come from other presets or extensions,
prefer the default runtime-resolution model.

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

To move back to runtime resolution, reset each materialized `## Constitution Check` section in
`.specify/templates/plan-template.md` to the pointer:

```text
## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]
```

Then remove this preset. See `docs/upgrade.md` for details.

## License

MIT
