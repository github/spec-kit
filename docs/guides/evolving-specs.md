# Evolving Specs in Existing Projects

If the repository has not been initialized with Spec Kit yet, start with
[Adopting Spec Kit in an Existing Project](existing-projects.md). This page
covers how to maintain feature artifacts after delivery and deliver subsequent
changes.

Existing projects need two separate maintenance loops:

- **Spec Kit project-file updates** refresh managed commands, scripts,
  templates, and shared memory files.
- **Feature artifact evolution** maintains repository-specific `specs/`
  artifacts according to the team's post-delivery persistence convention.

Use the [upgrade workflow](../upgrade.md) when you need newer Spec Kit project
files. Use one of the artifact persistence models below to decide how completed
feature artifacts are maintained when requirements or implementation insights
change an existing project. None is required or the default.

For the conceptual model definitions, see
[Spec Persistence Models](../concepts/spec-persistence.md).

## Shared Feature Delivery Loop

All three persistence models use the same delivery/completeness process:
specify -> plan -> tasks -> implement -> converge. Repeat implementation and
convergence until the agreed feature is complete.

For a new feature or a later change requiring implementation:

1. Make the intended contract explicit in `spec.md`. Use `/speckit.specify` to
   create a new feature directory under `specs/`, or revise an existing spec
   according to your team's persistence convention.
2. Run `/speckit.plan` or revise `plan.md` to define the implementation approach.
3. Run `/speckit.tasks` or revise `tasks.md` to derive the work breakdown.
   Run `/speckit.analyze` before implementation to catch cross-artifact gaps.
4. Run `/speckit.implement` and review the resulting code and artifact diffs.
5. Run `/speckit.converge` to assess implementation against the spec, plan, and
   tasks, governed by the constitution. If it appends tasks for remaining gaps,
   repeat `/speckit.implement` and `/speckit.converge` until the agreed feature
   is complete.

Converge is append-only: its only possible write is adding tasks to `tasks.md`.
It does not choose a persistence strategy or rewrite the artifacts to accept
code as a replacement for documented intent.

Core has no dedicated command that automatically reconciles differences among
`spec.md`, `plan.md`, and `tasks.md`. `/speckit.analyze` reports inconsistencies
without changing the artifacts. A team can reconcile them directly, or an
extension can provide commands or hooks that do so during or after delivery
according to that extension's documented behavior. Those actions do not change
the responsibilities of the core commands.

Discoveries may arise during delivery under any model. If they lead to an
agreed change of intent, make the revised contract explicit in the artifacts
and deliver against it. Reconciliation may occur during delivery, but the
maintenance choices below describe what the team persists after delivery; they
do not replace this loop.

## Flow-Forward Spec

Use flow-forward when each completed feature directory should remain a
historical record.

After delivery, retain the completed artifacts without changing them. For
another feature or a follow-up change requiring implementation, create a new
feature directory and use the shared delivery loop above.

The previous feature directory remains intact for audit, comparison, or
explaining how the project reached its current state. Use clear feature names or
cross-links when a new directory supersedes or extends earlier work.

## Living Spec

Use living spec when `spec.md` is the contract and `plan.md` and `tasks.md` are
derived from it.

After delivery, maintain `spec.md` as the contract. When intended behavior
changes, revise the existing `spec.md` first. Then reconcile downstream
artifacts so they match the updated spec:

1. Start from a clean working tree or a dedicated branch so every artifact
   change is reviewable.
2. Update `spec.md` with the intended contract.
3. Reconcile `plan.md` and `tasks.md` directly or through an extension according
   to the team's documented convention.
4. Run `/speckit.analyze` to report any remaining gaps between the spec, plan,
   and tasks.

These steps maintain the artifact set; they do not deliver changed behavior.
If the revised contract requires implementation, use the shared delivery loop
above against those explicit intended artifacts.

Preserve important implementation rationale before replacing derived artifacts.
If a plan or task list contains decisions that still matter, carry them forward
explicitly.

## Flow-Back Spec

Use flow-back when accepted discoveries inform maintenance across the artifact
set after delivery.

A discovery may have originated in `spec.md`, `plan.md`, `tasks.md`, or the
implementation, including during delivery. For post-delivery maintenance,
the team decides which discoveries to accept and brings the artifacts into
alignment with that agreed direction:

1. Capture the discovery in the artifact closest to the work.
2. Decide whether it changes intended behavior, implementation strategy, task
   breakdown, or only code.
3. Update any other artifacts that now disagree with the accepted direction.
4. Run `/speckit.analyze` to check for gaps across `spec.md`, `plan.md`, and
   `tasks.md`.

The implementation provides evidence for the team's decision; accepting code
does not automatically make it the intended contract. Reconcile the artifacts
directly or through an extension. Analyze and converge do not provide automatic
all-artifact reconciliation, and no core amendment command is required. If the
agreed direction requires implementation, use the shared delivery loop above
against explicit intended artifacts.

Flow-back is flexible, but it requires discipline. Do not leave a lower-level
change in `tasks.md` or code if `spec.md` still says something different and the
spec is meant to remain trustworthy.

## Before Updating Spec Kit Project Files

Before refreshing Spec Kit project files with the terminal command
`specify init --here --force --integration <your-agent>`, protect any
project-specific material that lives outside `specs/`, especially
`.specify/memory/constitution.md` and customized files under
`.specify/templates/` or `.specify/scripts/`. Use `<your-agent>` for the AI
coding agent integration used by the target project.

Your `specs/` directory is not part of the template package, but shared project
files can be overwritten by a forced refresh.
