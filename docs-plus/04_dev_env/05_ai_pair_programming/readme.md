# Building a Calculator with AI: Test-Driven Development Tutorial

## Complete Hands-Off Development with Gemini CLI/Qwen Code

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Project Setup](#project-setup)
4. [Stage 1: Addition Feature](#stage-1)
5. [Stage 2: Subtraction Feature](#stage-2)
6. [Stage 3: Multiplication Feature](#stage-3)
7. [Stage 4: Division Feature](#stage-4)
8. [Stage 5: CLI Interface](#stage-5)
9. [Stage 6: Error Handling](#stage-6)
10. [Final Review](#final-review)
11. [Conclusion](#conclusion)

---

## Overview {#overview}

In this tutorial, you will build a complete Python calculator application **without writing a single line of code yourself**. Instead, you'll direct Gemini CLI/Qwen Code (your AI assistant) through prompts to:

- Set up the project with UV (modern Python package manager)
- Write tests first (TDD - Test Driven Development)
- Implement features to make tests pass
- Use git for version control
- Create pull requests for each feature

**You will only write prompts. The AI does ALL the coding and command execution.**

### Platform Support

We highly recommend you that you should only work on:
- ✅ **Windows WSL** (Ubuntu or Debian recommended)
- ✅ **macOS** (both Intel and Apple Silicon)
- ✅ **Linux** (Ubuntu, Debian, Fedora, Arch, etc.)

All commands are Unix-based and work identically across these platforms. Windows users will not be doing development in Windows 11 but should be using Windows WSL. 

### Context7 Integration

This tutorial uses **Context7 MCP server** to provide **up-to-date documentation** for tools:
- **UV documentation** - Latest package manager commands
- **pytest documentation** - Current testing best practices
- **Git documentation** - Modern git workflows

Context7 ensures Gemini CLI/Qwen Code always has access to the latest tool documentation.

### Key Requirements

- **Python 3.12+** - Required for modern type hints with `|` union syntax
- **Type hints everywhere** - All code will use full type annotations
- **Cloud-based AI** - Gemini CLI/Qwen Code uses Cloud API (no local installation)

---

## Prerequisites {#prerequisites}

### What You Need

1. **Gemini CLI or Qwen Code CLI** - Cloud-based AI assistant
2. **Context7 MCP Server** - For up-to-date tool documentation
3. **Git** - Version control
4. **UV** - Python package manager
5. **Python 3.12+** - Required for modern type hints
6. **GitHub account** - For pull requests
7. **Qwen Auth** - From Alibaba Cloud


## Install Gemini CLI
```bash
# On Mac
brew install gemini-cli
# OR
npm install -g @google/gemini-cli

# verify
gemini --version
```

### Authenticate Gemini CLI

Login with Google (OAuth)
```bash
gemini
# when prompted, choose Login with Google and complete browser auth
```
Benefits (per official docs): free tier ~60 requests/min and 1,000 requests/day, 1M‑token context on Gemini 2.5 Pro; no key management.

### Install Qwen Code CLI

```bash
npm install -g @qwen-code/qwen-code@latest

qwen --version
# verify
qwen --help
```

### Authenticate Qwen Code

Qwen OAuth (🚀 Recommended – start in ~30 seconds)

```bash
# Just run this command and follow the browser authentication
qwen
```

What happens:
- Instant Setup: CLI opens your browser automatically
- One-Click Login: Authenticate with your qwen.ai account
- Automatic Management: Credentials cached locally for future use
- No Configuration: Zero setup required – just start coding!

Free Tier Benefits:
- ✅ 2,000 requests/day (no token counting needed)
- ✅ 60 requests/minute rate limit
- ✅ Automatic credential refresh
- ✅ Zero cost for individual users
- ℹ️ Note: Model fallback may occur to maintain service quality

### Verify System Requirements

**Prompt to GeminiCLI/Qwen Code:**

```
Check if the following tools are installed and show their versions:
- uv
- git  
- python3

Verify Python version is 3.12 or higher (required for modern type hints).
Use Context7 to get the latest UV documentation to verify correct installation.

If any tools are missing or Python is below 3.12, provide installation commands for my operating system and execute them.
```

**Expected Output:**
```
Platform: Ubuntu 22.04 (WSL2)
✓ uv: 0.5.2
✓ git: 2.34.1
✓ python3: 3.12.0 ✓ (Meets 3.12+ requirement)

Context7: Retrieved latest UV documentation
All requirements met!
```

### Context7 MCP Server Setup

**If Context7 is not configured, prompt:**

```
Help me set up Context7 MCP server integration with Qwen Code.
Context7 should provide access to documentation for:
- UV (Python package manager)
- pytest (testing framework)
- Git (version control)

Provide step-by-step instructions for my platform and execute them.
```

---

## Important Concepts

### Test-Driven Development (TDD)

The TDD cycle:
1. **RED**: Write a failing test
2. **GREEN**: Write minimum code to pass the test
3. **REFACTOR**: Improve code quality (optional)

### Your Role

You will **ONLY** give high-level prompts:
- "Create a git branch for the addition feature"
- "Write comprehensive tests for adding two numbers"
- "Implement the code to make the test pass"

**You will NOT:**
- Write any code
- Specify exact test cases
- Look up documentation

### Gemini CLI/Qwen Code's Role

Gemini CLI/Qwen Code will:
- Execute all commands
- Write all code with full type hints
- Design all test cases
- Run all tests
- Create git branches and commits
- Query Context7 for documentation

### Type Hints Requirement

**All code will use Python 3.12+ type hints:**
```python
# Modern union syntax with |
def add(a: int | float, b: int | float) -> int | float:
    return a + b

# Test functions
def test_add() -> None:
    assert add(2, 3) == 5
```

---

## Project Setup {#project-setup}

### Step 1: Create Project Directory

**Your Prompt:**
```
Create a new directory called 'calculator-tdd' in my home directory and navigate into it. 
Detect my operating system (WSL/macOS/Linux) and use appropriate commands.
Show me the commands you're running.
```

**Qwen Does:**
- Detects OS
- Runs: `mkdir ~/calculator-tdd && cd ~/calculator-tdd`
- Confirms creation

### Step 2: Initialize Git Repository

**Your Prompt:**
```
Initialize a new git repository in this directory. 
Set up a .gitignore file for Python projects (include .venv, __pycache__, .pytest_cache, *.pyc).
Create an initial commit with message "Initial commit: Project setup".
Show all commands.
```

**Gemini CLI/Qwen Does:**
- Runs: `git init`
- Creates `.gitignore`
- Runs: `git add .gitignore`
- Runs: `git commit -m "Initial commit: Project setup"`

### Step 3: Initialize UV Project

**Your Prompt:**
```
Initialize a new Python project using UV with the name 'calculator'.
Use Context7 to get the latest UV documentation for correct commands.
Add pytest as a development dependency.
Set Python version requirement to 3.12+.
Create structure:
- src/calculator/ directory
- tests/ directory
- README.md

Show the UV commands and file structure.
```

**Gemini CLI/Qwen Does:**
- Queries Context7 for UV docs
- Runs: `uv init calculator`
- Runs: `uv add --dev pytest`
- Sets Python 3.12+ in `pyproject.toml`
- Creates directories and files

### Step 4: GitHub Setup

**Your Prompt:**
```
1. Rename current branch to 'main'
2. Provide instructions for creating GitHub repository 'calculator-tdd'
3. Wait for my confirmation, then add remote and push
```

**Gemini CLI/Qwen Does:**
- Runs: `git branch -M main`
- Provides GitHub instructions
- Waits for confirmation

**You Do:**
- Create GitHub repository
- Reply: "Repository created, URL is: git@github.com:username/calculator-tdd.git"

**Gemini CLI/Qwen Then:**
- Runs: `git remote add origin <url>`
- Runs: `git push -u origin main`

### Step 5: Verify Setup

**Your Prompt:**
```
Run pytest to verify setup (no tests yet is fine).
Use Context7 to confirm correct pytest command for UV projects.
Show project structure.
```

**Gemini CLI/Qwen Does:**
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

## Stage 1: Addition Feature {#stage-1}

### RED Phase

**Your Prompt:**
```
Create a new git branch called 'feature/addition' from main.
```

**Gemini CLI/Qwen Does:**
- Runs: `git checkout -b feature/addition`

**Your Prompt:**
```
Using TDD, write comprehensive test cases for an 'add' function in 'tests/test_calculator.py'.
You decide what test cases cover all edge cases and normal scenarios.
The function doesn't exist yet - that's TDD.

IMPORTANT: 
- All test functions must have type hints (-> None)
- Use Context7 for pytest best practices

Run pytest to confirm tests fail (RED phase).
Show what test cases you created and why, then show pytest output.
```

**Gemini CLI/Qwen Creates:**
```python
from calculator import add
import pytest

def test_add_positive_numbers() -> None:
    """Test addition with positive integers"""
    assert add(2, 3) == 5
    assert add(100, 200) == 300

def test_add_with_zero() -> None:
    """Test addition with zero"""
    assert add(0, 0) == 0
    assert add(5, 0) == 5
    assert add(0, 5) == 5

def test_add_negative_numbers() -> None:
    """Test addition with negative numbers"""
    assert add(-1, -1) == -2
    assert add(-5, 3) == -2
    assert add(5, -3) == 2

def test_add_floats() -> None:
    """Test addition with floating point numbers"""
    assert add(0.1, 0.2) == pytest.approx(0.3)
    assert add(1.5, 2.5) == 4.0

def test_add_large_numbers() -> None:
    """Test addition with large numbers"""
    assert add(1000000, 2000000) == 3000000
```

**Gemini CLI/Qwen Explains:**
```
Test strategy covers:
1. Positive integers - basic functionality
2. Zero edge cases - identity property
3. Negative numbers - all sign combinations
4. Floats - precision handling with pytest.approx
5. Large numbers - no overflow issues

All tests use -> None type hint as required.
```

**Gemini CLI/Qwen Runs:**
- `uv run pytest`
- Shows import error (add doesn't exist) ✓ RED

### GREEN Phase

**Your Prompt:**
```
Implement the 'add' function in 'src/calculator/__init__.py' to make tests pass.

IMPORTANT: Use Python 3.12+ type hints with | union syntax.

Run pytest to confirm all tests pass (GREEN phase).
```

**Qwen Implements:**
```python
def add(a: int | float, b: int | float) -> int | float:
    """Add two numbers and return the result.
    
    Args:
        a: First number (int or float)
        b: Second number (int or float)
        
    Returns:
        Sum of a and b (int or float)
    """
    return a + b
```

**Gemini CLI/Qwen Runs:**
- `uv run pytest`
- All tests pass ✓ GREEN

### Commit and PR

**Your Prompt:**
```
1. Stage all changes
2. Commit with message "feat: Add addition functionality with tests"
3. Push feature/addition branch
4. Provide GitHub CLI command or instructions for PR
```

**Gemini CLI/Qwen Does:**
- Runs: `git add .`
- Runs: `git commit -m "feat: Add addition functionality with tests"`
- Runs: `git push -u origin feature/addition`
- Provides: `gh pr create --title "Feature: Add addition functionality" --body "Implements add() function with TDD. All tests pass." --base main --head feature/addition`

**You Do:**
- Create PR (don't merge yet)

**Your Prompt:**
```
Switch back to main branch.
```

**Gemini CLI/Qwen Does:**
- Runs: `git checkout main`

---

## Stage 2: Subtraction Feature {#stage-2}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/subtraction' from main.
Write comprehensive tests for a 'subtract' function in 'tests/test_calculator.py'.
Think about all important edge cases.

IMPORTANT: All test functions must have type hints (-> None).

Explain your test strategy, then run pytest to see RED.
```

**Gemini CLI/Qwen Does:**
- Creates branch
- Adds tests with type hints
- Explains strategy
- Shows failures

### GREEN Phase

**Your Prompt:**
```
Implement subtract function in 'src/calculator/__init__.py'.

IMPORTANT: Use Python 3.12+ type hints with | union syntax.

Run pytest to confirm all pass.
```

**Gemini CLI/Qwen Implements:**
```python
def add(a: int | float, b: int | float) -> int | float:
    """Add two numbers and return the result."""
    return a + b

def subtract(a: int | float, b: int | float) -> int | float:
    """Subtract b from a and return the result.
    
    Args:
        a: First number (int or float)
        b: Second number (int or float)
        
    Returns:
        Difference of a and b (int or float)
    """
    return a - b
```

**Gemini CLI/Qwen Runs:**
- All tests pass ✓ GREEN

### Commit and PR

**Your Prompt:**
```
Commit with "feat: Add subtraction functionality with tests"
Push and create PR for "Feature: Add subtraction functionality"
```

**You Do:**
- Create PR

**Your Prompt:**
```
Return to main branch.
```

---

## Stage 3: Multiplication Feature {#stage-3}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/multiplication' from main.
Write comprehensive tests for 'multiply' function.
Consider all edge cases for multiplication.

IMPORTANT: All test functions must have type hints (-> None).

Explain testing strategy, run pytest for RED.
```

### GREEN Phase

**Your Prompt:**
```
Implement multiply function.

IMPORTANT: Use Python 3.12+ type hints with | union syntax.

Run pytest for GREEN.
```

**Gemini CLI/Qwen Implements:**
```python
def multiply(a: int | float, b: int | float) -> int | float:
    """Multiply two numbers and return the result.
    
    Args:
        a: First number (int or float)
        b: Second number (int or float)
        
    Returns:
        Product of a and b (int or float)
    """
    return a * b
```

### Commit and PR

**Your Prompt:**
```
Commit with "feat: Add multiplication functionality with tests"
Push and create PR
```

**Your Prompt:**
```
Return to main branch.
```

---

## Stage 4: Division Feature {#stage-4}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/division' from main.
Write comprehensive tests for 'divide' function.
Think about edge cases (we'll handle division by zero later).

IMPORTANT: All test functions must have type hints (-> None).

Explain testing strategy, run pytest for RED.
```

### GREEN Phase

**Your Prompt:**
```
Implement divide function (simple version, no error handling yet).

IMPORTANT: Use Python 3.12+ type hints. Return type should be float.

Run pytest for GREEN.
```

**Gemini CLI/Qwen Implements:**
```python
def divide(a: int | float, b: int | float) -> float:
    """Divide a by b and return the result.
    
    Args:
        a: Numerator (int or float)
        b: Denominator (int or float)
        
    Returns:
        Quotient of a and b (always float)
    """
    return a / b
```

### Commit and PR

**Your Prompt:**
```
Commit with "feat: Add division functionality with tests"
Push and create PR
```

**Your Prompt:**
```
Return to main branch.
```

---

## Stage 5: CLI Interface {#stage-5}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/cli-interface' from main.

Design and write comprehensive tests for a CLI in 'tests/test_cli.py'.
The CLI should let users perform calculator operations from command line.
You decide:
- Interface design
- Arguments
- Output format
- Edge cases

IMPORTANT: All test functions must have type hints (-> None).

Explain design decisions and testing strategy, run pytest for RED.
```

### GREEN Phase

**Your Prompt:**
```
Implement CLI in 'src/calculator/__main__.py'.
Use argparse or sys.argv for arguments.

IMPORTANT: All functions must have Python 3.12+ type hints.

Run pytest for GREEN.
```

**Gemini CLI/Qwen Implements:**
```python
import sys
from calculator import add, subtract, multiply, divide

def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) != 4:
        print("Usage: python -m calculator <operation> <num1> <num2>")
        sys.exit(1)
    
    operation: str = sys.argv[1]
    try:
        num1: float = float(sys.argv[2])
        num2: float = float(sys.argv[3])
    except ValueError:
        print("Error: Arguments must be numbers")
        sys.exit(1)
    
    operations: dict[str, callable] = {
        'add': add,
        'subtract': subtract,
        'multiply': multiply,
        'divide': divide
    }
    
    if operation not in operations:
        print(f"Unknown operation: {operation}")
        sys.exit(1)
    
    result: int | float = operations[operation](num1, num2)
    print(result)

if __name__ == '__main__':
    main()
```

### Manual Testing

**Your Prompt:**
```
Test CLI manually:
- python -m calculator add 5 3
- python -m calculator multiply 4 7
- python -m calculator divide 10 2

Show outputs.
```

**Gemini CLI/Qwen Runs:**
- `uv run python -m calculator add 5 3` → 8.0
- `uv run python -m calculator multiply 4 7` → 28.0
- `uv run python -m calculator divide 10 2` → 5.0

### Commit and PR

**Your Prompt:**
```
Commit with "feat: Add CLI interface with tests"
Push and create PR
```

**Your Prompt:**
```
Return to main branch.
```

---

## Stage 6: Error Handling {#stage-6}

### RED Phase

**Your Prompt:**
```
Create branch 'feature/error-handling' from main.

Add comprehensive tests for error handling.
Think about what can go wrong:
- Division by zero
- Invalid CLI inputs
- Wrong types
- Edge cases

You decide error handling strategy.

IMPORTANT: All test functions must have type hints (-> None).

Explain strategy, run pytest for RED.
```

### GREEN Phase

**Your Prompt:**
```
Update divide function to handle division by zero.
Update CLI to handle invalid inputs gracefully.

IMPORTANT: Maintain all type hints.

Make all tests pass. Show GREEN.
```

**Gemini CLI/Qwen Updates:**
```python
def divide(a: int | float, b: int | float) -> float:
    """Divide a by b and return the result.
    
    Args:
        a: Numerator (int or float)
        b: Denominator (int or float)
        
    Returns:
        Quotient of a and b (float)
        
    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
```

### Commit and PR

**Your Prompt:**
```
Commit with "feat: Add comprehensive error handling"
Push and create PR
```

---

## Final Review {#final-review}

### Merge All PRs

**Your Prompt:**
```
List all open PRs.
Provide commands to merge them in order.
Update local main after each merge.
```

**You Do:**
- Merge all PRs via GitHub or CLI

### Run Complete Test Suite

**Your Prompt:**
```
Checkout main and pull latest.
Run complete test suite with coverage.
Show full pytest output.
```

**Gemini CLI/Qwen Runs:**
- `git checkout main && git pull`
- `uv run pytest -v --cov=calculator --cov-report=term-missing`

### Optional: Type Checking

**Your Prompt:**
```
Install and run mypy or pyright to verify all type hints are correct.
```

**Gemini CLI/Qwen Runs:**
- `uv add --dev mypy`
- `uv run mypy src/`
- Shows type checking results

### Create Documentation

**Your Prompt:**
```
Update README.md with:
- Project description
- Features list
- Installation instructions (UV, Python 3.12+)
- Platform notes (WSL/macOS/Linux)
- Usage examples (module import and CLI)
- Running tests
- All operations with examples

Show updated README.
```

**Your Prompt:**
```
Commit with "docs: Add comprehensive documentation"
Push to main.
```

### Final Structure

**Your Prompt:**
```
Show final project structure.
Show contents of all Python files.
Show git log with graph.
```

**Expected Final Structure:**
```
calculator-tdd/
├── .git/
├── .gitignore
├── pyproject.toml         # Python 3.12+ requirement
├── README.md
├── src/
│   └── calculator/
│       ├── __init__.py    # All functions with type hints
│       └── __main__.py    # CLI with type hints
└── tests/
    ├── __init__.py
    ├── test_calculator.py # Function tests with type hints
    └── test_cli.py        # CLI tests with type hints
```

---

## Tutorial Summary {#conclusion}

### What You Accomplished

**Without writing any code**, you directed AI to:

1. ✅ Set up modern Python project with UV
2. ✅ Use Python 3.12+ with modern type hints
3. ✅ Initialize git with proper workflows
4. ✅ Create 6 feature branches
5. ✅ Let AI design comprehensive test strategies
6. ✅ Write tests (RED phase)
7. ✅ Implement features (GREEN phase)
8. ✅ Create and merge 6 pull requests
9. ✅ Build fully functional calculator with:
   - Four operations with full type hints
   - CLI interface with type hints
   - Error handling
   - 100% test coverage
   - Professional documentation

### Skills Demonstrated

- **Test-Driven Development** - RED → GREEN cycle
- **Type Safety** - Python 3.12+ type hints throughout
- **Version Control** - Git branches, commits, PRs
- **Modern Python** - UV, pytest, type hints
- **AI-Assisted Development** - High-level prompts
- **Documentation Access** - Context7 for current docs
- **Cross-Platform** - WSL/macOS/Linux

### Key Prompting Patterns

**Successful prompts:**
- High-level: "Write comprehensive tests"
- Delegating: "You decide test cases"
- Documentation-aware: "Use Context7 for UV docs"
- Type-safe: "Use Python 3.12+ type hints"
- Structured: "1. Branch, 2. Tests, 3. Run pytest"
- Verifiable: "Show pytest output"

**What we DIDN'T specify:**
- Exact test cases
- Number of tests
- Code structure (except type hints)
- Platform commands
- Tool syntax

### Technology Stack

- **Gemini CLI/Qwen Code** - Cloud AI
- **Context7 MCP** - Documentation access
- **UV** - Python package manager
- **pytest** - Testing framework
- **Python 3.12+** - Modern type hints
- **Git** - Version control
- **Unix/Bash** - Universal commands

---

## Next Steps

### Extend the Calculator

**Your Prompt Ideas:**
```
Add power function with TDD.
Design tests for edge cases (negative exponents, zero, large numbers).
IMPORTANT: Use Python 3.12+ type hints.
```

```
Add square root function.
Design tests including error cases for negative numbers.
IMPORTANT: Full type annotations.
```

```
Refactor into Calculator class.
Design tests for class-based approach first.
IMPORTANT: Type hint class methods and attributes.
```

```
Add support for complex numbers.
Design tests for complex edge cases.
IMPORTANT: Use complex type in type hints.
```

```
Create FastAPI web API.
Design REST endpoints and tests.
IMPORTANT: Use FastAPI's type system with Python 3.12+ hints.
```

```
Add type checking to CI/CD.
Create GitHub Actions workflow with mypy or pyright.
```

### Troubleshooting

**Python Version Issues:**
```
Check version: python3 --version
Must be 3.12+
Install via: brew install python@3.12 (macOS)
Or: sudo apt install python3.12 (Ubuntu)
```


---

## Reflection Questions

1. How did directing AI differ from coding yourself?
2. What made good vs bad prompts?
3. Did TDD make sense?
4. How was the git workflow?
5. Could you maintain this code?
6. How was the platform experience?
7. Did Context7's documentation help?
8. How were Python 3.12+ type hints?
9. Did `|` union syntax feel natural?
10. Would you use type hints in your projects?

---

## Complete Prompt Reference

```plaintext
SETUP:
1. Check uv, git, python3 installed
2. Verify Python 3.12+
3. Verify Qwen Code CLI and API key
4. Create calculator-tdd directory
5. Initialize git with .gitignore
6. Initialize UV project, set Python 3.12+
7. Create GitHub repo, push to main

STAGE 1 - ADDITION:
8. Create branch feature/addition
9. Write tests with type hints (-> None), run pytest RED
10. Implement add with type hints (int | float), run pytest GREEN
11. Commit, push, create PR
12. Checkout main

STAGE 2 - SUBTRACTION:
13. Create branch feature/subtraction
14. Write tests with type hints, run pytest RED
15. Implement subtract with type hints, run pytest GREEN
16. Commit, push, create PR
17. Checkout main

STAGE 3 - MULTIPLICATION:
18. Create branch feature/multiplication
19. Write tests with type hints, run pytest RED
20. Implement multiply with type hints, run pytest GREEN
21. Commit, push, create PR
22. Checkout main

STAGE 4 - DIVISION:
23. Create branch feature/division
24. Write tests with type hints, run pytest RED
25. Implement divide with type hints (-> float), run pytest GREEN
26. Commit, push, create PR
27. Checkout main

STAGE 5 - CLI:
28. Create branch feature/cli-interface
29. Write CLI tests with type hints, run pytest RED
30. Implement CLI with full type hints, run pytest GREEN
31. Test CLI manually
32. Commit, push, create PR
33. Checkout main

STAGE 6 - ERROR HANDLING:
34. Create branch feature/error-handling
35. Write error tests with type hints, run pytest RED
36. Implement error handling maintaining type hints, run pytest GREEN
37. Commit, push, create PR
38. Checkout main

FINAL:
39. Merge all PRs
40. Run test suite with coverage
41. Optional: Run mypy/pyright
42. Update README (note Python 3.12+ requirement)
43. Show final structure with type hints
```

---

**Happy AI-Assisted Development!** 🚀

**Remember:** All code uses Python 3.12+ type hints with modern `|` union syntax!