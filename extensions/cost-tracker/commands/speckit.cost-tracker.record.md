---
description: "Update the Actual LLM Spend field in the current spec with the reported spend amount"
---

# Record LLM Spend

Update the **Actual LLM Spend (USD)** field in the active spec's `## Cost Allocation`
section to reflect the spend incurred during the most recent command.

## Outline

1. **Locate the active spec file**
   - Find the spec document for the current feature in `.specify/specs/`.
   - If no spec file is found, emit a warning and exit — do not create one.

2. **Determine the spend amount**
   - If invoked as an `after_implement` hook, check whether the integration
     reported token usage for the completed step.
   - If token counts are available, convert to USD using the model's published
     per-token pricing (default: haiku at $0.00025/1K input + $0.00125/1K output).
   - If token counts are not available, prompt:
     ```
     Enter the LLM spend for this step in USD (e.g. 0.04), or press Enter to skip:
     ```
     If the user presses Enter or provides a non-numeric value, skip and exit.

3. **Read the current value**
   - Parse the `## Cost Allocation` table in the spec.
   - Read the current **Actual LLM Spend (USD)** cell value.
   - If the cell is absent or contains a placeholder, treat current value as 0.

4. **Add and write back**
   - New total = current value + spend amount from step 2.
   - Overwrite the **Actual LLM Spend (USD)** cell with `$<new_total>` (2 decimal places).
   - Preserve all other table rows exactly.

5. **Threshold check**
   - Read **Approved LLM Budget (USD)** from the same table.
   - Compute `pct = new_total / approved * 100`.
   - If `pct >= 100`: emit
     ```
     ⛔ Budget exceeded: $<new_total> spent of $<approved> approved (<pct>%).
     Consider pausing and reviewing with your team before continuing.
     ```
   - If `pct >= warn_at_pct` (default 80, from config): emit
     ```
     ⚠  Budget warning: $<new_total> spent of $<approved> approved (<pct>%).
     ```
   - Otherwise: emit
     ```
     ✓ Spend recorded: $<new_total> of $<approved> approved (<pct>% used).
     ```

## Graceful Degradation

- If the spec has no `## Cost Allocation` section: skip with a one-line warning.
- If the approved budget field is absent or zero: skip the threshold check; still
  write the spend value.
- If the spec file is read-only or the write fails: emit an error message and exit
  without modifying the file.
