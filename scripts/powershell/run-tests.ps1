# Run Bicep Generator tests with various options

param(
    [Parameter(HelpMessage="Test type to run: all, unit, integration, e2e")]
    [ValidateSet("all", "unit", "integration", "e2e")]
    [string]$Type = "all",
    
    [Parameter(HelpMessage="Run tests matching given mark expression")]
    [string]$Markers = "",
    
    [Parameter(HelpMessage="Disable coverage reporting")]
    [switch]$NoCoverage,
    
    [Parameter(HelpMessage="Verbose output")]
    [switch]$Verbose,
    
    [Parameter(HelpMessage="Run tests in parallel")]
    [switch]$Parallel,
    
    [Parameter(HelpMessage="Run only previously failed tests")]
    [switch]$Failed,
    
    [Parameter(HelpMessage="Include slow tests")]
    [switch]$Slow,
    
    [Parameter(HelpMessage="Include Azure integration tests (requires credentials)")]
    [switch]$Azure,
    
    [Parameter(HelpMessage="Quick test run (unit tests only, no coverage)")]
    [switch]$Quick
)

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Help function
function Show-Help {
    Write-Host @"
Run Bicep Generator tests with various configurations.

USAGE:
    .\run-tests.ps1 [OPTIONS]

OPTIONS:
    -Type <TYPE>        Test type to run: all, unit, integration, e2e (default: all)
    -Markers <EXPR>     Run tests matching given mark expression
    -NoCoverage         Disable coverage reporting
    -Verbose            Verbose output
    -Parallel           Run tests in parallel
    -Failed             Run only previously failed tests
    -Slow               Include slow tests
    -Azure              Include Azure integration tests (requires credentials)
    -Quick              Quick test run (unit tests only, no coverage)

EXAMPLES:
    .\run-tests.ps1                                   # Run all tests with coverage
    .\run-tests.ps1 -Type unit                       # Run only unit tests
    .\run-tests.ps1 -Type integration -Verbose       # Run integration tests with verbose output
    .\run-tests.ps1 -Markers "not slow"              # Run tests excluding slow tests
    .\run-tests.ps1 -Azure                            # Run all tests including Azure tests
    .\run-tests.ps1 -Quick                            # Quick unit tests (no coverage)
    .\run-tests.ps1 -Type e2e -Slow                  # Run E2E tests including slow ones

"@
}

# Process quick option
if ($Quick) {
    $Type = "unit"
    $NoCoverage = $true
}

# Build pytest command
$pytestCmd = "pytest"

# Add test type marker
switch ($Type) {
    "unit" {
        $pytestCmd += " -m unit"
    }
    "integration" {
        $pytestCmd += " -m integration"
    }
    "e2e" {
        $pytestCmd += " -m e2e"
    }
    "all" {
        # Run all tests except azure by default
        if (!$Azure -and !$Markers.Contains("azure")) {
            $pytestCmd += " -m 'not azure'"
        }
    }
}

# Add additional markers
if ($Markers) {
    $pytestCmd += " $Markers"
}

if ($Failed) {
    $pytestCmd += " --lf"
}

if ($Slow) {
    if ($pytestCmd -match "-m '.*'") {
        $pytestCmd = $pytestCmd -replace "-m '(.*)'"," -m '$1 or slow'"
    } else {
        $pytestCmd += " -m slow"
    }
}

if ($Azure) {
    if ($pytestCmd -match "-m '.*'") {
        $pytestCmd = $pytestCmd -replace "-m '(.*)'"," -m '$1 or azure'"
    } else {
        $pytestCmd += " -m azure"
    }
}

# Add coverage options
if (!$NoCoverage) {
    $pytestCmd += " --cov=src/specify_cli/bicep --cov-report=term-missing --cov-report=html"
} else {
    $pytestCmd += " --no-cov"
}

# Add verbose option
if ($Verbose) {
    $pytestCmd += " -vv"
}

# Add parallel option
if ($Parallel) {
    $pytestCmd += " -n auto"
}

# Print configuration
Write-ColorOutput Green "=== Bicep Generator Test Runner ==="
Write-Host "Test Type: $Type"
Write-Host "Coverage: $(!$NoCoverage)"
Write-Host "Verbose: $Verbose"
Write-Host "Parallel: $Parallel"
Write-Host "Markers: $Markers"
Write-Host ""
Write-ColorOutput Yellow "Running command: $pytestCmd"
Write-Host ""

# Run tests
try {
    Invoke-Expression $pytestCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-ColorOutput Green "✅ All tests passed!"
        
        # Show coverage report location if enabled
        if (!$NoCoverage) {
            Write-ColorOutput Green "Coverage report: htmlcov/index.html"
        }
        
        exit 0
    } else {
        Write-Host ""
        Write-ColorOutput Red "❌ Tests failed!"
        exit 1
    }
} catch {
    Write-Host ""
    Write-ColorOutput Red "❌ Error running tests: $_"
    exit 1
}
