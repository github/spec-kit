#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Setup Claude Code hooks and skills for the current project.

.DESCRIPTION
    This script detects the project type and generates appropriate
    hook configurations for Claude Code.

.PARAMETER Json
    Output in JSON format

.EXAMPLE
    ./setup-hooks.ps1 -Json
    # Detect project and output JSON

.EXAMPLE
    ./setup-hooks.ps1
    # Human-readable output
#>

param(
    [switch]$Json,
    [switch]$Help
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# Source common functions
. (Join-Path $PSScriptRoot 'common.ps1')

# Get repository root
$RepoRoot = Get-RepoRoot

# Initialize detection variables
$ProjectType = "generic"
$PackageManager = ""
$TestRunner = ""
$Linter = ""
$Formatter = ""
$DetectedTools = @()

# Detect project type and tools
function Detect-Project {
    # Node.js / TypeScript
    $packageJsonPath = Join-Path $RepoRoot "package.json"
    if (Test-Path $packageJsonPath) {
        $script:ProjectType = "node"
        $script:DetectedTools += "node"

        # Detect package manager
        if (Test-Path (Join-Path $RepoRoot "pnpm-lock.yaml")) {
            $script:PackageManager = "pnpm"
        } elseif (Test-Path (Join-Path $RepoRoot "yarn.lock")) {
            $script:PackageManager = "yarn"
        } elseif (Test-Path (Join-Path $RepoRoot "bun.lockb")) {
            $script:PackageManager = "bun"
        } else {
            $script:PackageManager = "npm"
        }
        $script:DetectedTools += $script:PackageManager

        # Check for TypeScript
        if (Test-Path (Join-Path $RepoRoot "tsconfig.json")) {
            $script:ProjectType = "node-typescript"
            $script:DetectedTools += "typescript"
        }

        # Read package.json for tool detection
        $packageJson = Get-Content $packageJsonPath -Raw

        # Detect test runner
        if ($packageJson -match '"jest"') {
            $script:TestRunner = "jest"
            $script:DetectedTools += "jest"
        } elseif ($packageJson -match '"vitest"') {
            $script:TestRunner = "vitest"
            $script:DetectedTools += "vitest"
        } elseif ($packageJson -match '"mocha"') {
            $script:TestRunner = "mocha"
            $script:DetectedTools += "mocha"
        }

        # Detect linter
        $eslintConfigs = @(".eslintrc.json", ".eslintrc.js", ".eslintrc.cjs", "eslint.config.js", "eslint.config.mjs")
        $hasEslintConfig = $eslintConfigs | Where-Object { Test-Path (Join-Path $RepoRoot $_) } | Select-Object -First 1
        if ($hasEslintConfig -or ($packageJson -match '"eslint"')) {
            $script:Linter = "eslint"
            $script:DetectedTools += "eslint"
        }

        # Detect formatter
        $prettierConfigs = @(".prettierrc", ".prettierrc.json", "prettier.config.js")
        $hasPrettierConfig = $prettierConfigs | Where-Object { Test-Path (Join-Path $RepoRoot $_) } | Select-Object -First 1
        if ($hasPrettierConfig -or ($packageJson -match '"prettier"')) {
            $script:Formatter = "prettier"
            $script:DetectedTools += "prettier"
        }
        return
    }

    # Python
    $pyprojectPath = Join-Path $RepoRoot "pyproject.toml"
    $requirementsPath = Join-Path $RepoRoot "requirements.txt"
    $setupPyPath = Join-Path $RepoRoot "setup.py"

    if ((Test-Path $pyprojectPath) -or (Test-Path $requirementsPath) -or (Test-Path $setupPyPath)) {
        $script:ProjectType = "python"
        $script:DetectedTools += "python"

        # Detect package manager
        if (Test-Path (Join-Path $RepoRoot "poetry.lock")) {
            $script:PackageManager = "poetry"
            $script:DetectedTools += "poetry"
        } elseif (Test-Path (Join-Path $RepoRoot "Pipfile.lock")) {
            $script:PackageManager = "pipenv"
            $script:DetectedTools += "pipenv"
        } elseif (Test-Path (Join-Path $RepoRoot "uv.lock")) {
            $script:PackageManager = "uv"
            $script:DetectedTools += "uv"
        } else {
            $script:PackageManager = "pip"
            $script:DetectedTools += "pip"
        }

        # Detect test runner and linter from pyproject.toml
        if (Test-Path $pyprojectPath) {
            $pyproject = Get-Content $pyprojectPath -Raw

            if ($pyproject -match "pytest") {
                $script:TestRunner = "pytest"
                $script:DetectedTools += "pytest"
            }
            if ($pyproject -match "ruff" -or (Test-Path (Join-Path $RepoRoot "ruff.toml"))) {
                $script:Linter = "ruff"
                $script:Formatter = "ruff"
                $script:DetectedTools += "ruff"
            }
            if ($pyproject -match "black") {
                $script:Formatter = "black"
                $script:DetectedTools += "black"
            }
            if ($pyproject -match "mypy") {
                $script:DetectedTools += "mypy"
            }
        }

        # Also check pytest.ini
        if (Test-Path (Join-Path $RepoRoot "pytest.ini")) {
            $script:TestRunner = "pytest"
            if ($script:DetectedTools -notcontains "pytest") {
                $script:DetectedTools += "pytest"
            }
        }
        return
    }

    # Rust
    if (Test-Path (Join-Path $RepoRoot "Cargo.toml")) {
        $script:ProjectType = "rust"
        $script:PackageManager = "cargo"
        $script:TestRunner = "cargo-test"
        $script:Linter = "clippy"
        $script:Formatter = "rustfmt"
        $script:DetectedTools = @("rust", "cargo", "clippy", "rustfmt")
        return
    }

    # Go
    if (Test-Path (Join-Path $RepoRoot "go.mod")) {
        $script:ProjectType = "go"
        $script:PackageManager = "go-mod"
        $script:TestRunner = "go-test"
        $script:Formatter = "gofmt"
        $script:Linter = "go-vet"
        $script:DetectedTools = @("go", "gofmt", "go-vet")

        # Check for golangci-lint
        if ((Test-Path (Join-Path $RepoRoot ".golangci.yml")) -or (Test-Path (Join-Path $RepoRoot ".golangci.yaml"))) {
            $script:Linter = "golangci-lint"
            $script:DetectedTools += "golangci-lint"
        }
        return
    }

    # Java (Maven)
    if (Test-Path (Join-Path $RepoRoot "pom.xml")) {
        $script:ProjectType = "java-maven"
        $script:PackageManager = "maven"
        $script:TestRunner = "maven-test"
        $script:DetectedTools = @("java", "maven")
        return
    }

    # Java (Gradle)
    if ((Test-Path (Join-Path $RepoRoot "build.gradle")) -or (Test-Path (Join-Path $RepoRoot "build.gradle.kts"))) {
        $script:ProjectType = "java-gradle"
        $script:PackageManager = "gradle"
        $script:TestRunner = "gradle-test"
        $script:DetectedTools = @("java", "gradle")
        return
    }

    # .NET
    $hasCsproj = Get-ChildItem -Path $RepoRoot -Filter "*.csproj" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1
    $hasSln = Get-ChildItem -Path $RepoRoot -Filter "*.sln" -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hasCsproj -or $hasSln) {
        $script:ProjectType = "dotnet"
        $script:PackageManager = "dotnet"
        $script:TestRunner = "dotnet-test"
        $script:DetectedTools = @("dotnet")
        return
    }

    # Ruby
    if (Test-Path (Join-Path $RepoRoot "Gemfile")) {
        $script:ProjectType = "ruby"
        $script:PackageManager = "bundler"
        $script:DetectedTools = @("ruby", "bundler")

        $gemfile = Get-Content (Join-Path $RepoRoot "Gemfile") -Raw
        if ($gemfile -match "rspec") {
            $script:TestRunner = "rspec"
            $script:DetectedTools += "rspec"
        }
        if ($gemfile -match "rubocop") {
            $script:Linter = "rubocop"
            $script:DetectedTools += "rubocop"
        }
        return
    }

    # PHP
    if (Test-Path (Join-Path $RepoRoot "composer.json")) {
        $script:ProjectType = "php"
        $script:PackageManager = "composer"
        $script:DetectedTools = @("php", "composer")

        $composer = Get-Content (Join-Path $RepoRoot "composer.json") -Raw
        if ($composer -match "phpunit") {
            $script:TestRunner = "phpunit"
            $script:DetectedTools += "phpunit"
        }
        return
    }
}

# Run detection
Detect-Project

# Define output paths
$ClaudeDir = Join-Path $RepoRoot ".claude"
$SettingsFile = Join-Path $ClaudeDir "settings.json"
$SkillsDir = Join-Path $ClaudeDir "skills"
$HooksDir = Join-Path $ClaudeDir "hooks"

# Check if .claude directory already exists
$ClaudeExists = Test-Path $ClaudeDir
$SettingsExists = Test-Path $SettingsFile

# Output results
if ($Json) {
    # Build JSON output
    $toolsJson = $DetectedTools | ConvertTo-Json -Compress
    if ($DetectedTools.Count -eq 0) {
        $toolsJson = "[]"
    } elseif ($DetectedTools.Count -eq 1) {
        $toolsJson = "[`"$($DetectedTools[0])`"]"
    }

    $output = @{
        PROJECT_TYPE = $ProjectType
        PACKAGE_MANAGER = $PackageManager
        TEST_RUNNER = $TestRunner
        LINTER = $Linter
        FORMATTER = $Formatter
        DETECTED_TOOLS = $DetectedTools
        REPO_ROOT = $RepoRoot
        CLAUDE_DIR = $ClaudeDir
        SETTINGS_FILE = $SettingsFile
        SKILLS_DIR = $SkillsDir
        HOOKS_DIR = $HooksDir
        CLAUDE_EXISTS = $ClaudeExists
        SETTINGS_EXISTS = $SettingsExists
    }

    $output | ConvertTo-Json -Depth 3
} else {
    Write-Output "=== Project Detection Results ==="
    Write-Output ""
    Write-Output "Project Type: $ProjectType"
    Write-Output "Package Manager: $(if ($PackageManager) { $PackageManager } else { 'none detected' })"
    Write-Output "Test Runner: $(if ($TestRunner) { $TestRunner } else { 'none detected' })"
    Write-Output "Linter: $(if ($Linter) { $Linter } else { 'none detected' })"
    Write-Output "Formatter: $(if ($Formatter) { $Formatter } else { 'none detected' })"
    Write-Output ""
    Write-Output "Detected Tools: $(if ($DetectedTools.Count -gt 0) { $DetectedTools -join ', ' } else { 'none' })"
    Write-Output ""
    Write-Output "=== Claude Code Paths ==="
    Write-Output "Claude Directory: $ClaudeDir (exists: $ClaudeExists)"
    Write-Output "Settings File: $SettingsFile (exists: $SettingsExists)"
    Write-Output "Skills Directory: $SkillsDir"
    Write-Output "Hooks Directory: $HooksDir"
}
