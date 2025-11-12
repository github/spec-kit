---
description: Execute Kent Beck TDD cycle for next unmarked task from tasks.md
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This command implements **Kent Beck's "go" workflow** for Test-Driven Development. It finds the next unmarked task in `tasks.md`, implements it following strict TDD principles (Red → Green → Refactor), and commits the result.

1. **Load Context**: Read CLAUDE.md, spec.md, plan.md, tasks.md
2. **Find Next Task**: Locate first unmarked `- [ ]` task
3. **Execute TDD Cycle**: Red → Green → Refactor
4. **Commit**: Following Tidy First principles
5. **Mark Complete**: Update tasks.md

## Execution Flow

### Phase 0: Context Loading

1. **Verify Prerequisites**:
   - `CLAUDE.md` exists in project root (Kent Beck development guidelines)
   - `specs/[feature]/tasks.md` exists (task checklist)
   - Git working directory has no uncommitted changes in spec files (tasks.md, plan.md, spec.md)

   **If missing**:
   - ERROR: "CLAUDE.md not found. Run `/speckit.init-tdd` first."
   - ERROR: "tasks.md not found. Run `/speckit.tasks` first."
   - WARN: "Uncommitted changes detected in spec files. Consider committing before TDD cycle."

2. **Read Context Files**:
   ```bash
   # Required files
   CLAUDE.md                        # TDD methodology
   memory/constitution.md           # Project principles
   specs/[feature]/spec.md          # Feature requirements
   specs/[feature]/plan.md          # Architecture
   specs/[feature]/tasks.md         # Task checklist

   # Optional files (if present)
   specs/[feature]/data-model.md    # Data structures
   specs/[feature]/contracts/       # API specs
   ```

3. **Extract Key Information**:
   - Current feature name from branch/directory
   - Tech stack from plan.md
   - Test framework from plan.md (pytest, Jest, etc.)
   - Code conventions from CLAUDE.md

---

### Phase 1: Find Next Task

1. **Parse tasks.md**:
   ```markdown
   ## Phase 3: User Story 1 - User Registration

   - [x] T012 [US1] Create User model in src/models/user.py
   - [x] T013 [US1] Write User model tests in tests/test_user.py
   - [ ] T014 [US1] Implement UserService in src/services/user_service.py  ← NEXT
   - [ ] T015 [US1] Add user registration endpoint
   ```

2. **Identify Next Unmarked Task**:
   - Scan for first `- [ ]` (unchecked checkbox)
   - Extract task details:
     - **Task ID**: T014
     - **Story Label**: [US1]
     - **Description**: "Implement UserService in src/services/user_service.py"
     - **File Path**: `src/services/user_service.py`

3. **Validate Task**:
   - Task must have clear file path
   - Task must be actionable (not vague)
   - All prerequisite tasks (earlier in list) must be marked complete

   **If validation fails**:
   - ERROR: "Task T014 has no file path specified"
   - ERROR: "Task T012 is not complete yet (prerequisite)"

4. **Display to User**:
   ```
   📋 Next Task: T014 [US1]
   📝 Description: Implement UserService in src/services/user_service.py
   📁 File: src/services/user_service.py
   🎯 User Story: US1 - User Registration

   Starting TDD cycle...
   ```

---

### Phase 2: RED - Write Failing Test

**CRITICAL**: Follow Test-Driven Development strictly. Test MUST be written first.

1. **Determine Test File Location**:
   - If task mentions "test" → use specified path
   - If implementation file → infer test path from conventions:
     - Python: `src/services/user_service.py` → `tests/test_user_service.py`
     - TypeScript: `src/services/userService.ts` → `src/services/userService.test.ts`
     - (Follow project conventions from CLAUDE.md)

2. **Reference Spec for Behavior**:
   - Find relevant user story in spec.md (use [US1] label)
   - Extract acceptance criteria
   - Identify testable behavior

3. **Write Minimal Failing Test**:
   - Test name describes behavior (not implementation)
   - ✅ GOOD: `test_user_service_should_register_new_user()`
   - ❌ BAD: `test_register()`, `test1()`

   **Example**:
   ```python
   # tests/test_user_service.py
   def test_user_service_should_register_new_user():
       """User service should create new user with email and hashed password"""
       service = UserService()
       result = service.register_user(email="test@example.com", password="secret123")

       assert result.email == "test@example.com"
       assert result.password != "secret123"  # Should be hashed
       assert len(result.password) > 20       # Hashed passwords are long
   ```

4. **Run Test - Confirm Failure**:
   ```bash
   # Python example
   pytest tests/test_user_service.py::test_user_service_should_register_new_user -v

   # Expected output: FAILED (ModuleNotFoundError or AttributeError)
   ```

5. **Verify Correct Failure**:
   - Test fails for the RIGHT reason (missing implementation)
   - Test does NOT fail due to syntax error or wrong imports
   - Error message is clear about what's missing

   **If wrong failure**:
   - Fix test syntax/imports
   - Re-run until failure is "implementation missing"

---

### Phase 3: GREEN - Implement Minimum Code

**CRITICAL**: Write ONLY enough code to make test pass. No more.

1. **Create Implementation File** (if not exists):
   ```python
   # src/services/user_service.py
   ```

2. **Implement Minimum Logic**:
   - Use "simplest solution that could possibly work"
   - No premature abstractions
   - No "we might need this later"
   - Hardcode if necessary (refactor later)

   **Example**:
   ```python
   # src/services/user_service.py
   import hashlib
   from models.user import User

   class UserService:
       def register_user(self, email: str, password: str) -> User:
           # Hash password (simple implementation)
           hashed = hashlib.sha256(password.encode()).hexdigest()

           # Create user (minimum viable)
           user = User(email=email, password=hashed)

           return user
   ```

3. **Run Test Again**:
   ```bash
   pytest tests/test_user_service.py::test_user_service_should_register_new_user -v

   # Expected: PASSED ✅
   ```

4. **Run ALL Tests**:
   ```bash
   pytest  # Run entire test suite

   # Must be: All tests pass ✅
   ```

   **If any test fails**:
   - STOP immediately
   - Fix the regression
   - Do NOT proceed to refactor

---

### Phase 4: REFACTOR - Improve Structure (Optional)

**Only execute if refactoring is needed. Skip if code is already clean.**

1. **Identify Code Smells**:
   - [ ] Duplication exists?
   - [ ] Method too long (>20 lines)?
   - [ ] Unclear naming?
   - [ ] Hardcoded values should be constants?
   - [ ] Logic should be extracted?

   **If NO smells detected**: SKIP to Phase 5 (Commit)

2. **Make ONE Refactoring at a Time**:

   **Example - Extract hardcoded algorithm**:
   ```python
   # Before (hardcoded SHA256)
   hashed = hashlib.sha256(password.encode()).hexdigest()

   # After (extracted method)
   def _hash_password(self, password: str) -> str:
       return hashlib.sha256(password.encode()).hexdigest()

   hashed = self._hash_password(password)
   ```

3. **Run ALL Tests After Each Refactoring**:
   ```bash
   pytest
   # Must stay green ✅
   ```

4. **Repeat** until no more obvious improvements (max 3 refactorings per cycle)

5. **Final Test Run**:
   ```bash
   pytest
   # All tests must pass ✅
   ```

---

### Phase 5: COMMIT - Following Tidy First

**CRITICAL**: Separate structural commits from behavioral commits.

1. **Determine Commit Type**:

   **Behavioral commit** (this cycle added NEW functionality):
   ```bash
   git add src/services/user_service.py tests/test_user_service.py
   git commit -m "feat: add user registration to UserService

   Implements task T014 for user story US1.
   UserService.register_user() creates new users with hashed passwords.

   🤖 Generated with Claude Code"
   ```

   **Structural commit** (if refactoring was done):
   ```bash
   # If you did refactoring, commit it SEPARATELY
   git add src/services/user_service.py
   git commit -m "refactor: extract password hashing to private method

   Tidy First: moved SHA256 hashing logic to _hash_password() for clarity.
   No behavior changed. All tests still pass.

   🤖 Generated with Claude Code"
   ```

2. **Verify Commit**:
   ```bash
   git status
   # Should be: nothing to commit, working tree clean

   git log -1 --stat
   # Verify files and commit message
   ```

---

### Phase 6: Mark Task Complete

1. **Update tasks.md**:
   ```markdown
   ## Phase 3: User Story 1 - User Registration

   - [x] T012 [US1] Create User model in src/models/user.py
   - [x] T013 [US1] Write User model tests in tests/test_user.py
   - [x] T014 [US1] Implement UserService in src/services/user_service.py  ← COMPLETED
   - [ ] T015 [US1] Add user registration endpoint
   ```

2. **Commit Task Update**:
   ```bash
   git add specs/[feature]/tasks.md
   git commit -m "docs: mark task T014 as complete"
   ```

3. **Report to User**:
   ```
   ✅ Task T014 Complete

   📝 Test: test_user_service_should_register_new_user()
   ✅ Status: PASSED

   📁 Files Changed:
   - src/services/user_service.py (new)
   - tests/test_user_service.py (new)

   📊 Test Results:
   - Total tests: 15
   - Passed: 15 ✅
   - Failed: 0

   💾 Commits:
   - feat: add user registration to UserService (abc1234)
   - docs: mark task T014 as complete (def5678)

   🎯 Next Task: T015 [US1] Add user registration endpoint

   Ready for next cycle. Run `/speckit.go` again to continue.
   ```

---

## AI WARNING SIGNS - AUTO-DETECT

During execution, automatically check for Kent Beck's warning signs:

### 🚨 Detection 1: Repetition (Loops)

**Trigger**: Similar code patterns generated 2+ times in this session

**Example**:
```python
# RED FLAG: AI generated similar functions
def get_user(): ...
def fetch_user(): ...
def retrieve_user(): ...
```

**Action**:
1. STOP execution
2. WARN user: "⚠️ AI Warning Sign: Repetition detected"
3. Show duplicated patterns
4. Ask: "Should we extract a common abstraction?"
5. Wait for user confirmation before proceeding

---

### 🚨 Detection 2: Over-engineering

**Trigger**: Implementation goes beyond test requirements

**Example**:
```python
# Test only requires: register_user(email, password)
# AI added: caching, metrics, logging, retry logic, circuit breaker
# ❌ Over-engineering!
```

**Action**:
1. STOP execution
2. WARN user: "⚠️ AI Warning Sign: Unrequested features added"
3. List added features not in test
4. Ask: "Remove extra features and keep minimum?"
5. Revert to minimal implementation

---

### 🚨 Detection 3: Test Manipulation

**Trigger**: Test is modified to pass instead of fixing implementation

**Example**:
```python
# Original test (failing)
assert result == 15.5

# AI changed to (passing)
assert result is not None  # ❌ Weakened!
```

**Action**:
1. STOP execution immediately
2. ERROR: "❌ FATAL: Test manipulation detected"
3. REVERT all changes
4. Show original vs modified test
5. Require manual intervention

---

## Error Handling

### Common Errors

**ERROR 1: No unmarked tasks**
```
All tasks in tasks.md are complete! ✅

Next steps:
- Review implementation against spec.md
- Run full test suite: pytest
- Create pull request: /speckit.pr
```

**ERROR 2: Test won't pass**
```
❌ Test failed after 3 attempts

Test: test_user_service_should_register_new_user()
Error: AssertionError: Expected hashed password length > 20, got 8

Possible issues:
1. Test expectations are wrong (review spec.md)
2. Implementation has a bug (review code)
3. Missing dependency or setup

Action: Manual debugging required. Type 'continue' when ready.
```

**ERROR 3: Git conflicts**
```
❌ Cannot commit: merge conflicts detected

Files with conflicts:
- src/services/user_service.py

Action: Resolve conflicts manually, then run /speckit.go again.
```

---

## Guidelines for Success

### Do's ✅

- **Follow TDD strictly**: Test first, ALWAYS
- **Keep cycles small**: 5-10 minutes per task
- **Run tests frequently**: After every code change
- **Commit often**: After each green cycle
- **Read CLAUDE.md**: When uncertain about patterns
- **Reference spec.md**: To understand behavior
- **Ask user**: When ambiguous requirements

### Don'ts ❌

- **Never skip RED phase**: Always write failing test first
- **Never commit failing tests**: Only commit when green
- **Never mix commits**: Structural ≠ Behavioral
- **Never over-implement**: Just enough to pass test
- **Never modify test to pass**: Fix implementation instead
- **Never ignore warnings**: AI warning signs are serious

---

## Integration with Speckit Workflow

```
/speckit.specify        → Generate spec.md
    ↓
/speckit.plan          → Generate plan.md
    ↓
/speckit.tasks         → Generate tasks.md
    ↓
/speckit.init-tdd      → Generate CLAUDE.md (one-time)
    ↓
/speckit.go            → Implement task 1 (TDD)
    ↓
/speckit.go            → Implement task 2 (TDD)
    ↓
/speckit.go            → Implement task N (TDD)
    ↓
All tasks complete!
```

---

## Example Session

```bash
User: /speckit.go
AI: 📋 Next Task: T014 [US1]
📝 Description: Implement UserService in src/services/user_service.py
📁 File: src/services/user_service.py
🎯 User Story: US1 - User Registration

Starting TDD cycle...

---

## RED Phase: Writing failing test

Creating: tests/test_user_service.py

[Shows test code]

Running test...
❌ FAILED: ModuleNotFoundError: No module named 'services'

Good! Test fails for the right reason. Proceeding to GREEN phase...

---

## GREEN Phase: Implementing minimum code

Creating: src/services/user_service.py

[Shows implementation code]

Running test...
✅ PASSED

Running all tests...
✅ All 15 tests passed

---

## REFACTOR Phase: Improving structure

Checking for code smells...
- No duplication detected ✅
- Method length OK (8 lines) ✅
- Naming is clear ✅

No refactoring needed. Proceeding to COMMIT phase...

---

## COMMIT Phase

Creating commit...
✅ Committed: feat: add user registration to UserService (abc1234)
✅ Committed: docs: mark task T014 as complete (def5678)

---

✅ Task T014 Complete

📊 Summary:
- Tests written: 1
- Tests passing: 15/15
- Files created: 2
- Commits made: 2

🎯 Next Task: T015 [US1] Add user registration endpoint

Ready for next cycle. Run /speckit.go again to continue.
```

---

## Notes

- This command embodies Kent Beck's TDD methodology
- Strict adherence prevents AI warning signs (loops, over-engineering, test cheating)
- Each cycle should take 5-10 minutes
- Use `/speckit.go` repeatedly until all tasks complete
- Can be interrupted and resumed safely (git ensures atomicity)
