#!/usr/bin/env pwsh
# Generate project summary by analyzing existing codebase
[CmdletBinding()]
param(
	[switch]$Json,
	[switch]$Help
)
$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
	Write-Host "Usage: ./generate-project-summary.ps1 [-Json]"
	Write-Host ""
	Write-Host "Options:"
	Write-Host "  -Json    Output in JSON format"
	Write-Host "  -Help    Show this help message"
	exit 0
}

# Find repository root
function Find-RepositoryRoot {
	param(
		[string]$StartDir = $PWD,
		[string[]]$Markers = @('.git', '.specify')
	)
	$current = Resolve-Path $StartDir
	while ($true) {
		foreach ($marker in $Markers) {
			if (Test-Path (Join-Path $current $marker)) {
				return $current.Path
			}
		}
		$parent = Split-Path $current -Parent
		if ($parent -eq $current) {
			# Reached filesystem root without finding markers
			return $null
		}
		$current = $parent
	}
}

$repoRoot = Find-RepositoryRoot
if (-not $repoRoot) {
	Write-Error "Could not find repository root (no .git or .specify directory found)"
	exit 1
}

# Initialize arrays
$techFiles = @()
$directories = @()
$languages = @()

# Detect configuration files for different languages/frameworks
function Detect-ConfigFiles {
	param([string]$Root)

	$script:techFiles = @()
	$script:languages = @()

	# JavaScript/TypeScript
	if (Test-Path "$Root/package.json") {
		$script:techFiles += "package.json"
		$script:languages += "JavaScript/TypeScript"
	}
	if (Test-Path "$Root/tsconfig.json") { $script:techFiles += "tsconfig.json" }
	if (Test-Path "$Root/yarn.lock") { $script:techFiles += "yarn.lock" }
	if (Test-Path "$Root/pnpm-lock.yaml") { $script:techFiles += "pnpm-lock.yaml" }
	if (Test-Path "$Root/bun.lockb") { $script:techFiles += "bun.lockb" }

	# Python
	if (Test-Path "$Root/requirements.txt") {
		$script:techFiles += "requirements.txt"
		$script:languages += "Python"
	}
	if (Test-Path "$Root/pyproject.toml") {
		$script:techFiles += "pyproject.toml"
		$script:languages += "Python"
	}
	if (Test-Path "$Root/setup.py") {
		$script:techFiles += "setup.py"
		$script:languages += "Python"
	}
	if (Test-Path "$Root/Pipfile") {
		$script:techFiles += "Pipfile"
		$script:languages += "Python"
	}
	if (Test-Path "$Root/poetry.lock") { $script:techFiles += "poetry.lock" }

	# Go
	if (Test-Path "$Root/go.mod") {
		$script:techFiles += "go.mod"
		$script:languages += "Go"
	}
	if (Test-Path "$Root/go.sum") { $script:techFiles += "go.sum" }

	# Rust
	if (Test-Path "$Root/Cargo.toml") {
		$script:techFiles += "Cargo.toml"
		$script:languages += "Rust"
	}
	if (Test-Path "$Root/Cargo.lock") { $script:techFiles += "Cargo.lock" }

	# Java
	if (Test-Path "$Root/pom.xml") {
		$script:techFiles += "pom.xml"
		$script:languages += "Java"
	}
	if (Test-Path "$Root/build.gradle") {
		$script:techFiles += "build.gradle"
		$script:languages += "Java/Kotlin"
	}
	if (Test-Path "$Root/build.gradle.kts") {
		$script:techFiles += "build.gradle.kts"
		$script:languages += "Kotlin"
	}

	# Ruby
	if (Test-Path "$Root/Gemfile") {
		$script:techFiles += "Gemfile"
		$script:languages += "Ruby"
	}
	if (Test-Path "$Root/Gemfile.lock") { $script:techFiles += "Gemfile.lock" }

	# PHP
	if (Test-Path "$Root/composer.json") {
		$script:techFiles += "composer.json"
		$script:languages += "PHP"
	}
	if (Test-Path "$Root/composer.lock") { $script:techFiles += "composer.lock" }

	# C#/.NET
	$csprojFiles = Get-ChildItem -Path $Root -Filter "*.csproj" -File -Depth 2 -ErrorAction SilentlyContinue
	$fsprojFiles = Get-ChildItem -Path $Root -Filter "*.fsproj" -File -Depth 2 -ErrorAction SilentlyContinue
	$vbprojFiles = Get-ChildItem -Path $Root -Filter "*.vbproj" -File -Depth 2 -ErrorAction SilentlyContinue

	if ($csprojFiles -or $fsprojFiles -or $vbprojFiles) {
		foreach ($proj in ($csprojFiles + $fsprojFiles + $vbprojFiles)) {
			$script:techFiles += $proj.Name
		}
		$script:languages += "C#/.NET"
	}

	# Swift
	if (Test-Path "$Root/Package.swift") {
		$script:techFiles += "Package.swift"
		$script:languages += "Swift"
	}

	# Elixir
	if (Test-Path "$Root/mix.exs") {
		$script:techFiles += "mix.exs"
		$script:languages += "Elixir"
	}

	# C/C++
	if (Test-Path "$Root/CMakeLists.txt") {
		$script:techFiles += "CMakeLists.txt"
		$script:languages += "C/C++"
	}
	if (Test-Path "$Root/Makefile") { $script:techFiles += "Makefile" }

	# Code style/config files
	if (Test-Path "$Root/.editorconfig") { $script:techFiles += ".editorconfig" }
	if (Test-Path "$Root/.prettierrc") { $script:techFiles += ".prettierrc" }
	if (Test-Path "$Root/.prettierrc.json") { $script:techFiles += ".prettierrc.json" }
	if (Test-Path "$Root/.eslintrc") { $script:techFiles += ".eslintrc" }
	if (Test-Path "$Root/.eslintrc.json") { $script:techFiles += ".eslintrc.json" }
	if (Test-Path "$Root/rustfmt.toml") { $script:techFiles += "rustfmt.toml" }
}

# Detect key directories
function Detect-Directories {
	param([string]$Root)

	$script:directories = @()

	# Source directories
	if (Test-Path "$Root/src") { $script:directories += "src" }
	if (Test-Path "$Root/lib") { $script:directories += "lib" }
	if (Test-Path "$Root/app") { $script:directories += "app" }
	if (Test-Path "$Root/pkg") { $script:directories += "pkg" }
	if (Test-Path "$Root/internal") { $script:directories += "internal" }
	if (Test-Path "$Root/cmd") { $script:directories += "cmd" }

	# Test directories
	if (Test-Path "$Root/test") { $script:directories += "test" }
	if (Test-Path "$Root/tests") { $script:directories += "tests" }
	if (Test-Path "$Root/__tests__") { $script:directories += "__tests__" }
	if (Test-Path "$Root/spec") { $script:directories += "spec" }

	# Documentation
	if (Test-Path "$Root/docs") { $script:directories += "docs" }
	if (Test-Path "$Root/documentation") { $script:directories += "documentation" }

	# Configuration
	if (Test-Path "$Root/config") { $script:directories += "config" }
	if (Test-Path "$Root/conf") { $script:directories += "conf" }
	if (Test-Path "$Root/settings") { $script:directories += "settings" }

	# Frontend/Backend split
	if (Test-Path "$Root/frontend") { $script:directories += "frontend" }
	if (Test-Path "$Root/client") { $script:directories += "client" }
	if (Test-Path "$Root/web") { $script:directories += "web" }
	if (Test-Path "$Root/backend") { $script:directories += "backend" }
	if (Test-Path "$Root/server") { $script:directories += "server" }
	if (Test-Path "$Root/api") { $script:directories += "api" }

	# Database
	if (Test-Path "$Root/migrations") { $script:directories += "migrations" }
	if (Test-Path "$Root/models") { $script:directories += "models" }
	if (Test-Path "$Root/schemas") { $script:directories += "schemas" }

	# Monorepo
	if (Test-Path "$Root/packages") { $script:directories += "packages" }
	if (Test-Path "$Root/apps") { $script:directories += "apps" }
	if (Test-Path "$Root/services") { $script:directories += "services" }

	# Public/Static
	if (Test-Path "$Root/public") { $script:directories += "public" }
	if (Test-Path "$Root/static") { $script:directories += "static" }
	if (Test-Path "$Root/assets") { $script:directories += "assets" }

	# Build/Dist
	if (Test-Path "$Root/build") { $script:directories += "build" }
	if (Test-Path "$Root/dist") { $script:directories += "dist" }
	if (Test-Path "$Root/target") { $script:directories += "target" }
}

# Detect project type
function Detect-ProjectType {
	param([string]$Root)

	$type = "unknown"

	# Monorepo indicators
	if ((Test-Path "$Root/packages") -or (Test-Path "$Root/apps") -or (Test-Path "$Root/services")) {
		$type = "monorepo"
	}
	# Frontend + Backend split
	elseif ((Test-Path "$Root/frontend") -and (Test-Path "$Root/backend")) {
		$type = "fullstack-split"
	}
	elseif ((Test-Path "$Root/client") -and (Test-Path "$Root/server")) {
		$type = "fullstack-split"
	}
	# Web application
	elseif ((Test-Path "$Root/package.json") -and
			(Select-String -Path "$Root/package.json" -Pattern "react|vue|angular|svelte|next|nuxt" -Quiet)) {
		$type = "web-frontend"
	}
	# API/Backend
	elseif ((Test-Path "$Root/api") -or (Test-Path "$Root/server")) {
		$type = "backend-api"
	}
	# CLI tool
	elseif ((Test-Path "$Root/cmd") -or
			((Test-Path "$Root/package.json") -and (Select-String -Path "$Root/package.json" -Pattern "`"bin`":" -Quiet))) {
		$type = "cli-tool"
	}
	# Library
	elseif ((Test-Path "$Root/lib") -or
			((Test-Path "$Root/Cargo.toml") -and (Select-String -Path "$Root/Cargo.toml" -Pattern "\[lib\]" -Quiet))) {
		$type = "library"
	}
	# Generic application
	elseif (Test-Path "$Root/src") {
		$type = "application"
	}

	return $type
}

# Run detection
Detect-ConfigFiles $repoRoot
Detect-Directories $repoRoot
$projectType = Detect-ProjectType $repoRoot

# Deduplicate languages
$uniqueLanguages = $languages | Select-Object -Unique

# Output
if ($Json) {
	$result = @{
		REPO_ROOT = $repoRoot
		PROJECT_TYPE = $projectType
		TECH_FILES = $techFiles
		DIRECTORIES = $directories
		LANGUAGES = $uniqueLanguages
	}
	$result | ConvertTo-Json -Compress
} else {
	Write-Host "Repository Root: $repoRoot"
	Write-Host "Project Type: $projectType"
	Write-Host ""
	Write-Host "Languages:"
	foreach ($lang in $uniqueLanguages) {
		Write-Host "  - $lang"
	}
	Write-Host ""
	Write-Host "Configuration Files:"
	foreach ($file in $techFiles) {
		Write-Host "  - $file"
	}
	Write-Host ""
	Write-Host "Key Directories:"
	foreach ($dir in $directories) {
		Write-Host "  - $dir"
	}
}