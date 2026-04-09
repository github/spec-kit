---
description: Reverse-engineer a feature specification from an existing codebase using exhaustive multi-pass behavioral analysis aligned with the project constitution.
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a technical implementation plan for the reverse-engineered spec.
  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify requirements in the reverse-engineered specification.
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before reverse engineering)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_reverse` key
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

### Step 1 — Scope Resolution

Parse the user input from `$ARGUMENTS`:

**If `$ARGUMENTS` is non-empty**:
- Determine whether the value is a **directory path** or a **keyword**:
  - If it resolves to an existing directory within the current working directory, treat it as a **path scope**. All analysis in Steps 4–6 MUST be restricted to that directory tree.
  - Otherwise treat it as a **keyword scope**. Match the keyword against top-level directory names and module names in the repository. Identify the closest matching scope directory. If no match is found, inform the user and ask them to provide a more specific path or keyword, then stop.
- Derive `SCOPE_SHORT_NAME` from the last non-empty path segment of the resolved directory (e.g., `src/specify_cli/extensions` → `extensions`), or from the keyword directly.
- Set `ANALYSIS_ROOT` to the resolved directory path.
- Confirm to the user: `Analyzing scope: <ANALYSIS_ROOT>`

**If `$ARGUMENTS` is empty or absent**:
- Ask the user: "No scope provided. Analyze the **full repository**? Enter `yes` to proceed or provide a directory path or keyword to narrow the analysis."
- Wait for the response.
  - If the user confirms (`yes` / `y`), set `ANALYSIS_ROOT` to the current working directory and `SCOPE_SHORT_NAME` to the inferred project name (from the root directory basename or pyproject.toml name field if present).
  - If the user provides a path or keyword, process it as described above.
  - If the user cancels, stop and exit cleanly.

### Step 2 — Overwrite Protection

Before creating a branch or writing any files, check whether a spec directory matching `SCOPE_SHORT_NAME` already exists under `specs/`:

- Search `specs/` for any directory whose name contains `SCOPE_SHORT_NAME` (case-insensitive, ignoring numeric prefixes).
- If a match is found:
  - Display: `[yellow]Warning:[/yellow] A spec for "<SCOPE_SHORT_NAME>" may already exist at <matching_path>.`
  - Ask: "Do you want to continue and create a new spec? Enter `yes` to proceed or `no` to cancel."
  - Wait for the response. If `no` or ambiguous, stop.
- If no match is found, proceed.

### Step 3 — Load Constitution

Read `.specify/memory/constitution.md` in full.

Extract and internalize:
- All **MUST** rules from every principle (I through VII).
- The **analysis depth requirement** (Principle I: exhaustive multi-iteration analysis, not surface-level).
- The **language rules** (Principle III: no implementation terms in user-facing spec sections).
- The **quality gate requirements** (Principle II: all mandatory spec sections populated).

These rules govern both the depth of analysis and the quality of the generated specification.

### Step 4 — Structural Pass (Pass 1 of 2)

**Progress**: Display step status `Structural analysis (pass 1/2)` as running.

Perform an exhaustive structural scan of `ANALYSIS_ROOT`:

1. **Entry points**: Identify all public entry points — CLI commands, exported functions, registered hooks, script invocations.
2. **Module boundaries**: Map every module/package/directory and its stated responsibility (from module docstrings, `__init__.py`, or README files within scope).
3. **Data flows**: Trace how data enters the scope (parameters, files, stdin, environment variables), how it is transformed, and how it exits (return values, file writes, stdout, side effects).
4. **Exported interfaces**: Identify all public APIs, command signatures, and configuration contracts the scope exposes to callers.
5. **Test coverage patterns**: Scan test files within or referencing the scope. Note what behaviors have acceptance tests — these are high-confidence user-facing capabilities.
6. **Configuration files**: Read any `.json`, `.yaml`, `.toml`, `.ini` files within scope that define behavior.

Produce an **internal intermediate outline** (not written to disk):
```
STRUCTURAL_OUTLINE = {
  entry_points: [...],
  module_responsibilities: {...},
  data_flows: [...],
  public_interfaces: [...],
  tested_behaviors: [...],
  configuration_contracts: [...]
}
```

**Progress**: Mark `Structural analysis (pass 1/2)` as done.

### Step 5 — Behavioral Pass (Pass 2 of 2)

**Progress**: Display step status `Behavioral analysis (pass 2/2)` as running.

Using `STRUCTURAL_OUTLINE` as the foundation, perform a deeper behavioral reconstruction:

1. **User-facing flows**: For each entry point and tested behavior, reconstruct the complete user journey — what the user does, what the system does, what the user observes.
2. **Error handling flows**: Identify every error path visible in the code (exception handlers, validation failures, missing file cases, permission errors). Reconstruct the user experience when these occur.
3. **Observable outputs**: Catalogue every observable side effect — files written, output printed, state changed, external systems called.
4. **Acceptance scenario inference**: For each tested behavior, derive a Given/When/Then scenario from the test setup (Given), test action (When), and assertion (Then).
5. **Capability grouping**: Group related behaviors into user-facing capabilities. Each distinct capability that serves a separate user goal becomes one **user story** in the spec. There MUST be at least one user story per distinct capability.
6. **Success criteria derivation**: For each capability group, derive at least one measurable, technology-agnostic success criterion from observable behavior patterns (e.g., completion rate, error recovery, throughput handling). Do NOT derive success criteria from internal metrics (class counts, cache hit rates, etc.).

Update `STRUCTURAL_OUTLINE` with behavioral findings:
```
BEHAVIORAL_OUTLINE = {
  ...STRUCTURAL_OUTLINE,
  user_stories: [...],     // each with ≥2 Given/When/Then scenarios
  error_scenarios: [...],
  success_criteria: [...], // measurable, technology-agnostic
  assumptions: [...]
}
```

**Progress**: Mark `Behavioral analysis (pass 2/2)` as done.

### Step 6 — Spec Generation

**Progress**: Display step status `Generating specification` as running.

Run `.specify/scripts/bash/create-new-feature.sh "<full description of the scope>" --json --short-name "<SCOPE_SHORT_NAME>"` and parse the JSON output for `BRANCH_NAME` and `SPEC_FILE`.

Using `BEHAVIORAL_OUTLINE`, write the complete specification to `SPEC_FILE` following the `.specify/templates/spec-template.md` structure.

**CRITICAL language rules** (enforced by Principle III of the constitution):
- `## User Scenarios & Testing`, `## Requirements`, and `## Success Criteria` sections MUST contain **no** class names, function signatures, file paths, programming language names, framework names, or technology-specific terms.
- Write exclusively in business and user language — describe WHAT the system does and WHY it matters to users, never HOW it is implemented.
- Each user story from `BEHAVIORAL_OUTLINE.user_stories` maps to one `### User Story N` section (Priority P1 for first story, P2 for second, etc.).
- Each user story MUST have at least **2 Given/When/Then acceptance scenarios**.
- Each user story MUST have an `**Independent Test**` description.
- Functional Requirements MUST be numbered `FR-001`, `FR-002`, etc., use MUST/SHOULD language, and be independently testable.
- Success Criteria MUST be numbered `SC-001`, `SC-002`, etc. and be measurable (include percentages, counts, durations, or completion-based outcomes).
- The `## Assumptions` section MUST document scope boundaries, environmental dependencies, and what is explicitly out of scope for v1.

**Progress**: Mark `Generating specification` as done.

### Step 7 — Validate Specification

**Progress**: Display step status `Validating against quality checklist` as running.

Read the generated `SPEC_FILE` and evaluate it against the Specification Quality Checklist:

**Content Quality** (auto-evaluated):
- [ ] No implementation details (languages, frameworks, APIs) in user-facing sections
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed (User Scenarios, Requirements, Success Criteria, Assumptions)

**Requirement Completeness** (auto-evaluated):
- [ ] No `[NEEDS CLARIFICATION]` markers remain (or ≤ 3 if truly unresolvable)
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Success criteria are technology-agnostic
- [ ] All acceptance scenarios defined (Given/When/Then format)
- [ ] Edge cases identified
- [ ] Scope clearly bounded
- [ ] Dependencies and assumptions identified

**Feature Readiness** (auto-evaluated):
- [ ] All functional requirements have clear acceptance criteria
- [ ] User scenarios cover primary flows
- [ ] Feature meets measurable outcomes defined in Success Criteria
- [ ] No implementation details leak into specification

Write the checklist result to `<SPEC_FILE_DIR>/checklists/requirements.md` (create the directory if needed), marking each item `[x]` (pass) or `[ ]` (fail) based on evaluation.

**Progress**: Mark `Validating against quality checklist` as done.

### Step 8 — Resolve Clarifications (if needed)

Scan the generated spec for `[NEEDS CLARIFICATION: ...]` markers.

**If markers exist**:
- Count all markers. Keep the **3 most critical** (ranked by scope impact > UX impact > technical impact). For any beyond 3, make an informed guess based on context and document it in the `## Assumptions` section.
- For each of the ≤3 remaining markers, format a resolution question:

  ```markdown
  ## Question [N]: [Topic]

  **Context**: [Quote the relevant spec section containing the marker]

  **What we need to know**: [The specific question from the NEEDS CLARIFICATION marker]

  **Suggested Answers**:

  | Option | Answer | Implications |
  |--------|--------|--------------|
  | A      | [First suggested answer] | [What this means for the feature] |
  | B      | [Second suggested answer] | [What this means for the feature] |
  | C      | [Third suggested answer] | [What this means for the feature] |
  | Custom | Provide your own answer  | Describe the answer in plain text |

  **Your choice**: _[waiting for response]_
  ```

- Present all questions together before waiting for any response.
- After the user responds, replace each marker with the selected or provided answer.
- Re-run the checklist evaluation (Step 7) after all markers are resolved.

**If no markers exist**: Skip this step.

### Step 9 — Completion Report

**Progress**: Display all steps as done.

Output a completion summary:

```
[green]✓[/green] Specification created: <SPEC_FILE>
[green]✓[/green] Quality checklist:     <SPEC_FILE_DIR>/checklists/requirements.md
  Branch: <BRANCH_NAME>
  Scope:  <ANALYSIS_ROOT>
  Stories discovered: <count>
  Requirements generated: <count>
```

Suggest next steps:
- `[dim]Next: /speckit.plan — build the technical implementation plan[/dim]`
- `[dim]Or:   /speckit.clarify — resolve any remaining spec ambiguities[/dim]`

## Post-Execution Checks

**Check for extension hooks (after reverse engineering)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_reverse` key
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
