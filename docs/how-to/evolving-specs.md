# How to evolve specifications in an existing project

Use this guide when requirements change or implementation discoveries call for
a revision to an existing feature. It covers making the next intended contract
explicit and delivering against it, not choosing which artifacts to retain
afterward.

If the repository has not been initialized with Spec Kit yet, start with
[Adopting Spec Kit in an Existing Project](existing-projects.md).

## Assess the Change

Identify the affected behavior and review the available feature artifacts,
implementation, tests, and maintained design or product documentation.
Distinguish a defect against agreed intent from a proposed change to that intent.
The implementation is evidence for the discussion, not a replacement source of
requirements.

Decide whether the discovery changes intended behavior, implementation strategy,
task breakdown, or only code. A discovery may originate in a spec, plan, task
list, or the implementation, including during delivery. Its origin does not
determine which artifact is authoritative.

## Make the Revised Intent Explicit

Start from a clean working tree or a dedicated branch so every artifact change
is reviewable. Follow the team's chosen persistence convention when deciding
whether to create a new feature directory or revise retained artifacts.
If previous feature artifacts were retired, use the maintained requirements and
decision records to establish context rather than assuming the constitution
alone specifies the feature.

1. Write the intended contract in `spec.md`. Use `/speckit.specify` to create a
   new feature directory under `specs/`, or revise an existing spec.
2. Run `/speckit.plan` or revise `plan.md` to define the implementation approach.
3. Run `/speckit.tasks` or revise `tasks.md` to derive the work breakdown.
4. Run `/speckit.analyze` to report cross-artifact inconsistencies before
   implementation.

Core has no dedicated command that automatically reconciles differences among
`spec.md`, `plan.md`, and `tasks.md`. Analyze reports inconsistencies without
editing artifacts. Reconcile them directly, or use an extension according to
its documented behavior. Preserve important implementation rationale before
replacing derived artifacts.

If the team accepts a discovery that changes intent, reflect that agreement in
the affected artifacts. Do not leave a lower-level change in tasks or code
contradicting a spec that is meant to remain trustworthy.

## Deliver and Assess the Change

All persistence models use the same delivery/completeness process:
specify -> plan -> tasks -> implement -> converge.

1. Run `/speckit.implement` against the explicit intended artifacts.
2. Review the resulting implementation and artifact diffs.
3. Run `/speckit.converge` to assess implementation against the spec, plan, and
   tasks, governed by the constitution.
4. If converge appends tasks for remaining gaps, repeat implementation and
   convergence until the agreed feature is complete.

Converge is append-only: its only possible write is adding remaining work to
`tasks.md`. It does not rewrite artifacts to accept code as a replacement for
documented intent. Neither analyze nor converge selects a persistence strategy,
and extension-provided reconciliation does not change these core command
responsibilities.

Revising artifacts does not by itself deliver changed behavior. When a revision
requires implementation, complete this delivery loop. After delivery, apply the
team's retention and maintenance policy separately.

## See also

- [Persisting specifications](persisting-specs.md) - Choose what survives
  delivery and how retained artifacts are maintained.
- [Upgrade Spec Kit](../upgrade.md) - Refresh managed project files rather than
  changing feature requirements.
