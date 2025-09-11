# Incrementally update agent context files based on new feature plan
# Supports: CLAUDE.md, GEMINI.md, and .github/copilot-instructions.md

[CmdletBinding()]
param(
  [Parameter(Position = 0)]
  [ValidateSet("claude", "gemini", "copilot", "")]
  [string]$AgentType = ""
)

# Source common functions
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path -Path $ScriptDir -ChildPath "common.ps1")

$paths = Get-FeaturePaths
$NewPlan = $paths.IMPL_PLAN

# Define agent context file paths
$ClaudeFile = Join-Path -Path $paths.REPO_ROOT -ChildPath "CLAUDE.md"
$GeminiFile = Join-Path -Path $paths.REPO_ROOT -ChildPath "GEMINI.md"
$CopilotFile = Join-Path -Path $paths.REPO_ROOT -ChildPath ".github/copilot-instructions.md"

if (-not (Test-Path -Path $NewPlan -PathType Leaf)) {
  Write-Error "ERROR: No plan.md found at $NewPlan"
  exit 1
}

Write-Host "=== Updating agent context files for feature $($paths.CURRENT_BRANCH) ==="

# Extract tech details from the new plan using regex
$planContent = Get-Content -Path $NewPlan -Raw
$NewLang = if ($planContent -match '^\*\*Language/Version\*\*: (.*)') { $matches[1].Trim() } else { "" }
$NewFramework = if ($planContent -match '^\*\*Primary Dependencies\*\*: (.*)') { $matches[1].Trim() } else { "" }
$NewTesting = if ($planContent -match '^\*\*Testing\*\*: (.*)') { $matches[1].Trim() } else { "" }
$NewDb = if ($planContent -match '^\*\*Storage\*\*: (.*)') { $matches[1].Trim() } else { "" }
$NewProjectType = if ($planContent -match '^\*\*Project Type\*\*: (.*)') { $matches[1].Trim() } else { "" }

# Function to update a single agent context file
function Update-AgentFile {
  param(
    [string]$TargetFile,
    [string]$AgentName
  )

  Write-Host "Updating $AgentName context file: $TargetFile"

  if (-not (Test-Path -Path $TargetFile -PathType Leaf)) {
    Write-Host "Creating new $AgentName context file..."
    $templatePath = Join-Path -Path $paths.REPO_ROOT -ChildPath "templates/agent-file-template.md"
    if (-not (Test-Path -Path $templatePath)) {
      Write-Error "ERROR: Template not found at $templatePath"
      return
    }
    $content = Get-Content -Path $templatePath -Raw
    $projectName = Split-Path -Path $paths.REPO_ROOT -Leaf
    $content = $content -replace '\[PROJECT NAME\]', $projectName
    $content = $content -replace '\[DATE\]', (Get-Date -Format "yyyy-MM-dd")
    $content = $content -replace '\[EXTRACTED FROM ALL PLAN.MD FILES\]', "- $NewLang + $NewFramework ($($paths.CURRENT_BRANCH))"
        
    $structure = if ($NewProjectType -like "*web*") { "backend/`nfrontend/`ntests/" } else { "src/`ntests/" }
    $content = $content -replace '\[ACTUAL STRUCTURE FROM PLANS\]', $structure

    $commands = switch -Wildcard ($NewLang) {
      "*Python*" { "cd src && pytest && ruff check ." }
      "*Rust*" { "cargo test && cargo clippy" }
      "*JavaScript*" { "npm test && npm run lint" }
      "*TypeScript*" { "npm test && npm run lint" }
      default { "# Add commands for $NewLang" }
    }
    $content = $content -replace '\[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES\]', $commands
    $content = $content -replace '\[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE\]', "${NewLang}: Follow standard conventions"
    $content = $content -replace '\[LAST 3 FEATURES AND WHAT THEY ADDED\]', "- $($paths.CURRENT_BRANCH): Added $NewLang + $NewFramework"
  }
  else {
    Write-Host "Updating existing $AgentName context file..."
    $content = Get-Content -Path $TargetFile -Raw

    # Update Active Technologies
    if ($NewLang -and $content -notmatch [regex]::Escape($NewLang)) {
      $content = $content -replace '(## Active Technologies\s*\n)', "`$1- $NewLang + $NewFramework ($($paths.CURRENT_BRANCH))`n"
    }
    if ($NewDb -and $NewDb -ne "N/A" -and $content -notmatch [regex]::Escape($NewDb)) {
      $content = $content -replace '(## Active Technologies\s*\n)', "`$1- $NewDb ($($paths.CURRENT_BRANCH))`n"
    }

    # Update Recent Changes (keep top 3)
    if ($content -match '(?sm)## Recent Changes\n(.*?)\n\n') {
      $existingChanges = $matches[1] -split '\r?\n'
      $newChange = "- $($paths.CURRENT_BRANCH): Added $NewLang + $NewFramework"
      $updatedChanges = ($newChange, $existingChanges)[0..2] -join "`n"
      $content = $content -replace "(?sm)(## Recent Changes\n).*?(\n\n)", "`$1$updatedChanges`$2"
    }

    # Update date
    $content = $content -replace 'Last updated: \d{4}-\d{2}-\d{2}', ('Last updated: ' + (Get-Date -Format 'yyyy-MM-dd'))
  }

  # Preserve manual additions
  $manualAdditions = ""
  if ($content -match '(?sm)<!-- MANUAL ADDITIONS START -->(.*?)<!-- MANUAL ADDITIONS END -->') {
    $manualAdditions = $matches[0]
    $content = $content -replace [regex]::Escape($manualAdditions), ""
  }
  if ($manualAdditions) {
    $content = $content.Trim() + "`n`n" + $manualAdditions
  }
    
  $content | Set-Content -Path $TargetFile
  Write-Host "✅ $AgentName context file updated successfully" -ForegroundColor Green
}

# Update files based on argument or detect existing files
switch ($AgentType) {
  "claude" { Update-AgentFile -TargetFile $ClaudeFile -AgentName "Claude Code" }
  "gemini" { Update-AgentFile -TargetFile $GeminiFile -AgentName "Gemini CLI" }
  "copilot" { Update-AgentFile -TargetFile $CopilotFile -AgentName "GitHub Copilot" }
  "" {
    $fileUpdated = $false
    if (Test-Path $ClaudeFile) { Update-AgentFile -TargetFile $ClaudeFile -AgentName "Claude Code"; $fileUpdated = $true }
    if (Test-Path $GeminiFile) { Update-AgentFile -TargetFile $GeminiFile -AgentName "Gemini CLI"; $fileUpdated = $true }
    if (Test-Path $CopilotFile) { Update-AgentFile -TargetFile $CopilotFile -AgentName "GitHub Copilot"; $fileUpdated = $true }
        
    if (-not $fileUpdated) {
      Write-Host "No agent context files found. Creating Claude Code context file by default."
      Update-AgentFile -TargetFile $ClaudeFile -AgentName "Claude Code"
    }
  }
  default {
    Write-Error "ERROR: Unknown agent type '$AgentType'. Use: claude, gemini, copilot, or leave empty for all."
    exit 1
  }
}

Write-Host ""
Write-Host "Summary of changes:"
if ($NewLang) { Write-Host "- Added language: $NewLang" }
if ($NewFramework) { Write-Host "- Added framework: $NewFramework" }
if ($NewDb -and $NewDb -ne "N/A") { Write-Host "- Added database: $NewDb" }
