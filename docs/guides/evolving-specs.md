# Evolving Specs in Existing Projects

Existing projects need two separate maintenance loops:

- **Spec Kit project-file updates** refresh managed commands, scripts,
  templates, and shared memory files.
- **Feature artifact evolution** keeps repository-specific `specs/` artifacts
  aligned with the code and product behavior you intend to ship.

Use the [upgrade workflow](../upgrade.md) when you need newer Spec Kit project
files. Use one of the artifact persistence models below when requirements or
implementation insights change an existing project.

For the conceptual model definitions, see
[Spec Persistence Models](../concepts/spec-persistence.md).

## Flow-Forward Spec

Use flow-forward when each feature directory should remain a historical record.

When you add another feature or make a substantial follow-up change, create a
new feature spec through your installed `/speckit.specify` command and continue
through the standard flow:

1. Run `/speckit.specify` to create a new feature directory under `specs/`.
2. Run `/speckit.plan` to define the implementation approach.
3. Run `/speckit.tasks` to derive the work breakdown.
4. Run `/speckit.implement` and review the resulting code and artifact diffs.
5. Run `/speckit.converge` to verify completeness and generate tasks for remaining gaps. If tasks are appended, repeat `/speckit.implement` and `/speckit.converge` until the feature is fully complete.

The previous feature directory remains intact for audit, comparison, or
explaining how the project reached its current state. Use clear feature names or
cross-links when a new directory supersedes or extends earlier work.

## Living Spec

Use living spec when `spec.md` is the contract and `plan.md` and `tasks.md` are
derived from it.

When intended behavior changes, revise the existing `spec.md` first. Then
regenerate or manually revise downstream artifacts so they match the updated
spec:

1. Start from a clean working tree or a dedicated branch so every generated
   change is reviewable.
2. Update `spec.md` with `/speckit.clarify` or an explicit edit.
3. Rerun `/speckit.plan` or revise `plan.md` so the technical approach matches
   the revised spec.
4. Rerun `/speckit.tasks` or revise `tasks.md` so implementation work matches
   the revised plan.
5. Run `/speckit.analyze` before implementation resumes to catch gaps between
   the spec, plan, and tasks.
6. Run `/speckit.implement`, then review the code and artifact diffs together.
7. Run `/speckit.converge` to assess completion and append any remaining work to `tasks.md`. If tasks are appended, repeat `/speckit.implement` and `/speckit.converge` until the feature is fully complete.

Preserve important implementation rationale before replacing derived artifacts.
If a plan or task list contains decisions that still matter, carry them forward
explicitly.

## Flow-Back Spec

Use flow-back when implementation discoveries are allowed to reshape the
artifact set.

In this model, the first useful edit can happen wherever the insight lands:
`spec.md`, `plan.md`, `tasks.md`, or the implementation. After the change, bring
the artifact set back into alignment:

1. Capture the discovery in the artifact closest to the work.
2. Decide whether it changes intended behavior, implementation strategy, task
   breakdown, or only code.
3. Update any other artifacts that now disagree with the accepted direction.
4. Run `/speckit.analyze` to check for gaps across `spec.md`, `plan.md`, and
   `tasks.md`.
5. Continue implementation only after the artifact set describes the behavior
   and approach you want future contributors to trust.

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
