# 03 - CLI Interface (Complete Spec Loop)

## Overview

Now that you have the core calculator operations, you'll add a command-line interface to make the calculator usable. This is your second complete spec loop, building on what you already built.

**What you'll accomplish:**
- Design and build a CLI interface
- Learn how to handle command-line arguments
- Add integration tests for CLI functionality
- Make the calculator actually usable

## Prerequisites

- Complete [Basic Operations](02_basic_operations/readme.md)
- Have all four calculator operations working
- Understand the SDD workflow from the previous loop

## Complete Spec Loop

### Phase 1: Specify

**Your Prompt:**
```
/sp.specify

Feature: Command-line interface for calculator operations.
User journeys:
- Run calculator from command line with operation and two numbers
- Get clear error messages for invalid inputs
- See usage instructions when run incorrectly
 - Use calculator for quick calculations

 Acceptance criteria:
- CLI accepts operation (add, subtract, multiply, divide) and two numbers
- CLI outputs result in clear format
- CLI shows usage instructions for incorrect usage
- CLI handles invalid number inputs gracefully
- CLI can be run as: python -m calculator <operation> <num1> <num2>
 - All CLI functionality has full test coverage

 Constraints:
 - Use simple argument parsing (argparse or sys.argv)
 - Keep CLI simple and easy to use
 - Follow our constitution rules for error handling
 - No external CLI libraries (keep dependencies minimal)

Success metrics:
- CLI works for all four operations
- All CLI tests pass
- Error handling is clear and helpful
- Code follows our constitution rules
```

**Agent Does:**
- Creates new feature branch automatically
- Generates comprehensive spec file for CLI
- Defines user scenarios and edge cases
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
- Keep the CLI small and composable
- Use simple argument parsing and clear messages
- Create comprehensive CLI tests (unit + integration)
- Follow TDD approach, align with constitution rules
```

**Agent Does:**
- Creates technical implementation plan
- Defines CLI architecture and interfaces
- Establishes testing strategy for CLI
- Identifies architectural decisions
- Generates quick-start.md and plan.md files

**Why This Matters:**
The plan defines technical approach for the entire CLI at once (parsing, output format, error strategy). This keeps behavior consistent and easier to test.

### Phase 3: Tasks

**Your Prompt:**
```
/sp.tasks

Break plan into small tasks (T001..), each ≤ 3 minutes, testable, reversible.
Add dependencies between tasks; group into phases; mark deliverables per task.

Focus on:
- CLI argument parsing
- Input validation
- Output formatting
- Error handling
- Comprehensive testing
```

**Agent Does:**
- Breaks plan into numbered tasks (T001, T002, etc.)
- Groups tasks into logical phases
- Establishes task dependencies
- Creates tasks.md file with detailed breakdown

**Why This Matters:**
Tasks turn the CLI design into small, testable steps. You will apply the TDD loop for each slice (parsing, validation, output, errors).

Cadence: Keep tasks ≤ 3 minutes. After each task: tests → review → commit → continue.

### Phase 4: Implement

**Your Prompt:**
```
/sp.implement T001..T006

Rules: tests first, smallest diff, keep public API stable within a phase.
After each task: run tests, update checklist, note deltas to spec if needed.

Implementation strategy:
- Start with T001 (CLI structure)
- Implement argument parsing
- Add input validation
- Implement output formatting
- Add error handling
- Run tests after each task

Cadence: Keep tasks ≤ 3 minutes. After each task: tests → review → commit → continue.
```

**Agent Does:**
- Implements each task in sequence
- Runs tests after each task
- Updates task completion status
- Shows progress and test results
- Handles any implementation issues

## Example Task Breakdown (No Code Listings)

Below is an example of how your tasks might look at a high level. Your agent will generate the exact `tasks.md`:

- T001: Write failing unit tests for CLI parsing (RED)
- T002: Implement minimal parsing to pass tests (GREEN)
- T003: Refactor parsing and messages (REFACTOR), review, commit
- T004: Write failing unit tests for invalid inputs (RED)
- T005: Implement validation and error outputs (GREEN)
- T006: Refactor error handling (REFACTOR), review, commit
- T007: Write CLI integration tests (RED)
- T008: Implement end-to-end behavior and pass integration tests (GREEN)
- T009: Final refactor, documentation touch-ups, commit

### Manual Testing

**Your Prompt:**
```
Test the CLI manually with various operations and edge cases.
Show me the commands and outputs.
```

**Agent Does:**
- Tests all four operations
- Tests error cases
- Shows command outputs
- Verifies CLI works correctly

**Expected Manual Test Results:**
```bash
$ python -m calculator add 5 3
8

$ python -m calculator subtract 10 4
6

$ python -m calculator multiply 4 7
28

$ python -m calculator divide 15 3
5.0

$ python -m calculator add five 3
Error: Arguments must be numbers

$ python -m calculator invalid 5 3
Unknown operation: invalid

$ python -m calculator add 5
Usage: python -m calculator <operation> <num1> <num2>
```

### Task T005: Documentation Update

**Your Prompt:**
```
Update the README.md to include CLI usage instructions.
Show me the updated documentation.
```

**Agent Does:**
- Updates README.md with CLI usage
- Adds examples and installation instructions
- Shows the updated documentation

### Task T006: Final Verification

**Your Prompt:**
```
Run the complete test suite including CLI tests.
Show me the results and coverage report.
```

**Agent Does:**
- Runs all tests (calculator + CLI)
- Shows test results
- Displays coverage report
- Confirms all requirements met

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

### Step 2: Manual CLI Testing

**Your Prompt:**
```
Test the CLI with various scenarios:
1. All four operations with different numbers
2. Error cases (invalid operation, invalid numbers)
3. Edge cases (zero, negative numbers, floats)
```

**Agent Does:**
- Tests all scenarios
- Shows command outputs
- Confirms error handling works
- Verifies all operations work correctly

### Step 3: Type Checking

**Your Prompt:**
```
Run mypy to verify all type hints are correct.
```

**Agent Does:**
- Runs `uv run mypy src/`
- Shows type checking results
- Confirms no type errors

## Expected Final Structure

```
calculator-spp/
├── .speckit/
│   ├── memory/
│   │   └── constitution.md
│   └── specs/
│       ├── basic-operations/
│       └── cli-interface/
│           ├── spec.md
│           ├── plan.md
│           ├── tasks.md
│           └── quick-start.md
├── src/
│   └── calculator/
│       ├── __init__.py    # All four operations
│       └── __main__.py    # CLI interface
├── tests/
│   ├── test_calculator.py  # Calculator operation tests
│   ├── test_cli.py        # CLI unit tests
│   └── test_cli_integration.py  # CLI integration tests
└── README.md              # Updated with CLI usage
```

## Verification Checklist

- [ ] CLI accepts all four operations (add, subtract, multiply, divide)
- [ ] CLI handles invalid inputs gracefully
- [ ] CLI shows clear error messages
- [ ] CLI shows usage instructions for incorrect usage
- [ ] All CLI tests pass (unit + integration)
- [ ] Manual testing confirms CLI works
- [ ] Type checking passes with mypy
- [ ] Code quality passes with ruff
- [ ] README updated with CLI usage
- [ ] Spec loop artifacts created (.speckit/specs/cli-interface/)

## What's Next

You've successfully added a CLI interface to your calculator! The calculator is now fully functional from the command line. The next step is to add [Error Handling](04_error_handling/readme.md) to make the calculator more robust and user-friendly.

**Key Achievements:**
- ✅ CLI interface implemented and tested
- ✅ All four operations accessible from command line
- ✅ Comprehensive error handling
- ✅ Integration tests for CLI functionality
- ✅ Updated documentation

---

**Next:** [04 - Error Handling](04_error_handling/readme.md)
