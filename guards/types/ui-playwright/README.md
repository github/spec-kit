# UI Playwright Guard Type

## Overview

The `ui-playwright` guard type enables end-to-end UI testing using Playwright browser automation. It validates user interface functionality by running automated browser tests against your application.

## What This Guard Type Validates

- **UI Functionality**: User interactions, form submissions, navigation flows
- **Visual Rendering**: Page layouts, element visibility, responsive design
- **Cross-Browser Compatibility**: Tests across Chromium, Firefox, and WebKit
- **User Workflows**: End-to-end scenarios like checkout, registration, login
- **Dynamic Content**: AJAX interactions, Single Page Application behavior

## When to Use It

### ✅ Use This Guard Type When:

- Testing complete user workflows (e.g., checkout process)
- Validating UI changes that affect user experience
- Ensuring cross-browser compatibility
- Testing JavaScript-heavy applications
- Verifying responsive design across viewports
- Checking for visual regressions

### ❌ Don't Use This Guard Type When:

- Testing API endpoints directly (use `api-requests` instead)
- Running unit tests (use `unit-pytest` instead)
- Checking code quality (use `static-analysis-python` instead)
- Testing non-browser functionality

## Installation

Before using this guard type, install Playwright:

```bash
# Install Playwright with the browser engine you need
uvx playwright install chromium

# Or install all browsers
uvx playwright install
```

## Example Configurations

### Basic Smoke Test

```yaml
id: G002
guard_type: ui-playwright
name: ui-smoke-test
params:
  browser: chromium
  headless: true
  test_paths:
    - tests/ui/smoke/
  screenshots_on_failure: true
  timeout: 30000
```

### Checkout Flow Validation

```yaml
id: G003
guard_type: ui-playwright
name: checkout-flow
params:
  browser: chromium
  headless: true
  test_paths:
    - tests/ui/e2e/checkout.spec.js
  screenshots_on_failure: true
  timeout: 60000
```

### Cross-Browser Testing

```yaml
id: G004
guard_type: ui-playwright
name: cross-browser-tests
params:
  browser: webkit  # Test with Safari engine
  headless: false   # See the browser for debugging
  test_paths:
    - tests/ui/critical/
  screenshots_on_failure: true
  timeout: 45000
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `browser` | string | `chromium` | Browser engine: `chromium`, `firefox`, or `webkit` |
| `headless` | boolean | `true` | Run browser without GUI |
| `test_paths` | array | `["tests/ui/"]` | Paths to Playwright test files/directories |
| `screenshots_on_failure` | boolean | `true` | Capture screenshots when tests fail |
| `timeout` | integer | `30000` | Default timeout for tests (milliseconds) |

## Creating a Guard Instance

```bash
# Create a guard for UI smoke tests
specify guard create --type ui-playwright --name ui-smoke-test

# Edit the generated guard.yaml to configure parameters
# Then run the guard
specify guard run G00X
```

## Common Failure Patterns

### 1. Element Not Found

**Symptom**: Test fails with "Element not found" or timeout
**Cause**: Selector changed, element not loaded, dynamic content delay
**Fix**: 
- Update selectors in test files
- Add proper wait conditions
- Increase timeout if needed

### 2. Navigation Timeout

**Symptom**: "Navigation timeout of X ms exceeded"
**Cause**: Page taking too long to load
**Fix**:
- Increase timeout parameter
- Check network conditions
- Optimize page load performance

### 3. Flaky Tests

**Symptom**: Tests pass sometimes, fail other times
**Cause**: Race conditions, animations, dynamic content
**Fix**:
- Use proper wait strategies (`waitForSelector`, `waitForLoadState`)
- Avoid fixed `setTimeout` delays
- Ensure test isolation

### 4. Screenshot Failures

**Symptom**: Screenshots not captured on failure
**Cause**: Output directory missing, permissions issue
**Fix**:
- Ensure screenshot directory exists
- Check file permissions
- Verify `screenshots_on_failure: true` in params

## Debugging Failures

### View Guard History

```bash
# List recent runs
specify guard history G00X

# View detailed output for a specific run
specify guard history G00X --run-id <run-id>
```

### Run Tests Manually

```bash
# Run Playwright tests directly for debugging
uvx playwright test tests/ui/ --headed --debug
```

### Enable Headed Mode

Temporarily set `headless: false` in guard.yaml to see the browser:

```yaml
params:
  headless: false  # Watch tests run in real browser
```

### Check Screenshots

When tests fail with `screenshots_on_failure: true`, check:
- `test-results/` directory for Playwright output
- Guard details JSON for screenshot paths

## Example Test File

Create a basic Playwright test in `tests/ui/example.spec.js`:

```javascript
const { test, expect } = require('@playwright/test');

test('homepage loads successfully', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page).toHaveTitle(/My App/);
  await expect(page.locator('h1')).toBeVisible();
});

test('navigation works', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.click('text=About');
  await expect(page).toHaveURL(/.*about/);
});
```

## Integration with Workflow

### In Plan Phase

When planning features with UI components, identify validation checkpoints:

```markdown
## Guard Validation Strategy

| Checkpoint | Guard Type | Command |
|------------|------------|---------|
| Checkout flow | ui-playwright | `specify guard create --type ui-playwright --name checkout-e2e` |
```

### In Tasks Phase

Tag implementation tasks with guard validation:

```markdown
- [ ] T015 Implement checkout form [Guard: G003]
- [ ] T016 Add payment processing [Guard: G003]
```

### In Implementation Phase

Run guards after making UI changes:

```bash
# After implementing checkout form
specify guard run G003

# If failures occur
specify guard history G003  # Review what failed
```

## Best Practices

1. **Organize Tests**: Group related tests in directories (smoke/, e2e/, critical/)
2. **Use Page Objects**: Create reusable page object classes for complex UIs
3. **Isolate Tests**: Each test should be independent and idempotent
4. **Meaningful Selectors**: Use data-testid attributes for stable selectors
5. **Proper Waits**: Use Playwright's built-in wait mechanisms, not fixed delays
6. **Screenshot Strategy**: Enable screenshots for debugging, but review regularly
7. **Fast Feedback**: Keep smoke tests fast (<30s), detailed E2E tests separate

## Related Guard Types

- **unit-pytest**: For unit testing business logic
- **api-requests**: For testing API endpoints
- **static-analysis-python**: For code quality checks

## Troubleshooting

### Playwright not found

```bash
# Install Playwright globally via uvx
uvx playwright install chromium
```

### Tests run but guard reports failure

Check the guard history for detailed error messages:

```bash
specify guard history G00X --verbose
```

### Timeout errors

Increase the timeout parameter in guard.yaml:

```yaml
params:
  timeout: 60000  # 60 seconds
```

---

**Guard Type**: ui-playwright  
**Category**: ui  
**Engine**: Playwright  
**Language**: JavaScript/TypeScript (tests), Python (guard runner)
