# Feature Specification: Guard CLI Implementation

**Feature Branch**: `001-guard-cli`  
**Created**: 2025-10-19  
**Status**: Draft  
**Input**: User description: "Implement specify guard CLI command with extensible marketplace for AI-optimized guard types that generate opinionated boilerplate code"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Guard with Opinionated Boilerplate (Priority: P1)

AI agent needs to create a guard for validating a specific task (e.g., API endpoint testing). The agent executes `specify guard create --type api --name user-endpoints` and receives complete, working boilerplate code including test scaffolds, configuration files, Docker setup, and Makefile integration. The agent only needs to customize selectors and test data, not write test structure from scratch.

**Why this priority**: This is the core value proposition - guards must generate extensive boilerplate to be useful. Without this, guards are just empty wrappers.

**Independent Test**: Can be tested by running `specify guard create` and verifying that 200+ lines of opinionated code are generated, files are created in correct locations, and Makefile targets are added.

**Acceptance Scenarios**:

1. **Given** AI agent is implementing an API endpoint task, **When** agent executes `specify guard create --type api --name user-endpoints`, **Then** system generates guard ID (G001), creates test files with full boilerplate (pytest scaffolds, JSON schemas, fixtures), updates Makefile with test-guard-G001 target, and returns AI-readable next steps
2. **Given** guard G001 created for user-endpoints, **When** agent runs `specify guard run G001`, **Then** system executes Makefile target, runs pytest tests, and returns pass/fail with exit code 0 for success
3. **Given** guard boilerplate generated, **When** agent examines test files, **Then** files contain 200+ lines of opinionated code with best practices (proper assertions, fixtures, error handling, performance checks)

---

### User Story 2 - Discover Available Guard Types (Priority: P2)

AI agent needs to understand what guard types are available for different validation scenarios. Agent executes `specify guard types` and receives a categorized list of guard types (E2E, API, Database, Unit, Performance, Security, Lint, Schema) with descriptions, versions, and when to use each type.

**Why this priority**: Discovery is essential but happens before creation, so P2. Guards are useless if AI doesn't know what types exist.

**Independent Test**: Can be tested by running `specify guard types` and verifying formatted output shows categories, type names, versions, and descriptions.

**Acceptance Scenarios**:

1. **Given** AI agent planning validation strategy, **When** agent executes `specify guard types`, **Then** system displays categorized list of available guard types (docker-playwright, api, database, unit-pytest, unit-jest, integration, performance-locust, security-bandit, lint-ruff, schema-pydantic) with versions and AI-optimized usage hints
2. **Given** AI agent searching for specific validation type, **When** agent executes `specify guard types --filter e2e`, **Then** system returns only E2E testing guard types (docker-playwright, cypress)
3. **Given** new guard type installed, **When** agent executes `specify guard types`, **Then** output includes newly installed custom guard type

---

### User Story 3 - Execute Guard Validation (Priority: P1)

AI agent completes a task and needs to validate completion before marking task complete. Agent executes `specify guard run G001` and receives pass/fail result with detailed test output. On pass (exit 0), agent marks task complete. On fail (non-zero exit), agent investigates failures and fixes code.

**Why this priority**: Core guard execution is critical for the entire system. Without this, guards can't validate anything.

**Independent Test**: Can be tested by creating a guard, implementing code that should pass/fail, running guard, and verifying correct exit codes and output.

**Acceptance Scenarios**:

1. **Given** guard G001 exists for API endpoint, **When** agent executes `specify guard run G001` after implementing endpoint, **Then** system runs Makefile target test-guard-G001, executes tests, and returns exit code 0 with "✓ PASS: Guard G001 validation successful" plus test details
2. **Given** implementation has failing tests, **When** agent executes `specify guard run G001`, **Then** system returns exit code 1 with "✗ FAIL: Guard G001 validation failed" plus specific test failures and suggestions for fixes
3. **Given** guard execution times out after 5 minutes, **When** agent runs long-running guard, **Then** system returns exit code 2 with timeout error and partial results
4. **Given** task T012 has guard G003 registered, **When** agent executes `specify guard run --task T012`, **Then** system identifies guard G003 from tasks.md and executes it

---

### User Story 4 - List Guards for Current Feature (Priority: P3)

AI agent working on a feature needs to see what guards have been created for the current feature. Agent executes `specify guard list` and receives a table showing guard IDs, types, names, commands, and status.

**Why this priority**: Useful for tracking but not critical for MVP. Can manually track guards initially.

**Independent Test**: Can be tested by creating multiple guards, running `specify guard list`, and verifying output shows all guards with correct metadata.

**Acceptance Scenarios**:

1. **Given** feature has three guards (G001: docker-playwright/checkout, G002: api/users, G003: database/schema), **When** agent executes `specify guard list`, **Then** system displays table with guard IDs, types, names, execution commands, and creation timestamps
2. **Given** no guards created yet, **When** agent executes `specify guard list`, **Then** system displays message "No guards registered for feature 001-guard-cli"
3. **Given** guards registered in tasks.md, **When** agent executes `specify guard list`, **Then** output includes task IDs that reference each guard

---

### User Story 5 - Install Custom Guard Type (Priority: P4)

Organization needs to create and install a custom guard type encoding their specific testing best practices. Developer creates guard type package (manifest, scaffolder, templates, validator, docs, example), validates structure with `specify guard validate-type`, and installs with `specify guard install ./my-custom-guard/`.

**Why this priority**: Extensibility is important but not needed for initial MVP. Can be added once core guard types are proven.

**Independent Test**: Can be tested by creating a minimal guard type package, validating it, installing it, and using it to create a guard.

**Acceptance Scenarios**:

1. **Given** custom guard type package with valid structure, **When** developer executes `specify guard validate-type ./my-custom-guard/`, **Then** system validates manifest, scaffolder interface, template renderability, validator executability, and returns "Guard type ready for installation"
2. **Given** validated guard type, **When** developer executes `specify guard install ./my-custom-guard/`, **Then** system copies guard type to `.specify/guards/types/`, registers in types registry, and confirms "Installed: my-custom-guard@1.0.0"
3. **Given** custom guard type installed, **When** AI agent executes `specify guard create --type my-custom-guard --name validation`, **Then** system generates guard using custom type's scaffolder and templates

---

### Edge Cases

- What happens when guard execution fails due to missing dependencies (e.g., Docker not running)?
- How does system handle duplicate guard IDs if registry is corrupted?
- What happens when guard type scaffolder crashes during code generation?
- How does system handle Makefile updates when Makefile doesn't exist yet?
- What happens when guard is created but feature directory doesn't have required structure (tests/ directory)?
- How does system handle concurrent guard creation (race conditions in ID generation)?
- What happens when guard type template references variables that don't exist in context?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide `specify guard types` command that lists available guard types from marketplace with categories, versions, and descriptions
- **FR-002**: System MUST provide `specify guard create --type <type> --name <name>` command that generates sequential guard ID (G001, G002...) and creates opinionated boilerplate code (200+ lines typical)
- **FR-003**: System MUST provide `specify guard list` command that shows all guards registered for current feature with IDs, types, names, commands, and timestamps
- **FR-004**: System MUST provide `specify guard run <guard-id>` command that executes guard validation and returns exit code 0 for pass, non-zero for fail
- **FR-005**: System MUST provide `specify guard run --task <task-id>` command that identifies guard from tasks.md and executes it
- **FR-006**: System MUST provide `specify guard validate <guard-id>` command that validates guard configuration without executing tests
- **FR-007**: System MUST provide `specify guard install <path>` command that installs custom guard type from local directory or git repository
- **FR-008**: System MUST provide `specify guard validate-type <path>` command that validates guard type package structure
- **FR-009**: System MUST maintain guard registry in `.guards/registry.json` tracking all guards with metadata (ID, type, name, command, created timestamp, status)
- **FR-010**: System MUST generate guard IDs sequentially starting from G001 within each feature
- **FR-011**: Guard creation MUST generate complete boilerplate code including test files, configuration, Docker setup, and Makefile targets
- **FR-012**: Guard creation MUST update Makefile with new test-guard-{ID} target atomically (idempotent)
- **FR-013**: Guard creation MUST return AI-readable output including files created, command to execute, next steps, and customization instructions
- **FR-014**: Guard execution MUST run tests via Makefile target and capture stdout/stderr
- **FR-015**: Guard execution MUST return structured output (PASS/FAIL, test details, exit code, execution time)
- **FR-016**: Guard types MUST include at minimum: docker-playwright, api, database, unit-pytest, lint-ruff (5 core types for MVP)
- **FR-017**: Each guard type MUST include: manifest (guard-type.yaml), scaffolder (Python script), templates (Jinja2), validator (executable), documentation (Markdown), example (working code)
- **FR-018**: Guard type manifest MUST define: name, version, description, category, dependencies, compatibility, scaffolding spec, execution spec, AI hints
- **FR-019**: Guard type scaffolder MUST implement GuardScaffolder interface with scaffold() method returning file list and metadata
- **FR-020**: Guard type templates MUST use Jinja2 syntax and generate 200+ lines of opinionated code per guard
- **FR-021**: System MUST support filtering guard types by category with `specify guard types --filter <category>`
- **FR-022**: System MUST handle errors gracefully (missing dependencies, Docker not running, invalid guard ID, corrupted registry) with clear error messages
- **FR-023**: System MUST support guard execution timeout (default 300 seconds) with configurable override

### Key Entities

- **Guard**: Represents a specific validation checkpoint with ID (G001), type (docker-playwright), name (checkout-flow), command (make test-guard-G001), status, created timestamp
- **GuardType**: Represents a reusable guard template with name, version, category, scaffolder, templates, validator, manifest
- **GuardRegistry**: Central registry file (`.guards/registry.json`) tracking all guards for a feature
- **GuardTypeManifest**: Metadata file (guard-type.yaml) defining guard type specifications
- **GuardScaffolder**: Python class implementing code generation logic for a guard type
- **GuardValidator**: Executable that runs guard tests and returns pass/fail results

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI agent can create a guard and receive 200+ lines of working boilerplate code in under 5 seconds
- **SC-002**: Guard execution correctly identifies pass/fail with appropriate exit codes (0 = pass, non-zero = fail) 100% of the time
- **SC-003**: Guard types can be listed with categories and descriptions in under 1 second
- **SC-004**: Custom guard types can be installed and immediately used to create guards without errors
- **SC-005**: Guards created in one feature do not conflict with guards in other features (ID namespacing works)
- **SC-006**: Makefile updates are atomic and idempotent (re-running guard create doesn't corrupt Makefile)
- **SC-007**: Guard execution timeout prevents runaway tests (tests terminated after 5 minutes by default)
- **SC-008**: At least 5 core guard types implemented (docker-playwright, api, database, unit-pytest, lint-ruff) and functional

### Quality Gates *(defined by constitution)*

The following quality gates MUST pass before this feature is considered complete:

**Testing Requirements**:
- [ ] Unit tests passing (coverage ≥ 80% for guard CLI commands)
- [ ] Integration tests passing (end-to-end guard creation → execution → validation)
- [ ] End-to-end/acceptance tests passing for all user stories
- [ ] Performance tests passing (guard creation < 5s, execution respects timeout)

**Implementation Requirements**:
- [ ] All functional requirements (FR-001 through FR-023) implemented
- [ ] All acceptance scenarios passing
- [ ] Docker containerized testing environment functional
- [ ] Makefile testing targets operational (`make test`, `make test-unit`, `make test-integration`)

**Documentation Requirements**:
- [ ] README updated with guard CLI examples
- [ ] API documentation updated for guard commands
- [ ] Guard type specification document created (for extensibility)
- [ ] quickstart.md includes guard usage examples

**Code Quality**:
- [ ] Linting passing (`make lint` using ruff)
- [ ] Type checking passing (mypy for Python code)
- [ ] Code formatting applied (`make format` using ruff)
- [ ] Security scans passing (no vulnerabilities in dependencies)

## Assumptions

- Python 3.11+ is available (specified in pyproject.toml)
- uv package manager is available (used by Spec Kit)
- Docker is available for containerized guards (docker-playwright requires Docker)
- Makefile is supported on target platforms (Linux, macOS, Windows with Make)
- Git repository context is available (guard IDs scoped to feature branches)
- Jinja2 templating engine is acceptable for code generation
- YAML format is acceptable for guard type manifests
- JSON format is acceptable for guard registry storage
- Guard types stored in `.specify/guards/types/` directory
- Guard registry stored in `.guards/registry.json` per feature
- Guard metadata stored in `.guards/{guard-id}-metadata.json` per guard
