---
description: Run integration tests by starting services, executing acceptance scenarios, and reporting results
handoffs:
  - label: Fix Issues Found
    agent: speckit.implement
    prompt: Fix the validation issues found
  - label: Update Tasks
    agent: speckit.review
    prompt: Add correction tasks for validation failures
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

# Integration Validation

You are a **QA Engineer**. Your job is to validate the implementation by running the acceptance scenarios defined in the specification.

## User Input

```text
$ARGUMENTS
```

Consider user input for scope (specific user story, full validation, quick smoke test).

---

## Prerequisites

This command requires:

1. **MCP Server configured** - Run `/speckit.mcp` first if not done
2. **Specification with acceptance scenarios** - `spec.md` with User Stories
3. **Implementation complete** - Tasks marked as done in `tasks.md`

---

## Validation Modes

| Mode | Trigger | Scope |
|------|---------|-------|
| **Full** | "full", "all", default | All user stories in priority order |
| **Story** | "US1", "story 2", "P1" | Specific user story only |
| **Smoke** | "smoke", "quick" | P1 story happy path only |
| **API Only** | "api", "backend" | API endpoints without browser |
| **UI Only** | "ui", "frontend" | Browser tests only |

---

## Phase 1: Preparation

### Step 1.1: Load Context

Run `{SCRIPT}` to get paths, then load:

```
FEATURE_DIR/
├── spec.md          → User stories with acceptance scenarios
├── plan.md          → Technical implementation details
├── tasks.md         → Implementation progress
├── contracts/       → API contracts for endpoint testing
└── quickstart.md    → How to run the application
```

### Step 1.2: Parse Acceptance Scenarios

Extract testable scenarios from `spec.md`:

```markdown
### User Story 1 - [Title] (Priority: P1)

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]
```

Build a test matrix:

| Story | Scenario | Type | Steps | Status |
|-------|----------|------|-------|--------|
| US1 | Login success | UI+API | 5 | Pending |
| US1 | Login invalid | UI | 3 | Pending |
| US2 | Create order | API | 4 | Pending |

### Step 1.3: Check Implementation Progress

Read `tasks.md` to determine what's testable:

```markdown
## Testable Scope

Based on completed tasks:
- ✅ US1 - User Authentication (all tasks complete)
- ✅ US2 - Order Management (all tasks complete)
- ⚠️ US3 - Reporting (3/5 tasks complete - partial testing)
- ❌ US4 - Admin Panel (not started - skip)
```

---

## Phase 2: Environment Setup

### Step 2.1: Start Infrastructure

Using MCP tools (or bash fallback):

```
1. start_docker          → Start DB, Redis, etc.
2. Wait for containers   → health_check on each
3. start_service backend → Start backend service
4. Wait for backend      → health_check backend
5. start_service frontend → Start frontend
6. Wait for frontend     → health_check frontend
```

**Important**: Wait for each service to be healthy before proceeding.

### Step 2.2: Verify Environment

Run health checks on all services:

```markdown
## Environment Status

| Service | Status | URL |
|---------|--------|-----|
| Database | ✅ Running | localhost:5432 |
| Redis | ✅ Running | localhost:6379 |
| Backend | ✅ Healthy | http://localhost:8080/health |
| Frontend | ✅ Ready | http://localhost:5173 |
```

If any service fails:
1. Check logs: `service_logs <name> 50`
2. Report the error
3. Ask user how to proceed

### Step 2.3: Seed Test Data (if needed)

If `quickstart.md` specifies seed data:

```bash
# Run migrations
npm run db:migrate

# Seed test data
npm run db:seed
```

Or via API:
```
api_post /api/test/seed
```

---

## Phase 3: Execute Validation

### Step 3.1: For Each User Story (by priority)

Process stories in order: P1 → P2 → P3

```markdown
## Validating: US1 - User Authentication

### Scenario 1.1: Successful login

**Given**: A registered user exists
**When**: User enters valid credentials and clicks login
**Then**: User is redirected to dashboard

#### Steps:
```

### Step 3.2: Execute Scenario Steps

For each scenario, translate Gherkin to MCP actions:

**Given** (Setup):
```
# Create test data if needed
api_post /api/test/users {"email": "test@example.com", "password": "secret"}
```

**When** (Actions):
```
# UI Actions
browser_open /login
browser_fill #email test@example.com
browser_fill #password secret
browser_click button[type=submit]

# Or API Actions
api_post /api/auth/login {"email": "test@example.com", "password": "secret"}
```

**Then** (Assertions):
```
# UI Assertions
browser_wait_for .dashboard
browser_url → should contain "/dashboard"
browser_exists .welcome-message → should be true

# API Assertions
→ status should be 200
→ body should contain { "token": "..." }
```

### Step 3.3: Capture Evidence

For each scenario:

1. **Screenshot** on success: `browser_screenshot`
2. **Screenshot** on failure: `browser_screenshot`
3. **API Response**: Log response body
4. **Logs on failure**: `service_logs backend 20 "ERROR"`

### Step 3.4: Handle Failures

When a step fails:

```markdown
### ❌ Scenario 1.2: Login with invalid password - FAILED

**Failed at step**: Then user sees error message

**Expected**: Element `.error-message` exists with text "Invalid credentials"
**Actual**: Element `.error-message` not found

**Evidence**:
- Screenshot: [attached]
- Backend logs (last 10 lines with ERROR):
  ```
  [ERROR] AuthController: NullPointerException at line 45
  ```

**Probable Cause**: Backend error handling not implemented

**Suggested Fix**: Check `AuthController.java:45` for null check
```

Continue with remaining scenarios unless critical failure.

---

## Phase 4: Results & Reporting

### Step 4.1: Generate Validation Report

Create `FEATURE_DIR/validation/report-{date}.md`:

```markdown
# Validation Report: [Feature Name]

**Date**: {current_date}
**Scope**: {validation_mode}
**Duration**: {total_time}

## Summary

| Metric | Value |
|--------|-------|
| User Stories Tested | 3/4 |
| Scenarios Executed | 12 |
| Passed | 10 |
| Failed | 2 |
| Skipped | 1 |
| **Pass Rate** | **83%** |

## Results by User Story

### ✅ US1 - User Authentication (P1)

| Scenario | Status | Duration |
|----------|--------|----------|
| Successful login | ✅ Pass | 2.3s |
| Invalid password | ✅ Pass | 1.8s |
| Account locked | ✅ Pass | 1.5s |

### ⚠️ US2 - Order Management (P2)

| Scenario | Status | Duration |
|----------|--------|----------|
| Create order | ✅ Pass | 3.1s |
| Cancel order | ❌ Fail | 2.0s |
| Order history | ✅ Pass | 2.5s |

**Failure Details**:

#### Cancel order - FAILED

- **Step**: When user clicks cancel button
- **Error**: Element `#cancel-btn` not found
- **Screenshot**: `validation/screenshots/us2-cancel-fail.png`
- **Logs**: No errors in backend

### ❌ US3 - Reporting (P3)

| Scenario | Status | Duration |
|----------|--------|----------|
| Generate report | ❌ Fail | 5.0s |

**Failure Details**:

#### Generate report - FAILED

- **Step**: Then PDF is downloaded
- **Error**: Timeout waiting for download
- **Backend Log**: `[ERROR] ReportService: Template not found`

## Failed Scenarios Summary

| Story | Scenario | Error | Impact |
|-------|----------|-------|--------|
| US2 | Cancel order | Element not found | Medium |
| US3 | Generate report | Template missing | High |

## Recommendations

### Critical (Block Release)
1. Fix report template issue in `ReportService`

### High Priority
1. Add cancel button to order detail page

### Observations
- Login flow is solid
- API response times are good (<500ms)
- Consider adding loading states for better UX
```

### Step 4.2: Save Screenshots

Save all screenshots to `FEATURE_DIR/validation/screenshots/`:

```
validation/
├── report-2024-01-15.md
└── screenshots/
    ├── us1-login-success.png
    ├── us2-cancel-fail.png
    └── us3-report-fail.png
```

### Step 4.3: Create Correction Tasks

If failures found, update `tasks.md` with correction tasks (using smart insertion from `/speckit.review`):

```markdown
### 🔧 Validation Corrections (Added {date})

> **Source**: Integration validation report
> **Must complete before**: Release

- [ ] T089 [CRITICAL] [US3] Fix missing report template in ReportService
- [ ] T090 [HIGH] [US2] Add cancel button to OrderDetail component
```

---

## Phase 5: Cleanup

### Step 5.1: Stop Services

```
stop_all          → Stop all application services
stop_docker       → Stop Docker containers
browser_close     → Close browser
```

### Step 5.2: Reset Test Data (optional)

```bash
npm run db:reset
```

Or leave data for debugging if failures occurred.

---

## Output

Present to user:

```markdown
## Validation Complete

**Pass Rate**: 83% (10/12 scenarios)

### Quick Summary

✅ **US1 - User Authentication**: All passed
⚠️ **US2 - Order Management**: 1 failure (cancel button missing)
❌ **US3 - Reporting**: 1 failure (template error)

### Failed Scenarios

1. **US2/Cancel order**: Element `#cancel-btn` not found
2. **US3/Generate report**: Template not found in ReportService

### Files Generated

- `validation/report-2024-01-15.md` - Full report
- `validation/screenshots/` - Evidence

### Correction Tasks Added

- T089: Fix report template (CRITICAL)
- T090: Add cancel button (HIGH)

### Next Steps

Choose an action:
- [Fix Issues] → `/speckit.implement` to fix the failures
- [Re-validate] → `/speckit.validate` after fixes
- [Review Report] → Open `validation/report-2024-01-15.md`
```

---

## Fallback: No MCP Server

If MCP server is not configured, use bash/tmux:

```bash
# Start services in background
tmux new-session -d -s backend 'cd backend && ./mvnw spring-boot:run'
tmux new-session -d -s frontend 'cd frontend && npm run dev'

# Wait for services
while ! curl -s http://localhost:8080/health > /dev/null; do sleep 1; done

# Run tests with curl for API
curl -X POST http://localhost:8080/api/auth/login -d '{"email":"test@example.com"}'

# For browser tests, recommend installing MCP
echo "For browser automation, run /speckit.mcp first"
```

Recommend running `/speckit.mcp` for full automation capabilities.
