# How to persist specifications after delivery

Spec Kit intentionally leaves teams in control of what happens to `spec.md`,
`plan.md`, and `tasks.md` after a feature is delivered. The toolkit gives you a
repeatable workflow, but it does not force one artifact maintenance strategy.

This page describes four models so teams can make that choice explicit.
None is the default, and none is required by Spec Kit.

All four retain the constitution as the project's overarching specification:
the principles, constraints, and quality expectations that govern every feature.
Feature specifications describe the behavior being delivered. The models differ
in what feature artifacts persist alongside that shared foundation, not in
whether the constitution continues to govern the project.

## Shared Delivery, Separate Persistence

Persistence is the team's choice of what to retain and maintain **after
delivery**, not an alternative way to deliver or determine completeness. All
four models use the same delivery process. Discoveries and artifact
reconciliation can occur during delivery under any model; their timing does not
define the persistence strategy.

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

Spec Kit also exposes a second question: which feature artifacts should persist
after delivery, and how should retained artifacts evolve when requirements
change? The models below describe that retention and maintenance strategy.

## Flow-Back Spec

Use flow-back when `spec.md`, `plan.md`, `tasks.md`, and the implementation are
all allowed to inform each other.

After delivery, accepted discoveries can inform maintenance edits to any
artifact. The team decides what those discoveries mean for intended behavior,
technical approach, or task breakdown. The team can reconcile `spec.md`,
`plan.md`, and `tasks.md` itself or use an extension whose documented behavior
does so. The implementation is evidence for that discussion, not a replacement
source of intent.

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
that make the lineage easy to follow. Use clear feature names or cross-links
when a new directory supersedes or extends earlier work.

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

## Constitution-Only

Use constitution-only when the constitution should be the only long-lived
document from the Spec Kit delivery artifact set in version control.

Feature artifacts still support specification, planning, implementation, and
review through the shared delivery process. After delivery, the team retires
them from the repository's maintained content. They may be archived externally,
such as with a pull request or in time-limited artifact storage, or discarded
under the team's retention policy. This is a spec-first lifecycle choice, not
a way to skip feature specifications during delivery.

The constitution remains the overarching project specification, but it does not
replace feature requirements, acceptance criteria, or implementation rationale.
Preserve any enduring knowledge in an agreed home, such as maintained product
documentation, design records, or an issue tracker, before retiring artifacts.
Constitution-only does not mean that the constitution is the project's only
lasting documentation.

Constitution-only works well when:

- the team wants feature artifacts for delivery without maintaining them afterward
- enduring requirements and decisions already have another maintained home
- keeping generated feature artifacts out of repository history reduces noise

Spec Kit's own repository illustrates this choice: it tracks
`.specify/memory/constitution.md`, while `specs/` is gitignored and feature
artifacts are not tracked. Enduring knowledge also lives in design documents,
documentation, tests, and contributor guidance. Excluding feature artifacts
from version control does not establish whether they are deleted or archived.

The main risk is losing intent and rationale that cannot be reliably recovered
by regenerating artifacts. External archival and deletion are team-owned
policies, not automatic Spec Kit behavior.

### Retiring Feature Artifacts

After delivery and review are complete:

1. Preserve enduring requirements, acceptance criteria, and decisions in their
   agreed home. Amend the constitution only when governing principles or
   constraints change; do not turn it into a collection of feature specifications.
2. Archive feature artifacts externally or discard them according to the team's
   retention policy. If reviewers still need them, provide an agreed review
   location before removing local copies.
3. Exclude future delivery artifacts from version control, or remove completed
   tracked artifacts through a reviewed change. Adding `specs/` to `.gitignore`
   does not untrack files already committed or erase repository history.

## Choosing a Model

The model is a team convention, not a CLI setting. A project can even use
different models in different areas, as long as contributors know which one
applies.

| Model | Post-delivery maintenance rule | Best fit | Watch out for |
|---|---|---|---|
| Flow-back spec | Reflect accepted discoveries in any artifact, then reconcile | Fast iteration and close collaboration | Silent drift between artifacts |
| Flow-forward spec | Create a new feature directory for new requirements | Audit trails and historical clarity | Duplicate or fragmented context |
| Living spec | Edit `spec.md`; regenerate derived artifacts | Spec as contract | Lost rationale in regenerated files |
| Constitution-only | Retain the constitution; retire completed feature artifacts from the repository | Delivery artifacts with enduring knowledge maintained elsewhere | Lost requirements or rationale without a lasting home |

If your team has not chosen a model yet, start by answering three questions:

1. Should completed feature artifacts remain in the repository? If not, where
   will enduring requirements and decisions live, and will artifacts be archived
   or discarded?
2. If retained, should completed feature directories be historical records or
   editable work areas?
3. Is a retained `spec.md` the single source of truth, or are `plan.md` and
   `tasks.md` allowed to become co-equal sources?

Once those answers are clear, document the convention in your project
constitution or team onboarding notes so future contributors know how to handle
changes.

## See also

- [Evolving specifications](evolving-specs.md) - Make intent explicit and deliver
  subsequent changes under the chosen persistence convention.
