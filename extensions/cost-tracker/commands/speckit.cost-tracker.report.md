---
description: "Show a budget summary table across all specs in the project"
---

# Cost Report

Display a budget summary table covering every spec in the current project that
has a `## Cost Allocation` section.

## Outline

1. **Discover specs**
   - Enumerate all `*.md` files under `.specify/specs/` (non-recursive).
   - For each file, attempt to parse the `## Cost Allocation` table.
   - Skip files where the section is absent or cannot be parsed.

2. **Extract fields per spec**
   For each spec with a Cost Allocation section, read:
   - **Feature** — the spec filename (without extension) or the first H1 heading
   - **Team** — from the Team row
   - **Cost Center** — from the Cost Center row
   - **Priority** — from the Feature Priority row
   - **Approved (USD)** — from the Approved LLM Budget row (parse `$X.XX` → float)
   - **Actual (USD)** — from the Actual LLM Spend row (parse `$X.XX` → float; 0 if placeholder)
   - **% Used** — compute `actual / approved * 100` (0 if approved is 0)

3. **Render the summary table**

   ```
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  LLM Cost Report                                   2024-01-15 14:30 UTC │
   ├──────────────────────┬───────────┬──────────┬────────┬───────┬──────────┤
   │ Feature              │ Priority  │ Approved │ Actual │ % Used│ Status   │
   ├──────────────────────┼───────────┼──────────┼────────┼───────┼──────────┤
   │ add-login            │ P1        │  $10.00  │  $7.80 │  78%  │ ✓ ok     │
   │ dark-mode            │ P2        │   $5.00  │  $4.10 │  82%  │ ⚠ warn   │
   │ data-export          │ P3        │   $3.00  │  $3.50 │ 117%  │ ⛔ over  │
   ├──────────────────────┼───────────┼──────────┼────────┼───────┼──────────┤
   │ TOTAL                │           │  $18.00  │ $15.40 │  86%  │ ⚠ warn   │
   └──────────────────────┴───────────┴──────────┴────────┴───────┴──────────┘
   ```

   Status legend:
   - `✓ ok` — below 80% of approved budget
   - `⚠ warn` — 80–99% of approved budget
   - `⛔ over` — 100%+ of approved budget

4. **Exit code**
   - Exit 0 if all features are under budget.
   - Exit 1 if any feature has exceeded its approved budget (for CI use).

## Options

This command accepts no arguments. Configuration comes from
`.specify/extensions/cost-tracker/cost-tracker-config.yml`:

```yaml
warn_at_pct: 80   # Percentage at which ⚠ warning status is shown
```

## Graceful Degradation

- If `.specify/specs/` does not exist or contains no parseable specs, print:
  ```
  No specs with Cost Allocation data found in .specify/specs/.
  Run /speckit.specify to create a spec, then add a ## Cost Allocation section.
  ```
- Specs where **Approved LLM Budget** is absent or zero are listed with
  `N/A` in the Approved and % Used columns and excluded from the total.
