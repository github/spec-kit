# Production deployment script for Bicep Generator feature

param(
    [Parameter(HelpMessage="Show what would be done without deploying")]
    [switch]$DryRun,
    
    [Parameter(HelpMessage="Skip running tests before deployment")]
    [switch]$SkipTests,
    
    [Parameter(HelpMessage="Skip building distribution packages")]
    [switch]$SkipBuild,
    
    [Parameter(HelpMessage="Target environment")]
    [ValidateSet("dev", "staging", "production")]
    [string]$Environment = "production",
    
    [Parameter(HelpMessage="Publish to PyPI")]
    [switch]$Publish,
    
    [Parameter(HelpMessage="Override version from pyproject.toml")]
    [string]$Version
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

# Get script and repo paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

# Get version from pyproject.toml if not specified
if (!$Version) {
    $pyprojectFile = Join-Path $repoRoot "pyproject.toml"
    $content = Get-Content $pyprojectFile -Raw
    if ($content -match 'version = "([^"]+)"') {
        $Version = $matches[1]
    }
    else {
        Write-ColorOutput Red "Error: Could not find version in pyproject.toml"
        exit 1
    }
}

Write-ColorOutput Green "=== Bicep Generator Deployment ==="
Write-Host "Version: $Version"
Write-Host "Environment: $Environment"
Write-Host "Dry Run: $DryRun"
Write-Host "Skip Tests: $SkipTests"
Write-Host "Skip Build: $SkipBuild"
Write-Host "Publish to PyPI: $Publish"
Write-Host ""

# Change to repo root
Set-Location $repoRoot

# Step 1: Validate environment
Write-ColorOutput Blue "Step 1: Validating environment..."

# Check if git working directory is clean
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-ColorOutput Yellow "Warning: Working directory has uncommitted changes"
    if (!$DryRun) {
        $response = Read-Host "Continue anyway? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-ColorOutput Red "Deployment cancelled"
            exit 1
        }
    }
}

# Check Python version
$pythonVersion = python --version
Write-Host "Python version: $pythonVersion"

# Check required tools
Write-Host "Checking required tools..."
$tools = @("git", "pip", "pytest")
foreach ($tool in $tools) {
    $found = Get-Command $tool -ErrorAction SilentlyContinue
    if (!$found) {
        Write-ColorOutput Red "Error: Required tool '$tool' not found"
        exit 1
    }
}

Write-ColorOutput Green "✓ Environment validated"
Write-Host ""

# Step 2: Run tests
if (!$SkipTests) {
    Write-ColorOutput Blue "Step 2: Running tests..."
    
    if ($DryRun) {
        Write-ColorOutput Yellow "Would run: pytest tests/bicep -m 'not azure' --cov=src/specify_cli/bicep --cov-fail-under=80"
    }
    else {
        pytest tests/bicep -m "not azure" --cov=src/specify_cli/bicep --cov-fail-under=80
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput Red "✗ Tests failed"
            exit 1
        }
    }
    
    Write-ColorOutput Green "✓ Tests passed"
    Write-Host ""
}
else {
    Write-ColorOutput Yellow "Skipping tests (not recommended for production)"
    Write-Host ""
}

# Step 3: Build distribution
if (!$SkipBuild) {
    Write-ColorOutput Blue "Step 3: Building distribution..."
    
    # Clean previous builds
    if (!$DryRun) {
        if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
        if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
        Get-ChildItem -Filter "*.egg-info" -Recurse | Remove-Item -Recurse -Force
    }
    else {
        Write-ColorOutput Yellow "Would clean: dist/, build/, *.egg-info"
    }
    
    # Install build dependencies
    if (!$DryRun) {
        pip install --upgrade build twine
    }
    else {
        Write-ColorOutput Yellow "Would install: build, twine"
    }
    
    # Build package
    if (!$DryRun) {
        python -m build
        
        # Check distribution
        twine check dist/*
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput Red "✗ Distribution check failed"
            exit 1
        }
    }
    else {
        Write-ColorOutput Yellow "Would run: python -m build"
        Write-ColorOutput Yellow "Would run: twine check dist/*"
    }
    
    Write-ColorOutput Green "✓ Distribution built"
    Write-Host ""
}
else {
    Write-ColorOutput Yellow "Skipping build"
    Write-Host ""
}

# Step 4: Tag release
Write-ColorOutput Blue "Step 4: Creating git tag..."

$tag = "v$Version"
$existingTag = git tag -l $tag 2>$null
if ($existingTag) {
    Write-ColorOutput Yellow "Warning: Tag $tag already exists"
}
else {
    if (!$DryRun) {
        git tag -a $tag -m "Release $tag - Bicep Generator Feature"
        Write-ColorOutput Green "✓ Created tag $tag"
        Write-ColorOutput Yellow "Push with: git push origin $tag"
    }
    else {
        Write-ColorOutput Yellow "Would create tag: $tag"
    }
}
Write-Host ""

# Step 5: Publish to PyPI (optional)
if ($Publish) {
    Write-ColorOutput Blue "Step 5: Publishing to PyPI..."
    
    if (!$DryRun) {
        # Check if PYPI_API_TOKEN is set
        if (!$env:PYPI_API_TOKEN) {
            Write-ColorOutput Red "Error: PYPI_API_TOKEN environment variable not set"
            exit 1
        }
        
        twine upload dist/* --skip-existing
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput Red "✗ PyPI upload failed"
            exit 1
        }
        
        Write-ColorOutput Green "✓ Published to PyPI"
    }
    else {
        Write-ColorOutput Yellow "Would run: twine upload dist/*"
    }
    Write-Host ""
}
else {
    Write-ColorOutput Yellow "Skipping PyPI publication"
    Write-Host ""
}

# Step 6: Summary
Write-ColorOutput Green "=== Deployment Summary ==="
Write-Host "Version: $Version"
Write-Host "Tag: $tag"
Write-Host "Environment: $Environment"
if ($Publish -and !$DryRun) {
    Write-Host "PyPI: https://pypi.org/project/specify-cli/$Version/"
}
Write-Host ""

if ($DryRun) {
    Write-ColorOutput Yellow "This was a dry-run. No changes were made."
    Write-Host "Run without -DryRun to perform actual deployment."
}
else {
    Write-ColorOutput Green "✅ Deployment completed successfully!"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Push the tag: git push origin $tag"
    Write-Host "2. Create GitHub release with notes from docs/bicep-generator/RELEASE-NOTES.md"
    if (!$Publish) {
        Write-Host "3. Optionally publish to PyPI: .\deploy-bicep-generator.ps1 -Publish"
    }
}
