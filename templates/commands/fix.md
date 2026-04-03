---
description: Receive an error (screenshot, log, message), diagnose it, and apply surgical corrections to spec files and source code within the current Spec Kit feature scope.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). This may contain an error message, a log block, a file path, or a description of what is broken.

---

## Interactions with other Spec Kit commands

`/speckit.fix` does not work in isolation. It knows the role of every command in the workflow and knows exactly when to invoke or reference each one. Full map:

```
/speckit.constitution  →  project-wide principles and constraints
/speckit.specify       →  defines the WHAT and WHY (user stories)
/speckit.clarify       →  clarifies ambiguous areas before planning
/speckit.plan          →  technical architecture and implementation decisions
/speckit.analyze       →  cross-artifact consistency check
/speckit.tasks         →  breaks plan into ordered, actionable tasks
/speckit.implement     →  executes tasks
/speckit.taskstoissues →  converts tasks into GitHub issues
/speckit.fix           →  (you) post-implementation error correction
/speckit.ask           →  ask any question, get a grounded answer and routing suggestion
```

---

## Data Path Quick Reference

Every project has a data flow chain, but naming varies by framework and architecture.  
**Step 1: identify the project's own chain from the stack trace paths and directory names.**  
**Step 2: map the error to a functional role. Fix the role where the error *originates*, not where it *surfaces*.**

### Step 1 — Infer the project's chain

Look at the file paths in the stack trace (or the `FEATURE_DIR` structure). Match against the most common patterns:

| Pattern | Typical chain | Common in |
|---|---|---|
| `views/`, `serializers/`, `models/` | `urls → middleware → view → serializer → model → db` | Django, DRF |
| `controllers/`, `services/`, `models/` | `router → middleware → controller → service → model → db` | Express, NestJS, Laravel, Rails |
| `handlers/`, `usecases/`, `repositories/` | `handler → use case → repository → data source` | Clean Architecture, Hexagonal |
| `resolvers/`, `schema/` | `query → resolver → data loader → db` | GraphQL (Apollo, Strawberry) |
| `commands/`, `lib/`, `cli/` | `entrypoint → argument parser → command → lib` | CLI tools |
| `consumers/`, `producers/`, `aggregates/` | `event bus → consumer → aggregate → event store` | Event-driven, CQRS |
| `components/`, `hooks/`, `store/` | `component → hook/store → api client → backend` | React, Vue, Angular (frontend only) |
| `functions/`, `triggers/` | `trigger → function → external service` | Serverless (Lambda, Azure Functions) |

If the project does not match any pattern, derive the chain from the actual directory names present in the stack trace. Name each role yourself — do not force a known pattern.

### Step 2 — Map the error signature to a functional role

Use **functional role names** that map to the project's own naming:

| Error signature | Functional role | Typical files (adapt to project) |
|---|---|---|
| `IntegrityError`, `OperationalError`, `ColumnNotFound`, `ForeignKeyViolation` | **data-access** | `models/`, `repositories/`, `entities/`, `dao/` |
| `ValidationError`, `SchemaError`, `SerializerError`, `422 Unprocessable` | **validation** | `serializers/`, `schemas/`, `validators/`, `forms/` |
| `AttributeError`, `TypeError`, `KeyError` inside a logic file | **business-logic** | `services/`, `usecases/`, `domain/`, `lib/` |
| `500 Internal Server Error`, unhandled exception in entry point | **entry-point** | `views/`, `controllers/`, `handlers/`, `resolvers/` |
| `401 Unauthorized`, `403 Forbidden`, `InvalidTokenError` | **guard** | `middleware/`, `auth/`, `guards/`, `interceptors/` |
| `404 Not Found`, route/path not matched | **routing** | `urls.py`, `routes/`, `router.*`, `app.*` |
| `ModuleNotFoundError`, `ImportError` | **config** | the importing file only |
| `FAILED tests/test_<name>.*::test_<fn>` | **test** | `tests/test_<name>.*` + the file under test |
| JS/TS `TypeError`, `Cannot read properties of undefined` | **ui** | `components/`, `pages/`, `views/` (frontend) |
| `fetch failed`, `axios error`, `CORS`, network error on client | **api-bridge** | `services/api.*`, `client.*`, `middleware/cors.*` |

**Rule: fix the functional role where the error *originates*, not where it *surfaces*.**  
A `NullPointerException` at the entry point often originates in the data-access layer returning `None`.  
An HTTP 500 in a view often originates in the business-logic layer throwing an uncaught exception.

---

## Phase 0 — Pre-flight

Before any extraction or triage, run these four checks in order. Each one can short-circuit the full workflow.

### 0.1 — Confidence threshold

If the input is too incomplete to triage (truncated log, blurry screenshot, ambiguous description), **do not guess**. Ask exactly one targeted question:

> "To diagnose this precisely, I need: [the one missing piece — full stack trace / the file path / the action that triggered the error]. Can you provide it?"

Do not proceed until you have enough information to fill the TRIAGE block.

### 0.2 — Multi-error input

If the input contains more than one distinct error (multiple FAILED tests, multiple exceptions):
1. List all errors found.
2. Identify the **most blocking** one (the one that causes others downstream, or the first in the execution chain).
3. Fix that one first. State explicitly: _"Fixing [error A] first. [Error B] and [Error C] are noted and will be addressed next if still present."_

### 0.3 — Recurrent error check

If `specs/[feature]/fix.md` exists, scan it (titles only — do not read full entries) before diagnosing:
- If a previous `FIX-NNN` entry addresses the same error → read that entry's `ROOT CAUSE` and `Decisions` sections before building the TRIAGE.
- If a previous fix was applied and the error recurred → the root cause was misidentified. Flag this explicitly in Phase 2: `RECURRENT: YES — previous fix FIX-NNN did not resolve the root cause`.

### 0.4 — Trivial fast path

If the error is trivially identifiable (one of the below), skip Phases 1–2 entirely and go directly to Phase 3:

| Trivial error | Direct action |
|---|---|
| `SyntaxError` with file:line | Open the file, fix the syntax, done |
| `ModuleNotFoundError: No module named 'x'` | Add the import or install the dependency |
| `NameError: name 'x' is not defined` | Check for typo or missing import |
| Typo in a config key (e.g. `DATABSE_URL`) | Fix the key name, done |
| `IndentationError` | Fix indentation at the given line |

For trivial fixes: write the `fix.md` entry with `SCOPE: 1 file`, skip Phase 4 invariants (write `not applicable — trivial fix`).

---

## Phase 1 — Extraction & Context reading

### 1.1 Extract the error

If `FEATURE_DIR` is not identifiable from the stack trace paths, run `{SCRIPT}` from repo root to derive it.

If an image is provided, extract:
- The **exact error message** (verbatim text)
- The **stack trace** if present (file, line, column)
- The **error type** (runtime, compile, test, lint, network, logic)
- The **visible context** (which screen, which action, which endpoint)

If code or logs are pasted, identify:
- The first abnormal line (the true entry point of the error)
- The call chain that led to this state

### 1.2 Triage — classify the error

**Before opening any file**, produce this block from the error message and stack trace alone (zero file I/O):

```
TRIAGE
  Error type  : [ValueError | HTTP 500 | FAILED | TypeError | etc.]
  Stack entry : [file:line — the exact line that threw]
  Role        : [functional role in this project's chain — e.g. data-access | validation | business-logic | entry-point | guard | routing | ui | api-bridge | config | test]
  Read set    : [2–5 files to open — derived from the Data Path Quick Reference — and nothing else]
```

Use **Step 1** of the Data Path Quick Reference to identify the project's own chain, then **Step 2** to map the error signature to a functional role. Open only the files listed in `Read set`.

If multiple features exist, identify the one related to the error (module name, endpoint, component) before building the read set.

**Third-party guard**: if `Stack entry` points to a file inside `node_modules/`, `site-packages/`, `vendor/`, or any external dependency directory, the bug is in your call site, not in the library. Shift `Stack entry` to the last in-project frame in the stack trace, and derive `Read set` from that frame instead.

### 1.3 Selective spec read

Read spec/plan/tasks **only if** one of these conditions holds after the triage — otherwise skip directly to Phase 2:

| Condition | What to read |
|---|---|
| The fix would change a public API or data contract | `plan.md` — the relevant section only |
| The expected behavior is unclear from the code alone | `spec.md` — the section relevant to the broken feature only |
| A task is confirmed missing or wrongly sequenced | `tasks.md` only |
| The fix may violate a project-wide constraint | `constitution.md` — if violated, **STOP** |
| None of the above | **Read nothing.** Fix directly from the Read Set. |

`constitution.md` is **never** read proactively — only as a guard when a fix might violate it.

After reading (if applicable):
- **Does the fix violate a principle in `constitution.md`?** → if yes, STOP
- **Does the error come from a gap between the plan and the implementation?**
- **Does the spec describe a different behavior from what is coded?**
- **Is there a task in `tasks.md` that was completed incorrectly or is missing entirely?**
- **Does the fix touch multiple features?** → recommend `/speckit.analyze` afterwards

---

## Phase 2 — Structured diagnosis

Produce a layered diagnosis before writing anything:

```
LAYER        : [functional role in this project — e.g. data-access | validation | business-logic | entry-point | guard | routing | ui | api-bridge | config | test]
ROOT CAUSE   : [precise technical cause, 1 sentence, referencing file:line]
CHAIN IMPACT : [does this error propagate to upstream roles? YES / NO — which ones?]
SPEC IMPACT  : [none | spec.md | plan.md | tasks.md | multiple — only if triage triggered a read]
NEW FEATURE  : [YES / NO — does a full resolution require behavior absent from all specs?]
SCOPE        : [2–5 files maximum — code files only unless spec read was triggered]
```

**If `SCOPE` lists more than 5 files → this is not a fix, it is a refactoring. Stop. Recommend `/speckit.plan` to revisit the architecture before proceeding.**

**If `NEW FEATURE = YES` → stop immediately and go to Phase 2b. Do not modify any file.**

---

## Phase 2b — Escalation: new feature detected

This phase is triggered **only if `NEW FEATURE = YES`** in the diagnosis.

### When to escalate?

The error requires a new feature (not a correction) if:
- The expected behavior exists **nowhere** in `spec.md`, `plan.md`, or `tasks.md`
- Implementing the fix would require adding a new module, endpoint, flow, or role not in scope
- The fix would impose an architectural decision that exceeds the scope of a correction
- The spec explicitly covers a different behavior — changing it would be an **evolution**, not a fix

### What you do

1. **Apply no correction.** Zero file changes.
2. **Explain the gap** in 2-3 sentences: what feature is missing, why the fix cannot exist without it.
3. **Generate a ready-to-use `/speckit.specify` prompt**, precisely describing what is missing.

### Escalation output format

```
⚠️ ESCALATION — New feature required

This error cannot be fixed within the current spec scope.

**Gap identified**: [2-3 sentence description of the missing behavior and why
it does not exist in the spec]

**Closest existing feature**: [feature or user story in spec.md that comes
closest, or "none" if entirely new]

---

Run this command to specify the missing feature:

/speckit.specify "[full description of the need — what the system must do,
in what context, for which user, with what expected outcome. Do not mention
the tech stack. Be precise about the WHY: why this behavior is necessary.
Include nominal cases and expected failure cases.]"

---

Full workflow to follow next:
  /speckit.specify   →  define the need
  /speckit.clarify   →  (recommended) resolve ambiguities
  /speckit.plan      →  technical architecture
  /speckit.analyze   →  check consistency with existing features
  /speckit.tasks     →  break into tasks
  /speckit.implement →  implement
  /speckit.fix       →  correct any errors that appear during implementation
```

### Rules for building the `/speckit.specify` prompt

The generated prompt must:
- Describe the **what** and **why**, not the **how**
- Mention the relevant user (role, usage context)
- Cover the **nominal case** (what must work)
- Cover at least **one failure case** (what must be handled)
- Be usable as-is without modification — it is a working prompt, not a draft

Well-formed prompt example:
```
/speckit.specify "When a user attempts an action that exceeds their permissions,
the system must display an explicit error message indicating what they can do instead,
rather than silently failing or redirecting to the home page.
Nominal case: the user sees the message and can navigate to an authorized action.
Failure case: if no alternative action exists, the message states this clearly."
```

---

### When `/speckit.fix` interacts with each command

| Command | `/speckit.fix` interacts when... | Action taken by `/speckit.fix` |
|---|---|---|
| `constitution` | The fix violates or exceeds a governing principle | Flag the conflict, **do not fix** — this file is read-only |
| `specify` | The error reveals unspecified behavior → new feature needed | Produce a ready-to-use `/speckit.specify` prompt (Phase 2b) |
| `clarify` | The spec is ambiguous and multiple interpretations are possible | Recommend `/speckit.clarify` before proceeding |
| `plan` | The fix requires revisiting an architectural decision | Update `plan.md` AND flag that `/speckit.plan` must be re-validated |
| `analyze` | The fix touches multiple features or creates cross-artifact inconsistency | Recommend `/speckit.analyze` after applying the fix |
| `tasks` | A task in `tasks.md` is missing, mis-ordered, or poorly defined | Update `tasks.md` directly; add any missing tasks |
| `implement` | The fix corrects an incomplete implementation of an existing task | Fix the code AND mark the relevant task in `tasks.md` |
| `taskstoissues` | After the fix, uncovered edge cases should be tracked as issues | Suggest `/speckit.taskstoissues` to open them |

---

## Phase 3 — Applying corrections

### Absolute rules

1. **Read before writing**: read the full file before any modification.
2. **Minimal change**: only modify what is broken. No opportunistic refactoring.
3. **Spec ↔ code consistency**: if you fix code in a way that diverges from the spec, update the spec at the same time.
4. **Respect the constitution**: every correction must stay within the constraints defined in `constitution.md`.
5. **No regression**: before applying, verify the fix does not break another user story.

### Corrections in spec `.md` files

Based on the `SPEC IMPACT` identified in Phase 2:

**`spec.md` affected** (ambiguous requirement, uncovered case, undefined behavior):
- Add or correct the relevant user story or acceptance criteria
- If the ambiguity runs deep → recommend `/speckit.clarify` before proceeding

**`plan.md` affected** (incorrect or incomplete technical decision):
- Adjust the faulty technical decision
- Explicitly note: _"This plan change should be re-validated via `/speckit.plan`"_

**`tasks.md` affected** (missing, mis-ordered, or poorly defined task):
- Mark the affected task as revised
- Add any missing sub-tasks or tasks with their dependencies
- If follow-up tasks should be tracked → suggest `/speckit.taskstoissues`

**Multiple artifacts affected**:
- Apply in order: `spec.md` → `plan.md` → `tasks.md` → code
- After applying → recommend `/speckit.analyze` to verify global consistency

Traceability marker in all modified `.md` files:
```markdown
<!-- FIX [DATE]: [short description of the correction] -->
```
Add this comment on the line above every modified section.

### Corrections in code

Apply changes directly. For each modified file, state:
- The file and relevant line
- The exact problem
- The change applied (clear mental diff)

---

## Phase 4 — Break the Logic

After correction, **break the logic into verifiable invariants**. For each applied fix, explicitly state:

```
INVARIANT 1 : [condition that must ALWAYS be true after this fix]
INVARIANT 2 : [condition that must ALWAYS be true after this fix]
EDGE CASE   : [boundary condition this fix does NOT yet cover — to watch]
```

Examples:
- `INVARIANT: a user without 'admin' role can never reach /admin/*`
- `INVARIANT: an account balance can never be negative after a transfer`
- `EDGE CASE: two concurrent transfers on the same account are not handled here`

For each edge case listed → evaluate whether a follow-up issue is warranted and suggest `/speckit.taskstoissues` if so.

### Validation test (mandatory)

Before moving to Phase 5, state how to verify the fix is effective:

```
VALIDATION : [exact command, scenario, or navigation path that confirms the error is gone
              — e.g. "run pytest tests/test_payment.py::test_transfer",
                     "POST /api/orders with missing field → expect 422 not 500",
                     "navigate to /checkout as anonymous user → expect redirect to /login"]
```

If no automated test covers this scenario → flag it:
`COVERAGE GAP: this fix has no automated test. Consider adding one via /speckit.tasks.`

---

## Phase 5 — Write to fix.md + final report

### 5.1 Write the entry in `specs/[###-feature-name]/fix.md`

**This step is mandatory, not optional.**

- If `fix.md` does not yet exist → create it from `.specify/templates/fix-template.md`, then write the first entry.
- If `fix.md` exists → read the last entry number, increment, **prepend** the new entry (most recent at top).

Fill every field in the template — leave nothing blank. If a section does not apply (e.g. no `.md` files modified), write `not modified` explicitly — do not delete the line.

### 5.2 Report displayed in chat

After writing to `fix.md`, display this summary in the conversation:

```
## Correction Report

**Error addressed** : [original error message]
**Root cause**      : [cause in 1 sentence]
**Entry logged**    : specs/[###-feature-name]/fix.md → FIX-[NNN]

**Files modified**:
- [ ] `specs/<feature>/spec.md`     — [description or "not modified"]
- [ ] `specs/<feature>/plan.md`     — [description or "not modified"]
- [ ] `specs/<feature>/tasks.md`    — [description or "not modified"]
- [ ] `src/...`                     — [description of the change]

**Recommended Spec Kit follow-up commands**:
- [ ] /speckit.clarify       — [if residual ambiguity remains in the spec]
- [ ] /speckit.plan          — [if plan.md was modified]
- [ ] /speckit.analyze       — [if multiple features were touched]
- [ ] /speckit.taskstoissues — [if edge cases should be tracked as issues]

**Invariants established**:
- [list]

**Edge cases not covered**:
- [list — full honesty]
```


