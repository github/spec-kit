# Automated Testing & Fix Workflow
# Run this to test everything and auto-fix common issues

$ErrorActionPreference = "Continue"

Write-Host "`n?? Running Automated Test Suite..." -ForegroundColor Cyan

# 1. Lint and auto-fix
Write-Host "`n?? Running ESLint..." -ForegroundColor Yellow
npm run lint 2>&1 | Tee-Object -Variable lintOutput
if ($LASTEXITCODE -ne 0) {
    Write-Host "??  Lint issues found, attempting auto-fix..." -ForegroundColor Yellow
    npx eslint . --ext ts,tsx --fix
}

# 2. Type check
Write-Host "`n?? Type checking..." -ForegroundColor Yellow
npx tsc --noEmit
if ($LASTEXITCODE -ne 0) {
    Write-Host "? TypeScript errors found - review manually" -ForegroundColor Red
} else {
    Write-Host "? Type check passed" -ForegroundColor Green
}

# 3. Unit tests
Write-Host "`n?? Running unit tests..." -ForegroundColor Yellow
npm run test -- --run
$unitTestResult = $LASTEXITCODE

# 4. Start dev server in background for E2E
Write-Host "`n?? Starting dev server..." -ForegroundColor Yellow
$devServer = Start-Process npm -ArgumentList "run", "dev" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 10

# 5. Run E2E smoke tests
Write-Host "`n?? Running smoke tests..." -ForegroundColor Yellow
npm run test:e2e
$e2eResult = $LASTEXITCODE

# Stop dev server
Stop-Process -Id $devServer.Id -Force

# 6. Generate coverage report
Write-Host "`n?? Generating coverage report..." -ForegroundColor Yellow
npm run test:coverage -- --run

# Summary
Write-Host "`n?? Test Summary:" -ForegroundColor Cyan
Write-Host "  Unit Tests: $(if ($unitTestResult -eq 0) { '? PASSED' } else { '? FAILED' })" -ForegroundColor $(if ($unitTestResult -eq 0) { 'Green' } else { 'Red' })
Write-Host "  E2E Tests:  $(if ($e2eResult -eq 0) { '? PASSED' } else { '? FAILED' })" -ForegroundColor $(if ($e2eResult -eq 0) { 'Green' } else { 'Red' })

if ($unitTestResult -eq 0 -and $e2eResult -eq 0) {
    Write-Host "`n?? All tests passed! Ready for production." -ForegroundColor Green
} else {
    Write-Host "`n??  Some tests failed. Review the output above." -ForegroundColor Yellow
}
