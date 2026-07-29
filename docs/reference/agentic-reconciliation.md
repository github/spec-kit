# Agentic Intent Reconciliation

The bundled, opt-in **reconcile** extension puts a human decision checkpoint around implementation. It captures what coding taught the team without allowing the current code to silently redefine the feature.

Install it with:

```bash
specify extension add reconcile
```

The extension registers two mandatory hooks:

```text
/speckit.reconcile.intent -> /speckit.implement -> /speckit.reconcile.decisions
```

> [!NOTE]
> Commands are written in `/speckit.*` form throughout this page. The exact invocation depends on your agent. Skills-based integrations may expose forms such as `$speckit-reconcile-intent`.

## Artifacts

The extension adds two files to the active feature directory:

- `intent.md` — the compact, human-approved outcome, constraints, non-goals, and success evidence.
- `decisions.md` — an append-only ledger of implementation-discovered proposals and their human resolutions.

The spec, plan, tests, tasks, and code remain useful artifacts. Intent determines why the feature exists; the decision ledger records how implementation learning changes—or does not change—those artifacts.

## `/speckit.reconcile.intent`

Runs automatically before implementation. On its first run it drafts `intent.md` from the feature context but will not create the file without explicit human approval. On later runs it:

- confirms that intent and spec do not materially contradict each other;
- refuses to infer approval from code, tests, tasks, or traces;
- blocks implementation while the decision ledger has unresolved proposals.

## `/speckit.reconcile.decisions`

Runs automatically after each implementation pass. It records only choices that affect behavior, constraints, contracts, architecture, scope, or success evidence—not ordinary edits.

Each proposal receives exactly one classification:

| Classification | Meaning |
|---|---|
| `implementation-defect` | Code failed to honor an already-approved artifact. |
| `contract-discovery` | Intent stands, but the spec or tests missed an externally relevant boundary. |
| `design-decision` | Implementation required an unsettled technical choice. |
| `intent-change` | The desired outcome or boundary itself must change. |
| `accidental-divergence` | Code made an unsupported choice that should be reversed or contained. |

The command then requires the human to accept, reject, or edit each proposal. An unattended run may append proposals, but it stops without propagating them.

Accepted decisions update only the artifacts appropriate to their classification. In particular, an `intent-change` updates `intent.md` first and records its decision ID; an implementation defect does not rewrite the spec to excuse the code.

## Reconciliation versus convergence

The two phases are complementary:

- Reconciliation asks: **What did implementation teach us, and which artifact has authority?**
- Convergence asks: **Does the implementation satisfy the resulting spec, plan, and tasks?**

Resolve every decision proposal before running `/speckit.converge`.
