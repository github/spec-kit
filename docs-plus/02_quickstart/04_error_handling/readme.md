# 04 - Error Handling (Complete Spec Loop)

## Overview

Now that you have a working calculator with CLI, you'll add error handling to make it robust and user-friendly. This is your third complete spec loop, focusing on edge cases and error scenarios.

**What you'll accomplish:**
- Add error handling for all operations
- Handle division by zero gracefully
- Improve CLI error messages and validation
- Add edge case testing and validation
- Make the calculator production-ready

## Prerequisites

- Complete [CLI Interface](03_cli_interface/readme.md)
- Have working calculator with CLI
- Understand error handling patterns from constitution

## Complete Spec Loop

### Phase 1: Specify

**Your Prompt:**
```
/sp.specify

Feature: Error handling for calculator operations.
User journeys:
- Handle division by zero gracefully with clear error messages
- Validate all inputs for mathematical operations
- Provide helpful error messages for invalid CLI inputs
- Handle edge cases like very large numbers, infinity, NaN
- Make sure calculator never crashes or produces unexpected results

Acceptance criteria:
- Division by zero raises clear, informative error
- All operations validate input types and ranges
- CLI provides helpful error messages for all error cases
- Error messages are consistent and user-friendly
- All error scenarios have full test coverage
- Calculator handles edge cases gracefully

Constraints:
- Follow our constitution rules for explicit error handling
- Use Python's built-in exception handling
- Keep error messages clear and actionable
- No silent failures or unexpected behavior

Success metrics:
- All error scenarios tested and handled
- Error messages are clear and helpful
- Calculator never crashes on valid inputs
- Code follows our constitution rules
```

**Agent Does:**
- Creates new feature branch automatically
- Generates comprehensive spec file for error handling
- Defines error scenarios and edge cases
- Establishes acceptance criteria
- Sets up testing requirements

Note: After running `/sp.specify`, a new Git branch is created for this feature. Complete all remaining steps for this feature on that branch, then open a PR when done.

### Phase 2: Plan

**Your Prompt:**
```
/sp.plan

Produce: architecture sketch, interfaces, data model, error taxonomy, NFRs.
Decisions needing ADR: enumerate candidates with options and tradeoffs.
Testing strategy: unit + integration cases derived from acceptance criteria.

Technical details:
- Define how division by zero will be handled
- Establish input validation rules for all operations
- Standardize CLI error handling and messages
- Create a comprehensive error test strategy
- Follow TDD approach for error handling
```

**Agent Does:**
- Creates technical implementation plan
- Defines error handling architecture
- Establishes testing strategy for error scenarios
- Identifies architectural decisions
- Generates quick-start.md and plan.md files

**Why This Matters:**
Designing error handling up front keeps behavior predictable and user-friendly. A consistent error strategy reduces surprises across the app.

### Phase 3: Tasks

**Your Prompt:**
```
/sp.tasks

Break plan into small tasks (T001..), each ≤ 3 minutes, testable, reversible.
Add dependencies between tasks; group into phases; mark deliverables per task.

Focus on:
- Division by zero handling
- Input validation for all operations
- CLI error message improvements
- Edge case testing
- Error handling tests
```

**Agent Does:**
- Breaks plan into numbered tasks (T001, T002, etc.)
- Groups tasks into logical phases
- Establishes task dependencies
- Creates tasks.md file with detailed breakdown

**Why This Matters:**
Tasks help you apply the TDD loop to each error scenario (RED → GREEN → REFACTOR → Commit), keeping changes small and safe.

Cadence: Keep tasks ≤ 3 minutes. After each task: tests → review → commit → continue.

### Phase 4: Implement

**Your Prompt:**
```
/sp.implement T001..T008

Rules: tests first, smallest diff, keep public API stable within a phase.
After each task: run tests, update checklist, note deltas to spec if needed.

Implementation strategy:
- Start with T001 (division by zero tests)
- Implement error handling for each operation
- Update CLI error handling
- Add comprehensive error tests
- Run tests after each task

Cadence: Keep tasks ≤ 3 minutes. After each task: tests → review → commit → continue.
```

**Agent Does:**
- Implements each task in sequence
- Runs tests after each task
- Updates task completion status
- Shows progress and test results
- Handles any implementation issues

## Verification Steps

### Step 1: Run Complete Test Suite

**Your Prompt:**
```
Run the complete test suite including all error handling tests.
Show me the results and coverage report.
```

**Agent Does:**
- Runs `uv run pytest -v --cov=calculator --cov-report=term-missing`
- Shows all tests passing
- Displays coverage report (should be 100%)
- Confirms error handling requirements met

### Step 2: Manual Error Testing

**Your Prompt:**
```
Test the CLI with various error scenarios:
1. Division by zero
2. Invalid number formats
3. Unknown operations
4. Edge cases (very large numbers, infinity, NaN)
```

**Agent Does:**
- Tests all error scenarios
- Shows command outputs
- Confirms error handling works correctly
- Verifies helpful error messages

### Step 3: Type Checking

**Your Prompt:**
```
Run mypy to verify all type hints are correct.
```

**Agent Does:**
- Runs `uv run mypy src/`
- Shows type checking results
- Confirms no type errors

## Expected Artifacts (Generated by Agent)

Your agent will create the appropriate spec artifacts under your project's specs directory (for example, a folder for this feature), along with changes to source code and tests per your constitution.

## Verification Checklist

- [ ] Division by zero handled gracefully
- [ ] Input validation for all operations
- [ ] Comprehensive error messages
- [ ] CLI error handling improved
- [ ] Edge cases tested and handled
- [ ] All error tests pass
- [ ] Manual testing confirms error handling
- [ ] Type checking passes with mypy
- [ ] Code quality passes with ruff
- [ ] Spec loop artifacts created (.speckit/specs/error-handling/)

## What's Next

You've successfully added comprehensive error handling to your calculator! The calculator is now robust and production-ready. The final step is to test everything together, merge all changes, and complete the project.

**Key Achievements:**
- ✅ Comprehensive error handling implemented
- ✅ Division by zero handled gracefully
- ✅ Input validation for all operations
- ✅ Improved CLI error messages
- ✅ Edge cases tested and handled
- ✅ Production-ready calculator

---

## Finalize & Merge

Once error handling is complete, finalize the feature and merge:

1. Run the complete test suite with coverage
2. Run type checking and linting
3. Manual CLI smoke: success and error paths
4. Merge feature branches in order (basic-operations → cli-interface → error-handling)
5. Update README with any changes
6. Clean up feature branches
