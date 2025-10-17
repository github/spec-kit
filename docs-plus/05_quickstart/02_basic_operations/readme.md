# 02 - Basic Operations (Complete Spec Loop)

## Overview

This is your first complete Spec-Driven Development loop. You'll build all four basic calculator operations (add, subtract, multiply, divide) using the full SDD workflow: Specify → Plan → Tasks → Implement.

**Key Learning:**
In vibe coding, you created each operation with a separate prompt. In SDD, you group related functionality into ONE feature, then break it into small tasks during planning. This teaches you the difference between FEATURES (user-facing) and TASKS (implementation steps).

**What you'll accomplish:**

- Complete your first spec loop with real complexity
- Learn to group features at the right level (user needs, not code functions)
- Understand the purpose of each SDD phase
- See how planning improves consistency and quality

## Prerequisites

- Complete [Constitution Setup](01_constitution/readme.md)
- Have your constitution established
- Be ready to work with your chosen AI agent

## Understanding Feature Grouping in SDD

### Why All 4 Operations in One Spec?

In the AI pair programming tutorial, you created each operation separately:

- "Add an add function" (one prompt)
- "Add a subtract function" (one prompt)
- "Add a multiply function" (one prompt)
- "Add a divide function" (one prompt)

In Spec-Driven Development, we group related functionality together to implement a particular feature because:

RULE: In Spec phase our focus is on the What and WHY not HOW

**From User Perspective:**

- Users want a "calculator with basic math operations"
- They don't think "I need 4 separate functions"
- The spec describes the USER NEED, not individual code functions

**From Planning Perspective:**

- Design data types ONCE (int | float) for all operations
- Plan error handling strategy ONCE
- Define testing approach ONCE
- More efficient and consistent

**From Implementation Perspective:**

- Individual operations become TASKS (T001: Add tests, T002: Add implementation, etc.)
- Tasks are small (≤ 3 minutes each)
- Better for tracking progress and TDD

### Key Difference: Feature vs Task

- **Feature (Spec level):** "Basic calculator operations" - what user wants
- **Tasks (Implementation level):** "T001: Create add function", "T002: Test add function" - how we build it

This is the fundamental shift from vibe coding to spec-driven development!

## Purpose of Each SDD Phase

Before we start, understand what each phase does:

### Phase 1: Specify (The WHAT)

- **Purpose:** Define what users need in plain English
- **Focus:** User journeys, acceptance criteria, success metrics
- **Avoid:** Technical details, code structure, implementation
- **Output:** spec.md file

### Phase 2: Plan (The HOW - Technical)

- **Purpose:** Design the technical architecture
- **Focus:** Data models, interfaces, testing strategy
- **Include:** Technical decisions, frameworks, tools
- **Output:** plan.md, data-model.md, contracts/

### Phase 3: Tasks (The BREAKDOWN)

- **Purpose:** Break plan into small, doable steps
- **Focus:** Each task ≤ 3 minutes, clear dependencies
- **Include:** TDD approach, test-first tasks
- **Output:** tasks.md with T001, T002, etc.

### Phase 4: Implement (The EXECUTION)

- **Purpose:** Build the code systematically
- **Focus:** Follow tasks, run tests, update progress
- **Include:** TDD cycle (Red → Green → Refactor)
- **Output:** Working, tested code

## Complete Spec Loop

### Phase 1: Specify

**Your Prompt:**

```
/sp.specify

Feature: Basic calculator operations with full testing.
User journeys:
- Add two numbers (positive, negative, zero, decimals)
- Subtract two numbers (all combinations)
- Multiply two numbers (including edge cases)
- Divide two numbers (we'll handle division by zero later)

Acceptance criteria:
- All operations work with whole numbers and decimals
- All operations return correct results
- All operations have full test coverage
- All functions use Python 3.12+ type hints
- All functions have clear docstrings

Success metrics:
- 100% test coverage for all operations
- Type checking passes with mypy
- Code follows our constitution rules
```

**Agent Does:**

- Creates new feature branch automatically
- Generates comprehensive spec file
- Defines user scenarios and edge cases
- Establishes acceptance criteria
- Sets up testing requirements

Note: After running `/sp.specify`, a new Git branch is created for this feature. Complete all remaining steps for this feature on that branch, then open a PR when done.

**Why This Matters:**
Notice we specified ALL four operations together because that's what a user wants - "basic calculator functionality". In vibe coding, you did 4 separate prompts. In SDD, we think at the FEATURE level (what user needs), not the FUNCTION level (code details).

### Phase 2: Plan

**Your Prompt:**

```
/sp.plan

Create: architecture sketch, interfaces, data model, error handling, requirements.
Decisions needing: list important choices with options and tradeoffs.
Testing strategy: unit + integration tests based on acceptance criteria.

Technical details:
- Use a simple, functional approach where it makes sense
- Use Python 3.12+ type hints with | union syntax
- Follow TDD: write tests first, then implementation
- Organize code and tests according to your constitution rules
```

**Agent Does:**

- Creates technical implementation plan
- Defines data models and interfaces
- Establishes testing strategy
- Identifies architectural decisions
- Generates quick-start.md and plan.md files

**Why This Matters:**
The plan defines technical architecture for ALL operations at once. This ensures consistency - same type hints, same error handling, same testing approach. Much more efficient than planning each operation separately!

### Phase 3: Tasks

**Your Prompt:**

```
/sp.tasks

Break plan into small tasks (T001..), each ≤ 3 minutes, testable, reversible.
Add dependencies between tasks; group into phases; mark deliverables per task. Group tasks by operations and for each operation like add use TDD approach so RED Tests, Green Tests and Refactor. After each group we pause for human review and on approval commit to github.

Focus on:
- Use Context7 MCP server and pull documentations instead of assuming you know the best.
- Use CLI commands where it;s more efficient than files manual creation.
- TDD approach (tests first for each operation)
- Small, step-by-step implementation
- Clear task dependencies
- Easy to undo changes
```

**Agent Does:**

- Breaks plan into numbered tasks (T001, T002, etc.)
- Groups tasks into logical phases
- Establishes task dependencies
- Creates tasks.md file with detailed breakdown

> **IMPORTANT:** Review the tasks and manually update or ask gemini. Never rely on the initial output as magical best solution. i.e:

```
update @specs/001-feature-basic-calculator/tasks.md so For first task we will make project in same directory using uv init command. And after each user story we shall pause to ask for Human Review as an explicit task and on approval commit or iterate as requested
```

**Why This Matters:**
Now the individual operations become TASKS (T001, T002, etc.). Each task is small and testable. This is where the granularity from vibe coding appears, but with better structure and planning behind it.

The tasks will break down like this for each operation:

- T001: Write failing tests for add (RED)
- T002: Write code to pass add tests (GREEN)
- T003: Refactor add if needed
- T004: Review and commit add operation
- T005: Write failing tests for subtract (RED)
- T006: Write code to pass subtract tests (GREEN)
- ... and so on

This is the TDD loop (Red → Green → Refactor) applied systematically!

Finally ask it to commit: `Commit current work as artificats and plan for feature`

### Phase 4: Implement

If our context limit is reached we can now just start a new session we already have the core artifacts.

**Your Prompt:**

```
/sp.implement let's complete Phase 1

Rules: tests first, smallest diff, keep public API stable within a phase.
After each task: run tests, update checklist, note deltas to spec if needed Mark completed tasks in tasks.md
```

**Agent Does:**

- Implements each task in sequence
- Runs tests after each task
- Updates task completion status
- Shows progress and test results
- Handles any implementation issues

**The TDD Loop for Each Operation:**

For each operation, the agent will follow this cycle:

**Step 1: RED Phase (Failing Tests)**

- Write comprehensive tests for the operation
- Run tests to confirm they fail (no implementation yet)
- Human reviews test coverage

**Step 2: GREEN Phase (Make Tests Pass)**

- Write minimal code to make tests pass
- Run tests to confirm they all pass
- Human reviews implementation

**Step 3: REFACTOR Phase (Improve Code)**

- Clean up code if needed
- Ensure code follows constitution standards
- Run tests again to ensure nothing broke

**Step 4: COMMIT**

- Human reviews the complete operation
- Commit the working operation
- Move to next operation

**Example for Addition Operation:**

1. Agent writes test_add_positive_numbers(), test_add_negative_numbers(), etc.
2. Agent runs pytest → All fail (RED) ✓
3. Human reviews tests and approves
4. Agent writes add() function implementation
5. Agent runs pytest → All pass (GREEN) ✓
6. Human reviews code and approves
7. Commit "feat: Add addition operation with tests"
8. Move to subtraction operation

This systematic approach ensures quality at each step!

## Verification Steps

### Step 1: Run Complete Test Suite

**Your Prompt:**

```
Run the complete test suite and show me the results.
Include coverage report to verify we meet the constitution requirements.
```

**Agent Does:**

- Runs `uv run pytest -v --cov=calculator --cov-report=term-missing`
- Shows all tests passing
- Displays coverage report (should be 100%)
- Confirms constitution requirements met

### Step 2: Type Checking

**Your Prompt:**

```
Run mypy to verify all type hints are correct.
```

**Agent Does:**

- Runs `uv run mypy src/`
- Shows type checking results
- Confirms no type errors

### Step 3: Code Quality Check

**Your Prompt:**

```
Run ruff to check code quality and formatting.
```

**Agent Does:**

- Runs `uv run ruff check src/ tests/`
- Shows linting results
- Confirms code follows standards

## Expected Artifacts (Generated by Agent)

Your agent will create the appropriate spec artifacts under your project's specs directory (for example, a folder for this feature), along with source code and tests organized per your constitution.

## Verification Checklist

- [ ] All four operations implemented (add, subtract, multiply, divide)
- [ ] All functions use Python 3.12+ type hints
- [ ] All functions have proper docstrings
- [ ] All tests pass (100% coverage)
- [ ] Type checking passes with mypy
- [ ] Code quality passes with ruff
- [ ] Spec loop artifacts created (.speckit/specs/basic-operations/)
- [ ] Tasks marked complete in tasks.md

## Ship It with `/sp.git.commit_pr`

Once every task is complete and all verification checks are green, hand the Git work to the agentic workflow command documented in [Core Commands · Step 8](../../06_core_commands/09_git_commit_pr/readme.md).

- Run `/sp.git.commit_pr Wrap up the basic calculator feature.` (or omit the argument and let it infer the summary)
- Approve the generated branch, commit message, and PR details before announcing completion
- If the command surfaces blockers (e.g., missing credentials), resolve them and re-run so the PR accurately reflects the finished loop

## What's Next

You've completed your first full spec loop! The basic operations are now implemented with comprehensive testing and documentation. The next step is to add a [CLI Interface](03_cli_interface/readme.md) to make the calculator usable from the command line.

**Key Achievements:**

- ✅ Complete SDD workflow mastered
- ✅ All four operations with tests
- ✅ Professional code quality standards
- ✅ Foundation for future features

---

**Next:** [03 - CLI Interface](03_cli_interface/readme.md)
