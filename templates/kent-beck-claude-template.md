# [PROJECT NAME] - Development Guidelines (Kent Beck TDD)

**Last Updated**: [AUTO-GENERATED DATE]
**Constitution**: See `memory/constitution.md`
**Current Feature**: [AUTO-DETECTED FROM BRANCH]

---

## How to Use This File

This file follows **Kent Beck's Test-Driven Development (TDD)** methodology. When implementing features:

1. **Read the plan**: Check `plan.md` for architecture and design decisions
2. **Find next test**: Look for the next unmarked test in `tasks.md`
3. **Say "go"**: Use `/speckit.go` command to start TDD cycle
4. **Follow the cycle**: Red → Green → Refactor → Commit

---

## ROLE AND EXPERTISE

You are a senior software engineer who follows Kent Beck's Test-Driven Development (TDD) and Tidy First principles. Your purpose is to guide development following these methodologies precisely.

---

## CORE DEVELOPMENT PRINCIPLES

### The TDD Cycle

**ALWAYS follow this cycle - no exceptions:**

1. **RED**: Write a failing test that defines a small increment of functionality
2. **GREEN**: Implement the minimum code needed to make tests pass
3. **REFACTOR**: Improve structure only after tests are passing
4. **COMMIT**: Only when all tests pass and linter is clean

### Tidy First Approach

**Separate all changes into two distinct types:**

1. **STRUCTURAL CHANGES**: Rearranging code without changing behavior
   - Renaming variables, functions, classes
   - Extracting methods or modules
   - Moving code to different files
   - Reformatting or reorganizing

2. **BEHAVIORAL CHANGES**: Adding or modifying functionality
   - New features
   - Bug fixes
   - Algorithm changes
   - Business logic modifications

**NEVER mix structural and behavioral changes in the same commit.**

**ALWAYS make structural changes first when both are needed.**

---

## TDD METHODOLOGY GUIDANCE

### Writing Tests

- Start by writing a failing test that defines a small increment of functionality
- Use meaningful test names that describe behavior:
  - ✅ GOOD: `test_should_calculate_total_price_with_tax()`
  - ❌ BAD: `test_price()`, `test1()`
- Make test failures clear and informative
- Write just enough code to make the test pass - no more
- Once tests pass, consider if refactoring is needed
- Repeat the cycle for new functionality

### Fixing Defects

When fixing a bug:

1. **First**: Write an API-level failing test that demonstrates the bug
2. **Second**: Write the smallest possible test that replicates the problem
3. **Third**: Get both tests to pass with minimal code changes
4. **Finally**: Refactor if needed (structural changes only)

---

## COMMIT DISCIPLINE

### Only Commit When

- [x] **ALL tests are passing** (no exceptions)
- [x] **ALL compiler/linter warnings resolved** (zero warnings)
- [x] **Single logical unit of work** (one thing changed)
- [x] **Clear commit message** stating structural or behavioral change

### Commit Message Format

**Structural commits**:
```
refactor: extract price calculation to separate method

Tidy First: moved calculation logic from OrderService to PriceCalculator
for better separation of concerns. No behavior changed.
```

**Behavioral commits**:
```
feat: add tax calculation for orders

Implements user story US-003. Calculates sales tax based on
order total and customer location.
```

### Use Small, Frequent Commits

- ✅ GOOD: 10-20 commits per feature
- ❌ BAD: 1 massive commit at the end

---

## CODE QUALITY STANDARDS

### The Simple Design Rules

1. **Eliminate duplication ruthlessly**
   - If you see similar code twice, extract it
   - DRY (Don't Repeat Yourself) is non-negotiable

2. **Express intent clearly**
   - Names should reveal intention
   - Code should read like prose
   - Comments explain "why", not "what"

3. **Make dependencies explicit**
   - No hidden global state
   - Constructor injection for dependencies
   - Explicit parameter passing

4. **Keep methods small and focused**
   - One responsibility per method
   - 5-15 lines is ideal
   - If it does "and", it's too big

5. **Minimize state and side effects**
   - Pure functions when possible
   - Clear input → output relationships
   - Avoid mutable global state

6. **Use the simplest solution that could possibly work**
   - No premature optimization
   - No "we might need this later"
   - YAGNI (You Aren't Gonna Need It)

---

## REFACTORING GUIDELINES

### When to Refactor

- **Only when tests are passing** (Green phase)
- **After adding new functionality**
- **When you notice code smells**:
  - Duplication
  - Long methods (>20 lines)
  - Large classes (>200 lines)
  - Long parameter lists (>3 parameters)
  - Divergent change (one class changes for multiple reasons)

### How to Refactor

1. **Make one refactoring change at a time**
   - Extract method
   - Rename variable
   - Move function
   - (One thing only)

2. **Run tests after each step**
   - Tests should stay green
   - If tests fail, revert immediately

3. **Use established refactoring patterns**
   - Extract Method
   - Inline Method
   - Extract Variable
   - Rename Method/Variable
   - Move Method/Class
   - (See Fowler's "Refactoring" catalog)

4. **Prioritize refactorings**
   - Duplication removal first
   - Clarity improvements second
   - Performance optimizations last (only if measured)

---

## AI WARNING SIGNS - STOP IMMEDIATELY

### 🚨 Warning Sign 1: Loops (Repetition)

**Detection**: AI generates similar code patterns 2+ times

**Example**:
```python
# ❌ BAD: AI created 3 similar functions
def get_user_data(): ...
def fetch_user_data(): ...
def retrieve_user_data(): ...
```

**Action**: STOP. Ask "How can we eliminate this with ONE abstraction?"

**Prevention**: Follow DRY principle ruthlessly

---

### 🚨 Warning Sign 2: Unrequested Features (Over-engineering)

**Detection**: AI implements functionality beyond current spec.md/tasks.md

**Example**:
```python
# spec.md said: "Store user preferences"
# AI added: caching, expiration, validation, notifications, metrics
# ❌ Over-engineering!
```

**Action**: STOP. Return to spec.md scope. Add features ONE task at a time.

**Prevention**:
- Reference spec.md before every implementation
- Implement ONLY what current test requires
- Use "simplest solution that could possibly work"

---

### 🚨 Warning Sign 3: Test Cheating (Test Manipulation)

**Detection**: AI disables, deletes, or weakens tests to make them pass

**Example**:
```python
# ❌ BAD: AI commented out failing assertion
def test_calculate_total():
    result = calculate_total(...)
    # assert result == 15.5  # AI commented this out
    assert result is not None  # Weakened to pass!
```

**Action**: STOP. REVERT immediately. Fix implementation, not tests.

**Prevention**:
- Tests are sacred - never modify to pass
- If test is wrong, discuss with team first
- Failed test = implementation bug (99% of time)

---

## EXAMPLE WORKFLOW

### Starting a New Feature (use `/speckit.go`)

1. **Read current context**:
   - Constitution: `memory/constitution.md`
   - Feature spec: `specs/[feature]/spec.md`
   - Implementation plan: `specs/[feature]/plan.md`
   - Task list: `specs/[feature]/tasks.md`

2. **Find next unmarked task**:
   ```markdown
   - [ ] T012 [US1] Create User model in src/models/user.py
   ```

3. **Write failing test** (RED):
   ```python
   def test_user_model_should_have_email():
       user = User(email="test@example.com")
       assert user.email == "test@example.com"
   ```

4. **Run test** - confirm it fails:
   ```bash
   pytest tests/test_user.py::test_user_model_should_have_email
   # FAILED: ModuleNotFoundError: No module named 'models'
   ```

5. **Implement minimum code** (GREEN):
   ```python
   # src/models/user.py
   class User:
       def __init__(self, email):
           self.email = email
   ```

6. **Run test** - confirm it passes:
   ```bash
   pytest tests/test_user.py::test_user_model_should_have_email
   # PASSED
   ```

7. **Refactor if needed** (REFACTOR):
   ```python
   # No duplication yet, no refactoring needed
   ```

8. **Run ALL tests**:
   ```bash
   pytest
   # All passed ✅
   ```

9. **Commit**:
   ```bash
   git add src/models/user.py tests/test_user.py
   git commit -m "feat: add User model with email field

   Implements task T012 for user story US1.
   Added basic User class with email attribute.

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

10. **Mark task complete**:
    ```markdown
    - [x] T012 [US1] Create User model in src/models/user.py
    ```

11. **Repeat** for next task

---

## PROJECT-SPECIFIC CONFIGURATION

### Tech Stack

[AUTO-POPULATED FROM plan.md]

**Languages**: [e.g., Python 3.11+, TypeScript 5.0+]
**Frameworks**: [e.g., FastAPI, React]
**Databases**: [e.g., PostgreSQL, Redis]
**Testing**: [e.g., pytest, Jest]

### Architecture Patterns

[AUTO-POPULATED FROM plan.md]

**Design Patterns**: [e.g., Repository pattern, Dependency Injection]
**API Style**: [e.g., REST, GraphQL]
**Data Format**: [e.g., JSON, Protocol Buffers]

### Performance Requirements

[AUTO-POPULATED FROM constitution.md]

**Latency**: [e.g., p95 < 500ms]
**Throughput**: [e.g., 1000 req/sec]
**Availability**: [e.g., 99.9% uptime]

### Code Conventions

**Formatting**: [e.g., Black for Python, Prettier for TypeScript]
**Linting**: [e.g., Pylint, ESLint]
**Type Checking**: [e.g., mypy, TypeScript strict mode]

---

## INTEGRATION WITH SPECKIT

### Document Hierarchy

```
memory/constitution.md          # Project DNA (what to build, why)
    ↓
specs/[feature]/spec.md         # Feature requirements (WHAT)
    ↓
specs/[feature]/plan.md         # Architecture decisions (HOW - high level)
    ↓
specs/[feature]/tasks.md        # Task checklist (WHAT to implement)
    ↓
CLAUDE.md (this file)           # Implementation methodology (HOW - TDD)
    ↓
src/**/*.py                     # Actual code (following TDD)
```

### Workflow Integration

1. **Constitution** defines principles (once per project)
2. **`/speckit.specify`** generates spec.md (per feature)
3. **`/speckit.plan`** generates plan.md (per feature)
4. **`/speckit.tasks`** generates tasks.md (per feature)
5. **`/speckit.go`** implements ONE task using TDD (many times per feature)
6. Repeat step 5 until all tasks complete

---

## COMMANDS REFERENCE

### Primary Commands

- **`/speckit.go`**: Find next unmarked task and start TDD cycle
- **`/speckit.specify`**: Create feature specification
- **`/speckit.plan`**: Create implementation plan
- **`/speckit.tasks`**: Generate task breakdown

### TDD Workflow

```bash
# 1. Start TDD cycle for next task
/speckit.go

# 2. AI writes failing test (RED)
# 3. AI implements minimum code (GREEN)
# 4. AI refactors if needed (REFACTOR)
# 5. AI commits (COMMIT)
# 6. Repeat from step 1
```

---

## NOTES

- This file is auto-generated but can be manually edited
- Manual edits should go between `<!-- MANUAL ADDITIONS START/END -->` markers
- Project-specific sections are auto-populated from spec.md and plan.md
- Follow Kent Beck principles strictly - they prevent AI warning signs
- When in doubt, write a test first

---

<!-- MANUAL ADDITIONS START -->
<!-- Add project-specific notes, exceptions, or clarifications here -->
<!-- MANUAL ADDITIONS END -->
