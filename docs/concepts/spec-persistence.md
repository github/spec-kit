# Spec Persistence Models

Spec Kit intentionally leaves teams in control of what happens to `spec.md`,
`plan.md`, and `tasks.md` after requirements change. The toolkit gives you a
repeatable workflow, but it does not force one artifact maintenance strategy.

This page names three common models so teams can make that choice explicit.
None is the default, and none is required by Spec Kit.

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
requirements change? The models below describe that mutation strategy.

## Flow-Back Spec

Use flow-back when `spec.md`, `plan.md`, `tasks.md`, and the implementation are
all allowed to inform each other.

In this model, edits can begin in any artifact. A developer might update
`tasks.md` during implementation, revise `plan.md` after a technical discovery,
or adjust `spec.md` after a product clarification. The team then reconciles the
artifact set manually so the final project history still makes sense.

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

In this model, teams update `spec.md` first and then regenerate or revise
`plan.md` and `tasks.md` from that source. The plan and task list are still
valuable, but they are treated as disposable derivations rather than permanent
sources of truth.

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

| Model | Mutation rule | Best fit | Watch out for |
|---|---|---|---|
| Flow-back spec | Edit any artifact, then reconcile | Fast iteration and close collaboration | Silent drift between artifacts |
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
