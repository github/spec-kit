<!--
  Fix log template for a feature
  Input: Error reports, screenshots, logs from post-implementation
  Filled in by the /speckit.fix command — one entry per correction applied.
  Location: specs/[###-feature-name]/fix.md
  Note: This file is created on the first correction. Each new correction is prepended (newest first).
-->

# Fix Log — [FEATURE NAME]

Branch: [###-feature-name] | Spec: [link to spec.md] | Plan: [link to plan.md]

> Chronological record of all corrections applied to this feature after implementation.
> Order: newest first. Each entry is written by `/speckit.fix` at the time of the correction.

---

<!--
  ─────────────────────────────────────────────────────
  ENTRY TEMPLATE — copy this block for each new fix
  ─────────────────────────────────────────────────────
-->

## FIX-001 · [YYYY-MM-DD] · [Short title — what was broken and what was done]

> **Error origin**
> ```
> [Verbatim error message, stack trace, or description of the screenshot]
> ```

| Field | Value |
|---|---|
| **Error type** | `runtime` \| `compile` \| `test` \| `lint` \| `network` \| `logic` |
| **Detected in** | `[file path or UI screen where the error appeared]` |
| **Root cause** | [One precise sentence — the actual cause, not a paraphrase of the error] |
| **Spec impact** | `none` \| `spec.md` \| `plan.md` \| `tasks.md` \| `multiple` |

---

### Decisions

| # | Decision | Rationale |
|---|---|---|
| 1 | [Technical or spec choice made] | [Why this and not an alternative] |
| 2 | [Technical or spec choice made] | [Why this and not an alternative] |

---

### Files modified

| File | Type | Change description |
|---|---|---|
| `specs/[###-feature-name]/spec.md` | `spec` | [What changed and why — or "not modified"] |
| `specs/[###-feature-name]/plan.md` | `plan` | [What changed and why — or "not modified"] |
| `specs/[###-feature-name]/tasks.md` | `tasks` | [What changed and why — or "not modified"] |
| `src/[path/to/file]` | `code` | [What changed and why] |

---

### Invariants established

- `INVARIANT:` [Condition that must always be true after this fix]
- `INVARIANT:` [Condition that must always be true after this fix]

### Edge cases not covered

- `EDGE CASE:` [Boundary condition identified but not addressed in this fix]

### Spec Kit follow-up commands

- [ ] `/speckit.clarify` — [reason, if applicable]
- [ ] `/speckit.plan` — [reason if plan.md was modified]
- [ ] `/speckit.analyze` — [reason if multiple features were touched]
- [ ] `/speckit.taskstoissues` — [reason if edge cases should be tracked as issues]

---

<!--
  ─────────────────────────────────────────────────────
  ADD NEXT ENTRY ABOVE THIS LINE (newest first)
  ─────────────────────────────────────────────────────
-->
