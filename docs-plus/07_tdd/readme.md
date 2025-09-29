# Module 07 – Test-Driven Development (TDD)

> **The implementation discipline for SDD tasks: write tests first, implement minimal code, refactor safely.**

You've learned **Spec-Driven Development (SDD)** for design thinking and **Prompt History Records (PHR)** for capturing learning. Now learn **Test-Driven Development (TDD)** - the implementation discipline that makes your SDD tasks executable with quality and safety.

[Test-Driven Development](https://www.geeksforgeeks.org/software-engineering/test-driven-development-tdd/) (TDD) is a software development practice where you write automated tests **before** writing the production code. The rhythm is tight and iterative: you specify behavior with a failing test, write the minimum code to pass it, then clean up the design—repeating until the feature is complete.

## The core loop (red → green → refactor)

1. **Red** – Write a small test that captures a tiny slice of desired behavior. Run it and watch it fail (proves the test is valid).
2. **Green** – Write the simplest production code to make that test pass. Don’t overbuild.
3. **Refactor** – Improve the code’s design (names, duplication, structure) with tests guarding you. All tests must stay green.
4. Repeat, growing behavior in tiny steps.

## Where the tests live

* **Unit tests**: verify small pieces (functions/classes) in isolation. Fast and abundant.
* **Component/integration tests**: check interactions with DBs, APIs, queues.
* **End-to-end/acceptance tests**: validate user-visible flows against specs (often BDD style).

## Why teams use TDD

* **Fewer defects & faster feedback** (failures show up minutes after a change).
* **Better design** (APIs shaped by how they’re used).
* **Regression safety** (a growing suite that catches breakages).
* **Confidence to refactor** (enables continuous improvement).

## A tiny example (Python + pytest)

Goal: add an `is_prime(n)` function.

**1) Red**

```python
# test_primes.py
from primes import is_prime

def test_two_is_prime():
    assert is_prime(2) is True
```

Run `pytest` → fails (no implementation yet).

**2) Green**

```python
# primes.py
def is_prime(n):
    if n == 2:
        return True
    return False
```

Test passes—but only for 2.

**3) Next red**

```python
def test_three_is_prime():
    assert is_prime(3) is True

def test_four_is_not_prime():
    assert is_prime(4) is False
```

Failing again → expand implementation just enough to pass, then refactor. Keep iterating (add more cases, handle edges), always in small steps with tests first.

## How TDD fits into a delivery workflow

* **Local dev:** run tests on save (e.g., `pytest -q`, `vitest --watch`, `npm test`).
* **Pre-push hooks:** block bad commits (`pre-commit`, `husky`).
* **CI/CD:** run the full suite in pipelines (GitHub Actions, GitLab CI). Merge only if green.
* **Code review:** reviewers look for clear tests that describe behavior; tests act as executable spec.
* **Refactoring & maintenance:** change code confidently; green tests prove behavior is intact.

## Practical tips

* Keep tests **fast and focused** (milliseconds → seconds).
* Test **behavior, not implementation details** (avoid locking tests to private internals).
* Start with **happy path**, then add edge/error cases.
* Use **fakes/mocks** at the boundaries (DB, network) to keep unit tests fast and deterministic.
* Aim for **high value coverage**, not just a high coverage number.
* When a bug appears, first **write a failing test** that reproduces it—then fix it.

## Common pitfalls

* Writing big tests that cover multiple behaviors at once (hard to diagnose).
* Over-mocking, which couples tests to internals.
* Skipping refactoring; the “green” phase without the cleanup erodes design quality.

## Tooling examples

* **Python:** pytest, unittest, factory\_boy, responses, pytest-mock.
* **JS/TS:** Jest/Vitest, Testing Library, Playwright/Cypress (for E2E).
* **Java:** JUnit, AssertJ, Mockito, Spring Test.
* **.NET:** xUnit/NUnit, Moq, FluentAssertions.

In short: TDD is “specify by test, implement minimally, improve relentlessly.” Done well, it accelerates delivery while raising quality.

## PDD Pairs Beautifully with TDD.

Think of it as **“prompts driving the spec, tests guarding the spec”**… aka creativity **but with two suits on** (double-breasted quality).

Here’s the clean way to combine them:

## How PDD × TDD fit together

* **PDD**: You express intent and constraints as **sequential prompts**; the AI writes code, docs, and scaffolding. (You’re the orchestra conductor; the AI’s the very caffeinated strings section.)
* **TDD**: You enforce correctness with the **Red → Green → Refactor** loop. (If it’s not red first, it’s probably *read* later—in a postmortem.)

Together, you get *fast generation* + *provable behavior*. That’s velocity with seatbelts—no bug-shaped projectiles.

---

## The combined loop (operational playbook)

1. **Architect micro-spec (PDD) →** Define one tiny outcome + acceptance criteria.
2. **Write failing tests (TDD: Red) →** Prompt the AI to add only the tests that encode the criteria.
3. **Generate the smallest code to pass (TDD: Green, via PDD prompt) →** Ask for the **minimal diff**.
4. **Refactor (TDD: Refactor) →** Prompt for internal cleanup with tests staying green.
5. **Explain & Record →** Prompt for an explainer summary + update/append an ADR.
6. **Repeat** in baby steps (so small even your linter smiles).

*You’re still not hand-coding; you’re hand-**spec-ing**. The AI does the typing, you do the judging—like a benevolent code sommelier.*

---

# Example: add `/chat` validation (PDD + TDD prompts)

**Step 1 — Micro-spec (PDD)**
“Design a minimal slice: `/chat` must reject requests missing `user_message` with 400 and JSON error `{code:'MISSING_USER_MESSAGE'}`. Keep public interfaces stable.”

**Step 2 — Red (TDD)**
“Add failing tests: `tests/test_chat_contract.py::test_missing_user_message_returns_400`. Include positive/negative cases and schema checks. No implementation changes.”

**Step 3 — Green (PDD minimal diff)**
“Implement the smallest change to pass the new tests. Do not refactor unrelated code. No new dependencies. Output diff-only.”

**Step 4 — Refactor (TDD)**
“Refactor validation into a tiny module `app/validation.py`; keep tests green; add docstrings. No behavior changes.”

**Step 5 — Explain + ADR**
“Summarize the change in 8 bullets and add ADR ‘0003—Input validation strategy’ with alternatives considered.”

*Result: feature locked down tighter than a prod database on Friday evening.*

---

## Example: tools + guardrails with TDD gates

* **Red**: “Add tests asserting: (1) `calculator('2+2') → '4'`; (2) invalid expressions return a friendly error; (3) outputs conform to `ChatReply` and reject >1200 chars.”
* **Green**: “Implement `@function_tool calculator` with safe eval; add guardrail enforcing `ChatReply`. Minimal diff.”
* **Refactor**: “Extract safe-eval, centralize error messages, keep tests green, update README with usage examples.”

*Yes, your calculator now has better manners than some CLI tools.*

---

## Prompt templates you can reuse (copy/paste)

**TDD: Red (tests only)**

```
Add failing tests for <behavior>. Include edge/negative cases and clear names. 
No production code changes. Keep the diff minimal and runnable offline.
```

**TDD: Green (smallest diff)**

```
Make the smallest change necessary to pass tests/<path>::<test_name>. 
Do not refactor unrelated code. No new dependencies. Output diff-only.
```

**TDD: Refactor (safety rails)**

```
Refactor internals for clarity/performance. Preserve public APIs and behavior. 
All tests must remain green. Provide a short refactor summary.
```

**PDD: Explainer + ADR**

```
Summarize the change in 8 bullets: purpose, interfaces, files touched, tests added, risks, 
how to extend. Then add/append an ADR with context, options, decision, consequences.
```

---

## CI & policy to make it stick (lightweight, effective)

* **Pre-merge checks**: lint, type, unit, *contract tests*, coverage threshold (e.g., ≥80%).
* **“No green, no merge”**: PRs must include tests for new behavior.
* **ADR link required** when public interfaces or dependencies change.
* **Diff size guard**: encourage “smallest diff” prompts to avoid yak-herding PRs.

*This is how you keep the suit pressed while still dancing.*

---

## Common pitfalls (and guard prompts)

* **Scope creep** → Add “Out of scope:” to every prompt. (Like “no pizza toppings beyond three.”)
* **Prompt drift** → Freeze the micro-spec; if intent changes, update spec first, then regenerate.
* **Gigantic diffs** → Use “diff-only + smallest change” phrasing religiously.
* **Tests that depend on the network** → Mock the model/tool; make CI deterministic (future you will bake cookies in your honor).

---

## Bottom line

PDD is strongest **with** TDD: prompts define the "what," tests enforce the "correct," and tiny diffs keep the team fast and sane. It's vibe coding's creativity **but with a suit on**—and TDD is the tie clip that stops quality from flapping in the wind.

---

## TDD: The Implementation Discipline for SDD Tasks

**You've completed SDD and PHR - now learn TDD to implement your tasks with quality and safety.**

### The Complete Workflow: SDD → TDD → PHR

**Step 1: SDD Design Phase** (You've learned this)
```bash
/spec "Design user authentication system"
/plan "Implement auth with technical architecture"  
/tasks "Break auth into implementable tasks"
```

**Step 2: TDD Implementation Phase** (This module)
```bash
# For each task, use TDD cycles:

# Task: User validation
# Red: "Add failing tests for email validation. Include edge/negative cases and clear names. No production code changes."
# Green: "Make the smallest change necessary to pass the email validation tests. No new dependencies. Output diff-only."
# Refactor: "Refactor validation logic for clarity. Preserve public APIs and behavior. All tests must remain green."

# Task: User creation  
# Red: "Add failing tests for user creation. Test database save and user ID return."
# Green: "Implement user creation to pass the tests. Minimal implementation only."
# Refactor: "Extract user creation logic into service class. Keep tests green."

# Task: Authentication
# Red: "Add failing tests for login endpoint. Test credential validation and JWT return."
# Green: "Implement login endpoint to pass the tests. No over-engineering."
# Refactor: "Clean up authentication logic. All tests must remain green."
```

**Step 3: PHR Documentation Phase** (You've learned this)
```bash
/phr "Completed user authentication with TDD implementation"
```

### Why This Works

- **SDD provides design thinking** (user journeys, architecture, planning)
- **TDD provides implementation discipline** (tests first, incremental, quality)
- **PHR captures learning** (what worked, what didn't, next steps)
- **Together**: Well-designed, well-tested, well-documented features

**Key Insight**: TDD is the **implementation discipline** that makes your SDD tasks executable with quality and safety.

---

## TDD Prompt Templates for SDD Tasks

### Red Phase (Tests Only)
```
Add failing tests for <behavior>. Include edge/negative cases and clear names. 
No production code changes. Keep the diff minimal and runnable offline.
```

### Green Phase (Minimal Implementation)
```
Make the smallest change necessary to pass tests/<path>::<test_name>. 
Do not refactor unrelated code. No new dependencies. Output diff-only.
```

### Refactor Phase (Clean Up)
```
Refactor internals for clarity/performance. Preserve public APIs and behavior. 
All tests must remain green. Provide a short refactor summary.
```

## How to Use TDD with Your SDD Tasks

### Step 1: Get Your SDD Tasks
```bash
# After completing SDD workflow, you'll have tasks like:
# - "Add user validation for email and password"
# - "Implement user creation with database save"
# - "Create login endpoint with JWT authentication"
```

### Step 2: Implement Each Task with TDD
```bash
# For each task, follow Red → Green → Refactor:

# Example: "Add user validation for email and password"

# Red: Write failing tests
Add failing tests for email validation. Include edge/negative cases and clear names. 
No production code changes. Keep the diff minimal and runnable offline.

# Green: Implement minimal code
Make the smallest change necessary to pass the email validation tests. 
No new dependencies. Output diff-only.

# Refactor: Clean up code
Refactor validation logic for clarity. Preserve public APIs and behavior. 
All tests must remain green. Provide a short refactor summary.
```

### Step 3: Record Your Learning
```bash
# After completing each task, capture the learning
/phr "Completed user validation with TDD - learned about edge case testing"
/phr "Completed user creation with TDD - learned about database integration patterns"
/phr "Completed authentication with TDD - learned about JWT implementation"
```

### Step 4: Move to Next Task
Repeat the Red → Green → Refactor cycle for each SDD task until your feature is complete.

**That's it!** Use TDD to implement your SDD tasks with quality and safety, then capture your learning with PHRs.

