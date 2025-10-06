# Building a Calculator with AI: Test-Driven Development Tutorial

## Complete Hands-Off Development with Qwen Code

### Overview

In this tutorial, you will build a complete Python calculator application **without writing a single line of code yourself**. Instead, you'll direct Qwen Code (your AI assistant) through prompts to:

- Set up the project with UV (modern Python package manager)
- Write tests first (TDD - Test Driven Development)
- Implement features to make tests pass
- Use git for version control
- Create pull requests for each feature

**You will only write prompts. The AI does ALL the coding and command execution.**

### Platform Support

This tutorial works on:

✅ Windows WSL (Ubuntu recommended)
✅ macOS (both Intel and Apple Silicon)
✅ Linux (Ubuntu, Debian, Fedora, Arch, etc.)

All commands are Unix-based and work identically across these platforms.

### Context7 Integration

This tutorial uses **Context7 MCP server** to provide **up-to-date documentation** for the tools we're using:
- **UV documentation** - Latest package manager commands and features
- **pytest documentation** - Current testing best practices
- **Git documentation** - Modern git workflows

Context7 ensures Qwen Code always has access to the latest documentation, preventing outdated or incorrect command suggestions.


---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Stage 1: Addition Feature](#stage-1-addition)
4. [Stage 2: Subtraction Feature](#stage-2-subtraction)
5. [Stage 3: Multiplication Feature](#stage-3-multiplication)
6. [Stage 4: Division Feature](#stage-4-division)
7. [Stage 5: CLI Interface](#stage-5-cli)
8. [Stage 6: Error Handling](#stage-6-errors)
9. [Final Review](#final-review)

---

## Prerequisites {#prerequisites}

### What You Need Installed

1. **Qwen Code** (local AI assistant)
2. **Git** (version control)
3. **UV** (Python package manager)
4. **GitHub account** (for pull requests)

### Verify Installation

**Prompt to Qwen Code:**

```
Check if the following tools are installed and show their versions:
- uv
- git
- python3
If any are missing, provide the installation commands for my OS.
```

Qwen will check and tell you what's installed or what needs to be installed.

---

## Important Tutorial Concepts

### Test-Driven Development (TDD)

The TDD cycle is:
1. **RED**: Write a failing test
2. **GREEN**: Write minimum code to pass the test
3. **REFACTOR**: Improve code quality (optional)

### Your Role

You will **ONLY** give high-level prompts like:
- "Create a git branch for the addition feature"
- "Write a test for adding two numbers"
- "Implement the code to make the test pass"

**You will NOT:**
- Write any Python code
- Write any git commands
- Write any terminal commands
- Create any files manually

### Qwen Code's Role

Qwen Code will:
- Execute all commands
- Write all code
- Run all tests
- Create git branches
- Make commits
- Create pull requests

---

## Project Setup {#project-setup}

### Step 1: Create Project Directory

**Your Prompt:**
```
Create a new directory called 'calculator-tdd' and navigate into it. 
Show me the command you're running and confirm when done.
```

**What Qwen Does:**
- Runs: `mkdir calculator-tdd && cd calculator-tdd`
- Confirms creation

### Step 2: Initialize Git Repository

**Your Prompt:**
```
Initialize a new git repository in this directory. 
Set up a .gitignore file appropriate for Python projects (include .venv, __pycache__, .pytest_cache, *.pyc).
Create an initial commit with message "Initial commit: Project setup".
Show me all commands you execute.
```

**What Qwen Does:**
- Runs: `git init`
- Creates `.gitignore` file
- Runs: `git add .gitignore`
- Runs: `git commit -m "Initial commit: Project setup"`

### Step 3: Initialize UV Project

**Your Prompt:**
```
Initialize a new Python project using UV package manager with the name 'calculator'.
Add pytest as a development dependency.
Create a basic project structure with:
- src/calculator/ directory for source code
- tests/ directory for tests
- README.md with project description
Show me the UV commands and file structure you create.
```

**What Qwen Does:**
- Runs: `uv init calculator`
- Runs: `uv add --dev pytest`
- Creates directory structure
- Creates `src/calculator/__init__.py`
- Creates `tests/__init__.py`
- Creates README.md

### Step 4: Create Main Branch and Push to GitHub

**Your Prompt:**
```
1. Rename the current branch to 'main' if it's not already
2. Create a new empty repository on GitHub called 'calculator-tdd' (provide me the git commands to run, I'll do the GitHub UI part)
3. After I confirm the GitHub repo is created, add it as remote origin and push

Wait for my confirmation before pushing.
```

**What Qwen Does:**
- Runs: `git branch -M main`
- Provides: Instructions for GitHub repo creation
- Waits for your confirmation
- After you confirm: runs `git remote add origin <url>` and `git push -u origin main`

**You Do:**
- Go to GitHub
- Create repository "calculator-tdd"
- Copy the repository URL
- Reply to Qwen: "Repository created, URL is: git@github.com:yourusername/calculator-tdd.git"

### Step 5: Verify Setup

**Your Prompt:**
```
Run pytest to verify the testing framework is working. 
Show me the output even though we have no tests yet.
Then show me the current project structure using the 'tree' command or 'ls -R'.
```

**What Qwen Does:**
- Runs: `uv run pytest`
- Runs: `tree` or `ls -R`
- Shows output

**Expected Structure:**
```
calculator-tdd/
├── .git/
├── .gitignore
├── pyproject.toml
├── README.md
├── src/
│   └── calculator/
│       └── __init__.py
└── tests/
    └── __init__.py
```

---

## Stage 1: Addition Feature {#stage-1-addition}

### RED Phase: Create Failing Test

**Your Prompt:**
```
Create a new git branch called 'feature/addition' from main.
Show me the git command you use.
```

**What Qwen Does:**
- Runs: `git checkout -b feature/addition`

**Your Prompt:**
```
Using TDD approach, write comprehensive test cases for an 'add' function in 'tests/test_calculator.py'.
You decide what test cases are important to cover all edge cases and normal scenarios.
The function doesn't exist yet - we're following TDD.

Run pytest to confirm the tests fail (RED phase).
Show me what test cases you created and why, then show the pytest output.
```

**What Qwen Does:**
- Creates `tests/test_calculator.py`:
```python
from calculator import add

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_with_negative():
    assert add(-1, 1) == 0

def test_add_zeros():
    assert add(0, 0) == 0
```
- Runs: `uv run pytest`
- Shows failing output (import error)

### GREEN Phase: Make Tests Pass

**Your Prompt:**
```
Now implement the minimal code needed to make these tests pass.
Create the 'add' function in 'src/calculator/__init__.py'.
Run pytest again to confirm all tests pass (GREEN phase).
Show me the implementation and test results.
```

**What Qwen Does:**
- Modifies `src/calculator/__init__.py`:
```python
def add(a, b):
    return a + b
```
- Runs: `uv run pytest`
- Shows passing output (all green)

### Commit and Push

**Your Prompt:**
```
1. Stage all changes
2. Commit with message "feat: Add addition functionality with tests"
3. Push the feature/addition branch to GitHub
4. Show me all git commands you execute
```

**What Qwen Does:**
- Runs: `git add .`
- Runs: `git commit -m "feat: Add addition functionality with tests"`
- Runs: `git push -u origin feature/addition`

### Create Pull Request

**Your Prompt:**
```
Provide me with the GitHub CLI command to create a pull request, or tell me what to do in the GitHub UI.
The PR should:
- Title: "Feature: Add addition functionality"
- Description: "Implements add() function following TDD. Tests included."
- Base: main
- Compare: feature/addition
```

**What Qwen Does:**
- Provides: `gh pr create --title "Feature: Add addition functionality" --body "Implements add() function following TDD. Tests included." --base main --head feature/addition`
- Or provides: Step-by-step UI instructions

**You Do:**
- Run the GitHub CLI command OR
- Go to GitHub and create PR manually
- **Do NOT merge yet** (we'll merge after all features)

**Your Prompt:**
```
Switch back to the main branch.
Show me the git command.
```

**What Qwen Does:**
- Runs: `git checkout main`

---

## Stage 2: Subtraction Feature {#stage-2-subtraction}

### RED Phase: Create Failing Test

**Your Prompt:**
```
Create a new branch 'feature/subtraction' from main.
Show me the command.
```

**What Qwen Does:**
- Runs: `git checkout -b feature/subtraction`

**Your Prompt:**
```
Write comprehensive tests for a 'subtract' function in 'tests/test_calculator.py'.
Think about all the important edge cases and scenarios that should be tested.
Explain your test strategy, then run pytest to see these new tests fail (RED).
```

**What Qwen Does:**
- Adds to `tests/test_calculator.py`:
```python
from calculator import add, subtract

# ... existing add tests ...

def test_subtract_positive_numbers():
    assert subtract(5, 3) == 2

def test_subtract_with_zero():
    assert subtract(0, 5) == -5

def test_subtract_same_numbers():
    assert subtract(10, 10) == 0

def test_subtract_negative_numbers():
    assert subtract(-5, -3) == -2
```
- Runs: `uv run pytest`
- Shows import error (subtract doesn't exist)

### GREEN Phase: Make Tests Pass

**Your Prompt:**
```
Implement the subtract function in 'src/calculator/__init__.py'.
Run pytest to confirm all tests pass.
Show implementation and results.
```

**What Qwen Does:**
- Adds to `src/calculator/__init__.py`:
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
```
- Runs: `uv run pytest`
- Shows all tests passing

### Commit, Push, and PR

**Your Prompt:**
```
1. Stage changes
2. Commit with message "feat: Add subtraction functionality with tests"
3. Push feature/subtraction branch
4. Provide GitHub CLI command or instructions for creating PR titled "Feature: Add subtraction functionality"
```

**What Qwen Does:**
- Executes git commands
- Provides PR creation command/instructions

**You Do:**
- Create the PR (don't merge yet)

**Your Prompt:**
```
Switch back to main branch.
```

**What Qwen Does:**
- Runs: `git checkout main`

---

## Stage 3: Multiplication Feature {#stage-3-multiplication}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/multiplication' from main.
Write comprehensive tests for a 'multiply' function.
Consider all important edge cases and scenarios for multiplication.
Explain your testing strategy, then run pytest to see failures (RED).
```

**What Qwen Does:**
- Runs: `git checkout -b feature/multiplication`
- Adds tests to `tests/test_calculator.py`
- Runs: `uv run pytest`
- Shows failures

### GREEN Phase

**Your Prompt:**
```
Implement the multiply function to make tests pass.
Run pytest to confirm GREEN.
Show code and results.
```

**What Qwen Does:**
- Adds to `src/calculator/__init__.py`:
```python
def multiply(a, b):
    return a * b
```
- Runs: `uv run pytest`
- Shows passing tests

### Commit, Push, and PR

**Your Prompt:**
```
Commit with message "feat: Add multiplication functionality with tests"
Push and provide PR creation command for "Feature: Add multiplication functionality"
```

**What Qwen Does:**
- Executes git workflow
- Provides PR command

**You Do:**
- Create PR

**Your Prompt:**
```
Return to main branch.
```

---

## Stage 4: Division Feature {#stage-4-division}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/division' from main.
Write comprehensive tests for a 'divide' function.
Think about edge cases for division (but we'll handle division by zero in a later stage).
Explain what you're testing and why, then run pytest to see RED.
```

**What Qwen Does:**
- Creates branch
- Writes tests
- Shows failures

### GREEN Phase

**Your Prompt:**
```
Implement divide function (simple version, no error handling yet).
Make tests pass.
Show GREEN.
```

**What Qwen Does:**
- Implements:
```python
def divide(a, b):
    return a / b
```
- Shows passing tests

### Commit, Push, and PR

**Your Prompt:**
```
Commit with "feat: Add division functionality with tests"
Push and create PR for "Feature: Add division functionality"
```

**You Do:**
- Create PR
- Return to main

---

## Stage 5: CLI Interface {#stage-5-cli}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/cli-interface' from main.

Design and write comprehensive tests for a command-line interface in 'tests/test_cli.py'.
The CLI should allow users to perform calculator operations from the command line.
You decide:
- What the interface should look like
- What arguments it should accept
- What output format makes sense
- What edge cases need testing

Explain your design decisions and testing strategy.
Then run pytest to see RED.
```

**What Qwen Does:**
- Creates branch
- Creates `tests/test_cli.py`
- Writes tests using pytest and/or subprocess
- Shows failures

### GREEN Phase

**Your Prompt:**
```
Implement a CLI in 'src/calculator/__main__.py' that makes the tests pass.
Use argparse or sys.argv to parse command line arguments.
Run pytest to confirm GREEN.
```

**What Qwen Does:**
- Creates `src/calculator/__main__.py`:
```python
import sys
from calculator import add, subtract, multiply, divide

def main():
    if len(sys.argv) != 4:
        print("Usage: python -m calculator <operation> <num1> <num2>")
        sys.exit(1)
    
    operation = sys.argv[1]
    num1 = float(sys.argv[2])
    num2 = float(sys.argv[3])
    
    operations = {
        'add': add,
        'subtract': subtract,
        'multiply': multiply,
        'divide': divide
    }
    
    if operation not in operations:
        print(f"Unknown operation: {operation}")
        sys.exit(1)
    
    result = operations[operation](num1, num2)
    print(result)

if __name__ == '__main__':
    main()
```
- Shows passing tests

### Manual Testing

**Your Prompt:**
```
Test the CLI manually with these commands:
- python -m calculator add 5 3
- python -m calculator multiply 4 7
- python -m calculator divide 10 2

Show me the outputs.
```

**What Qwen Does:**
- Runs each command
- Shows outputs

### Commit, Push, and PR

**Your Prompt:**
```
Commit with "feat: Add CLI interface with tests"
Push and create PR for "Feature: Add CLI interface"
```

---

## Stage 6: Error Handling {#stage-6-errors}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/error-handling' from main.

Add comprehensive tests for error handling throughout the calculator.
Think about what can go wrong:
- Division by zero
- Invalid inputs to CLI
- Wrong types
- Edge cases

You decide what errors should be caught and how they should be handled.
Write tests for all error scenarios you can think of.
Explain your error handling strategy, then run pytest to see RED.
```

**What Qwen Does:**
- Creates branch
- Adds comprehensive error tests
- Shows failures

### GREEN Phase

**Your Prompt:**
```
Update the divide function to handle division by zero properly.
Update the CLI to handle invalid inputs gracefully.
Make all tests pass.
Show GREEN.
```

**What Qwen Does:**
- Updates `divide()` function:
```python
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
```
- Updates CLI with try-except blocks
- Shows passing tests

### Commit, Push, and PR

**Your Prompt:**
```
Commit with "feat: Add comprehensive error handling"
Push and create PR for "Feature: Add error handling"
```

---

## Final Review {#final-review}

### Merge All Pull Requests

**Your Prompt:**
```
We have created multiple PRs. Now let's merge them in order:
1. List all open PRs using GitHub CLI
2. Provide commands to merge them in the order they were created
3. After each merge, update the local main branch
```

**What Qwen Does:**
- Runs: `gh pr list`
- Provides merge commands for each PR in order
- Updates local main after each merge

**You Do:**
- Execute merge commands (or merge via GitHub UI)

### Run Complete Test Suite

**Your Prompt:**
```
After all merges, checkout main and pull latest changes.
Run the complete test suite.
Show me the full pytest output with coverage if possible.
```

**What Qwen Does:**
- Runs: `git checkout main && git pull`
- Runs: `uv run pytest -v --cov=calculator`
- Shows comprehensive test results

### Create Documentation

**Your Prompt:**
```
Update the README.md file to include:
- Project description
- Features list
- Installation instructions using UV
- Usage examples for both module import and CLI
- Running tests instructions
- All calculator operations with examples

Show me the updated README.
```

**What Qwen Does:**
- Creates comprehensive README.md
- Shows content

**Your Prompt:**
```
Commit the README update with message "docs: Add comprehensive documentation"
Push to main.
```

### Final Project Structure

**Your Prompt:**
```
Show me the final project structure using tree or ls -R.
Show me the contents of all Python files.
Show me the git log with graph.
```

**What Qwen Does:**
- Shows complete structure
- Shows all code files
- Runs: `git log --graph --oneline --all`

**Expected Final Structure:**
```
calculator-tdd/
├── .git/
├── .gitignore
├── pyproject.toml
├── README.md
├── src/
│   └── calculator/
│       ├── __init__.py      (add, subtract, multiply, divide)
│       └── __main__.py      (CLI interface)
└── tests/
    ├── __init__.py
    ├── test_calculator.py   (function tests)
    └── test_cli.py          (CLI tests)
```

---

## Tutorial Summary

### What You Accomplished

**Without writing any code yourself**, you directed an AI to:

1. ✅ Set up a modern Python project with UV
2. ✅ Initialize git repository
3. ✅ Create 6 feature branches
4. ✅ **Design comprehensive test strategies** for each feature
5. ✅ Write comprehensive tests (TDD - RED phase)
6. ✅ Implement features (TDD - GREEN phase)
7. ✅ Create 6 pull requests
8. ✅ Merge all features into main
9. ✅ Build a fully functional calculator with:
   - Addition, subtraction, multiplication, division
   - Command-line interface
   - Comprehensive error handling
   - Complete test coverage
10. ✅ Document the project

### Skills Demonstrated

- **Test-Driven Development (TDD)**: Red → Green cycle
- **Test Design**: Letting AI identify edge cases and important scenarios
- **Version Control**: Git branches, commits, PRs
- **Modern Python Tooling**: UV package manager
- **AI-Assisted Development**: Directing AI through high-level prompts
- **Software Engineering Workflow**: Feature branches, testing, documentation
- **Delegation**: Trusting AI to make implementation decisions

### Key Prompting Patterns

**Successful prompts were:**
- **High-level**: "Write comprehensive tests for addition"
- **Delegating**: "You decide what test cases are important"
- **Structured**: "1. Create branch, 2. Write tests, 3. Run pytest"
- **Contextual**: "Following TDD, write failing test first"
- **Asking for reasoning**: "Explain your testing strategy"
- **Verifiable**: "Show me the output of pytest"

**Notice what we DIDN'T specify:**
- ❌ Exact test case values
- ❌ Number of tests needed
- ❌ Specific implementation details
- ❌ Code structure

The AI figured all that out!

---

## Next Steps

### Extend the Calculator

Continue practicing by prompting Qwen Code to add:

**Your Prompt Ideas:**
```
Add power/exponent function following TDD. 
You design the tests considering edge cases like negative exponents, zero, large numbers.
```

```
Add square root function. 
Design comprehensive tests including error cases.
You decide how to handle negative numbers.
```

```
Add memory functions (store, recall, clear).
Design the interface and write appropriate tests.
```

```
Add history feature that logs all calculations.
Design what information should be logged and how to retrieve it.
Write comprehensive tests.
```

```
Add support for chain calculations (e.g., "5 + 3 * 2").
Design the parsing logic and write thorough tests for order of operations.
```

```
Create a simple web API.
Design the REST endpoints and write comprehensive API tests.
```

```
Add configuration file support.
Design what should be configurable and write tests for configuration loading.
```

```
Create GitHub Actions CI/CD workflow.
Design the workflow and ensure it tests everything properly.
```

### Advanced Challenges

**Your Prompt:**
```
Refactor the calculator into a Calculator class with methods.
Design comprehensive tests for the class-based approach first.
Ensure they fail, then implement.
Create PR for this refactoring.
```

**Your Prompt:**
```
Add support for complex numbers to all operations.
Design tests that cover complex number edge cases.
Follow TDD. Create branch, tests, implementation, PR.
```

**Your Prompt:**
```
Create a GUI using tkinter or PyQt.
Design the interface and write comprehensive tests for user interactions.
Follow TDD where possible.
```

---

## Reflection Questions

After completing this tutorial, consider:

1. **How did directing AI differ from coding yourself?**
   - Was it faster? Slower?
   - Did you think differently about the problem?

2. **What made good vs bad prompts?**
   - Which prompts worked well?
   - Which needed clarification?
   - Was it better to specify test cases or let AI decide?
   - Did the AI choose good test cases?

3. **Did TDD make sense?**
   - Did writing tests first help?
   - Were the tests valuable?

4. **How was the git workflow?**
   - Did feature branches help organize work?
   - Were PRs useful even working alone?

5. **Could you maintain this code?**
   - Do you understand what was created?
   - Could you modify it?
   - Could you explain it to someone else?

---

## Complete Example Prompts Reference

### Project Initialization
```
Create directory calculator-tdd and navigate into it
Initialize git repository and create .gitignore for Python
Initialize UV project named calculator with pytest as dev dependency
Create src/calculator/ and tests/ directories with __init__.py files
```

### TDD Cycle Template
```
RED Phase:
Create branch feature/<feature-name> from main
Write comprehensive tests for <feature-name>
You decide what test cases cover important scenarios and edge cases
Explain your testing strategy
Run pytest to confirm tests fail

GREEN Phase:
Implement <feature-name> to make tests pass
Run pytest to confirm all tests pass

Commit & Push:
Commit with "feat: <description>"
Push branch and create PR
Return to main branch
```

### Verification Prompts
```
Show me the current project structure
Run pytest with verbose output
Show git log with graph
Show git status
List all branches
Show file contents of <filename>
```

### Command Examples
```
Execute: git checkout -b feature/addition
Execute: uv run pytest -v
Execute: git commit -m "feat: Add addition"
Show me what command would do X before running it
```

---

## Troubleshooting

### If Tests Fail Unexpectedly

**Your Prompt:**
```
The tests are failing. Show me:
1. The complete pytest output
2. The test file contents
3. The implementation file contents
4. Suggest what might be wrong
```

### If Git Issues Occur

**Your Prompt:**
```
I'm getting a git error. Show me:
1. Current git status
2. Current branch
3. What the error means
4. How to fix it
```

### If UV Commands Fail

**Your Prompt:**
```
UV command failed. Show me:
1. The exact error message
2. The uv --version output
3. Contents of pyproject.toml
4. Suggested fix
```

### If Qwen Doesn't Execute Commands

**Your Prompt:**
```
Please execute the following command and show me the output:
<command>

Do not just suggest it, actually run it and show results.
```

---

## Conclusion

Congratulations! You've built a complete, tested, documented Python project **entirely through AI prompts**.

You've learned:
- How to direct AI effectively
- Test-Driven Development methodology
- Professional git workflows
- Modern Python tooling (UV)
- Feature branch strategy
- Pull request process

**The key insight**: You can build software by clearly communicating intent to AI, just as you would to a human developer. The better your prompts, the better the results.

Keep practicing with your own projects, and you'll develop an intuition for effective AI-assisted development!

---

## Appendix: Complete Prompt Script

Here's every prompt in order for quick reference:

```plaintext
1. Check if uv, git, python3 are installed
2. Create calculator-tdd directory and navigate into it
3. Initialize git repository with Python .gitignore, initial commit
4. Initialize UV project 'calculator', add pytest, create structure
5. Rename branch to main, provide GitHub repo setup instructions
6. [Create GitHub repo] Confirm repo created with URL
7. Add remote origin and push
8. Run pytest to verify setup, show project structure

STAGE 1 - ADDITION:
9. Create branch feature/addition
10. Write comprehensive tests for add function, you decide test cases, explain strategy, run pytest (RED)
11. Implement add function, run pytest (GREEN)
12. Commit "feat: Add addition functionality with tests", push, create PR
13. Checkout main

STAGE 2 - SUBTRACTION:
14. Create branch feature/subtraction
15. Write comprehensive tests for subtract, you decide edge cases, run pytest (RED)
16. Implement subtract function, run pytest (GREEN)
17. Commit, push, create PR
18. Checkout main

STAGE 3 - MULTIPLICATION:
19. Create branch feature/multiplication
20. Write comprehensive tests for multiply, design test strategy, run pytest (RED)
21. Implement multiply function, run pytest (GREEN)
22. Commit, push, create PR
23. Checkout main

STAGE 4 - DIVISION:
24. Create branch feature/division
25. Write comprehensive tests for divide, think about edge cases, run pytest (RED)
26. Implement divide function, run pytest (GREEN)
27. Commit, push, create PR
28. Checkout main

STAGE 5 - CLI:
29. Create branch feature/cli-interface
30. Design CLI interface and write comprehensive tests, explain design, run pytest (RED)
31. Implement CLI in __main__.py, run pytest (GREEN)
32. Test CLI manually with examples
33. Commit, push, create PR
34. Checkout main

STAGE 6 - ERROR HANDLING:
35. Create branch feature/error-handling
36. Design error handling strategy and write comprehensive tests, run pytest (RED)
37. Implement error handling, run pytest (GREEN)
38. Commit, push, create PR
39. Checkout main

FINAL:
40. List all PRs, merge them in order
41. Pull latest main, run complete test suite with coverage
42. Update README with documentation
43. Commit README, push to main
44. Show final project structure and code
45. Show git log graph
```

---

**Happy AI-Assisted Development!** 🚀