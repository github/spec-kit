# Intent Reconciliation Extension

The `reconcile` extension adds a human checkpoint around implementation. It keeps the implementation from silently becoming the source of truth when coding reveals a constraint, missing contract, design choice, or change in desired outcome.

It does not replace `spec.md`, and it does not regenerate documents from code. It adds two small artifacts to the active feature:

```text
specs/<feature>/
├── intent.md       # Compact, explicitly approved outcome and boundaries
└── decisions.md    # Append-only proposals and human resolutions
```

## Installation

```bash
specify extension add reconcile
```

Installation registers two mandatory lifecycle hooks:

```text
reconcile.intent -> implement -> reconcile.decisions
```

Because the extension is opt-in, the core Spec Kit workflow is unchanged until a team chooses to install it.

## Commands

| Command | Purpose |
|---|---|
| `speckit.reconcile.intent` | Runs before implementation. Establishes or confirms `intent.md` and refuses to proceed while the decision ledger contains unresolved proposals. |
| `speckit.reconcile.decisions` | Runs after implementation. Finds implementation-discovered decisions, classifies them, records proposals, and requires a human to accept, reject, or edit each one. |

## The five classifications

Every discovered difference must be classified before anything is changed:

| Classification | Authority | Normal propagation |
|---|---|---|
| `implementation-defect` | Existing approved artifacts | Add corrective implementation work; do not rewrite intent or contracts to excuse the defect. |
| `contract-discovery` | Approved intent | Update the spec and tests after approval. |
| `design-decision` | Approved intent and contract | Update the plan or research rationale after approval. |
| `intent-change` | Human decision only | Update `intent.md` first, then bring downstream artifacts into alignment. |
| `accidental-divergence` | Existing approved artifacts | Reject or reverse an unsupported implementation choice. |

Implementation is evidence in this workflow, not authority. In particular, a passing test does not prove that intent should change, and code is never used to overwrite an artifact without an explicit resolution.

## Append-only decision history

`decisions.md` is an audit log. Existing proposal and resolution records are never edited or deleted. A resolution is appended as a new record that references its proposal:

```markdown
## DEC-0007 — Proposal

- **Observed during**: T031
- **Classification**: design-decision
- **Observation**: The upstream API has no atomic bulk operation.
- **Proposed decision**: Use bounded batches with compensating retries.
- **Evidence**: API contract and failing integration test.
- **Affected artifacts**: plan.md, research.md
- **Status**: proposed

## DEC-0007 — Resolution

- **Decision**: accepted
- **Approved by**: <human-supplied identity>
- **Resolved**: <ISO 8601 timestamp>
- **Edits authorized**: plan.md, research.md
- **Notes**: Accepted for this feature only.
```

An automated or unattended run may record proposals, but it must stop with them unresolved. It may not infer human approval.

## Relationship to convergence

Reconciliation and convergence answer different questions:

- `reconcile` asks what implementation taught the team and which artifact has authority.
- `converge` checks whether the implementation satisfies the resulting spec, plan, and tasks.

Run convergence only after all reconciliation proposals have resolutions.
