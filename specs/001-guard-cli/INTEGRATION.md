# Guard CLI Integration Guide

## Overview

This document explains how guards integrate into the Spec-Driven Development workflow and provides practical examples of guard usage throughout the feature lifecycle.

## Integration Points

### 1. Constitution (Principle V) ✅ COMPLETE

**Location**: `memory/constitution.md`

Guards are established as **Principle V: Guard-Driven Task Validation** with the following requirements:

- Tasks MUST NOT be marked complete without a passing guard
- Guards MUST be CLI commands executable without human interpretation
- Guards MUST be generated during planning phase
- Guard IDs MUST be registered alongside tasks
- AI agents MUST execute guards before marking tasks complete

**Status**: ✓ Constitution updated, principle active

### 2. Guard CLI Implementation ✅ COMPLETE

**Location**: `src/specify_cli/guards/`

Fully functional guard system with:
- 5 core guard types (unit-pytest, api, database, lint-ruff, docker-playwright)
- 4 commands (create, run, list, types)
- Registry system with atomic file locking
- 18 passing unit tests

**Usage**:
```bash
# Discover available guard types
specify guard types

# Create a guard
specify guard create --type unit-pytest --name my-feature

# List all guards
specify guard list

# Execute a guard
specify guard run G001
```

### 3. Workflow Integration ⚠️ PARTIAL

Currently guards are **manually invoked**. To make guards a natural part of the workflow, we need to update:

#### A. `/tasks` Command Template

**File**: `templates/commands/tasks.md`

**Current State**: Tasks are generated without guard IDs

**Proposed Enhancement**: Add guard creation step to task generation:

```markdown
## Step 4.5: Generate Guards for Critical Tasks

For each user story, identify critical validation checkpoints and create guards:

1. Scan tasks for validation opportunities:
   - API endpoints → api guard type
   - Database migrations → database guard type
   - UI workflows → docker-playwright guard type
   - Business logic → unit-pytest guard type
   - Code quality → lint-ruff guard type

2. Generate guards using `specify guard create`:
   ```bash
   specify guard create --type api --name user-authentication
   specify guard create --type unit-pytest --name payment-processing
   ```

3. Register guard IDs in tasks.md:
   ```markdown
   - [ ] T012 [US1] Implement user authentication API [Guard: G001]
   - [ ] T015 [US1] Implement payment processing logic [Guard: G002]
   ```
```

#### B. `/implement` Command Template

**File**: `templates/commands/implement.md`

**Current State**: Tasks marked complete based on implementation only

**Proposed Enhancement**: Add guard validation before task completion:

```markdown
## Step 8.5: Guard Validation (Before Marking Task Complete)

Before marking any task as [X] completed:

1. Check if task has an associated guard:
   - Parse task description for `[Guard: G###]` marker
   - If no guard found, proceed with normal completion
   - If guard found, execute guard validation

2. Execute guard:
   ```bash
   specify guard run G###
   ```

3. Interpret results:
   - Exit code 0 → Mark task [X] as complete
   - Exit code non-zero → Do NOT mark task complete
   - Report guard failure to user
   - Suggest fixes based on guard output

4. Update tasks.md with guard execution metadata (optional):
   ```markdown
   - [X] T012 [US1] Implement user authentication API [Guard: G001 ✓]
   ```
```

#### C. `/plan` Command Template

**File**: `templates/commands/plan.md`

**Proposed Enhancement**: Add guard planning to constitution check:

```markdown
## Constitutional Principle V: Guard-Driven Task Validation

- [ ] Critical validation checkpoints identified in specification
- [ ] Guard types selected for each checkpoint:
  - API contracts → api guard type
  - UI workflows → docker-playwright guard type
  - Database schema → database guard type
  - Code quality → lint-ruff guard type
  - Business logic → unit-pytest guard type
- [ ] Guard generation plan documented
- [ ] Guard execution integrated into implementation workflow
```

## Practical Workflow Examples

### Example 1: Feature with API Guards

**Scenario**: Implementing a user authentication feature

1. **Planning** (`/plan`):
   ```markdown
   Guards identified:
   - G001: API contract test for /auth/login endpoint (api guard)
   - G002: API contract test for /auth/register endpoint (api guard)
   - G003: Session management unit tests (unit-pytest guard)
   ```

2. **Task Generation** (`/tasks`):
   ```markdown
   - [ ] T010 [US1] Implement login endpoint in src/api/auth.py [Guard: G001]
   - [ ] T011 [US1] Implement register endpoint in src/api/auth.py [Guard: G002]
   - [ ] T012 [US1] Implement session manager in src/services/session.py [Guard: G003]
   ```

3. **Guard Creation**:
   ```bash
   specify guard create --type api --name login-endpoint
   specify guard create --type api --name register-endpoint
   specify guard create --type unit-pytest --name session-manager
   ```

4. **Implementation** (`/implement`):
   ```
   Implementing T010...
   ✓ Code written for login endpoint
   
   Executing guard G001...
   $ specify guard run G001
   ✗ Guard G001 FAILED
     - Test 1: Endpoint returns 401 for invalid credentials ✓
     - Test 2: Endpoint returns 200 for valid credentials ✗
     - Test 3: Response includes JWT token ✗
   
   Fixing implementation based on guard feedback...
   
   Re-executing guard G001...
   $ specify guard run G001
   ✓ Guard G001 PASSED
   
   ✓ T010 marked complete with passing guard
   ```

### Example 2: Feature with E2E Guards

**Scenario**: Implementing a checkout flow

1. **Guards Created**:
   ```bash
   specify guard create --type docker-playwright --name checkout-flow
   ```

2. **Task with Guard**:
   ```markdown
   - [ ] T020 [US2] Implement complete checkout workflow [Guard: G004]
   ```

3. **Implementation Flow**:
   - Implement checkout UI components
   - Implement payment integration
   - Execute guard: `specify guard run G004`
   - Guard opens browser, tests end-to-end flow
   - If guard passes → Task complete
   - If guard fails → Review Playwright output, fix issues

### Example 3: Meta-Circular Guards

**Scenario**: Guard CLI feature itself (this project!)

The guard CLI was implemented with guards validating guards:

```bash
# Guards created for guard CLI implementation
specify guard create --type unit-pytest --name guard-registry
specify guard create --type unit-pytest --name guard-executor
specify guard create --type unit-pytest --name guard-types
```

Tasks included guard execution:
```markdown
- [X] T008 Create GuardRegistry class [Guard: test_registry.py ✓]
- [X] T010 Create GuardExecutor class [Guard: test_executor.py ✓]
- [X] T011 Create GuardType class [Guard: test_types.py ✓]
```

## Guard Types Decision Matrix

| Validation Need | Guard Type | Example Use Case |
|----------------|------------|------------------|
| API endpoints, HTTP contracts | `api` | REST API validation, GraphQL testing |
| Database schema, migrations | `database` | Schema consistency, migration rollback tests |
| Browser workflows, UI interactions | `docker-playwright` | E2E checkout flows, form submissions |
| Business logic, algorithms | `unit-pytest` | Payment calculations, validation rules |
| Code quality, style | `lint-ruff` | Python code standards, PEP 8 compliance |
| Performance benchmarks | `performance` | Response time < 200ms, throughput tests |
| Security scans | `security` | Vulnerability checks, auth validation |

## Migration Path for Existing Projects

For projects already using Spec Kit without guards:

1. **Adopt gradually**: Don't retrofit all features at once
2. **Start with new features**: Apply guard-driven validation to new work
3. **Identify critical paths**: Retrofit guards for high-risk areas (auth, payments, data integrity)
4. **Document exceptions**: If a task truly doesn't need a guard, document why

## Benefits of Guard Integration

1. **Objective completion criteria**: No more "looks good to me" - guards provide binary pass/fail
2. **AI agent accountability**: Forces AI to write code that passes real tests
3. **Faster feedback loops**: Catch issues during implementation, not in review
4. **Living documentation**: Guards document expected behavior as executable code
5. **Regression prevention**: Guards become regression tests automatically

## Status Summary

| Component | Status | Next Steps |
|-----------|--------|------------|
| Constitution (Principle V) | ✅ Complete | None |
| Guard CLI implementation | ✅ Complete | Optional: Add more guard types |
| `/tasks` template integration | ⚠️ Manual | Update template to auto-suggest guards |
| `/implement` template integration | ⚠️ Manual | Update template to auto-execute guards |
| `/plan` template integration | ⚠️ Manual | Update template to include guard planning |
| Documentation | ✅ This file | Publish to docs/ if desired |

## Recommendation

**For immediate use**: Guards are fully functional but require manual invocation. Users can:
- Run `specify guard create` during planning
- Add `[Guard: G###]` markers to tasks manually
- Run `specify guard run G###` before marking tasks complete

**For seamless integration**: Update the three command templates (tasks, implement, plan) to automate guard creation and validation. This makes guards a natural part of the workflow rather than an optional add-on.
