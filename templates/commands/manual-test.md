---
description: Generate a manual test guide (test.md) for the current feature. Produces step-by-step curl-based test cases covering every API endpoint, every acceptance scenario, good cases, bad cases, and edge cases. Run after /speckit.plan and before /speckit.tasks.
handoffs:
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Run Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-spec
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec
  py: scripts/python/check_prerequisites.py --json --require-spec
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). If the user supplies a base URL, auth token variable names, or environment-specific details, incorporate them into every example in the generated test.md.

## Pre-Execution Checks

**Check for extension hooks (before manual test generation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_manual_test` key.
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue normally.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable.
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation.
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
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently.

## Outline

### Step 1 — Locate feature directory

Run `{SCRIPT}` from repo root and parse JSON for `FEATURE_DIR` and `AVAILABLE_DOCS`. All paths must be absolute. If `spec.md` is missing, STOP and tell the user to run `/speckit.specify` first.

### Step 2 — Load source artifacts

Read the following from `FEATURE_DIR` (load all that exist):

| Artifact | Required | Purpose |
|---|---|---|
| `spec.md` | ✅ | User stories, acceptance scenarios, edge cases, functional requirements |
| `plan.md` | ✅ | Tech stack, base paths, auth mechanism, response codes |
| `contracts/*.md` | If present | Exact endpoint paths, request/response shapes, error codes |
| `data-model.md` | If present | Entity fields, constraints, state machines |
| `quickstart.md` | If present | Integration scenarios that must be covered |
| `/memory/constitution.md` | If present | Security rules, PII handling, audit requirements |

### Step 3 — Extract the test surface

From the loaded artifacts, build an internal inventory (do not emit this):

1. **Endpoint list**: every HTTP method + path defined in contracts or plan, grouped by resource.
2. **Acceptance scenario list**: every numbered acceptance scenario from every user story in spec.md, tagged by priority (P1, P2, P3).
3. **Edge case list**: every edge case bullet from spec.md.
4. **State machine list** (if data-model.md present): every valid state transition and every invalid one.
5. **Auth roles**: every role (admin, user, service, anonymous) and which endpoints each may/may not call.
6. **Constraint list**: field validation rules (min/max, pattern, required/optional, immutable fields) from contracts and data-model.

### Step 4 — Plan the test cases

For **each endpoint** produce at minimum:

- One **happy-path** test (correct auth, valid payload, expected 2xx).
- One **bad auth** test (no token → 401, wrong role → 403).
- One test per **notable error code** the contract documents (400, 404, 409, 501, etc.).
- One test per **field validation constraint** (out-of-range, wrong type, missing required, extra unknown field, illegal pattern).
- One test per **state transition** (both valid and invalid, e.g., submitting OTP to an already-FAILED session).
- One test per **edge case** from spec.md that maps to this endpoint.

For **end-to-end flows** (multi-step sequences from acceptance scenarios or quickstart.md), produce:

- One complete happy-path flow running all steps in order with save-and-reuse of IDs between steps.
- One flow demonstrating a key failure mode (e.g., retry exhaustion, duplicate creation, disabled provider).

### Step 5 — Generate `test.md`

Read `.specify/templates/manual-test-template.md` for structural guidance. Write the completed file to `FEATURE_DIR/test.md`. Follow the **Template Rules** below exactly — replace every placeholder with real content from the loaded artifacts.

### Step 6 — Verify completeness

After writing, check internally:
- Every endpoint in the inventory has at least one test.
- Every P1 acceptance scenario has at least one test.
- Every edge case from spec.md has at least one test.
- Every auth role has at least one forbidden-access test.

If any gap is found, add the missing tests before finishing.

## Template Rules

The generated `test.md` MUST follow this structure. Do not omit sections; mark them `N/A` only if the spec genuinely has no content for them.

### Required sections (in order)

1. **Header** — feature name, links to spec.md and plan.md (and contracts/ if present)
2. **Prerequisites** — service URL, token variables, any entity IDs needed; shell variable block
3. **One section per resource group** — e.g. "Provider Management", "Verifications", "Transient Flows"
4. **Edge Cases & Security Tests** — auth (401/403), PII log inspection, field boundary validation
5. **Full End-to-End Smoke Test** — single copy-paste bash script with `echo "=== Step N ==="` separators
6. **Quick Reference table** — one row per TEST-NN

### Test case format (REQUIRED for every test)

```markdown
### TEST-{NN} — {Test name: action + subject}

**What it tests**: {Which acceptance scenario, FR-###, or edge case — one sentence}

```bash
{curl command}
```

**✅ Expected — Good case**
- HTTP `{code}`
- {body/header assertion 1}
- {body/header assertion 2}

**❌ Bad case — {label}**
```bash
{curl command}
```
→ Expected: `{code}` ({reason})
```

### Shell variable conventions

- Define `BASE`, all token variables, and commonly reused IDs in **Prerequisites**.
- Capture IDs from responses using `python3 -c` one-liners (no `jq` dependency).
- Use `curl -k -s` for all commands (`-k` = local TLS, `-s` = silent).
- Use `-o /dev/null -w "%{http_code}"` for status-code-only assertions.
- Use `| python3 -m json.tool` for pretty-printed body assertions.

### Security tests (mandatory — at least one per feature)

- One test: unauthenticated access → `401`.
- One test per role: underprivileged role → `403`.
- One test: PII/OTP does not appear in plaintext in service logs — run `docker logs {service}` and grep for known sensitive terms.

### State machine tests (when data-model.md has a state machine)

- One test per valid state transition.
- One test per invalid transition (attempting an action on a terminal-state entity).
- One test for lazy expiry/timeout detection if the spec describes it.

### End-to-end smoke test (mandatory)

- One complete multi-step bash script covering the primary happy path.
- Each step has an `echo "=== Step N: ... ==="` separator and a comment with the expected HTTP code.
- Final line: `echo "=== Done ==="`

### Quick reference table (mandatory — final element)

| # | Method | Path | Auth | Good | Bad |
|---|---|---|---|---|---|
| TEST-NN | `METHOD` | `/path` | Role | code | codes |

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_manual_test`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_manual_test` key.
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue to the Completion Report.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable.
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation.
- For each executable hook, output the following based on its `optional` flag:
  - **Mandatory hook** (`optional: false`) — **You MUST emit `EXECUTE_COMMAND:` for each mandatory hook**:
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## Completion Report

Report to the user:
- Path to the generated `test.md`
- Total test count
- Test count per section
- P1 acceptance scenarios covered (count and list)
- Edge cases covered (count and list)
- Auth role coverage: which roles were tested for which endpoints
- Any gaps found and auto-filled in Step 6

## Done When

- [ ] `test.md` written to `FEATURE_DIR/test.md`
- [ ] Every endpoint has ≥1 happy-path test and ≥1 error test
- [ ] Every P1 acceptance scenario has ≥1 test
- [ ] Every edge case in spec.md has ≥1 test
- [ ] At least one 401 test and one 403 test per auth-restricted resource group
- [ ] At least one log-inspection security test (no PII in logs)
- [ ] End-to-end smoke test present as the final functional section
- [ ] Quick reference table present as the final element
- [ ] Extension hooks dispatched or skipped according to Mandatory Post-Execution Hooks above
- [ ] Completion reported to user
