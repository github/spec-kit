---
description: Execute implementation following the plan and tasks with strict TDD enforcement and validation gates
---

# Implement - Execute Feature Implementation with TDD Enforcement

**Implementation Target**: $ARGUMENTS

## Capability Mode Detection

**The script automatically detects your current workflow:**

- **Parent feature branch** (`username/jira-123.feature-name`):
   - Reads from: `specs/jira-123.feature-name/plan.md`, `tasks.md`
   - Implementation: Single PR workflow (<1000 LOC total)

- **Capability branch** (`username/jira-123.feature-name-cap-001`):
   - Reads from: `specs/jira-123.feature-name/cap-001-auth/plan.md`, `tasks.md`
   - Implementation: Atomic PR workflow (~1000 LOC total, 800-1200 acceptable)
   - PR target: `cap-001` branch → `main` (not to parent branch)

**No flag needed** - detection is automatic based on branch name pattern.

See "Capability PR Workflow (Atomic PRs)" section below for detailed workflow.

---

## Pre-Implementation Validation

1. **Run prerequisite check**: `scripts/bash/check-implementation-prerequisites.sh --json` from repo root
   - Parse FEATURE_DIR, PLAN_PATH, TASKS_PATH, BRANCH
   - Verify plan.md and tasks.md exist
   - Check for constitutional compliance markers

2. **Load implementation context**:
   - **REQUIRED**: Read `memory/constitution.md` for constitutional requirements
   - **REQUIRED**: Read `tasks.md` for complete task list and execution order
   - **REQUIRED**: Read `plan.md` for tech stack, architecture, and validation gates
   - **IF EXISTS**: Read `data-model.md` for entities and relationships
   - **IF EXISTS**: Read `contracts/` for API specifications and contract tests
   - **IF EXISTS**: Read `research.md` for technical decisions and constraints
   - **IF EXISTS**: Read `quickstart.md` for integration test scenarios

3. **Parse task structure**:
   - Extract task phases: Setup, Tests, Core, Integration, Polish
   - Identify task dependencies and [P] parallel markers
   - Build execution graph respecting dependencies
   - Validate TDD ordering (tests before implementation)

## Phase 0: Setup & Initialization

### Constitutional Gate Check

**ULTRATHINK**: Before proceeding with implementation, deeply analyze:
- What are the fundamental constitutional violations that could derail this entire implementation?
- How do the architectural decisions in plan.md align with long-term system evolution?
- What are the testing strategy implications that could compromise the TDD approach?
- Which CLI interface decisions will affect user adoption and future feature development?
- What observability gaps could lead to production debugging nightmares?

- [ ] Library-first architecture confirmed in plan.md
- [ ] CLI interface design documented
- [ ] Test-first approach validated in tasks.md
- [ ] Observability requirements identified

### Project Setup Tasks
- Initialize project structure per plan.md
- Install dependencies and dev tools
- Configure linters, formatters, and git hooks
- Create base library structure with CLI scaffolding
- Run: `/validate plan` to ensure readiness

## Phase 1: Test-First Development (RED Phase)

### CRITICAL: Tests MUST be written, committed, and FAILING before ANY implementation

**Think hard**: Before writing tests, carefully consider:
- What are the most critical test scenarios that will validate the core business value?
- How can the test structure support parallel development while maintaining dependencies?
- Which test failures will provide the most informative feedback during development?
- What are the integration points that need the most comprehensive test coverage?

### Testing Standards Reference

**CRITICAL**: Follow `~/.claude/instructions/standards/python/testing.md` for all test code.

**Test Quality**: The `testing-quality-check` skill enforces context-sensitive quality standards (ratios, smells, refactoring patterns).

**5-Layer Testing Standard**:
- **Layer 1 (🔴 CI/CD)**: Pure pytest-style functions, 90% coverage, module mocking in conftest.py
- **Layer 2 (🔴 TDD)**: This workflow enforces WHEN (outside-in order), standards define HOW (test patterns)
- **Layer 3 (🟢 PRIMARY)**: pytest functions + fixtures + assert statements
- **Layer 3 (🟡 LEGACY)**: unittest.TestCase allowed for existing tests
- **Layer 4 (🔵)**: Organization (contract/, unit/, integration/, functional/), mocking patterns
- **Layer 5 (🟠)**: Advanced techniques (hypothesis, snapshot, benchmarks)

**Test Directory Structure** (from Layer 1):
```
tests/
├── contract/       # Contract tests (write first)
├── unit/           # Unit tests (write second)
├── integration/    # Integration tests (write third)
├── functional/     # Functional tests (write fourth)
└── conftest.py     # Module-level mocking, session fixtures
```

**Test Creation Order**:
1. **Contract Tests** [P] - One per API endpoint/contract → `tests/contract/`
   - Write pytest-style contract tests from contracts/*.md
   - Follow Layer 3 PRIMARY pattern (functions + fixtures + assert)
   - Tests must fail with import/module errors (implementation doesn't exist)

   **Example** (pytest-style):
   ```python
   # tests/contract/test_user_api.py
   import pytest

   @pytest.fixture
   def api_client():
       from src.app import app  # This import will FAIL initially
       return app.test_client()

   def test_create_user_contract(api_client):
       """Contract: POST /users returns 201 with user object"""
       response = api_client.post("/users", json={
           "email": "test@example.com",
           "name": "Test User"
       })

       assert response.status_code == 201
       assert "id" in response.json
   ```

   - Commit: `/smart-commit "test: add failing contract tests for [feature]"`

2. **Entity/Model Tests** [P] - One per data model entity → `tests/unit/test_models.py`
   - Write pytest-style unit tests for models
   - Test validation, business rules, constraints
   - Tests must fail (models don't exist yet)

   **Example** (pytest-style):
   ```python
   # tests/unit/test_user_model.py
   import pytest
   from src.models import User  # This import will FAIL initially

   def test_user_creation_with_valid_data():
       """Test creating user with valid email"""
       user = User(email="test@example.com", name="Test")

       assert user.email == "test@example.com"
       assert user.name == "Test"

   def test_user_creation_with_invalid_email():
       """Test user creation fails with invalid email"""
       with pytest.raises(ValueError, match="Invalid email"):
           User(email="invalid", name="Test")
   ```

   - Commit: `/smart-commit "test: add failing model tests"`

3. **Integration Tests** - Sequential by dependency → `tests/integration/`
   - Write pytest-style integration tests
   - Test component interactions, workflows from spec.md
   - Include error scenarios

   **Example** (pytest-style):
   ```python
   # tests/integration/test_user_workflow.py
   import pytest

   @pytest.fixture
   def test_db():
       """Test database with cleanup"""
       from src.database import create_test_db  # Will FAIL initially
       db = create_test_db()
       yield db
       db.cleanup()

   def test_create_and_retrieve_user(test_db):
       """Test complete user creation and retrieval flow"""
       from src.services.user_service import UserService  # Will FAIL

       service = UserService(db=test_db)
       user = service.create(email="test@example.com", name="Test")
       retrieved = service.get(user["id"])

       assert retrieved["email"] == "test@example.com"
   ```

   - Commit: `/smart-commit "test: add failing integration tests"`

**Validation Gate**:
```bash
# Verify all tests are failing appropriately
npm test || python -m pytest || go test ./...
# Expected: All tests should fail with implementation-not-found errors
```

## Phase 2: Core Implementation (GREEN Phase)

### Implementation Rules

**Think**: Before implementing each component, carefully consider:
- What is the minimal code needed to make the failing tests pass?
- How does this implementation align with existing codebase patterns?
- Are there any TDD violations (implementing features without failing tests)?

- Only write enough code to make tests pass
- No features without corresponding failing tests
- Follow patterns from ai_docs/ and existing code
- Respect [P] markers for parallel execution

**Execution Flow**:
1. **Models/Entities** [P] - Implement data structures
   - Create model files per data-model.md
   - Add validation logic
   - Run tests: expect some to pass
   - Commit: `/smart-commit "feat: implement [entity] models"`

2. **Core Services** - Sequential implementation
   - Implement business logic services
   - Add error handling and logging
   - Follow existing service patterns
   - Commit: `/smart-commit "feat: implement [service] logic"`

3. **API/CLI Endpoints** [P] - Implement interfaces
   - Create endpoint handlers
   - Wire up to services
   - Add input validation
   - Commit: `/smart-commit "feat: implement [endpoint] handlers"`

4. **Integration Layer** - Connect components
   - Wire up dependencies
   - Configure middleware
   - Set up database connections
   - Commit: `/smart-commit "feat: integrate [component] layers"`

**Validation Gate**:
```bash
# All existing tests should now pass
npm test || python -m pytest || go test ./...
/validate implementation
```

## Phase 3: Refactor & Polish (REFACTOR Phase)

### Code Quality Improvements

**Think hard**: Before refactoring, carefully consider:
- What are the patterns that emerged during implementation that could be abstracted?
- How can the code be made more maintainable without changing behavior?
- Which performance optimizations provide the most value with the least risk?
- What are the potential breaking changes that need to be avoided?

- [ ] Refactor for clarity without changing behavior
- [ ] Extract common patterns to utilities
- [ ] Optimize performance bottlenecks
- [ ] Improve error messages and logging
- [ ] Add comprehensive documentation

### Additional Testing
- [ ] Add edge case tests
- [ ] Include performance benchmarks
- [ ] Add property-based tests (if applicable)
- [ ] Verify test coverage metrics

### Final Validation
```bash
# Run full validation suite
/validate implementation --comprehensive
/validate repository
/review
```

## Phase 4: Documentation & Delivery

### Documentation Tasks
- [ ] Update README with usage examples
- [ ] Document API in OpenAPI/Swagger format
- [ ] Add inline code documentation
- [ ] Create architecture decision records (ADRs)
- [ ] Update CHANGELOG.md

### Smart Commit Integration
```bash
# Create comprehensive commit for the feature
/smart-commit "feat: complete implementation of [feature-name]

- Implemented [key components]
- Added comprehensive test coverage
- Follows constitutional principles
- Validates against all quality gates"
```

## Capability PR Workflow (Atomic PRs)

### If on capability branch (e.g., `username/jira-123.feature-cap-001`):

1. **Verify atomic scope**:
   - Run: `git diff main --stat` to confirm ~1000 LOC total (800-1200 acceptable)
   - Break down: Implementation LOC vs Test LOC (target ratio ≥0.8:1)
   - If Total <800 OR Total >1200 OR Test ratio <0.8:1: document justification in PR description

2. **Create PR to main**:
   ```bash
   gh pr create --base main --title "feat(cap-001): [capability description]" \
     --body "$(cat <<'EOF'
   ## Summary
   Implements Cap-001: [capability name] from [parent feature]

   - [Key component 1]
   - [Key component 2]
   - [Key component 3]

   ## LOC Impact
   - Implementation: XXX LOC (target 400-600)
   - Tests: XXX LOC (target 400-600, ratio ≥0.8:1)
   - Total: XXX LOC (target ~1000, acceptable 800-1200)

   ## Dependencies
   - Depends on: [cap-XXX if any]
   - Enables: [cap-YYY that depend on this]

   ## Test Coverage
   - Contract tests: ✓
   - Integration tests: ✓
   - All tests passing: ✓

   Part of parent feature: specs/[jira-123.feature-name]/
   EOF
   )"
   ```

3. **After PR approval and merge**:
   ```bash
   # Switch back to parent branch
   git checkout [username]/[jira-123.feature-name]

   # Pull latest main to sync merged changes
   git pull origin main

   # Optional: delete local capability branch
   git branch -d [username]/[jira-123.feature-name]-cap-001
   ```

4. **Repeat for next capability**:
   ```bash
   # Start next capability
   /plan --capability cap-002 "Next capability tech details"
   # Creates new branch: username/jira-123.feature-name-cap-002
   # Repeat implement → PR → merge cycle
   ```

### Benefits of Capability PR Workflow:
- **Fast reviews**: 800-1200 LOC reviewed in 1-2 days vs 2000+ LOC taking 7+ days
- **Parallel development**: Multiple team members work on different capabilities simultaneously
- **Early integration**: Merge to main quickly, catch integration issues early
- **Manageable TDD**: Test-first approach easier with smaller scope (impl + tests both bounded)
- **Clear ownership**: Each PR has focused scope and clear acceptance criteria
- **Bounded test growth**: Prevents test files from ballooning without limit

## Error Handling & Recovery

### On Test Failure (Phase 1)
- Expected behavior - tests should fail initially
- If tests pass without implementation, review test quality
- Ensure tests actually test business requirements

### On Implementation Failure (Phase 2)
- Run targeted validation: `/validate implementation [failing-component]`
- Check ai_docs/ for library-specific gotchas
- Review existing patterns for similar implementations
- Use `/debug` command if systematic issues persist

### On Validation Failure (Any Phase)
- Stop implementation immediately
- Run `/validate --verbose` for detailed diagnostics
- Address all critical issues before proceeding
- Document any constitutional exceptions needed

## Parallel Execution Support

Tasks marked [P] can be executed concurrently:
```bash
# Example parallel execution for test creation
parallel ::: \
  "create test-auth.py" \
  "create test-user.py" \
  "create test-permissions.py"
```

## Progress Tracking

Use TodoWrite tool throughout:
- Mark task as in_progress when starting
- Mark completed immediately upon finishing
- Update with blockers if encountered
- Add new tasks discovered during implementation

## Constitutional Enforcement

**NON-NEGOTIABLE Requirements**:
1. Tests MUST exist and fail before implementation
2. Features MUST be implemented as libraries
3. Libraries MUST expose CLI interfaces
4. All code MUST have structured logging
5. Git history MUST show tests before implementation

## Success Criteria

Implementation is complete when:
- [ ] All tasks from tasks.md are marked completed
- [ ] All tests pass (unit, integration, contract)
- [ ] `/validate implementation` passes all gates
- [ ] Code review complete with no blockers
- [ ] Documentation updated and accurate
- [ ] Smart commits document the journey
