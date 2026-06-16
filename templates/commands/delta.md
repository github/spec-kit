---
description: Compute the gap between the constitution's Vision & Direction and the current repo state (code + specs) to recommend the next feature.
handoffs:
  - label: Specify Next Feature
    agent: speckit.specify
    prompt: Specify the next feature recommended by the delta report. I want to build...
---

## User Input

```text
$ARGUMENTS
```

User input is optional. When provided, treat it as a focus hint (e.g., a specific
Long-Term Objective to prioritize, a constraint like "no infra work this cycle",
or a candidate feature to evaluate against the Vision).

## Pre-Execution Checks

**Check for extension hooks (before delta)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_delta` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

The `__SPECKIT_COMMAND_DELTA__` command pairs with the Vision & Direction section
of the constitution. `__SPECKIT_COMMAND_SPECIFY__` adds work *incrementally*;
this command answers the orthogonal question: **given everything we have shipped
so far, what should we build next to close the gap to the Vision?**

It is a read-only analysis (plus a single write to `.specify/memory/delta.md`).
Do **not** create specs, branches, plans, or tasks here.

Follow this execution flow:

1. **Load the Vision**:
   - Read `.specify/memory/constitution.md`.
   - Extract the **Vision & Direction** section: North Star, Target Users & Value,
     **Long-Term Objectives** (the primary unit of comparison), and **Non-Goals**.
   - If the section is missing or still contains bracketed placeholders, abort with
     an error instructing the user to run `__SPECKIT_COMMAND_CONSTITUTION__` first.

2. **Inventory cumulative work** (what has been built so far):
   - List every directory under `specs/` (skip `_delta/` if present). For each:
     - Read `spec.md` (title, primary requirement, success criteria).
     - Read `plan.md` if present (technical approach, scope).
     - Read `tasks.md` if present and count completed vs total tasks (look for
       `- [x]` vs `- [ ]` markers, or whatever convention the project uses).
   - This is the **spec-side** view of cumulative work.

3. **Inspect repo state** (what is actually in the code):
   - Use `git log --oneline -n 50` to sample recent activity.
   - Read top-level `README.md` and any `docs/` index for the project's
     self-described capabilities.
   - Walk the primary source tree (e.g., `src/`, `app/`, `lib/`, or whatever the
     repo uses) at one level deep to identify shipped modules/packages.
   - Read `CHANGELOG.md` if it exists — this is often the highest-signal source.
   - This is the **reality-side** view; it catches drift between specs and code.

4. **Compute the delta** — for each Long-Term Objective, classify status:
   - **Met** — clear evidence in code + specs that the objective holds today.
   - **Partial** — some progress, with specific gaps (name them).
   - **Untouched** — no meaningful progress.
   - **Drift** — code has diverged from what specs claim, or the objective has
     been undermined by recent work.

   For each Partial / Untouched objective, identify the smallest concrete
   feature that would move it forward. Cross-check candidates against
   **Non-Goals** and drop any that violate them.

5. **Rank candidate next features** by:
   - **Leverage** — how many objectives the feature advances at once.
   - **Unblocking** — does it unlock other roadmap items?
   - **Cost/risk** — rough size, and whether it sits in a fragile area.
   - **Sequencing** — does it depend on something not yet shipped?

   Pick the top 1 as the **primary recommendation** and keep up to 2 alternates.
   If the user supplied a focus hint in `$ARGUMENTS`, bias ranking accordingly
   and note the bias in the report.

6. **Write the delta report** to `.specify/memory/delta.md` (overwrite). Use this
   structure exactly:

   ```markdown
   # Delta Report

   **Generated**: YYYY-MM-DD
   **Constitution Version**: <version line from constitution.md>
   **Focus Hint**: <verbatim $ARGUMENTS, or "none">

   ## Vision Snapshot
   - **North Star**: <one line>
   - **Long-Term Objectives**: <bullet list, verbatim from constitution>

   ## Cumulative Build
   <Per-feature table or list summarizing specs/ — name, status, primary outcome.
   Include a one-line summary of repo-level capabilities derived from code inspection.>

   ## Objective Status
   | Objective | Status | Evidence | Gap |
   |-----------|--------|----------|-----|
   | <obj 1>   | Met / Partial / Untouched / Drift | <spec or code pointer> | <what is missing> |
   ...

   ## Recommended Next Feature
   **Title**: <short imperative phrase>
   **Why now**: <which objectives it advances; leverage rationale>
   **Scope sketch**: <2–4 bullets — enough to feed into `__SPECKIT_COMMAND_SPECIFY__`>
   **Non-Goals respected**: <which non-goals this avoids violating>
   **Estimated size**: S / M / L
   **Dependencies**: <prior specs or external prerequisites, or "none">

   ## Alternates
   1. <Title> — <one-line rationale>
   2. <Title> — <one-line rationale>

   ## Drift & Risks
   <Anything noticed during inspection that does NOT belong in the next feature
   but should be flagged: spec/code divergence, Non-Goal violations in flight,
   stalled features.>
   ```

7. **Report completion** to the user with:
   - Path: `.specify/memory/delta.md`
   - One-line summary of the recommended next feature.
   - Count of objectives at each status (Met / Partial / Untouched / Drift).
   - Suggested next command: `__SPECKIT_COMMAND_SPECIFY__ <the recommended feature>`.

## Constraints

- **Read-mostly**: the only file this command writes is `.specify/memory/delta.md`.
  Do not create spec directories, branches, or modify the constitution.
- **No new objectives**: if you believe the Vision itself is wrong or stale,
  surface it in the *Drift & Risks* section and recommend the user run
  `__SPECKIT_COMMAND_CONSTITUTION__` — do not silently invent objectives here.
- **Respect Non-Goals**: a recommendation that violates a stated Non-Goal is a
  bug in this command, not a feature.
- **Honest "Untouched"**: do not pad evidence to make objectives look further
  along than they are. The value of this command is calibration, not optimism.

## Post-Execution Checks

**Check for extension hooks (after delta)**:
Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_delta` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
