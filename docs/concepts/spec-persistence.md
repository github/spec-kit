# Spec Persistence Models

Spec Kit intentionally leaves teams in control of what happens to `spec.md`,
`plan.md`, and `tasks.md` after a feature is delivered. The toolkit gives you a
repeatable workflow, but it does not force one artifact maintenance strategy.

This page names three common models so teams can make that choice explicit.
None is the default, and none is required by Spec Kit.

## Shared Delivery, Separate Persistence

All three models use the same feature delivery process:
specify -> plan -> tasks -> implement -> converge. Repeat implement and
converge until the agreed feature is complete.

Converge assesses the implementation against the feature's spec, plan, and
tasks, governed by the constitution. It is append-only: its only possible write
is adding remaining work to `tasks.md`. It does not select a persistence model,
rewrite intent to match code, or treat approval of code as agreement with
documented intent.

The core workflow does not reconcile differences among `spec.md`, `plan.md`,
and `tasks.md`. Analyze reports inconsistencies without editing artifacts, and
converge only appends missing implementation work to `tasks.md`. Teams can
reconcile artifacts themselves, and extensions can provide their own commands
or hooks to do so during or after delivery. That behavior belongs to the team
or extension; it does not change the responsibilities of the core commands.

Persistence is the team's choice of how to maintain artifacts **after
delivery**, not an alternative way to deliver or determine completeness.
Discoveries can occur during implementation, but their timing does not define
the persistence model. Reconciliation can also occur before delivery without
becoming part of the core workflow or the persistence strategy. If the team
agrees to change the intended contract, make that intent explicit in the
artifacts and deliver against it.

A later change requiring implementation still goes through the shared delivery
process and convergence against its explicit intended artifacts, whether those
artifacts are new or revised. See
[Evolving Specs in Existing Projects](../guides/evolving-specs.md) for practical
guidance.

## Two Separate Questions

Spec-driven development has a temporal question: how long should the
specification matter? One
[overview of SDD tooling](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
frames that lifecycle in three levels:

- **Spec-first**: write a spec before coding, then allow it to be discarded.
- **Spec-anchored**: keep the spec after implementation and use it for future
  changes.
- **Spec-as-source**: treat the spec as the only human-edited source and
  regenerate implementation artifacts from it.

Spec Kit also exposes a second question: what happens to the artifact set when
requirements change after delivery? The models below describe that maintenance
strategy.

## Flow-Back Spec

Use flow-back when `spec.md`, `plan.md`, `tasks.md`, and the implementation are
all allowed to inform each other.

After delivery, accepted discoveries can inform maintenance edits to any
artifact. The team decides what those discoveries mean for intended behavior,
technical approach, or task breakdown. The team can reconcile `spec.md`,
`plan.md`, and `tasks.md` itself or use an extension whose documented behavior
does so. The implementation is evidence for that discussion, not a replacement
source of intent.

This is a team-owned maintenance convention, not a requirement for a new core
amendment command or an artifact-rewriting role for analyze or converge.
Extension-provided reconciliation remains extension behavior, whether it runs
during or after delivery. If reconciliation identifies implementation work,
deliver that change through the shared process against the explicit intended
artifacts.

Flow-back works well when:

- the team is small enough to notice and reconcile drift quickly
- implementation discoveries are expected to reshape the original plan
- speed matters more than preserving each intermediate decision as immutable
  history

The main risk is silent divergence. If the team changes lower-level artifacts
without reflecting the decision back into `spec.md`, future contributors may
not know which artifact to trust.

## Flow-Forward Spec

Use flow-forward when each feature directory should remain a historical record.

In this model, completed artifacts are treated as immutable. When requirements
change, the team creates a new feature directory instead of mutating the
existing `spec.md`, `plan.md`, or `tasks.md`. The older directory remains useful
for audit, comparison, or explaining how the project reached its current state.

Flow-forward works well when:

- auditability and traceability matter
- features are well-scoped and rarely revisited in place
- the team wants a clear sequence of requirement changes over time

The main tradeoff is duplication. Related decisions can be spread across
multiple feature directories, so teams need naming, linking, or review habits
that make the lineage easy to follow.

## Living Spec

Use living spec when `spec.md` is the contract and the other artifacts are
derived from it.

After delivery, teams maintain `spec.md` as the contract, updating it first when
intended behavior changes, then regenerating or revising `plan.md` and
`tasks.md` from that source. The plan and task list are still valuable, but they
are treated as disposable derivations rather than permanent sources of truth.

Living spec works well when:

- the product contract is stable enough to own the workflow
- the team is comfortable regenerating derived artifacts after spec changes
- consistency between requirements and implementation matters more than keeping
  every intermediate plan intact

The main risk is losing useful implementation rationale if derived artifacts are
discarded without preserving important decisions elsewhere.

## Choosing a Model

The model is a team convention, not a CLI setting. A project can even use
different models in different areas, as long as contributors know which one
applies.

| Model | Post-delivery maintenance rule | Best fit | Watch out for |
|---|---|---|---|
| Flow-back spec | Reflect accepted discoveries in any artifact, then reconcile | Fast iteration and close collaboration | Silent drift between artifacts |
| Flow-forward spec | Create a new feature directory for new requirements | Audit trails and historical clarity | Duplicate or fragmented context |
| Living spec | Edit `spec.md`; regenerate derived artifacts | Spec as contract | Lost rationale in regenerated files |

If your team has not chosen a model yet, start by answering two questions:

1. Should completed feature directories be historical records or editable work
   areas?
2. Is `spec.md` the single source of truth, or are `plan.md` and `tasks.md`
   allowed to become co-equal sources?

Once those answers are clear, document the convention in your project
constitution or team onboarding notes so future contributors know how to handle
changes.
