#!/usr/bin/env pwsh

# Project Analysis Script (PowerShell)
#
# This script performs comprehensive project analysis against all SpecKit specifications
# to verify whether the project meets defined expectations.
#
# It also supports Universal Adoption features: discovering existing projects in any codebase.
#
# Usage: ./project-analysis.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -CheckPatterns      Enable code pattern analysis (Security, DRY, KISS, SOLID)
#   -Discover           Discover all projects in repository (Universal Adoption)
#   -DeepAnalysis       Parse dependency files for detailed technology info (Phase 2)
#   -Cached             Use cached discovery results (0 tokens!)
#   -Force              Force rescan, ignore cache
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$CheckPatterns,
    [switch]$Discover,
    [switch]$DeepAnalysis,
    [switch]$Cached,
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: project-analysis.ps1 [OPTIONS]

Perform comprehensive project analysis against all SpecKit specifications.

OPTIONS:
  -Json               Output in JSON format
  -CheckPatterns      Enable code pattern analysis (Security, DRY, KISS, SOLID)
  -Discover           Discover all projects in repository (Universal Adoption)
  -DeepAnalysis       Parse dependency files for detailed technology info (Phase 2)
  -Cached             Use cached discovery results (0 tokens!)
  -Force              Force rescan, ignore cache
  -Help, -h           Show this help message

EXAMPLES:
  # Basic project analysis (existing specs)
  .\project-analysis.ps1 -Json

  # Analysis with pattern checking
  .\project-analysis.ps1 -Json -CheckPatterns

  # Discover all projects (Universal Adoption - Phase 1)
  .\project-analysis.ps1 -Discover -Json

  # Discover with deep analysis (Phase 2: frameworks, versions, dependencies)
  .\project-analysis.ps1 -Discover -DeepAnalysis -Json

  # Use cached discovery (0 tokens!)
  .\project-analysis.ps1 -Discover -Cached -Json

  # Force rescan with deep analysis
  .\project-analysis.ps1 -Discover -DeepAnalysis -Force -Json

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get repository root
$repoRoot = Get-RepoRoot

#region Universal Adoption - Project Discovery Functions

function Get-ProjectIndicators {
    <#
    .SYNOPSIS
    Returns list of file indicators for different project types
    #>
    return @(
        @{ Pattern = "package.json"; Type = "nodejs"; Priority = 1 }
        @{ Pattern = "requirements.txt"; Type = "python"; Priority = 1 }
        @{ Pattern = "pyproject.toml"; Type = "python"; Priority = 1 }
        @{ Pattern = "go.mod"; Type = "go"; Priority = 1 }
        @{ Pattern = "Cargo.toml"; Type = "rust"; Priority = 1 }
        @{ Pattern = "pom.xml"; Type = "java"; Priority = 1 }
        @{ Pattern = "build.gradle"; Type = "java"; Priority = 1 }
        @{ Pattern = "*.csproj"; Type = "csharp"; Priority = 1 }
        @{ Pattern = "*.sln"; Type = "csharp"; Priority = 2 }
        @{ Pattern = "Gemfile"; Type = "ruby"; Priority = 1 }
        @{ Pattern = "composer.json"; Type = "php"; Priority = 1 }
        @{ Pattern = "CMakeLists.txt"; Type = "cpp"; Priority = 1 }
    )
}

function Get-ExcludedDirectories {
    <#
    .SYNOPSIS
    Returns list of directories to exclude from discovery
    #>
    return @(
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        ".git",
        "build",
        "dist",
        "target",
        "__pycache__",
        ".next",
        ".nuxt",
        "bin",
        "obj",
        "packages",
        ".speckit"
    )
}

#endregion

#region Phase 2 - Deep Technology Detection

function Get-NodeJsDetails {
    param([string]$ProjectPath)

    <#
    .SYNOPSIS
    Parse package.json to extract framework, dependencies, build tools
    Token Budget: ~300-500 tokens (selective parsing)
    #>

    $pkgJsonPath = Join-Path $ProjectPath "package.json"
    if (-not (Test-Path $pkgJsonPath)) {
        return $null
    }

    try {
        $pkg = Get-Content $pkgJsonPath -Raw | ConvertFrom-Json

        $details = @{
            language = "javascript"
            framework = $null
            framework_version = $null
            runtime = "nodejs"
            runtime_version = $pkg.engines.node
            build_tools = @()
            test_frameworks = @()
            key_dependencies = @()
        }

        # Detect framework from dependencies
        if ($pkg.dependencies) {
            if ($pkg.dependencies.express) {
                $details.framework = "Express"
                $details.framework_version = $pkg.dependencies.express
            } elseif ($pkg.dependencies.fastify) {
                $details.framework = "Fastify"
                $details.framework_version = $pkg.dependencies.fastify
            } elseif ($pkg.dependencies.'@nestjs/core') {
                $details.framework = "NestJS"
                $details.framework_version = $pkg.dependencies.'@nestjs/core'
            } elseif ($pkg.dependencies.koa) {
                $details.framework = "Koa"
                $details.framework_version = $pkg.dependencies.koa
            } elseif ($pkg.dependencies.react) {
                $details.framework = "React"
                $details.framework_version = $pkg.dependencies.react
            } elseif ($pkg.dependencies.vue) {
                $details.framework = "Vue"
                $details.framework_version = $pkg.dependencies.vue
            } elseif ($pkg.dependencies.angular) {
                $details.framework = "Angular"
                $details.framework_version = $pkg.dependencies.angular
            } elseif ($pkg.dependencies.svelte) {
                $details.framework = "Svelte"
                $details.framework_version = $pkg.dependencies.svelte
            } elseif ($pkg.dependencies.next) {
                $details.framework = "Next.js"
                $details.framework_version = $pkg.dependencies.next
            } elseif ($pkg.dependencies.nuxt) {
                $details.framework = "Nuxt"
                $details.framework_version = $pkg.dependencies.nuxt
            }
        }

        # Detect build tools from devDependencies
        if ($pkg.devDependencies) {
            if ($pkg.devDependencies.webpack) { $details.build_tools += "webpack" }
            if ($pkg.devDependencies.vite) { $details.build_tools += "vite" }
            if ($pkg.devDependencies.rollup) { $details.build_tools += "rollup" }
            if ($pkg.devDependencies.esbuild) { $details.build_tools += "esbuild" }
            if ($pkg.devDependencies.parcel) { $details.build_tools += "parcel" }
            if ($pkg.devDependencies.typescript) { $details.build_tools += "typescript" }
        }

        # Detect test frameworks
        if ($pkg.devDependencies) {
            if ($pkg.devDependencies.jest) { $details.test_frameworks += "jest" }
            if ($pkg.devDependencies.mocha) { $details.test_frameworks += "mocha" }
            if ($pkg.devDependencies.vitest) { $details.test_frameworks += "vitest" }
            if ($pkg.devDependencies.cypress) { $details.test_frameworks += "cypress" }
            if ($pkg.devDependencies.playwright) { $details.test_frameworks += "playwright" }
        }

        # Extract key dependencies (limit to top 5)
        if ($pkg.dependencies) {
            $deps = $pkg.dependencies.PSObject.Properties.Name | Select-Object -First 5
            $details.key_dependencies = $deps
        }

        return $details
    } catch {
        Write-Verbose "Failed to parse package.json: $_"
        return $null
    }
}

function Get-PythonDetails {
    param([string]$ProjectPath)

    <#
    .SYNOPSIS
    Parse requirements.txt or pyproject.toml to extract framework
    Token Budget: ~200-400 tokens
    #>

    $details = @{
        language = "python"
        framework = $null
        framework_version = $null
        runtime = "python"
        runtime_version = $null
        build_tools = @()
        test_frameworks = @()
        key_dependencies = @()
    }

    # Try pyproject.toml first
    $pyprojectPath = Join-Path $ProjectPath "pyproject.toml"
    if (Test-Path $pyprojectPath) {
        try {
            $content = Get-Content $pyprojectPath -Raw

            # Detect framework
            if ($content -match 'fastapi') {
                $details.framework = "FastAPI"
                if ($content -match 'fastapi[>=~]+([0-9.]+)') {
                    $details.framework_version = $matches[1]
                }
            } elseif ($content -match 'django') {
                $details.framework = "Django"
                if ($content -match 'django[>=~]+([0-9.]+)') {
                    $details.framework_version = $matches[1]
                }
            } elseif ($content -match 'flask') {
                $details.framework = "Flask"
                if ($content -match 'flask[>=~]+([0-9.]+)') {
                    $details.framework_version = $matches[1]
                }
            }

            # Detect build tools
            if ($content -match 'poetry') { $details.build_tools += "poetry" }
            if ($content -match 'setuptools') { $details.build_tools += "setuptools" }

            # Detect test frameworks
            if ($content -match 'pytest') { $details.test_frameworks += "pytest" }

            return $details
        } catch {
            Write-Verbose "Failed to parse pyproject.toml: $_"
        }
    }

    # Fallback to requirements.txt
    $reqPath = Join-Path $ProjectPath "requirements.txt"
    if (Test-Path $reqPath) {
        try {
            $lines = Get-Content $reqPath | Select-Object -First 20

            foreach ($line in $lines) {
                $line = $line.Trim()
                if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
                    continue
                }

                # Detect framework
                if ($line -match '^fastapi') {
                    $details.framework = "FastAPI"
                    if ($line -match 'fastapi[>=~]+([0-9.]+)') {
                        $details.framework_version = $matches[1]
                    }
                } elseif ($line -match '^django') {
                    $details.framework = "Django"
                    if ($line -match 'django[>=~]+([0-9.]+)') {
                        $details.framework_version = $matches[1]
                    }
                } elseif ($line -match '^flask') {
                    $details.framework = "Flask"
                    if ($line -match 'flask[>=~]+([0-9.]+)') {
                        $details.framework_version = $matches[1]
                    }
                }

                # Collect key dependencies
                $pkg = $line -split '[>=~<]' | Select-Object -First 1
                if ($details.key_dependencies.Count -lt 5) {
                    $details.key_dependencies += $pkg
                }
            }

            # Detect test frameworks
            if ($lines -match 'pytest') { $details.test_frameworks += "pytest" }

            return $details
        } catch {
            Write-Verbose "Failed to parse requirements.txt: $_"
        }
    }

    return $details
}

function Get-GoDetails {
    param([string]$ProjectPath)

    <#
    .SYNOPSIS
    Parse go.mod to extract framework
    Token Budget: ~200-300 tokens
    #>

    $goModPath = Join-Path $ProjectPath "go.mod"
    if (-not (Test-Path $goModPath)) {
        return $null
    }

    try {
        $content = Get-Content $goModPath -Raw

        $details = @{
            language = "go"
            framework = $null
            framework_version = $null
            runtime = "go"
            runtime_version = $null
            build_tools = @("go")
            test_frameworks = @("go test")
            key_dependencies = @()
        }

        # Extract Go version
        if ($content -match 'go ([0-9.]+)') {
            $details.runtime_version = $matches[1]
        }

        # Detect framework
        if ($content -match 'github.com/gin-gonic/gin') {
            $details.framework = "Gin"
            if ($content -match 'github.com/gin-gonic/gin v([0-9.]+)') {
                $details.framework_version = $matches[1]
            }
        } elseif ($content -match 'github.com/labstack/echo') {
            $details.framework = "Echo"
            if ($content -match 'github.com/labstack/echo/v4 v([0-9.]+)') {
                $details.framework_version = $matches[1]
            }
        } elseif ($content -match 'github.com/gofiber/fiber') {
            $details.framework = "Fiber"
            if ($content -match 'github.com/gofiber/fiber/v2 v([0-9.]+)') {
                $details.framework_version = $matches[1]
            }
        } elseif ($content -match 'github.com/go-chi/chi') {
            $details.framework = "Chi"
        }

        # Extract key dependencies
        $deps = [regex]::Matches($content, 'require \(([\s\S]*?)\)') `
            | ForEach-Object { $_.Groups[1].Value } `
            | ForEach-Object { $_ -split "`n" } `
            | Where-Object { $_ -match '^\s*github.com' } `
            | ForEach-Object { ($_ -split ' ')[0].Trim() } `
            | Select-Object -First 5

        $details.key_dependencies = $deps

        return $details
    } catch {
        Write-Verbose "Failed to parse go.mod: $_"
        return $null
    }
}

function Get-RustDetails {
    param([string]$ProjectPath)

    <#
    .SYNOPSIS
    Parse Cargo.toml to extract framework
    Token Budget: ~200-300 tokens
    #>

    $cargoPath = Join-Path $ProjectPath "Cargo.toml"
    if (-not (Test-Path $cargoPath)) {
        return $null
    }

    try {
        $content = Get-Content $cargoPath -Raw

        $details = @{
            language = "rust"
            framework = $null
            framework_version = $null
            runtime = "rust"
            runtime_version = $null
            build_tools = @("cargo")
            test_frameworks = @("cargo test")
            key_dependencies = @()
        }

        # Detect framework
        if ($content -match 'actix-web') {
            $details.framework = "Actix Web"
            if ($content -match 'actix-web = "([0-9.]+)"') {
                $details.framework_version = $matches[1]
            }
        } elseif ($content -match 'rocket') {
            $details.framework = "Rocket"
            if ($content -match 'rocket = "([0-9.]+)"') {
                $details.framework_version = $matches[1]
            }
        } elseif ($content -match 'axum') {
            $details.framework = "Axum"
            if ($content -match 'axum = "([0-9.]+)"') {
                $details.framework_version = $matches[1]
            }
        }

        # Extract dependencies
        if ($content -match '\[dependencies\]([\s\S]*?)(\[|$)') {
            $depsSection = $matches[1]
            $deps = [regex]::Matches($depsSection, '^([a-zA-Z0-9_-]+) =', [System.Text.RegularExpressions.RegexOptions]::Multiline) `
                | ForEach-Object { $_.Groups[1].Value } `
                | Select-Object -First 5
            $details.key_dependencies = $deps
        }

        return $details
    } catch {
        Write-Verbose "Failed to parse Cargo.toml: $_"
        return $null
    }
}

function Get-JavaDetails {
    param([string]$ProjectPath)

    <#
    .SYNOPSIS
    Parse pom.xml or build.gradle to extract framework
    Token Budget: ~300-400 tokens
    #>

    $details = @{
        language = "java"
        framework = $null
        framework_version = $null
        runtime = "java"
        runtime_version = $null
        build_tools = @()
        test_frameworks = @()
        key_dependencies = @()
    }

    # Try pom.xml (Maven)
    $pomPath = Join-Path $ProjectPath "pom.xml"
    if (Test-Path $pomPath) {
        $details.build_tools += "maven"

        try {
            $content = Get-Content $pomPath -Raw

            # Detect Spring Boot
            if ($content -match 'spring-boot-starter') {
                $details.framework = "Spring Boot"
                if ($content -match '<spring-boot.version>([0-9.]+)</spring-boot.version>') {
                    $details.framework_version = $matches[1]
                }
            }

            # Detect test framework
            if ($content -match 'junit') { $details.test_frameworks += "junit" }

            return $details
        } catch {
            Write-Verbose "Failed to parse pom.xml: $_"
        }
    }

    # Try build.gradle (Gradle)
    $gradlePath = Join-Path $ProjectPath "build.gradle"
    if (Test-Path $gradlePath) {
        $details.build_tools += "gradle"

        try {
            $content = Get-Content $gradlePath -Raw

            # Detect Spring Boot
            if ($content -match 'spring-boot') {
                $details.framework = "Spring Boot"
                if ($content -match "springBootVersion = '([0-9.]+)'") {
                    $details.framework_version = $matches[1]
                }
            }

            # Detect test framework
            if ($content -match 'junit') { $details.test_frameworks += "junit" }

            return $details
        } catch {
            Write-Verbose "Failed to parse build.gradle: $_"
        }
    }

    return $details
}

function Get-CSharpDetails {
    param([string]$ProjectPath)

    <#
    .SYNOPSIS
    Parse *.csproj to extract framework
    Token Budget: ~200-300 tokens
    #>

    $csprojFiles = Get-ChildItem -Path $ProjectPath -Filter "*.csproj" -ErrorAction SilentlyContinue
    if (-not $csprojFiles) {
        return $null
    }

    $csprojPath = $csprojFiles[0].FullName

    try {
        $content = Get-Content $csprojPath -Raw

        $details = @{
            language = "csharp"
            framework = $null
            framework_version = $null
            runtime = "dotnet"
            runtime_version = $null
            build_tools = @("msbuild", "dotnet")
            test_frameworks = @()
            key_dependencies = @()
        }

        # Extract target framework
        if ($content -match '<TargetFramework>([^<]+)</TargetFramework>') {
            $details.runtime_version = $matches[1]
        }

        # Detect ASP.NET Core
        if ($content -match 'Microsoft.AspNetCore') {
            $details.framework = "ASP.NET Core"
            if ($content -match 'Microsoft.AspNetCore.App.*Version="([0-9.]+)"') {
                $details.framework_version = $matches[1]
            }
        }

        # Detect test frameworks
        if ($content -match 'xunit') { $details.test_frameworks += "xunit" }
        if ($content -match 'NUnit') { $details.test_frameworks += "nunit" }
        if ($content -match 'MSTest') { $details.test_frameworks += "mstest" }

        # Extract package references
        $pkgs = [regex]::Matches($content, '<PackageReference Include="([^"]+)"') `
            | ForEach-Object { $_.Groups[1].Value } `
            | Select-Object -First 5
        $details.key_dependencies = $pkgs

        return $details
    } catch {
        Write-Verbose "Failed to parse *.csproj: $_"
        return $null
    }
}

#endregion

#region Phase 1 - Project Discovery (continued)

function Test-PathExcluded {
    param(
        [string]$Path,
        [string[]]$ExcludePatterns
    )

    foreach ($pattern in $ExcludePatterns) {
        if ($Path -match [regex]::Escape($pattern)) {
            return $true
        }
    }
    return $false
}

function Get-CacheHash {
    param([string]$RepoRoot)

    <#
    .SYNOPSIS
    Compute hash of indicator files for cache invalidation
    #>

    $indicators = Get-ProjectIndicators
    $excludePatterns = Get-ExcludedDirectories

    $allFiles = @()
    foreach ($indicator in $indicators) {
        $found = Get-ChildItem -Path $RepoRoot -Filter $indicator.Pattern -Recurse -File -ErrorAction SilentlyContinue `
            | Where-Object { -not (Test-PathExcluded -Path $_.FullName -ExcludePatterns $excludePatterns) } `
            | Select-Object -ExpandProperty FullName

        $allFiles += $found
    }

    if ($allFiles.Count -eq 0) {
        return "empty"
    }

    # Sort and join for consistent hashing
    $hashInput = ($allFiles | Sort-Object) -join "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($hashInput)
    $stream = [System.IO.MemoryStream]::new($bytes)
    $hash = Get-FileHash -InputStream $stream -Algorithm MD5
    $stream.Dispose()

    return $hash.Hash
}

function Get-CachedDiscovery {
    param(
        [string]$RepoRoot,
        [bool]$ForceRescan
    )

    <#
    .SYNOPSIS
    Load cached discovery results if valid
    #>

    $cacheFile = Join-Path $RepoRoot ".speckit" "cache" "discovery.json"

    if ($ForceRescan) {
        Write-Verbose "Force rescan requested, ignoring cache"
        return $null
    }

    if (-not (Test-Path $cacheFile)) {
        Write-Verbose "No cache file found"
        return $null
    }

    try {
        $cached = Get-Content $cacheFile -Raw | ConvertFrom-Json

        # Validate cache hash
        $currentHash = Get-CacheHash -RepoRoot $RepoRoot
        if ($cached.cache_hash -eq $currentHash) {
            Write-Host "✓ Using cached discovery (0 tokens!)" -ForegroundColor Green
            Write-Verbose "Cache hit! Last scan: $($cached.scanned_at)"
            return $cached
        } else {
            Write-Verbose "Cache invalid (file structure changed)"
            return $null
        }
    } catch {
        Write-Verbose "Failed to load cache: $_"
        return $null
    }
}

function Save-DiscoveryCache {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Discovery
    )

    <#
    .SYNOPSIS
    Save discovery results to cache
    #>

    $cacheDir = Join-Path $RepoRoot ".speckit" "cache"
    $cacheFile = Join-Path $cacheDir "discovery.json"

    # Create cache directory if it doesn't exist
    if (-not (Test-Path $cacheDir)) {
        New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null
    }

    # Save cache
    $Discovery | ConvertTo-Json -Depth 10 | Out-File $cacheFile -Encoding UTF8

    Write-Verbose "Discovery cached to: $cacheFile"
}

function Find-Projects {
    param(
        [string]$RepoRoot,
        [bool]$DeepAnalysis = $false
    )

    <#
    .SYNOPSIS
    Discover all projects in repository (metadata-only by default)
    Phase 2: When DeepAnalysis=true, parse dependency files for framework details
    #>

    Write-Verbose "Scanning repository: $RepoRoot"

    $indicators = Get-ProjectIndicators
    $excludePatterns = Get-ExcludedDirectories
    $projects = @()
    $projectDirs = @{}  # Track unique project directories

    foreach ($indicator in $indicators) {
        Write-Verbose "Searching for: $($indicator.Pattern)"

        $found = Get-ChildItem -Path $RepoRoot -Filter $indicator.Pattern -Recurse -File -ErrorAction SilentlyContinue `
            | Where-Object {
                $path = $_.FullName
                $excluded = Test-PathExcluded -Path $path -ExcludePatterns $excludePatterns
                -not $excluded
            }

        foreach ($file in $found) {
            $projectPath = $file.DirectoryName
            $relativePath = $projectPath.Replace($RepoRoot, "").TrimStart('\', '/')

            # Generate project ID (normalize path)
            $projectId = $relativePath -replace '[\\/]', '-' -replace '^-', '' -replace '-$', ''
            if ([string]::IsNullOrWhiteSpace($projectId)) {
                $projectId = "root"
            }

            # Check if we've already found this project
            if ($projectDirs.ContainsKey($projectPath)) {
                # Update if this indicator has higher priority
                $existing = $projectDirs[$projectPath]
                if ($indicator.Priority -lt $existing.Priority) {
                    $projectDirs[$projectPath] = @{
                        Type = $indicator.Type
                        Indicator = $file.Name
                        Priority = $indicator.Priority
                    }
                }
            } else {
                $projectDirs[$projectPath] = @{
                    Type = $indicator.Type
                    Indicator = $file.Name
                    Priority = $indicator.Priority
                }
            }
        }
    }

    # Convert to project objects
    foreach ($projectPath in $projectDirs.Keys) {
        $info = $projectDirs[$projectPath]
        $relativePath = $projectPath.Replace($RepoRoot, "").TrimStart('\', '/')

        # Generate project ID
        $projectId = $relativePath -replace '[\\/]', '-' -replace '^-', '' -replace '-$', ''
        if ([string]::IsNullOrWhiteSpace($projectId)) {
            $projectId = "root"
        }

        # Generate project name (from directory name)
        $projectName = Split-Path $projectPath -Leaf
        if ([string]::IsNullOrWhiteSpace($projectName)) {
            $projectName = "Root Project"
        }

        # Get project metadata (size, file count)
        $files = Get-ChildItem -Path $projectPath -Recurse -File -ErrorAction SilentlyContinue `
            | Where-Object {
                -not (Test-PathExcluded -Path $_.FullName -ExcludePatterns $excludePatterns)
            }

        $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
        $fileCount = $files.Count

        # Get last modified time
        $lastModified = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
        if (-not $lastModified) {
            $lastModified = Get-Date
        }

        # Classify project type (basic heuristic)
        $projectType = "unknown"
        if (Test-Path (Join-Path $projectPath "src" "components")) {
            $projectType = "frontend"
        } elseif (Test-Path (Join-Path $projectPath "api")) {
            $projectType = "backend-api"
        } elseif (Test-Path (Join-Path $projectPath "cmd")) {
            $projectType = "cli"
        } elseif ($info.Indicator -match "\.sln$|\.csproj$") {
            if (Test-Path (Join-Path $projectPath "Controllers")) {
                $projectType = "backend-api"
            }
        } elseif ($projectPath -match "service") {
            $projectType = "backend-api"
        } else {
            # Default based on indicator type
            switch ($info.Type) {
                "nodejs" { $projectType = "unknown" }  # Could be frontend or backend
                "python" { $projectType = "backend-api" }
                "go" { $projectType = "backend-api" }
                "rust" { $projectType = "cli" }
                "csharp" { $projectType = "backend-api" }
                default { $projectType = "unknown" }
            }
        }

        # Phase 2: Deep Analysis (optional)
        $techDetails = $null
        if ($DeepAnalysis) {
            Write-Verbose "Performing deep analysis for: $projectName"

            switch ($info.Type) {
                "nodejs" { $techDetails = Get-NodeJsDetails -ProjectPath $projectPath }
                "python" { $techDetails = Get-PythonDetails -ProjectPath $projectPath }
                "go" { $techDetails = Get-GoDetails -ProjectPath $projectPath }
                "rust" { $techDetails = Get-RustDetails -ProjectPath $projectPath }
                "java" { $techDetails = Get-JavaDetails -ProjectPath $projectPath }
                "csharp" { $techDetails = Get-CSharpDetails -ProjectPath $projectPath }
                default { $techDetails = $null }
            }
        }

        # Build project object
        $projectObj = [PSCustomObject]@{
            id = $projectId
            name = $projectName
            path = $relativePath
            abs_path = $projectPath
            type = $projectType
            technology = $info.Type
            indicator_file = $info.Indicator
            size_bytes = $totalSize
            file_count = $fileCount
            last_modified = $lastModified.ToString("o")
        }

        # Add deep analysis details if available
        if ($techDetails) {
            $projectObj | Add-Member -NotePropertyName "framework" -NotePropertyValue $techDetails.framework
            $projectObj | Add-Member -NotePropertyName "framework_version" -NotePropertyValue $techDetails.framework_version
            $projectObj | Add-Member -NotePropertyName "runtime" -NotePropertyValue $techDetails.runtime
            $projectObj | Add-Member -NotePropertyName "runtime_version" -NotePropertyValue $techDetails.runtime_version
            $projectObj | Add-Member -NotePropertyName "build_tools" -NotePropertyValue $techDetails.build_tools
            $projectObj | Add-Member -NotePropertyName "test_frameworks" -NotePropertyValue $techDetails.test_frameworks
            $projectObj | Add-Member -NotePropertyName "key_dependencies" -NotePropertyValue $techDetails.key_dependencies
        } else {
            $projectObj | Add-Member -NotePropertyName "framework" -NotePropertyValue "unknown"
        }

        $projects += $projectObj
    }

    Write-Host "Found $($projects.Count) projects" -ForegroundColor Green

    return $projects
}

function Invoke-ProjectDiscovery {
    param(
        [string]$RepoRoot,
        [bool]$UseCache,
        [bool]$ForceRescan,
        [bool]$DeepAnalysis = $false
    )

    <#
    .SYNOPSIS
    Main discovery function - checks cache or performs scan
    Phase 2: Optionally performs deep analysis when DeepAnalysis=true
    #>

    # Check cache first (unless force or deep analysis requested)
    # Note: Deep analysis results are not cached separately yet
    if ($UseCache -and -not $ForceRescan -and -not $DeepAnalysis) {
        $cached = Get-CachedDiscovery -RepoRoot $RepoRoot -ForceRescan $ForceRescan
        if ($cached) {
            return $cached
        }
    }

    Write-Host "Scanning repository..." -ForegroundColor Cyan
    if ($DeepAnalysis) {
        Write-Host "Deep analysis enabled - parsing dependency files..." -ForegroundColor Cyan
    }

    # Perform discovery
    $projects = Find-Projects -RepoRoot $RepoRoot -DeepAnalysis $DeepAnalysis

    # Compute cache hash
    $cacheHash = Get-CacheHash -RepoRoot $RepoRoot

    # Build discovery result
    $discovery = [PSCustomObject]@{
        version = "1.0"
        scanned_at = (Get-Date).ToString("o")
        repo_root = $RepoRoot
        cache_hash = $cacheHash
        total_projects = $projects.Count
        projects = $projects
    }

    # Cache results
    Save-DiscoveryCache -RepoRoot $RepoRoot -Discovery $discovery

    return $discovery
}

function Format-DiscoveryReport {
    param([PSCustomObject]$Discovery)

    <#
    .SYNOPSIS
    Format discovery results as human-readable report
    #>

    Write-Output ""
    Write-Output "# Project Discovery Report"
    Write-Output ""
    Write-Output "**Scanned:** $($Discovery.repo_root)"
    Write-Output "**Cache:** $(if ($Discovery.scanned_at) { 'Fresh scan' } else { 'Using cached' })"
    Write-Output "**Projects Found:** $($Discovery.total_projects)"
    Write-Output ""
    Write-Output "## Projects"
    Write-Output ""

    # Check if deep analysis was performed
    $hasDeepAnalysis = $Discovery.projects[0].PSObject.Properties.Name -contains "runtime"

    $i = 1
    foreach ($project in $Discovery.projects) {
        $sizeKB = [math]::Round($project.size_bytes / 1024, 0)
        $path = if ($project.path) { $project.path } else { "(root)" }

        Write-Output "### $i. $($project.name)"
        Write-Output ""
        Write-Output "- **ID:** $($project.id)"
        Write-Output "- **Type:** $($project.type)"
        Write-Output "- **Technology:** $($project.technology)"
        Write-Output "- **Path:** $path"
        Write-Output "- **Size:** ${sizeKB}KB ($($project.file_count) files)"

        if ($hasDeepAnalysis) {
            if ($project.framework -and $project.framework -ne "unknown") {
                $fwVersion = if ($project.framework_version) { " ($($project.framework_version))" } else { "" }
                Write-Output "- **Framework:** $($project.framework)$fwVersion"
            }

            if ($project.runtime_version) {
                Write-Output "- **Runtime:** $($project.runtime) $($project.runtime_version)"
            }

            if ($project.build_tools -and $project.build_tools.Count -gt 0) {
                Write-Output "- **Build Tools:** $($project.build_tools -join ', ')"
            }

            if ($project.test_frameworks -and $project.test_frameworks.Count -gt 0) {
                Write-Output "- **Test Frameworks:** $($project.test_frameworks -join ', ')"
            }

            if ($project.key_dependencies -and $project.key_dependencies.Count -gt 0) {
                Write-Output "- **Key Dependencies:** $($project.key_dependencies -join ', ')"
            }
        } else {
            if ($project.framework -and $project.framework -ne "unknown") {
                Write-Output "- **Framework:** $($project.framework)"
            }
        }

        Write-Output ""
        $i++
    }

    Write-Output ""
    Write-Output "## Next Steps"
    Write-Output ""
    Write-Output "``````powershell"
    Write-Output "# View detailed info for a project"
    Write-Output "/speckit.project-analysis --project=<project-id>"
    Write-Output ""
    Write-Output "# Onboard all projects"
    Write-Output "/speckit.onboard --all"
    Write-Output ""
    Write-Output "# Onboard specific projects"
    Write-Output "/speckit.onboard --projects=<id1>,<id2>"
    Write-Output "``````"
    Write-Output ""

    if (-not $Discovery.cache_hash) {
        Write-Output "**Note:** Run again with -Cached to use zero tokens!"
        Write-Output ""
    }
}

#endregion

# Main execution logic
if ($Discover) {
    # Universal Adoption: Discover existing projects
    Write-Verbose "Running in discovery mode"

    $discovery = Invoke-ProjectDiscovery `
        -RepoRoot $repoRoot `
        -UseCache $Cached.IsPresent `
        -ForceRescan $Force.IsPresent `
        -DeepAnalysis $DeepAnalysis.IsPresent

    if ($Json) {
        $discovery | ConvertTo-Json -Compress -Depth 10
    } else {
        Format-DiscoveryReport -Discovery $discovery
    }

    exit 0
}

# Standard mode: Analyze existing specs

$specsDir = Join-Path $repoRoot "specs"
$constitutionFile = Join-Path $repoRoot "memory" "constitution.md"

# Check if specs directory exists
if (-not (Test-Path $specsDir -PathType Container)) {
    if ($Json) {
        [PSCustomObject]@{
            error = "Specs directory not found"
            specs_dir = $specsDir
        } | ConvertTo-Json -Compress
    } else {
        Write-Error "ERROR: Specs directory not found: $specsDir"
    }
    exit 1
}

# Function to check if a file exists
function Test-SpecFile {
    param(
        [string]$SpecDir,
        [string]$FileName
    )
    $filePath = Join-Path $SpecDir $FileName
    Test-Path $filePath -PathType Leaf
}

# Function to count lines in a file
function Get-LineCount {
    param([string]$FilePath)

    if (Test-Path $FilePath -PathType Leaf) {
        (Get-Content $FilePath | Measure-Object -Line).Lines
    } else {
        0
    }
}

# Collect all spec directories
$specDirs = Get-ChildItem -Path $specsDir -Directory | Select-Object -ExpandProperty Name

# Sort spec directories by numeric prefix
$sortedSpecs = $specDirs | Sort-Object

# Check if constitution file exists
$constitutionExists = Test-Path $constitutionFile -PathType Leaf

# Detect programming languages in the repository
function Get-DetectedLanguages {
    $languages = @()

    if (Test-Path (Join-Path $repoRoot "package.json")) { $languages += "JavaScript/TypeScript" }
    if (Test-Path (Join-Path $repoRoot "pyproject.toml")) { $languages += "Python" }
    if (Test-Path (Join-Path $repoRoot "setup.py")) { $languages += "Python" }
    if (Test-Path (Join-Path $repoRoot "requirements.txt")) { $languages += "Python" }
    if (Test-Path (Join-Path $repoRoot "go.mod")) { $languages += "Go" }
    if (Test-Path (Join-Path $repoRoot "Cargo.toml")) { $languages += "Rust" }
    if (Test-Path (Join-Path $repoRoot "pom.xml")) { $languages += "Java" }
    if (Test-Path (Join-Path $repoRoot "build.gradle")) { $languages += "Java" }
    if (Test-Path (Join-Path $repoRoot "Gemfile")) { $languages += "Ruby" }
    if (Test-Path (Join-Path $repoRoot "composer.json")) { $languages += "PHP" }
    if (Get-ChildItem -Path $repoRoot -Filter "*.csproj" -File) { $languages += "C#" }

    if ($languages.Count -eq 0) {
        return "Unknown"
    } else {
        return ($languages -join ",")
    }
}

$detectedLanguages = Get-DetectedLanguages

# Find source code directories
function Get-SourceDirs {
    $sourceDirs = @()

    if (Test-Path (Join-Path $repoRoot "src") -PathType Container) { $sourceDirs += "src" }
    if (Test-Path (Join-Path $repoRoot "lib") -PathType Container) { $sourceDirs += "lib" }
    if (Test-Path (Join-Path $repoRoot "app") -PathType Container) { $sourceDirs += "app" }
    if (Test-Path (Join-Path $repoRoot "source") -PathType Container) { $sourceDirs += "source" }
    if (Test-Path (Join-Path $repoRoot "pkg") -PathType Container) { $sourceDirs += "pkg" }

    if ($sourceDirs.Count -eq 0) {
        return ""
    } else {
        return ($sourceDirs -join ",")
    }
}

$sourceDirs = Get-SourceDirs

# Build spec information
$specs = @()
foreach ($specName in $sortedSpecs) {
    $specDir = Join-Path $specsDir $specName

    $hasSpec = Test-SpecFile -SpecDir $specDir -FileName "spec.md"
    $hasPlan = Test-SpecFile -SpecDir $specDir -FileName "plan.md"
    $hasTasks = Test-SpecFile -SpecDir $specDir -FileName "tasks.md"
    $hasResearch = Test-SpecFile -SpecDir $specDir -FileName "research.md"
    $hasDataModel = Test-SpecFile -SpecDir $specDir -FileName "data-model.md"
    $hasQuickstart = Test-SpecFile -SpecDir $specDir -FileName "quickstart.md"
    $hasContracts = Test-Path (Join-Path $specDir "contracts") -PathType Container

    $specLines = Get-LineCount -FilePath (Join-Path $specDir "spec.md")
    $planLines = Get-LineCount -FilePath (Join-Path $specDir "plan.md")
    $tasksLines = Get-LineCount -FilePath (Join-Path $specDir "tasks.md")

    $specs += [PSCustomObject]@{
        name = $specName
        dir = $specDir
        has_spec = $hasSpec
        has_plan = $hasPlan
        has_tasks = $hasTasks
        has_research = $hasResearch
        has_data_model = $hasDataModel
        has_quickstart = $hasQuickstart
        has_contracts = $hasContracts
        spec_lines = $specLines
        plan_lines = $planLines
        tasks_lines = $tasksLines
    }
}

# Output results
if ($Json) {
    [PSCustomObject]@{
        repo_root = $repoRoot
        specs_dir = $specsDir
        constitution_exists = $constitutionExists
        constitution_file = $constitutionFile
        pattern_check_enabled = $CheckPatterns.IsPresent
        detected_languages = $detectedLanguages
        source_dirs = $sourceDirs
        total_specs = $sortedSpecs.Count
        specs = $specs
    } | ConvertTo-Json -Compress -Depth 10
} else {
    Write-Output "=== Project Analysis ==="
    Write-Output ""
    Write-Output "Repository Root: $repoRoot"
    Write-Output "Specs Directory: $specsDir"
    Write-Output "Constitution: $(if ($constitutionExists) { '✓ Found' } else { '✗ Missing' })"
    Write-Output "Detected Languages: $detectedLanguages"
    Write-Output "Source Directories: $sourceDirs"
    Write-Output "Pattern Check: $(if ($CheckPatterns) { 'Enabled' } else { 'Disabled' })"
    Write-Output ""
    Write-Output "Total Specifications: $($sortedSpecs.Count)"
    Write-Output ""

    foreach ($spec in $specs) {
        Write-Output "[$($spec.name)]"
        Write-Output "  spec.md:       $(if ($spec.has_spec) { 'true' } else { 'false' })"
        Write-Output "  plan.md:       $(if ($spec.has_plan) { 'true' } else { 'false' })"
        Write-Output "  tasks.md:      $(if ($spec.has_tasks) { 'true' } else { 'false' })"
        Write-Output "  research.md:   $(if ($spec.has_research) { 'true' } else { 'false' })"
        Write-Output "  data-model.md: $(if ($spec.has_data_model) { 'true' } else { 'false' })"
        Write-Output ""
    }
}
