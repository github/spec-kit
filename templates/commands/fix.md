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
- If a previous `FIX-NNN` entry addresses the same error → read that entry's `ROOT CAUSE`, `Decisions`, and `POST-FIX VERIFICATION` sections before building the TRIAGE.
- If a previous fix was applied and the error recurred → **the root cause was misidentified**. This is critical. Flag this explicitly in Phase 2: `RECURRENT: YES — previous fix FIX-NNN did not resolve the root cause`.

**Recurrence rules:**
- Do NOT re-apply the same category of fix (e.g., if FIX-001 added a null check and the error recurred, do NOT add another null check)
- The new diagnosis MUST go at least one WHY deeper than the previous attempt
- Read the previous fix's causal chain to understand where it went wrong
- State explicitly: _"FIX-NNN targeted WHY-[N]. The error persisted because the true root cause is deeper: WHY-[N+1]: [explanation]."_

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

## Phase 2 — Smart Diagnosis

Follow the full diagnostic workflow below. **Do not skip steps.** Each step narrows the search space; skipping leads to speculative fixes.

### Diagnostic checklist

```
Debugging progression:
- [ ] Step 1 : Collect additional information (if needed)
- [ ] Step 2 : Reproduce the problem
- [ ] Step 3 : Isolate the failure zone
- [ ] Step 4 : Deep error analysis
- [ ] Step 5 : Formulate ranked hypotheses
- [ ] Step 6 : Test hypotheses
- [ ] Step 7 : Produce layered diagnosis
```

### Step 1 : Collect additional information

Beyond what was gathered in Phase 0/1, ensure you have:

| Information | Why it's critical |
|---|---|
| **Exact** and complete error message | A missing word can change the diagnosis |
| Complete stack trace | Identifies the precise execution path |
| Language, framework, versions | Bugs are often version-specific |
| OS and environment (dev/staging/prod) | Behavior can vary by environment |
| Steps to reproduce | Without reproduction, diagnosis is speculative |
| Expected vs observed behavior | Reveals the delta |
| Recent changes (`git diff`, latest commits) | The bug is often in the most recent code |
| Complete logs around the error (not just the error line) | Context often reveals the cause |
| Did it work before? If so, what changed? | Bisection technique |

**If the user has not provided critical information**, ask for it. Do not guess.

### Step 2 : Reproduce the problem

A bug you cannot reproduce is a bug you cannot reliably fix.

- Attempt reproduction with the provided steps
- If not reproducible: check environmental conditions (specific data, timing, concurrency, database state)
- For intermittent bugs: look for race conditions, state dependencies, or timing issues

### Step 3 : Isolate the failure zone

Use the **functional role** from the TRIAGE block (Phase 1.2) to narrow the scope:

1. **Which file?** — The stack trace indicates the originating file
2. **Which function?** — Identify the function in the stack trace
3. **Which line?** — The line number in the error message
4. **Which state?** — What variables had what values at that point?

**Isolation techniques**:
- Read the code around the error line (±20 lines minimum)
- Walk up the call chain in the stack trace
- Check function inputs (parameters, global variables, database state)
- Look for recent changes on this file (`git log --oneline -10 file.ext`)

### Step 4 : Deep error analysis

#### Reading the stack trace

Read from **bottom to top** (the cause is often at the bottom, the effect at the top):

```
Traceback (most recent call last):          ← Most recent call is at the bottom
  File "main.py", line 42, in run          ← Entry point
    result = process(data)
  File "processor.py", line 18, in process ← Intermediate call
    return transform(item)
  File "transform.py", line 7, in transform ← ROOT CAUSE HERE
    return item.name.upper()
AttributeError: 'NoneType' object has no attribute 'name'
                                            ← Final message = the symptom
```

**Analysis**: `item` is `None` at line 7 of `transform.py`. Why? Trace back: where does `item` come from? From `process()` line 18. And `data`? From `run()` line 42.

#### Common error patterns by language

<details>
<summary><strong>Python</strong></summary>

| Error | Likely cause | Investigation |
|---|---|---|
| `TypeError: 'NoneType' object is not subscriptable` | Function returns `None` instead of dict/list | Check return value of the calling function |
| `ImportError: No module named 'x'` | Module not installed or wrong virtualenv | `pip list \| grep x`, check `which python` |
| `KeyError: 'x'` | Missing key in a dictionary | Use `.get('x', default)` or verify data source |
| `IndentationError` | Tabs and spaces mixed | Configure editor for spaces only |
| `RecursionError: maximum recursion depth exceeded` | Infinite recursion, missing base case | Check the stop condition of the recursive function |
| `FileNotFoundError` | Relative vs absolute path, missing file | Check `os.getcwd()` and the exact path |
| `UnicodeDecodeError` | File encoding mismatch | Specify `encoding='utf-8'` or identify real encoding |

</details>

<details>
<summary><strong>JavaScript / TypeScript</strong></summary>

| Error | Likely cause | Investigation |
|---|---|---|
| `TypeError: Cannot read properties of undefined (reading 'x')` | Property access on `undefined` | Check access chain: `a?.b?.c` |
| `ReferenceError: x is not defined` | Undeclared variable or out of scope | Check import, scope, and closures |
| `SyntaxError: Unexpected token` | Malformed JSON, missing parenthesis, invalid JSX | Check parsed input and syntax |
| `ERR_MODULE_NOT_FOUND` | Wrong import or missing package | Check `node_modules`, `package.json`, `.js`/`.mjs` extensions |
| `Maximum call stack size exceeded` | Infinite recursion | Look for circular calls |
| `CORS error` | Server not returning CORS headers | Configure the server, not the client |
| `Unhandled Promise rejection` | Missing `await` or absent `.catch()` | Add async error handling |

</details>

<details>
<summary><strong>Java</strong></summary>

| Error | Likely cause | Investigation |
|---|---|---|
| `NullPointerException` | Access to a null object | Identify which object is null on the line |
| `ClassNotFoundException` | Incorrect classpath, missing dependency | Check Maven/Gradle dependencies |
| `ConcurrentModificationException` | Modifying a collection during iteration | Use an Iterator or a copy |
| `OutOfMemoryError: Java heap space` | Memory leak or data too large | Analyze with a profiler, increase heap |
| `StackOverflowError` | Infinite recursion | Check the stop condition |

</details>

<details>
<summary><strong>C# / .NET</strong></summary>

| Error | Likely cause | Investigation |
|---|---|---|
| `NullReferenceException` | Access to a null object | Identify the null object, use `?.` |
| `InvalidOperationException: Sequence contains no elements` | `.First()` on an empty collection | Use `.FirstOrDefault()` |
| `System.IO.FileNotFoundException` | Incorrect path | Check relative path vs Build Output directory |
| `HttpRequestException` | Network problem or incorrect URL | Check URL, DNS, firewall |

</details>

<details>
<summary><strong>PHP</strong></summary>

| Error | Likely cause | Investigation |
|---|---|---|
| `Fatal error: Call to undefined function` | Function doesn't exist or extension not loaded | Check `phpinfo()`, extension, namespace |
| `Warning: Undefined array key` | Access to non-existent key | Use `isset()` or `??` |
| `Fatal error: Maximum execution time exceeded` | Infinite loop or processing too long | Check loops, optimize or increase `max_execution_time` |
| `PDOException: SQLSTATE[42S02]` | Non-existent table | Check table name and connected database |

</details>

<details>
<summary><strong>Go / Rust / Ruby</strong></summary>

| Language | Error | Likely cause | Investigation |
|---|---|---|---|
| Go | `nil pointer dereference` | Dereferencing a nil pointer | Check nil before access |
| Go | `index out of range` | Slice access beyond length | Verify slice length before indexing |
| Go | `deadlock! all goroutines are asleep` | Channel or mutex deadlock | Check goroutine synchronization |
| Rust | `borrow checker` errors | Ownership/lifetime violation | Restructure borrows or use `clone()` |
| Rust | `unwrap()` on `None`/`Err` | Unchecked Option/Result | Use `match`, `if let`, or `?` operator |
| Ruby | `NoMethodError: undefined method for nil:NilClass` | Calling a method on nil | Check nil with `&.` safe navigation |
| Ruby | `LoadError: cannot load such file` | Missing gem or wrong require path | Check Gemfile and require path |

</details>

<details>
<summary><strong>SQL</strong></summary>

| Error | Likely cause | Investigation |
|---|---|---|
| `Deadlock detected` | Two transactions blocking each other | Analyze lock order, reduce transaction duration |
| `Column 'x' is ambiguous` | Join with same-name columns | Prefix with table name `table.column` |
| `Subquery returns more than 1 row` | Subquery returns multiple results where one is expected | Add `LIMIT 1` or use `IN` instead of `=` |

</details>

### Step 5 : Formulate ranked hypotheses

Always rank by **decreasing probability** and **ease of verification**:

1. **Simple, recent errors** (90% of bugs)
   - Typo, misspelled variable
   - Recent change that broke something
   - Copy-paste with an unadapted variable

2. **Data and state errors** (frequent)
   - Unexpected null/undefined value
   - Input data in unexpected format
   - Inconsistent database state
   - Stale cache

3. **Logic errors** (moderately frequent)
   - Inverted condition (`>` instead of `<`, `&&` instead of `||`)
   - Off-by-one (loop iterates one too many or too few times)
   - Wrong order of operations
   - Unhandled edge case

4. **Import and dependency errors**
   - Module not installed
   - Incompatible version
   - Circular import
   - Dependency conflict

5. **Concurrency and timing errors**
   - Race condition
   - Deadlock
   - Unawaited async operation
   - Timeout

6. **Environment errors**
   - Dev/prod differences
   - Missing environment variables
   - File permissions
   - Network/DNS

### Step 6 : Test hypotheses

For each hypothesis, starting from the most probable:
- Identify a quick test to confirm or rule it out
- If confirmed → proceed to the fix
- If ruled out → move to the next hypothesis

**Testing techniques**:
- Add a `print()` / `console.log()` / `var_dump()` at key points
- Check values in the debugger
- Execute part of the code in isolation
- Test with simplified data
- Compare with a working version (`git diff`, `git stash`)

### Step 7 : Produce the layered diagnosis

After completing Steps 1–6, produce the layered diagnosis before writing anything:

```
LAYER        : [functional role in this project — e.g. data-access | validation | business-logic | entry-point | guard | routing | ui | api-bridge | config | test]
ROOT CAUSE   : [precise technical cause, 1 sentence, referencing file:line]
CHAIN IMPACT : [does this error propagate to upstream roles? YES / NO — which ones?]
SPEC IMPACT  : [none | spec.md | plan.md | tasks.md | multiple — only if triage triggered a read]
NEW FEATURE  : [YES / NO — does a full resolution require behavior absent from all specs?]
SCOPE        : [2–5 files maximum — code files only unless spec read was triggered]
```

#### 5-Whys causal chain (mandatory)

**Do NOT stop at the first "why".** The location of the error is NOT the root cause. The root cause is the deepest reason the error exists. Apply the "5 Whys" technique:

```
WHY-1 : [What failed? — the immediate error]
WHY-2 : [Why did that happen? — the condition that caused it]
WHY-3 : [Why did that condition exist? — the upstream origin]
WHY-4 : [Why was the upstream origin possible? — the missing guard or logic gap]
WHY-5 : [Why was there no guard? — the architectural or design gap]
```

Stop when the next "why" would leave the scope of a fix (→ architecture / new feature).

**Example — superficial vs deep diagnosis:**

❌ Superficial (will NOT fix the bug durably):
```
ROOT CAUSE: `user.name` is None at line 42 of views.py
FIX: add `if user.name is not None` guard
```

✅ Deep (fixes the actual cause):
```
WHY-1 : `user.name` is None at line 42 of views.py → AttributeError
WHY-2 : `get_user()` returns a User object with name=None
WHY-3 : The database row has NULL in the name column
WHY-4 : The registration endpoint does not validate that name is non-empty
WHY-5 : The serializer has no `required` constraint on the name field
ROOT CAUSE: Missing validation in serializers.py:UserSerializer — name field allows blank/null
FIX: Add `required=True, allow_blank=False` to the name field in UserSerializer
```

**The fix must target the WHY where the chain breaks — not the line where the error surfaces.**

#### Self-check: symptom vs root cause

Before proceeding, answer these 3 questions. If any answer is "yes", your diagnosis is incomplete — go deeper.

| Question | If YES → action |
|---|---|
| Does my fix add a null check / try-catch / default value at the crash site? | You are masking the symptom. Ask WHY the value is null/invalid in the first place. |
| Could the same error reappear with slightly different input? | Your fix is input-specific, not cause-specific. Generalize by fixing the producer, not the consumer. |
| Am I fixing the file where the error *surfaces* rather than where the bad data *originates*? | Trace back the call chain. The fix belongs upstream. |

**If `SCOPE` lists more than 5 files → this is not a fix, it is a refactoring. Stop. Recommend `/speckit.plan` to revisit the architecture before proceeding.**

**If `NEW FEATURE = YES` → stop immediately and go to Phase 2b. Do not modify any file.**

---

## Phase 2c — Pre-fix proof (mandatory gate)

**Do NOT open any file for editing until this gate is passed.**

Before writing a single line of code, produce this proof block:

```
PRE-FIX PROOF
  Error reproduction : [exact command or action that triggers the error NOW]
  Causal chain       : [WHY-1 → WHY-2 → ... → WHY-N from the 5-Whys above]
  Fix target         : [exact file:line:function where the change will be made]
  What changes        : [1-sentence description of the code change]
  Why this fixes it   : [explain how this change BREAKS the causal chain — which WHY does it eliminate?]
  Why nothing else    : [explain why no other file needs to change for the error to disappear]
  Prediction          : [after applying the fix, re-running the reproduction → what EXACT output do you expect?]
```

**Rules:**
- `Fix target` must be at the level identified by the 5-Whys, NOT at the crash site (unless they are the same)
- `Why this fixes it` must reference a specific WHY from the causal chain
- `Prediction` must be falsifiable — a concrete expected output, not "it should work"
- If you cannot fill `Prediction` with confidence → your diagnosis is incomplete, go back to Phase 2 Step 3

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

**Format for each code correction**:

```
ROOT CAUSE  : [explanation in one sentence]
FILE        : [path/file.ext], line [N]

BEFORE (buggy code):
[original code]

AFTER (fix):
[corrected code]

EXPLANATION : [why this fixes the problem — reference which WHY from the causal chain is eliminated]
```

### 3.1 — Mandatory post-fix verification (EXECUTE, do not just state)

**This is not optional. Do not skip. Do not just describe what to run — actually run it.**

After applying the fix:

1. **Re-run the exact reproduction** from `PRE-FIX PROOF → Error reproduction`
2. **Compare output** to `PRE-FIX PROOF → Prediction`
3. **Produce the verification block**:

```
POST-FIX VERIFICATION
  Command run   : [exact command or action executed]
  Expected      : [from Prediction]
  Actual        : [what actually happened]
  Status        : PASS ✅ | FAIL ❌
```

**If `Status = FAIL ❌`** → **do NOT try another quick fix**. Go to **Phase 3.2 — Fix-Failed Protocol**.

**If `Status = PASS ✅`** → proceed to Phase 4.

### 3.2 — Fix-Failed Protocol

When a fix does not resolve the error, the diagnosis was wrong. Do NOT:
- ❌ Add another guard/check on top of the first fix
- ❌ Try a "slightly different" version of the same fix
- ❌ Wrap the area in try/catch to suppress the error
- ❌ Apply multiple changes hoping one will stick

**Instead, follow this escalation:**

```
FIX-FAILED ESCALATION
  Attempt #     : [1, 2, or 3]
  What was tried : [the fix that was just applied]
  Why it failed  : [the actual output vs expected — what does the persisting error tell us?]
  New insight    : [what does this failure REVEAL about the true root cause?]
  Revised WHY    : [update the 5-Whys chain with this new information]
```

**Escalation rules:**

| Attempt | Action |
|---|---|
| Attempt 1 failed | The 5-Whys chain was incomplete. Go one WHY deeper. Re-read the call chain from scratch. Re-run Phase 2 Steps 3–7 with the new insight. |
| Attempt 2 failed | The functional role was misidentified. Go back to Phase 1.2 TRIAGE and reassign the `Role`. The error likely originates in a different layer than assumed. Expand `Read set` to include the adjacent layer. |
| Attempt 3 failed | **STOP fixing. This is not a simple bug.** Revert all attempted fixes. Report: _"After 3 attempts, the root cause could not be reliably identified. The error may involve multiple interacting systems or a design flaw. Recommend `/speckit.plan` to investigate the architecture, or `/speckit.clarify` to re-examine the expected behavior."_ |

**Critical rule: each attempt must fix at a DIFFERENT level of the causal chain.** If attempt 1 fixed at the crash site, attempt 2 must fix upstream. Repeating the same level = repeating the same mistake.

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

---

## Appendix A — Bug Categories Deep-Dive

### Runtime Errors

The most common. The program starts but crashes during execution.

**NullPointerException / TypeError: Cannot read property of undefined** — systematic diagnostic:
1. Identify the object that is null on the error line
2. Trace back: where does this object come from? Who initialized it?
3. Check all paths to this line: is there a path where the object is not initialized?
4. Check function returns: can the calling function return null?
5. Check external data: can the database, API, or file return null?

**Division by zero / Index out of bounds**:
- Check divisor/index values before the operation
- Trace the provenance of these values
- Add guards: `if (divisor !== 0)`, `if (index < array.length)`

**Stack Overflow (infinite recursion)**:
- Does the recursive function have a base case (stop condition)?
- Is the base case reachable? (do arguments converge toward the base case?)
- Are there mutual recursive calls (A calls B which calls A)?

### Logic Errors

The program doesn't crash but produces an incorrect result. The hardest to diagnose.

**Diagnostic method**:
1. Identify the input and expected output vs obtained output
2. Trace execution step by step with prints/logs at each stage
3. Compare intermediate values with what is expected
4. The first divergence point = the bug zone

**Condition bugs**: `>` vs `>=`, `&&` vs `||` (De Morgan's laws: `!(A && B)` = `!A || !B`), `==` vs `===` in JS, missing parentheses in compound conditions.

**Off-by-one bugs**: `for (i = 0; i < n; i++)` vs `for (i = 0; i <= n; i++)` — one element difference. Array index: first = 0, last = length - 1. Substring/slice: inclusive vs exclusive bound depends on the language.

**Order of operations bugs**: initialization after use, resource close before processing ends, return placed too early cutting the remaining logic.

### Performance Problems

The program works but is too slow.

**Structured diagnosis**:
1. **Measure before optimizing**: identify the real bottleneck, not a supposed one
2. **N+1 queries**: a query in a loop that should be a single query with a join
3. **Algorithmic complexity**: O(n²) in a nested loop → can a hashmap achieve O(n)?
4. **Memory leaks**: undetached listeners, circular references, unbounded caches, unclosed connections
5. **Missing cache**: an expensive computation or query is repeated needlessly
6. **Missing database index**: `EXPLAIN` / `EXPLAIN ANALYZE` on slow queries

### Environment & Deployment Problems

Code works locally but not in production (or vice-versa).

**Systematic checklist**:

| Verification | Command / Action |
|---|---|
| Identical versions? | Compare runtime, framework, dependency versions |
| Environment variables? | Verify all required vars are defined in prod |
| File permissions? | `ls -la` on affected files |
| Network/DNS? | `ping`, `curl`, `nslookup` to verify connectivity |
| SSL certificates? | Check validity and certificate chain |
| Database? | Identical schema? Migrations up to date? Test vs prod data? |
| Memory/CPU? | Are limits sufficient? |
| Prod logs? | Temporarily enable detailed logging |

### Async & Concurrency Problems

The most subtle bugs. Occur intermittently.

**Race conditions**: two async operations modify the same resource; execution order is not guaranteed. Fix: mutex, locks, transactions, or restructure to avoid concurrent access.

**Promises / async-await**: missing `await` → function continues without waiting for result; `.then()` that doesn't return the promise → broken promise chain; `try/catch` that doesn't wrap the `await`.

**Deadlocks (SQL/threads)**: two transactions lock resources in different order. Fix: always lock in the same order, reduce transaction duration.

---

## Appendix B — Debugging Tools by Language

| Language | Debugger | Profiler | Linter |
|---|---|---|---|
| Python | `pdb`, VS Code debugger | `cProfile`, `py-spy` | `pylint`, `ruff`, `mypy` |
| JavaScript | Chrome DevTools, VS Code | Chrome Performance, `clinic.js` | `eslint`, `typescript` |
| TypeScript | VS Code debugger, Chrome DevTools | `clinic.js`, `0x` | `eslint`, `tsc --noEmit` |
| Java | IntelliJ/Eclipse debugger | `JProfiler`, `VisualVM` | `SpotBugs`, `SonarQube` |
| C# | Visual Studio debugger | `dotTrace`, `PerfView` | `Roslyn analyzers` |
| PHP | `xdebug` | `Blackfire`, `xhprof` | `phpstan`, `psalm` |
| Go | `dlv` (Delve) | `pprof` | `golangci-lint` |
| Rust | `gdb`/`lldb`, VS Code | `perf`, `flamegraph` | `clippy` |
| Ruby | `debug` gem, `byebug` | `stackprof`, `rack-mini-profiler` | `rubocop` |
| SQL | `EXPLAIN ANALYZE` | Query analyzer (DBMS) | — |

---

## Appendix C — Debugging Anti-Patterns

| Anti-pattern | Why it's harmful | Good practice |
|---|---|---|
| Modify code randomly | Can introduce new bugs | Understand first, fix second |
| Ignore the error message | The message almost always contains the answer | Read every word of the error message |
| Comment out code to "see if it works" | Hides the problem instead of solving it | Use the debugger or logs |
| Fix the symptom | The bug will return in another form | Find and fix the root cause |
| Don't test the fix | The fix may be incomplete or introduce a regression | Always verify + add a test |
| Change multiple things at once | Impossible to know which change fixed the bug | One change at a time |
| "It works on my machine" | The prod environment is different | Reproduce in an environment close to prod |


