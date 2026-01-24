---
description: Run integration tests by starting services, executing acceptance scenarios, and reporting results
semantic_anchors:
  - ATDD                  # Acceptance Test-Driven Development - tests before code, executable specs
  - BDD Gherkin           # Given-When-Then scenarios, Dan North, Cucumber
  - Specification by Example  # Concrete examples as living documentation
  - Exploratory Testing   # Session-based, charter-driven, observe beyond scripts
  - Regression Testing    # Verify unchanged functionality still works
handoffs:
  - label: Diagnose & Fix
    agent: speckit.fix
    prompt: Diagnose why the feature is failing and create a correction plan
  - label: Quick Fix
    agent: speckit.implement
    prompt: Fix the validation issues found (use when root cause is clear)
  - label: Update Tasks
    agent: speckit.review
    prompt: Add correction tasks for validation failures
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

# Integration Validation

> **Activated Frameworks**: ATDD for executable specs, BDD Gherkin for scenario syntax, Exploratory Testing for regression/side-effect discovery.

You are an **ATDD Practitioner**. Your job is to validate implementation by executing BDD Gherkin acceptance scenarios as living documentation, while applying Exploratory Testing mindset to discover regressions and side effects.

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

### Step 1.2: Parse Acceptance Scenarios (BDD Gherkin)

> **Apply**: BDD Gherkin syntax - Given (context), When (action), Then (outcome). These are executable Specification by Example.

Extract testable scenarios from `spec.md`:

```markdown
### User Story 1 - [Title] (Priority: P1)

**Acceptance Scenarios** (BDD Gherkin):

1. **Given** [precondition/context], **When** [user action], **Then** [observable outcome]
2. **Given** [precondition/context], **When** [user action], **Then** [observable outcome]
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

**CRITICAL**: Track validation execution status. The final report MUST reflect reality:
- If validation was interrupted → Report as **INCOMPLETE**
- If scenarios could not be executed → Report as **ERROR**
- If all scenarios ran but some failed → Report as **FAILED** with details
- ONLY report **PASSED** if ALL scenarios were executed AND passed

### Validation Execution Tracking

Maintain a running status during validation:

```markdown
## Validation Execution Log

| Timestamp | Event | Status | Details |
|-----------|-------|--------|---------|
| {time} | Start validation | ⏳ Running | Mode: {mode} |
| {time} | US1 Scenario 1 | ✅ Pass | 2.3s |
| {time} | US1 Scenario 2 | ❌ Fail | Element not found |
| {time} | US2 Scenario 1 | ⚠️ Error | Service unavailable |
| {time} | Validation ended | ❌ Incomplete | Stopped at US2 due to error |
```

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

### Step 3.5: Handle Execution Errors

**IMPORTANT**: Distinguish between test failures and execution errors:

| Type | Example | Action |
|------|---------|--------|
| **Test Failure** | Assertion failed, element not found | Record failure, continue testing |
| **Execution Error** | Service crashed, timeout, MCP error | Record error, attempt recovery or stop |
| **Critical Error** | Infrastructure down, cannot proceed | Stop validation, report incomplete |

When an execution error occurs:

```markdown
### ⚠️ EXECUTION ERROR at US2 Scenario 1

**Error Type**: Service Unavailable
**Error Message**: Backend returned 503 after 3 retries
**Impact**: Cannot continue testing US2 and beyond

**Recovery Attempted**:
- Restart backend service: Failed
- Wait 30s and retry: Failed

**Decision**: Marking validation as INCOMPLETE
```

**NEVER mark validation as successful if execution errors occurred.** The report must clearly state that not all scenarios could be tested.

### Step 3.6: Capture Out-of-Scope Issues (Exploratory Testing)

> **Apply**: Exploratory Testing mindset - observe beyond scripted scenarios. Session-based discovery of regressions and side effects.

**CRITICAL**: While executing BDD scenarios, apply Exploratory Testing to discover issues OUTSIDE the current test scope. These MUST be captured.

#### Types of Out-of-Scope Issues (Regression Testing Categories)

| Type | Description | Example |
|------|-------------|---------|
| **Regression** | Previously working feature now broken (Regression Testing focus) | Login worked last week, now fails |
| **Side Effect** | Action in one module breaks another (coupling issue) | Adding item to cart clears user session |
| **Unexpected Error** | Error in unrelated component (hidden dependency) | Console error from analytics during checkout |
| **Performance Degradation** | Noticeably slower (non-functional regression) | Page load 1s → 5s |
| **UI/UX Anomaly** | Visual or interaction issue (Exploratory discovery) | Button misaligned, wrong color, flicker |
| **Data Inconsistency** | Data doesn't match invariants (data integrity issue) | User count shows -1, dates wrong format |

#### How to Capture

During scenario execution, watch for:

1. **Console errors** not related to the current test
2. **Visual anomalies** in other parts of the UI
3. **Slow responses** or timeouts in unrelated components
4. **Broken navigation** or links
5. **Data display issues** anywhere on screen

When found, document immediately:

```markdown
### 🔍 OUT-OF-SCOPE ISSUE DISCOVERED

**Discovered During**: US2 - Order Management / Create order scenario
**Component Affected**: Navigation Menu (unrelated to current test)

**Issue**: Main navigation dropdown fails to open after order creation
**Severity**: HIGH (affects all pages)
**Type**: Regression / Side Effect

**Evidence**:
- Screenshot: `validation/screenshots/nav-broken-after-order.png`
- Console: `TypeError: Cannot read property 'toggle' of undefined`

**Reproduction**:
1. Complete order creation
2. Click on main navigation menu
3. Dropdown doesn't appear

**Notes**: This was working before. Likely regression from recent changes.
```

#### Create Bug Reports for Out-of-Scope Issues

These issues MUST also be added to `validation/bugs/`:

```markdown
---
status: open
severity: high
type: regression
user_story: NONE
discovered_during: US2 - Create order
component: Navigation Menu
created: {current_date}
---

# BUG-003: Navigation menu broken after order creation

## Summary

Navigation dropdown stops working after completing an order.

## Discovery Context

This issue was discovered while testing US2 (Order Management).
It is NOT related to the order feature itself but was triggered by it.

## Type: REGRESSION

This functionality was working before. Likely caused by recent changes.

...
```

#### Out-of-Scope Issue Severity

Even if not in the test scope, assess severity based on impact:

| Severity | Criteria |
|----------|----------|
| **critical** | Blocks core functionality across the app |
| **high** | Significantly impacts user experience |
| **medium** | Noticeable but has workaround |
| **low** | Minor, cosmetic, or edge case |

**IMPORTANT**: Do NOT ignore out-of-scope issues just because they're "not part of the test". If you see something broken, report it.

---

## Phase 4: Results & Reporting

### Step 4.1: Determine Overall Validation Status

**CRITICAL**: Before generating the report, determine the TRUE validation status:

```markdown
## Validation Status Determination

Check these conditions IN ORDER:

1. **Were there execution errors that prevented testing?**
   - YES → Status: ❌ **INCOMPLETE** - Cannot determine feature quality
   - NO → Continue to step 2

2. **Were all planned scenarios executed?**
   - NO → Status: ⚠️ **PARTIAL** - Some scenarios not tested
   - YES → Continue to step 3

3. **Did any scenarios fail?**
   - YES → Status: ❌ **FAILED** - Feature has issues that must be fixed
   - NO → Status: ✅ **PASSED** - All scenarios passed
```

**IMPORTANT**:
- ONLY report "PASSED" or "All Green" if EVERY scenario was executed AND passed
- If validation was interrupted, clearly state what was NOT tested
- The fix command relies on this report being accurate

### Step 4.2: Generate Validation Report

Create `FEATURE_DIR/validation/report-{date}.md`:

```markdown
# Validation Report: [Feature Name]

**Date**: {current_date}
**Scope**: {validation_mode}
**Duration**: {total_time}
**Status**: {PASSED|FAILED|INCOMPLETE|PARTIAL}

## ⚠️ Validation Status: {STATUS}

> {Clear explanation of what this status means}
>
> **PASSED**: All scenarios executed successfully - feature is ready
> **FAILED**: Some scenarios failed - issues must be fixed (see details below)
> **INCOMPLETE**: Validation could not complete - execution errors occurred
> **PARTIAL**: Some scenarios were skipped - cannot fully assess quality

## Summary

| Metric | Value |
|--------|-------|
| User Stories Tested | 3/4 |
| Scenarios Executed | 12 |
| Passed | 10 |
| Failed | 2 |
| Skipped | 1 |
| Execution Errors | 0 |
| **Out-of-Scope Issues** | **3** |
| **Pass Rate** | **83%** |
| **Overall Status** | **FAILED** |

> ⚠️ **Note**: 3 additional issues were discovered outside the test scope (regressions, side effects). See "Out-of-Scope Issues" section.

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

## Out-of-Scope Issues Discovered

> These issues were found during testing but are NOT part of the tested scenarios.
> They may be regressions, side effects, or pre-existing bugs.

| Bug ID | Type | Component | Severity | Discovered During |
|--------|------|-----------|----------|-------------------|
| BUG-003 | Regression | Navigation Menu | HIGH | US2 - Create order |
| BUG-004 | Side Effect | User Session | CRITICAL | US2 - Add to cart |
| BUG-005 | UI Anomaly | Footer | LOW | US1 - Login |

### BUG-003: Navigation menu broken after order creation

- **Type**: Regression
- **Component**: Navigation Menu (not related to Order feature)
- **Discovered While**: Testing US2 - Create order scenario
- **Severity**: HIGH
- **Description**: Navigation dropdown fails to open after completing order
- **Evidence**: `validation/screenshots/nav-broken-after-order.png`

### BUG-004: User session cleared unexpectedly

- **Type**: Side Effect
- **Component**: Session Management
- **Discovered While**: Testing US2 - Add to cart scenario
- **Severity**: CRITICAL
- **Description**: Adding item to cart logs user out
- **Evidence**: Console shows session token invalidated

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

### Step 4.3: Create Bug Reports

**CRITICAL**: For each failure or issue found, create an individual bug report file in `FEATURE_DIR/validation/bugs/`.

This directory is the SOURCE OF TRUTH for the `/speckit.fix` command. Each bug gets its own file.

#### Bug File Format

Create one file per bug: `validation/bugs/BUG-{number}-{short-desc}.md`

```markdown
---
status: open
severity: critical
type: scenario_failure
user_story: US3
scenario: Generate report
created: {current_date}
---

# BUG-001: Report template not found

## Summary

When generating a PDF report, the system fails with "Template not found" error.

## Reproduction Steps

1. Navigate to Reports section
2. Click "Generate Monthly Report"
3. Select date range
4. Click "Download PDF"

## Expected Behavior

PDF file downloads with the monthly report data.

## Actual Behavior

Error displayed: "Template not found"
Backend log: `[ERROR] ReportService: Template not found at /templates/monthly.ftl`

## Evidence

- Screenshot: `../screenshots/us3-report-fail.png`
- Backend logs attached below

## Technical Analysis

**Probable Cause**: Template file missing or path misconfigured
**Affected Files**: `src/services/ReportService.java:45`
**Suggested Fix**: Check template path configuration in `application.yml`

## Metadata

- **Detected During**: Integration validation
- **Validation Report**: `report-{date}.md`
- **Blocking**: Release
```

#### Bug Types

| Type | Description | Origin |
|------|-------------|--------|
| **scenario_failure** | A test scenario failed | Testing user story |
| **regression** | Previously working feature now broken | Discovered during testing |
| **side_effect** | Action in one area breaks another | Discovered during testing |
| **performance** | Slow response or degradation | Observed during testing |
| **ui_anomaly** | Visual or interaction issue | Observed during testing |
| **data_issue** | Data inconsistency or corruption | Observed during testing |

#### Bug Severity Levels

| Severity | Criteria | Example |
|----------|----------|---------|
| **critical** | Core functionality broken, no workaround | Login fails, data corruption |
| **high** | Important feature broken | Cancel button missing, export fails |
| **medium** | Feature works with issues | Slow performance, UI glitch |
| **low** | Minor issue, cosmetic | Typo, alignment issue |

#### Bug Status Values

| Status | Meaning |
|--------|---------|
| **open** | Bug identified, not yet addressed |
| **in_progress** | Fix is being worked on |
| **resolved** | Fix applied and verified |
| **wont_fix** | Decided not to fix (documented reason) |

Create bug files for ALL failures found during validation:

```
validation/
├── report-{date}.md
├── screenshots/
│   └── ...
└── bugs/
    ├── BUG-001-report-template-missing.md
    ├── BUG-002-cancel-button-not-found.md
    └── ...
```

### Step 4.4: Create Correction Tasks

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

Present to user with CLEAR status indication:

**CRITICAL**: The output MUST clearly indicate whether the feature is ready or not. Do NOT say "Validation Complete" if there are failures or errors.

```markdown
## Validation Result: {STATUS}

{Use appropriate header based on status:}
- ✅ **VALIDATION PASSED** - Feature is ready
- ❌ **VALIDATION FAILED** - Issues must be fixed
- ⚠️ **VALIDATION INCOMPLETE** - Could not test all scenarios
- ⚠️ **VALIDATION PARTIAL** - Some scenarios skipped

**Scenarios**: {passed}/{total} passed ({pass_rate}%)

### Status by User Story

✅ **US1 - User Authentication**: All passed
❌ **US2 - Order Management**: 1 failure (cancel button missing)
❌ **US3 - Reporting**: 1 failure (template error)

### Issues Found

> **IMPORTANT**: These issues MUST be fixed before the feature can be considered complete.

| # | User Story | Scenario | Issue | Severity |
|---|------------|----------|-------|----------|
| 1 | US2 | Cancel order | Element `#cancel-btn` not found | HIGH |
| 2 | US3 | Generate report | Template not found in ReportService | CRITICAL |

### Execution Errors (if any)

> These errors prevented some scenarios from being tested. The feature cannot be validated until these are resolved.

| # | User Story | Error | Impact |
|---|------------|-------|--------|
| - | - | - | - |

### Files Generated

- `validation/report-{date}.md` - Full report with all details
- `validation/screenshots/` - Evidence for failures
- `validation/bugs/` - Individual bug reports (used by `/speckit.fix`)

### Bug Reports Created

> These bug files are the input for `/speckit.fix`. Run fix without arguments to process all open bugs.

**Scenario Failures**:
| Bug ID | Severity | User Story | Issue |
|--------|----------|------------|-------|
| BUG-001 | CRITICAL | US3 | Report template not found |
| BUG-002 | HIGH | US2 | Cancel button missing |

**Out-of-Scope Issues** (regressions, side effects, other discoveries):
| Bug ID | Type | Component | Severity | Issue |
|--------|------|-----------|----------|-------|
| BUG-003 | Regression | Navigation | HIGH | Menu broken after order |
| BUG-004 | Side Effect | Session | CRITICAL | Cart action logs out user |

> ⚠️ Out-of-scope issues may affect other features. Review and prioritize accordingly.

### Correction Tasks Added

- T089: Fix report template (CRITICAL)
- T090: Add cancel button (HIGH)

### Required Actions

{Based on status:}

**If FAILED or INCOMPLETE**:
> The feature is NOT ready. Run `/speckit.fix` to diagnose and fix the issues.

**If PASSED**:
> The feature is ready for release.

### Next Steps

- [Diagnose & Fix] → `/speckit.fix` to analyze and fix issues
- [Re-validate] → `/speckit.validate` after fixes
- [Review Report] → Open `validation/report-{date}.md`
```

**NEVER present a "Validation Complete" message that could be mistaken for success when there are failures.**

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
