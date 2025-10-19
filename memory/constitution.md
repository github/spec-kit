<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.1.0
Modified principles: None
Added sections:
  - Principle V: Guard-Driven Task Validation
  - Guard System section
  - CLI Extension: specify guard command
Added date: 2025-10-18

Previous version (1.0.0):
  - Principle I: Specification-Driven Development
  - Principle II: Makefile-Driven Testing Boundaries
  - Principle III: Test Diversity & Formal Completion
  - Principle IV: Docker-Based Repeatability
  - Testing Standards section
  - Quality Gates section

Templates requiring updates:
  ✅ templates/plan-template.md - Add guard generation to Constitution Check
  ✅ templates/tasks-template.md - Add guard IDs to task format, guard execution in phases
  ⚠ templates/commands/plan.md - Add guard generation step
  ⚠ templates/commands/tasks.md - Add guard registration step
  ⚠ templates/commands/implement.md - Add guard validation checks
  ⚠ src/specify_cli/__init__.py - Implement `specify guard` command

Follow-up TODOs:
  - Implement `specify guard` CLI command with guard types (docker-playwright, api, database, etc.)
  - Create guard template files for common guard types
  - Add guard execution to /speckit.implement workflow
  - Document guard system in docs/
  - Add examples to quickstart.md
-->

# Spec Kit Constitution

## Core Principles

### I. Specification-Driven Development

Every feature MUST begin with a clear, testable specification before any implementation work begins. Specifications define the "what" and "why" before technical planning addresses the "how".

**Non-negotiable rules:**
- Feature work MUST NOT start without a completed spec.md in the feature directory
- Specifications MUST include user stories with independent test criteria
- Specifications MUST define measurable success criteria
- Technical implementation plans MUST reference and align with the specification

**Rationale**: Specifications serve as the contract between intent and implementation. Starting with clear specifications reduces rework, ensures alignment with user needs, and provides a verification baseline for implementation correctness.

### II. Makefile-Driven Testing Boundaries

All testing workflows MUST be orchestrated through Makefiles to create hard, repeatable boundaries around the technology stack. Makefiles serve as the single interface for all quality assurance activities.

**Non-negotiable rules:**
- Every project MUST have a Makefile with standardized testing targets
- Testing commands MUST NOT require direct knowledge of underlying tools
- Makefile targets MUST encapsulate environment setup, execution, and teardown
- Standard targets MUST include: `make test`, `make test-unit`, `make test-integration`, `make test-performance`, `make test-e2e`
- CI/CD pipelines MUST invoke testing exclusively through Makefile targets
- Makefile MUST support `make help` to document all available targets

**Rationale**: Makefiles provide technology-agnostic abstraction over diverse testing tools. This creates consistent testing interfaces across projects, simplifies onboarding, enables tool migrations without workflow changes, and ensures testing procedures are documented as executable code.

### III. Test Diversity & Formal Completion

Features MUST demonstrate quality through multiple testing strategies, each addressing different quality dimensions. Completion is defined by passing formal quality gates, not just implementation delivery.

**Non-negotiable rules:**
- Features MUST include at minimum: unit tests, integration tests, and acceptance tests
- Performance-critical features MUST include performance tests with documented baseline metrics
- User-facing features MUST include end-to-end tests (e.g., Playwright, Selenium)
- Analysis functions in specifications MUST pass automated validation checks
- Test coverage MUST meet project-specific thresholds (documented in plan.md)
- All quality gate tests MUST be automated and executable via Makefile
- Features are NOT considered complete until all quality gates pass

**Formal completion requirements:**
- All tests passing (unit, integration, e2e, performance as applicable)
- Code coverage meets threshold
- Performance metrics meet baseline
- Security scans pass (if applicable)
- Documentation updated
- Acceptance criteria from spec.md verified

**Rationale**: Different testing strategies catch different classes of defects. Unit tests verify component correctness, integration tests verify component interactions, e2e tests verify user workflows, and performance tests verify non-functional requirements. Formal completion criteria prevent premature closure and ensure consistent quality standards.

### IV. Docker-Based Repeatability

All testing environments MUST be reproducible through Docker containerization to ensure consistency across development, CI, and production contexts.

**Non-negotiable rules:**
- Testing MUST execute within Docker containers (local and CI)
- Makefile test targets MUST handle container lifecycle (build, run, cleanup)
- Container images MUST pin all dependency versions
- Test data MUST be containerized or generated deterministically
- No "works on my machine" exceptions - container environment is ground truth
- Container configurations MUST be versioned alongside code

**Rationale**: Docker containers eliminate environment drift, ensure reproducible test results, simplify CI/CD configuration, and provide production-like testing environments. Containerization makes it impossible for tests to depend on undocumented local state.

### V. Guard-Driven Task Validation

Every task MUST have an executable guard—a CLI-invocable test that provides non-negotiable, automated validation of task completion. Guards are physical checkpoints that prevent AI agents from marking tasks complete without objective verification.

**Non-negotiable rules:**
- Tasks MUST NOT be marked complete without a passing guard
- Guards MUST be CLI commands executable without human interpretation
- Guards MUST be deterministic (same input → same pass/fail result)
- Guards MUST be generated during planning phase via `specify guard` command
- Guard IDs MUST be registered alongside tasks in tasks.md
- AI agents MUST execute guards before marking tasks complete
- Guard failures MUST halt task progression until resolved

**Guard types** (non-exhaustive, extensible):
- `docker-playwright`: Browser automation tests in containerized environment
- `api`: API contract and integration tests
- `database`: Database schema, query, and data validation tests
- `unit`: Unit test suites for specific components
- `integration`: Cross-component integration tests
- `performance`: Performance benchmark validation
- `security`: Security scan and vulnerability checks
- `lint`: Code quality and style enforcement
- `schema`: Data schema validation (database, API, config)

**Guard lifecycle:**
1. **Generation** (`/speckit.plan`): Planner identifies checkpoints → generates guards via `specify guard command=<type>`
2. **Registration** (`/speckit.tasks`): Tasks.md includes guard IDs alongside task descriptions
3. **Execution** (`/speckit.implement`): AI executes guard before marking task complete
4. **Validation**: Guard pass/fail determines task completion status

**Guard structure** (CLI output):
```bash
$ specify guard run <guard-id>
✓ PASS: Guard <guard-id> validation successful
  - Test 1: API endpoint returns 200 OK
  - Test 2: Response schema matches contract
  - Test 3: Response time < 200ms
  
$ echo $?
0  # Exit code 0 = pass, non-zero = fail
```

**Rationale**: Guards eliminate subjective completion criteria and "looks good to me" validation. By encoding validation as executable CLI commands, guards provide objective, repeatable checkpoints that AI agents must satisfy. This creates strong incentives for AI agents to generate robust implementations that pass hard tests, not just syntactically valid code. Guards bridge the gap between specification intent and implementation verification.

## Testing Standards

### Testing Strategy Requirements

Projects MUST document their testing strategy in plan.md including:
- Testing approach for each quality dimension (unit, integration, e2e, performance)
- Tools selected for each testing layer
- Coverage thresholds and measurement approach
- Performance baselines and acceptable ranges
- Test data strategy (fixtures, factories, seeding)

### Makefile Testing Targets (Standard Interface)

```makefile
# Required targets
help:           # Display this help message
test:           # Run all tests (unit + integration + e2e)
test-unit:      # Run unit tests only
test-integration: # Run integration tests only
test-e2e:       # Run end-to-end tests
test-performance: # Run performance tests
lint:           # Run code quality checks
format:         # Format code according to standards
coverage:       # Generate test coverage report
clean:          # Clean test artifacts and containers

# Optional but recommended
test-watch:     # Run tests in watch mode for development
test-debug:     # Run tests with debugger enabled
test-specific:  # Run specific test file or pattern (usage: make test-specific TEST=path)
docker-build:   # Build test Docker images
docker-clean:   # Remove test containers and images
```

### Performance Testing Requirements

Features identified as performance-critical MUST include:
- Baseline performance metrics (response time, throughput, resource usage)
- Automated performance test suite
- Performance regression detection in CI
- Performance results documented in feature spec or quickstart.md

## Guard System

### Guard Command Specification

The `specify guard` CLI command manages guard creation, registration, and execution through an extensible marketplace of highly opinionated guard types:

```bash
# List available guard types from marketplace
specify guard types [--filter <category>]

# Create a new guard (returns full boilerplate scaffolding)
specify guard create --type <guard-type> --name <guard-name> [--feature <feature-id>]

# List guards for current feature
specify guard list [--feature <feature-id>]

# Execute a specific guard
specify guard run <guard-id>

# Execute all guards for a task
specify guard run --task <task-id>

# Validate guard configuration
specify guard validate <guard-id>

# Install a guard type from marketplace
specify guard install <guard-type-package>

# Publish a custom guard type to marketplace (future)
specify guard publish <guard-definition-path>
```

**Guard creation returns**:
- Guard ID (unique identifier, e.g., `G001`, `G002`)
- Guard type and version
- Full boilerplate code scaffold (test files, config, Docker setup, Makefile targets)
- CLI command to execute the guard
- Setup instructions for repository integration
- Expected output format
- Pass/fail exit code convention

**Design Philosophy - AI-Optimized Guards**:
- Guards are ONLY used by AI agents, NOT humans
- Extreme opinions encouraged (best practices encoded)
- Full boilerplate generation (zero manual setup)
- Deterministic structure (same guard type → identical layout)
- Self-contained validation (guard includes all dependencies)
- Progressive enhancement (marketplace evolves with best practices)

### Guard Marketplace & Opinionated Types

The guard marketplace provides extensible, highly opinionated guard types optimized for AI agent consumption. Each guard type delivers complete boilerplate scaffolding with zero manual configuration required.

**Core Design Principles**:
1. **Full Scaffolding**: Guard creation returns complete, runnable code (tests, configs, Docker, Makefile)
2. **Extreme Opinions**: Each guard type encodes industry best practices (AI doesn't need flexibility, needs correctness)
3. **Zero Setup**: Guard setup is automated (dependencies installed, configs written, paths created)
4. **Deterministic Structure**: Same guard type always generates identical directory structure
5. **Extensible Marketplace**: Community can contribute guard types following standardized interfaces

**Guard Type Anatomy**:

Each marketplace guard type MUST provide:
- **Manifest** (`guard-type.yaml`): Metadata, version, dependencies, compatibility
- **Scaffolder** (Python/shell script): Code generation logic
- **Templates** (Jinja2): Boilerplate code templates (tests, configs, Docker)
- **Validator** (executable): Guard execution and result interpretation
- **Documentation** (Markdown): AI-readable setup and usage instructions
- **Example** (working code): Reference implementation

**Example: docker-playwright Guard Type**

```bash
$ specify guard create --type docker-playwright --name "checkout-flow"

✓ Installing guard type: docker-playwright@1.2.0
  - Pulling Docker image: speckit/guard-playwright:1.2.0
  - Creating directory: tests/e2e/
  - Generating boilerplate...

✓ Created Guard G001: docker-playwright/checkout-flow

Files created:
  tests/e2e/checkout.spec.ts          # Playwright test scaffold
  tests/e2e/playwright.config.ts      # Playwright configuration
  tests/e2e/docker-compose.yml        # Test environment
  .guards/G001-metadata.json          # Guard execution metadata
  Makefile (updated)                  # Added test-guard-G001 target

Makefile target added:
  test-guard-G001:
    docker-compose -f tests/e2e/docker-compose.yml up -d
    docker run --rm --network=host \
      -v $(PWD)/tests/e2e:/tests \
      speckit/guard-playwright:1.2.0 \
      npx playwright test checkout.spec.ts
    docker-compose -f tests/e2e/docker-compose.yml down

Execute with:
  $ make test-guard-G001
  OR
  $ specify guard run G001

Next steps:
  1. Review generated test: tests/e2e/checkout.spec.ts
  2. Customize test scenarios for your checkout flow
  3. Run guard: specify guard run G001
```

**Boilerplate Generated** (checkout.spec.ts):

```typescript
// tests/e2e/checkout.spec.ts
// Generated by specify guard docker-playwright@1.2.0
// Guard ID: G001
// Target: checkout-flow validation

import { test, expect } from '@playwright/test';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to checkout page
    await page.goto('http://localhost:3000/checkout');
  });

  test('checkout button is visible', async ({ page }) => {
    const checkoutBtn = page.locator('[data-testid="checkout-button"]');
    await expect(checkoutBtn).toBeVisible();
  });

  test('payment form renders correctly', async ({ page }) => {
    const paymentForm = page.locator('form[name="payment"]');
    await expect(paymentForm).toBeVisible();
    
    // Verify required fields present
    await expect(page.locator('input[name="cardNumber"]')).toBeVisible();
    await expect(page.locator('input[name="expiryDate"]')).toBeVisible();
    await expect(page.locator('input[name="cvv"]')).toBeVisible();
  });

  test('order confirmation appears after valid submission', async ({ page }) => {
    // Fill payment details
    await page.fill('input[name="cardNumber"]', '4242424242424242');
    await page.fill('input[name="expiryDate"]', '12/25');
    await page.fill('input[name="cvv"]', '123');
    
    // Submit
    await page.click('[data-testid="submit-payment"]');
    
    // Verify confirmation
    await expect(page.locator('[data-testid="order-confirmation"]'))
      .toBeVisible({ timeout: 5000 });
  });

  test('validates required fields', async ({ page }) => {
    // Attempt submission with empty form
    await page.click('[data-testid="submit-payment"]');
    
    // Expect validation errors
    await expect(page.locator('.error-cardNumber')).toBeVisible();
  });

  test('performance: checkout completes in under 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    
    // Complete checkout flow
    await page.fill('input[name="cardNumber"]', '4242424242424242');
    await page.fill('input[name="expiryDate"]', '12/25');
    await page.fill('input[name="cvv"]', '123');
    await page.click('[data-testid="submit-payment"]');
    await page.waitForSelector('[data-testid="order-confirmation"]');
    
    const duration = Date.now() - startTime;
    expect(duration).toBeLessThan(3000);
  });
});
```

**Example: api Guard Type**

```bash
$ specify guard create --type api --name "user-endpoints"

✓ Installing guard type: api@2.0.1
  - Installing dependencies: pytest, requests, jsonschema
  - Creating directory: tests/api/guards/
  - Generating boilerplate...

✓ Created Guard G002: api/user-endpoints

Files created:
  tests/api/guards/G002_user_endpoints.py       # API test suite
  tests/api/guards/G002_schemas.json            # JSON schemas
  tests/api/conftest.py                         # pytest fixtures
  tests/api/docker-compose.yml                  # API test environment
  .guards/G002-metadata.json                    # Guard metadata
  Makefile (updated)                            # Added test-guard-G002 target

Execute with:
  $ make test-guard-G002
  OR
  $ specify guard run G002
```

**Boilerplate Generated** (G002_user_endpoints.py):

```python
# tests/api/guards/G002_user_endpoints.py
# Generated by specify guard api@2.0.1
# Guard ID: G002
# Target: user-endpoints contract validation

import pytest
import requests
from jsonschema import validate
import json

BASE_URL = "http://localhost:8000"  # Auto-detected from quickstart.md

# Load JSON schemas
with open('tests/api/guards/G002_schemas.json') as f:
    SCHEMAS = json.load(f)

@pytest.fixture
def api_client():
    """Fixture providing configured API client"""
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})
    return session

class TestUserEndpoints:
    """Contract tests for User API endpoints"""
    
    def test_get_users_returns_200(self, api_client):
        """GET /api/users returns 200 OK"""
        response = api_client.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
    
    def test_get_users_response_schema(self, api_client):
        """GET /api/users response matches schema"""
        response = api_client.get(f"{BASE_URL}/api/users")
        validate(instance=response.json(), schema=SCHEMAS['users_list'])
    
    def test_post_user_creates_resource(self, api_client):
        """POST /api/users creates new user"""
        payload = {
            "email": "test@example.com",
            "name": "Test User"
        }
        response = api_client.post(f"{BASE_URL}/api/users", json=payload)
        assert response.status_code == 201
        assert 'id' in response.json()
    
    def test_post_user_response_schema(self, api_client):
        """POST /api/users response matches schema"""
        payload = {"email": "test@example.com", "name": "Test User"}
        response = api_client.post(f"{BASE_URL}/api/users", json=payload)
        validate(instance=response.json(), schema=SCHEMAS['user_detail'])
    
    def test_get_user_by_id(self, api_client):
        """GET /api/users/{id} returns user details"""
        # Create user first
        create_resp = api_client.post(
            f"{BASE_URL}/api/users",
            json={"email": "test@example.com", "name": "Test"}
        )
        user_id = create_resp.json()['id']
        
        # Fetch by ID
        response = api_client.get(f"{BASE_URL}/api/users/{user_id}")
        assert response.status_code == 200
        assert response.json()['id'] == user_id
    
    def test_post_user_validates_email(self, api_client):
        """POST /api/users validates email format"""
        payload = {"email": "invalid-email", "name": "Test"}
        response = api_client.post(f"{BASE_URL}/api/users", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_response_time_under_200ms(self, api_client):
        """API responses complete in under 200ms"""
        import time
        start = time.time()
        response = api_client.get(f"{BASE_URL}/api/users")
        duration = (time.time() - start) * 1000
        assert duration < 200, f"Response took {duration}ms"
```

**Marketplace Guard Types** (initial set):

| Guard Type | Version | Purpose | Scaffolding Includes |
|------------|---------|---------|----------------------|
| `docker-playwright` | 1.2.0 | Browser E2E testing | Playwright config, test scaffolds, Docker Compose, page objects |
| `api` | 2.0.1 | REST API contract tests | pytest suite, JSON schemas, fixtures, mock server |
| `database` | 1.5.0 | Schema & migration validation | SQL validators, migration tests, seed data, schema diffs |
| `unit-pytest` | 3.0.0 | Python unit tests | pytest structure, fixtures, mocks, coverage config |
| `unit-jest` | 2.1.0 | JavaScript unit tests | Jest config, test utils, mocks, coverage setup |
| `integration` | 1.3.0 | Service integration tests | Testcontainers setup, service mocks, integration fixtures |
| `performance-locust` | 1.0.2 | Load testing | Locust scripts, performance scenarios, reporting |
| `security-bandit` | 1.1.0 | Python security scanning | Bandit config, vulnerability checks, SAST rules |
| `lint-ruff` | 2.0.0 | Python linting | Ruff config, formatting rules, pre-commit hooks |
| `schema-pydantic` | 1.4.0 | Data model validation | Pydantic models, validation tests, serialization checks |

### Guard Registration in tasks.md

Tasks reference their guards using the guard ID:

```markdown
- [ ] T012 [P] [US1] Create User model in src/models/user.py [G003: database/user-schema]
- [ ] T015 [US1] Implement POST /api/users endpoint in src/api/users.py [G002: api/user-endpoints]
- [ ] T020 [US2] Implement checkout flow in frontend [G001: docker-playwright/checkout-flow]
```

Format: `[G###: <guard-type>/<guard-name>]`

### Guard Execution During Implementation

The `/speckit.implement` command enforces guard validation:

1. **Before task execution**: Verify guard exists and is executable
2. **After task implementation**: Execute guard automatically
3. **On guard failure**: 
   - Report failure details (which tests failed, why)
   - DO NOT mark task as complete
   - Provide guard output for debugging
   - Suggest fixes based on failure type
4. **On guard pass**: Mark task as complete, proceed to next task

### Extending the Guard Marketplace

**Creating Custom Guard Types**:

Organizations can create custom guard types following the standardized guard type specification:

**Guard Type Structure**:
```
my-custom-guard/
├── guard-type.yaml              # Manifest (metadata, version, dependencies)
├── scaffolder.py                # Code generation logic
├── templates/                   # Jinja2 templates for boilerplate
│   ├── test_template.py.j2
│   ├── config_template.yaml.j2
│   └── docker_template.yml.j2
├── validator.py                 # Guard execution & result parsing
├── README.md                    # AI-optimized documentation
└── example/                     # Reference implementation
    ├── sample_test.py
    └── expected_output.json
```

**Guard Type Manifest** (guard-type.yaml):
```yaml
name: my-custom-guard
version: 1.0.0
description: |
  Highly opinionated guard for [specific validation purpose].
  Optimized for AI agent consumption.
category: [unit|integration|e2e|performance|security|schema|lint]
author: Your Org
license: MIT

dependencies:
  runtime:
    - docker: ">=20.10"
    - make: ">=4.0"
  language:
    python: ">=3.11"
  packages:
    - pytest>=7.0
    - custom-validator>=2.0

compatibility:
  languages: [python, javascript, go]
  frameworks: [fastapi, flask, express]
  
scaffolding:
  creates:
    - tests/custom/guards/{guard_id}_{name}.py
    - tests/custom/conftest.py
    - tests/custom/docker-compose.yml
  updates:
    - Makefile
    - .gitignore
    
execution:
  command: "make test-guard-{guard_id}"
  timeout: 300
  exit_codes:
    success: 0
    failure: 1
    error: 2

ai_hints:
  when_to_use: |
    Use this guard when validating [specific scenario].
    Best for: [use cases]
    Not suitable for: [anti-patterns]
  
  boilerplate_explanation: |
    This guard generates opinionated boilerplate that:
    - [Benefit 1]
    - [Benefit 2]
    - Assumes: [Assumptions]
```

**Scaffolder Implementation** (scaffolder.py):
```python
# scaffolder.py - Guard type code generator
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml

class GuardScaffolder:
    def __init__(self, guard_id: str, name: str, feature_dir: Path):
        self.guard_id = guard_id
        self.name = name
        self.feature_dir = feature_dir
        self.env = Environment(loader=FileSystemLoader('templates'))
    
    def scaffold(self) -> dict:
        """Generate boilerplate code for this guard"""
        created_files = []
        
        # Create test directory
        test_dir = self.feature_dir / 'tests' / 'custom' / 'guards'
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Render test template
        test_template = self.env.get_template('test_template.py.j2')
        test_content = test_template.render(
            guard_id=self.guard_id,
            name=self.name,
            # AI-optimized: Include extensive scaffolding
            test_cases=self._generate_test_cases(),
            fixtures=self._generate_fixtures(),
            assertions=self._generate_assertions()
        )
        
        test_file = test_dir / f"{self.guard_id}_{self.name}.py"
        test_file.write_text(test_content)
        created_files.append(test_file)
        
        # Generate config files (Docker, pytest, etc.)
        # ... (additional scaffolding)
        
        # Update Makefile
        self._update_makefile()
        
        return {
            'guard_id': self.guard_id,
            'files_created': created_files,
            'command': f'make test-guard-{self.guard_id}',
            'next_steps': self._generate_next_steps()
        }
    
    def _generate_test_cases(self) -> list:
        """AI-optimized: Generate opinionated test case scaffolding"""
        # Return extensive boilerplate test cases
        # encoding best practices for this guard type
        pass
    
    def _update_makefile(self):
        """Atomically add guard target to Makefile"""
        # Idempotent Makefile update
        pass
```

**Installing Custom Guard Types**:

```bash
# From local directory
$ specify guard install ./my-custom-guard/

# From git repository
$ specify guard install git+https://github.com/org/my-guard-type.git

# From guard marketplace (future)
$ specify guard install marketplace://org/my-guard-type@1.0.0
```

**Guard Type Validation**:
```bash
# Validate guard type structure
$ specify guard validate-type ./my-custom-guard/

✓ Manifest valid (guard-type.yaml)
✓ Scaffolder implements required interface
✓ Templates render correctly
✓ Validator executable
✓ Documentation AI-optimized
✓ Example reference implementation works

Guard type ready for installation!
```

### Guard Best Practices

**Guard naming conventions**:
- Use kebab-case: `user-authentication`, `checkout-flow`
- Be specific: `post-user-endpoint` not `user-api`
- Reference component: `user-service-unit-tests`

**Guard scope**:
- One guard per logical validation unit
- Guards should be independent (no inter-guard dependencies)
- Guards test task completion, not entire features
- Multiple tasks can share a guard if validating same capability

**Guard maintenance**:
- Guards versioned with code
- Guard updates require constitution approval (guards are contracts)
- Failed guards must be fixed, not deleted
- Guard refactoring follows same rigor as code refactoring

**Guard Type Philosophy**:
- **Extreme opinions encouraged**: Encode industry best practices, don't provide options
- **Full boilerplate always**: AI shouldn't make choices, should get working code
- **Deterministic output**: Same inputs → identical scaffolding every time
- **AI-optimized docs**: Documentation written for AI comprehension, not human reading
- **Progressive enhancement**: Marketplace evolves as best practices improve

## Quality Gates

### Pre-Implementation Gates

Before `/speckit.implement` execution:
- [ ] Specification (spec.md) complete with user stories and acceptance criteria
- [ ] Technical plan (plan.md) complete with testing strategy documented
- [ ] Guards generated for all validation checkpoints
- [ ] Task breakdown (tasks.md) includes guard IDs for all tasks
- [ ] Checklists (if used) reviewed and acceptance criteria clear
- [ ] All guards executable and validated via `specify guard validate`

### Implementation Gates

During `/speckit.implement` execution:
- [ ] Guards executed BEFORE marking tasks complete
- [ ] All guards passing before moving to next task
- [ ] Guard failures investigated and resolved
- [ ] Tests written BEFORE implementation for each component (TDD)
- [ ] All tests passing before moving to next task
- [ ] Code coverage meeting threshold at each checkpoint
- [ ] Makefile targets functional and documented

### Completion Gates

Before feature considered complete:
- [ ] All task guards passing
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All e2e/acceptance tests passing
- [ ] Performance tests passing (if applicable)
- [ ] Code coverage ≥ threshold (defined in plan.md)
- [ ] All linting/formatting checks passing
- [ ] Documentation updated (README, quickstart.md, API docs)
- [ ] Specification acceptance criteria verified
- [ ] Docker containers building and tests passing in containerized environment
- [ ] Guard audit: `specify guard run --all` passes with zero failures

## Governance

### Amendment Process

This constitution MUST be versioned and tracked in `.specify/memory/constitution.md`. Amendments follow semantic versioning:

- **MAJOR** (X.0.0): Backward-incompatible changes to governance or principle removals/redefinitions
- **MINOR** (0.X.0): New principles added or materially expanded guidance
- **PATCH** (0.0.X): Clarifications, wording improvements, typo fixes

All amendments MUST:
1. Update the constitution version number
2. Update LAST_AMENDED_DATE to current date
3. Add Sync Impact Report as HTML comment documenting changes
4. Propagate changes to dependent templates (plan-template.md, spec-template.md, tasks-template.md)
5. Update command files if workflow changes

### Compliance Review

All feature work MUST demonstrate constitutional compliance:

- Specifications MUST be reviewed against Specification-Driven Development principle
- Implementation plans MUST document testing strategy per Test Diversity principle
- Task breakdowns MUST include Makefile setup and Docker configuration tasks
- Implementation MUST NOT proceed if quality gates are undefined or incomplete
- Pull requests MUST verify all quality gates passed before merge

### Violations & Justification

Deviations from constitutional principles MUST be:
1. Documented in plan.md Complexity Tracking section
2. Justified with clear rationale for why principle cannot be followed
3. Approved by project maintainer or technical lead
4. Time-boxed with plan to return to compliance

No violations are permitted for:
- Specification-Driven Development (Principle I)
- Formal Completion Requirements (Principle III gates)
- Guard-Driven Task Validation (Principle V) - tasks without guards cannot be marked complete

### Runtime Guidance

For AI agent-specific guidance on applying these principles during development, agents should reference agent-specific guidance files (e.g., `CLAUDE.md`, `.github/copilot-instructions.md`) as those files are updated to align with constitutional principles.

**Version**: 1.1.0 | **Ratified**: 2025-10-18 | **Last Amended**: 2025-10-18
