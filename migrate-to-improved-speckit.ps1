#
# Spec-Kit Migration Script (PowerShell)
# Upgrades existing spec-kit project to include Phases 1-5 improvements
#
# Usage: .\migrate-to-improved-speckit.ps1 [-SourceDir <path>]
#

param(
    [string]$SourceDir
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "Spec-Kit Migration to Improved Version"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# Check if we're in a spec-kit project
if (-not (Test-Path "specs") -or -not (Test-Path "templates")) {
    Write-ColorOutput "Error: This doesn't appear to be a spec-kit project" "Red"
    Write-Host "Please run this script from your spec-kit project root directory."
    exit 1
}

# Get source spec-kit directory
if (-not $SourceDir) {
    Write-ColorOutput "No source directory provided." "Yellow"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  1. Clone improved spec-kit to temp directory and use it"
    Write-Host "  2. Provide path to existing improved spec-kit clone"
    Write-Host ""
    $option = Read-Host "Enter option [1 or 2]"

    if ($option -eq "1") {
        Write-Host ""
        Write-ColorOutput "Cloning improved spec-kit..." "Blue"
        $SourceDir = Join-Path $env:TEMP "spec-kit-improved-$(Get-Date -Format 'yyyyMMddHHmmss')"

        git clone https://github.com/guisantossi/spec-kit.git $SourceDir
        Push-Location $SourceDir
        git checkout claude/improve-s-feature-011CUtKowzjCGGTB49vfnCEm
        Pop-Location

        Write-ColorOutput "✓ Cloned to $SourceDir" "Green"
    }
    else {
        $SourceDir = Read-Host "Enter path to improved spec-kit"
    }
}

if (-not (Test-Path $SourceDir)) {
    Write-ColorOutput "Error: Source directory not found: $SourceDir" "Red"
    exit 1
}

$tokenBudgetPath = Join-Path $SourceDir "scripts\bash\token-budget.sh"
if (-not (Test-Path $tokenBudgetPath)) {
    Write-ColorOutput "Error: Source doesn't appear to be improved spec-kit" "Red"
    Write-Host "Missing: scripts\bash\token-budget.sh"
    exit 1
}

$ProjectDir = Get-Location
$BackupDir = Join-Path $ProjectDir ".speckit-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host ""
Write-Host "Source: $SourceDir"
Write-Host "Target: $ProjectDir"
Write-Host "Backup: $BackupDir"
Write-Host ""

$confirm = Read-Host "Proceed with migration? [y/N]"
if ($confirm -notmatch '^[Yy]$') {
    Write-Host "Migration cancelled."
    exit 0
}

Write-Host ""
Write-ColorOutput "Step 1: Creating backup..." "Blue"
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

# Backup critical files
if (Test-Path "memory\constitution.md") {
    Copy-Item "memory\constitution.md" $BackupDir -Force
}
if (Test-Path "templates\commands") {
    Copy-Item "templates\commands" $BackupDir -Recurse -Force
}
if (Test-Path ".gitignore") {
    Copy-Item ".gitignore" $BackupDir -Force
}

Write-ColorOutput "✓ Backup created at $BackupDir" "Green"

Write-Host ""
Write-ColorOutput "Step 2: Copying new bash scripts..." "Blue"
New-Item -ItemType Directory -Path "scripts\bash" -Force | Out-Null

# Copy all Phase 1-5 bash scripts
$bashScripts = @(
    "token-budget.sh",
    "validate-spec.sh",
    "semantic-search.sh",
    "session-prune.sh",
    "error-analysis.sh",
    "clarify-history.sh"
)

foreach ($script in $bashScripts) {
    $sourcePath = Join-Path $SourceDir "scripts\bash\$script"
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath "scripts\bash\" -Force
    }
}

# Update existing scripts if they exist
$existingScripts = @("setup-ai-doc.sh", "project-analysis.sh")
foreach ($script in $existingScripts) {
    $sourcePath = Join-Path $SourceDir "scripts\bash\$script"
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath "scripts\bash\" -Force
    }
}

Write-ColorOutput "✓ Bash scripts copied" "Green"

Write-Host ""
Write-ColorOutput "Step 3: Copying PowerShell scripts..." "Blue"
New-Item -ItemType Directory -Path "scripts\powershell" -Force | Out-Null

# Copy all PowerShell scripts
$psSourceDir = Join-Path $SourceDir "scripts\powershell"
if (Test-Path $psSourceDir) {
    Get-ChildItem -Path $psSourceDir -Filter "*.ps1" | ForEach-Object {
        Copy-Item $_.FullName "scripts\powershell\" -Force
    }
}

Write-ColorOutput "✓ PowerShell scripts copied" "Green"

Write-Host ""
Write-ColorOutput "Step 4: Copying new command templates..." "Blue"
New-Item -ItemType Directory -Path "templates\commands" -Force | Out-Null

# Copy new command templates
$commandTemplates = @(
    "budget.md",
    "validate.md",
    "find.md",
    "prune.md",
    "error-context.md",
    "clarify-history.md",
    "resume.md"
)

foreach ($template in $commandTemplates) {
    $sourcePath = Join-Path $SourceDir "templates\commands\$template"
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath "templates\commands\" -Force
    }
}

# Update existing templates
$existingTemplates = @("document.md")
foreach ($template in $existingTemplates) {
    $sourcePath = Join-Path $SourceDir "templates\commands\$template"
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath "templates\commands\" -Force
    }
}

# Copy quick-ref template
$quickRefSource = Join-Path $SourceDir "templates\quick-ref-template.md"
if (Test-Path $quickRefSource) {
    Copy-Item $quickRefSource "templates\" -Force
}

Write-ColorOutput "✓ Command templates copied" "Green"

Write-Host ""
Write-ColorOutput "Step 5: Copying Git hooks..." "Blue"
New-Item -ItemType Directory -Path "hooks" -Force | Out-Null

$hooksSource = Join-Path $SourceDir "hooks"
if (Test-Path $hooksSource) {
    Get-ChildItem -Path $hooksSource | ForEach-Object {
        Copy-Item $_.FullName "hooks\" -Recurse -Force
    }
}

Write-ColorOutput "✓ Git hooks copied" "Green"

Write-Host ""
Write-ColorOutput "Step 6: Copying documentation..." "Blue"

$platformCompatSource = Join-Path $SourceDir "PLATFORM-COMPATIBILITY.md"
if (Test-Path $platformCompatSource) {
    Copy-Item $platformCompatSource . -Force
}

$workflowSource = Join-Path $SourceDir "IMPROVED-WORKFLOW.md"
if (Test-Path $workflowSource) {
    Copy-Item $workflowSource . -Force
}

Write-ColorOutput "✓ Documentation copied" "Green"

Write-Host ""
Write-ColorOutput "Step 7: Updating .gitignore..." "Blue"

$gitignoreContent = if (Test-Path ".gitignore") { Get-Content ".gitignore" -Raw } else { "" }

if ($gitignoreContent -notmatch ".speckit-cache") {
    Add-Content -Path ".gitignore" -Value @"

# Spec-kit Phase 1-5 additions
.speckit-cache/
.speckit-analysis-cache.json
.speckit-progress.json
.speckit/memory/session-summary-*.md
.speckit.config.json
"@
    Write-ColorOutput "✓ .gitignore updated" "Green"
}
else {
    Write-ColorOutput "  .gitignore already contains spec-kit entries (skipped)" "Yellow"
}

Write-Host ""
Write-ColorOutput "Step 8: Creating sample config..." "Blue"

if (-not (Test-Path ".speckit.config.json")) {
    $configExampleSource = Join-Path $SourceDir ".speckit.config.json.example"
    if (Test-Path $configExampleSource) {
        Copy-Item $configExampleSource . -Force
        Write-ColorOutput "✓ Sample config created (.speckit.config.json.example)" "Green"
    }
}
else {
    Write-ColorOutput "  .speckit.config.json already exists (skipped)" "Yellow"
}

Write-Host ""
Write-ColorOutput "Step 9: Installing Git pre-commit hook..." "Blue"

if (Test-Path ".git") {
    $installHook = Read-Host "Install Git pre-commit hook? [y/N]"
    if ($installHook -match '^[Yy]$') {
        $hookDest = ".git\hooks\pre-commit"

        if (Test-Path $hookDest) {
            Write-ColorOutput "  Backing up existing pre-commit hook" "Yellow"
            Copy-Item $hookDest (Join-Path $BackupDir "pre-commit.old") -Force
        }

        # Copy hook (symlinks don't work well on Windows)
        Copy-Item "hooks\pre-commit" $hookDest -Force

        Write-ColorOutput "✓ Pre-commit hook installed" "Green"
        Write-ColorOutput "  Note: Requires Git Bash to execute" "Yellow"
    }
    else {
        Write-ColorOutput "  Skipped" "Yellow"
    }
}
else {
    Write-ColorOutput "  Not a git repository (skipped)" "Yellow"
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-ColorOutput "Migration Complete!" "Green"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""
Write-Host "New features available:"
Write-Host "  /speckit.budget              - Track token usage"
Write-Host "  /speckit.validate --all      - Validate all specs"
Write-Host "  /speckit.find `"query`"        - Semantic code search"
Write-Host "  /speckit.prune               - Compress session context"
Write-Host "  /speckit.error-context       - AI-assisted error debugging"
Write-Host "  /speckit.clarify-history     - View clarification decisions"
Write-Host ""
Write-Host "Enhanced features:"
Write-Host "  /speckit.project-analysis --diff-only      - 80-95% faster"
Write-Host "  /speckit.project-analysis --incremental    - 70-90% faster"
Write-Host "  /speckit.document                          - Now generates quick-ref.md"
Write-Host ""
Write-Host "Quick verification (PowerShell):"
Write-Host "  .\scripts\powershell\token-budget.ps1"
Write-Host "  .\scripts\powershell\validate-spec.ps1 -All"
Write-Host ""
Write-Host "Documentation:"
Write-Host "  cat PLATFORM-COMPATIBILITY.md    - Cross-platform usage guide"
Write-Host "  cat IMPROVED-WORKFLOW.md          - New workflow examples"
Write-Host ""
Write-Host "Backup location: $BackupDir"
Write-Host ""
Write-ColorOutput "Next steps:" "Blue"
Write-Host "  1. Test new features: .\scripts\powershell\token-budget.ps1"
Write-Host "  2. Validate your specs: .\scripts\powershell\validate-spec.ps1 -All"
Write-Host "  3. Review documentation: cat PLATFORM-COMPATIBILITY.md"
Write-Host "  4. Commit changes: git add -A; git commit -m 'Upgrade to improved spec-kit'"
Write-Host ""
Write-Host "Happy coding! 🚀"
