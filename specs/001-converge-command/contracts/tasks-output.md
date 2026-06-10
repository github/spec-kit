# Contract: `tasks.md` Append Format

Defines exactly how `/speckit.converge` appends remaining work so that
`/speckit.implement` consumes it without special handling.

## Placement

- Appended at the **end** of `tasks.md`.
- Introduced by a new phase header. `N` is the next phase number after the highest existing
  phase:

```markdown
## Phase N — Convergence
```

- If a previous Convergence phase already exists from an earlier run, a new run appends a
  new, separately-numbered Convergence phase below it (existing tasks are never rewritten).

## Task line format

Each appended task is a standard checklist item continuing the existing numbering:

```markdown
- [ ] T<NNN>: <imperative description> per <source-ref> (<gap-type>)
```

- `T<NNN>`: next integer after the highest existing task ID in the file.
- `<source-ref>`: the requirement / criterion / plan decision / constitution principle the
  task traces to (e.g. `FR-003`, `SC-002`, `US1/AC2`, `plan: storage decision`,
  `Constitution II`).
- `<gap-type>`: one of `missing`, `partial`, `contradicts`, `unrequested`.

### Example

```markdown
## Phase 6 — Convergence

- [ ] T041: Append-only enforcement — block writes to spec.md/plan.md in converge per FR-008 (missing)
- [ ] T042: Surface convergence result to after_converge hook per FR-015 (partial)
- [ ] T043: Remove undocumented base-branch git lookup not called for by plan per Constitution II (unrequested)
```

## Numbering rules

1. Scan all existing task IDs in `tasks.md`; let `M` be the maximum.
2. Assign appended tasks `M+1, M+2, …` in finding order (CRITICAL/HIGH first).
3. Never reuse or renumber existing IDs.

## Clean (converged) case

When there is no remaining work, the command MUST NOT modify `tasks.md` at all — no empty
Convergence phase header is written (FR-011). The clean result is reported in-session only.

## Idempotency expectation

Re-running after some appended tasks are completed yields **fewer or zero** new tasks
(SC-005). Converge does not deduplicate against prior Convergence phases mechanically; it
re-assesses the current code state, so already-completed work simply produces no new
finding.
