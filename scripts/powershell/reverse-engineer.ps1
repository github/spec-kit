#!/usr/bin/env pwsh

# Spec-Kit Reverse Engineering Script (PowerShell)
#
# Phase 4: Reverse Engineering
#
# This script extracts APIs and data models from existing code to generate
# specifications. Uses Phase 2 framework detection to select appropriate extractors.
#
# Usage: ./reverse-engineer.ps1 [OPTIONS]
#
# OPTIONS:
#   -Project <id>       Project ID to reverse engineer
#   -All                Reverse engineer all onboarded projects
#   -APIs               Extract API endpoints only
#   -Models             Extract data models only
#   -MaxEndpoints <n>   Maximum endpoints to extract (default: 50, for token efficiency)
#   -MaxModels <n>      Maximum models to extract (default: 20, for token efficiency)
#   -Force              Overwrite existing reverse-engineered specs
#   -DryRun             Show what would be extracted without creating files
#   -Json               Output results in JSON format
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [string]$Project,
    [switch]$All,
    [switch]$APIs,
    [switch]$Models,
    [int]$MaxEndpoints = 50,
    [int]$MaxModels = 20,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: reverse-engineer.ps1 [OPTIONS]

Extract APIs and data models from existing code to generate specifications.

OPTIONS:
  -Project <id>       Project ID to reverse engineer
  -All                Reverse engineer all onboarded projects
  -APIs               Extract API endpoints only
  -Models             Extract data models only
  -MaxEndpoints <n>   Maximum endpoints to extract (default: 50)
  -MaxModels <n>      Maximum models to extract (default: 20)
  -Force              Overwrite existing reverse-engineered specs
  -DryRun             Show what would be extracted without creating files
  -Json               Output results in JSON format
  -Help, -h           Show this help message

EXAMPLES:
  # Reverse engineer specific project
  .\reverse-engineer.ps1 -Project api

  # Extract APIs only
  .\reverse-engineer.ps1 -Project api -APIs

  # Extract models only
  .\reverse-engineer.ps1 -Project api -Models

  # Reverse engineer all projects
  .\reverse-engineer.ps1 -All

  # Dry run (preview)
  .\reverse-engineer.ps1 -Project api -DryRun

  # Custom limits for token efficiency
  .\reverse-engineer.ps1 -Project api -MaxEndpoints 20 -MaxModels 10

"@
    exit 0
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get repository root
$repoRoot = Get-RepoRoot

#region Helper Functions

function Get-ProjectMetadata {
    param(
        [string]$RepoRoot,
        [string]$ProjectId
    )

    <#
    .SYNOPSIS
    Load project metadata from Phase 3
    #>

    $metadataFile = Join-Path $RepoRoot ".speckit" "metadata" "$ProjectId.json"

    if (-not (Test-Path $metadataFile)) {
        throw "Project metadata not found: $metadataFile. Run onboard.ps1 first."
    }

    try {
        $metadata = Get-Content $metadataFile -Raw | ConvertFrom-Json
        return $metadata
    } catch {
        throw "Failed to load project metadata: $_"
    }
}

function Get-SpeckitConfig {
    param([string]$RepoRoot)

    <#
    .SYNOPSIS
    Load spec-kit configuration
    #>

    $configFile = Join-Path $RepoRoot ".speckit" "config.json"

    if (-not (Test-Path $configFile)) {
        throw "Spec-kit not initialized. Run onboard.ps1 first."
    }

    try {
        $config = Get-Content $configFile -Raw | ConvertFrom-Json
        return $config
    } catch {
        throw "Failed to load configuration: $_"
    }
}

#endregion

#region API Extraction Functions

function Find-ExpressEndpoints {
    param(
        [string]$ProjectPath,
        [int]$MaxEndpoints
    )

    <#
    .SYNOPSIS
    Extract API endpoints from Express.js code
    Token Budget: ~500-1000 tokens
    #>

    Write-Verbose "Extracting Express endpoints from: $ProjectPath"

    $endpoints = @()
    $patterns = @(
        'app\.(get|post|put|patch|delete|all)\([''"]([^''"]+)[''"]',
        'router\.(get|post|put|patch|delete|all)\([''"]([^''"]+)[''"]'
    )

    # Find JavaScript/TypeScript files
    $files = Get-ChildItem -Path $ProjectPath -Include "*.js","*.ts" -Recurse -File -ErrorAction SilentlyContinue `
        | Where-Object { $_.FullName -notmatch 'node_modules|test|spec|dist|build' } `
        | Select-Object -First 100  # Limit files for token efficiency

    foreach ($file in $files) {
        try {
            $content = Get-Content $file.FullName -Raw

            foreach ($pattern in $patterns) {
                $matches = [regex]::Matches($content, $pattern)

                foreach ($match in $matches) {
                    $method = $match.Groups[1].Value.ToUpper()
                    $path = $match.Groups[2].Value

                    # Extract handler context (10 lines)
                    $lines = $content -split "`n"
                    $matchLine = ($content.Substring(0, $match.Index) -split "`n").Count
                    $contextStart = [Math]::Max(0, $matchLine - 2)
                    $contextEnd = [Math]::Min($lines.Count, $matchLine + 8)
                    $context = $lines[$contextStart..$contextEnd] -join "`n"

                    $endpoints += [PSCustomObject]@{
                        method = $method
                        path = $path
                        file = $file.FullName.Replace($ProjectPath, "").TrimStart('\', '/')
                        line = $matchLine + 1
                        context = $context
                        confidence = "high"
                    }

                    if ($endpoints.Count -ge $MaxEndpoints) {
                        Write-Warning "  Reached max endpoints limit ($MaxEndpoints)"
                        return $endpoints
                    }
                }
            }
        } catch {
            Write-Verbose "  Failed to parse file: $($file.Name) - $_"
        }
    }

    Write-Verbose "  Found $($endpoints.Count) Express endpoints"
    return $endpoints
}

function Find-FastAPIEndpoints {
    param(
        [string]$ProjectPath,
        [int]$MaxEndpoints
    )

    <#
    .SYNOPSIS
    Extract API endpoints from FastAPI code
    Token Budget: ~500-1000 tokens
    #>

    Write-Verbose "Extracting FastAPI endpoints from: $ProjectPath"

    $endpoints = @()
    $patterns = @(
        '@app\.(get|post|put|patch|delete)\([''"]([^''"]+)[''"]',
        '@router\.(get|post|put|patch|delete)\([''"]([^''"]+)[''"]'
    )

    # Find Python files
    $files = Get-ChildItem -Path $ProjectPath -Include "*.py" -Recurse -File -ErrorAction SilentlyContinue `
        | Where-Object { $_.FullName -notmatch '__pycache__|test|tests|\.venv|venv' } `
        | Select-Object -First 100

    foreach ($file in $files) {
        try {
            $content = Get-Content $file.FullName -Raw

            foreach ($pattern in $patterns) {
                $matches = [regex]::Matches($content, $pattern)

                foreach ($match in $matches) {
                    $method = $match.Groups[1].Value.ToUpper()
                    $path = $match.Groups[2].Value

                    # Extract function definition
                    $lines = $content -split "`n"
                    $matchLine = ($content.Substring(0, $match.Index) -split "`n").Count
                    $contextStart = $matchLine
                    $contextEnd = [Math]::Min($lines.Count, $matchLine + 10)
                    $context = $lines[$contextStart..$contextEnd] -join "`n"

                    # Try to extract Pydantic model from function signature
                    $responseModel = if ($context -match 'response_model=(\w+)') { $matches[1] } else { $null }
                    $requestModel = if ($context -match ':\s*(\w+)\s*=') { $matches[1] } else { $null }

                    $endpoints += [PSCustomObject]@{
                        method = $method
                        path = $path
                        file = $file.FullName.Replace($ProjectPath, "").TrimStart('\', '/')
                        line = $matchLine + 2
                        context = $context
                        request_model = $requestModel
                        response_model = $responseModel
                        confidence = "high"
                    }

                    if ($endpoints.Count -ge $MaxEndpoints) {
                        Write-Warning "  Reached max endpoints limit ($MaxEndpoints)"
                        return $endpoints
                    }
                }
            }
        } catch {
            Write-Verbose "  Failed to parse file: $($file.Name) - $_"
        }
    }

    Write-Verbose "  Found $($endpoints.Count) FastAPI endpoints"
    return $endpoints
}

function Find-GinEndpoints {
    param(
        [string]$ProjectPath,
        [int]$MaxEndpoints
    )

    <#
    .SYNOPSIS
    Extract API endpoints from Gin (Go) code
    Token Budget: ~500-1000 tokens
    #>

    Write-Verbose "Extracting Gin endpoints from: $ProjectPath"

    $endpoints = @()
    $pattern = '\.(\w+)\([''"]([^''"]+)[''"]\s*,\s*(\w+)'

    # Find Go files
    $files = Get-ChildItem -Path $ProjectPath -Include "*.go" -Recurse -File -ErrorAction SilentlyContinue `
        | Where-Object { $_.FullName -notmatch 'vendor|test' } `
        | Select-Object -First 100

    foreach ($file in $files) {
        try {
            $content = Get-Content $file.FullName -Raw

            $matches = [regex]::Matches($content, $pattern)

            foreach ($match in $matches) {
                $methodCall = $match.Groups[1].Value
                $method = switch ($methodCall) {
                    "GET" { "GET" }
                    "POST" { "POST" }
                    "PUT" { "PUT" }
                    "PATCH" { "PATCH" }
                    "DELETE" { "DELETE" }
                    default { $null }
                }

                if (-not $method) { continue }

                $path = $match.Groups[2].Value
                $handler = $match.Groups[3].Value

                $lines = $content -split "`n"
                $matchLine = ($content.Substring(0, $match.Index) -split "`n").Count

                $endpoints += [PSCustomObject]@{
                    method = $method
                    path = $path
                    handler = $handler
                    file = $file.FullName.Replace($ProjectPath, "").TrimStart('\', '/')
                    line = $matchLine + 1
                    confidence = "high"
                }

                if ($endpoints.Count -ge $MaxEndpoints) {
                    Write-Warning "  Reached max endpoints limit ($MaxEndpoints)"
                    return $endpoints
                }
            }
        } catch {
            Write-Verbose "  Failed to parse file: $($file.Name) - $_"
        }
    }

    Write-Verbose "  Found $($endpoints.Count) Gin endpoints"
    return $endpoints
}

function Extract-ProjectAPIs {
    param(
        [string]$ProjectPath,
        [string]$Framework,
        [int]$MaxEndpoints
    )

    <#
    .SYNOPSIS
    Extract APIs based on detected framework
    #>

    Write-Verbose "Extracting APIs for framework: $Framework"

    $endpoints = switch -Wildcard ($Framework) {
        "Express*" { Find-ExpressEndpoints -ProjectPath $ProjectPath -MaxEndpoints $MaxEndpoints }
        "FastAPI*" { Find-FastAPIEndpoints -ProjectPath $ProjectPath -MaxEndpoints $MaxEndpoints }
        "Gin*" { Find-GinEndpoints -ProjectPath $ProjectPath -MaxEndpoints $MaxEndpoints }
        default {
            Write-Warning "No API extractor for framework: $Framework"
            @()
        }
    }

    return $endpoints
}

#endregion

#region Data Model Extraction Functions

function Find-PydanticModels {
    param(
        [string]$ProjectPath,
        [int]$MaxModels
    )

    <#
    .SYNOPSIS
    Extract Pydantic models from Python code
    Token Budget: ~300-500 tokens
    #>

    Write-Verbose "Extracting Pydantic models from: $ProjectPath"

    $models = @()
    $pattern = 'class\s+(\w+)\(BaseModel\):'

    $files = Get-ChildItem -Path $ProjectPath -Include "*.py" -Recurse -File -ErrorAction SilentlyContinue `
        | Where-Object { $_.FullName -notmatch '__pycache__|test|tests|\.venv|venv' } `
        | Select-Object -First 50

    foreach ($file in $files) {
        try {
            $content = Get-Content $file.FullName -Raw

            $matches = [regex]::Matches($content, $pattern)

            foreach ($match in $matches) {
                $modelName = $match.Groups[1].Value
                $lines = $content -split "`n"
                $matchLine = ($content.Substring(0, $match.Index) -split "`n").Count

                # Extract fields (next 20 lines or until next class)
                $fields = @()
                for ($i = $matchLine + 1; $i -lt [Math]::Min($lines.Count, $matchLine + 20); $i++) {
                    $line = $lines[$i].Trim()

                    if ($line -match '^class\s+\w+' -or $line -match '^def\s+\w+') {
                        break
                    }

                    if ($line -match '^(\w+):\s*(.+)') {
                        $fieldName = $matches[1]
                        $fieldType = $matches[2] -replace '=.*', '' -replace '\s+', ''
                        $fields += [PSCustomObject]@{
                            name = $fieldName
                            type = $fieldType
                        }
                    }
                }

                $models += [PSCustomObject]@{
                    name = $modelName
                    file = $file.FullName.Replace($ProjectPath, "").TrimStart('\', '/')
                    line = $matchLine + 1
                    fields = $fields
                    confidence = "high"
                }

                if ($models.Count -ge $MaxModels) {
                    Write-Warning "  Reached max models limit ($MaxModels)"
                    return $models
                }
            }
        } catch {
            Write-Verbose "  Failed to parse file: $($file.Name) - $_"
        }
    }

    Write-Verbose "  Found $($models.Count) Pydantic models"
    return $models
}

function Find-TypeScriptInterfaces {
    param(
        [string]$ProjectPath,
        [int]$MaxModels
    )

    <#
    .SYNOPSIS
    Extract TypeScript interfaces and types
    Token Budget: ~300-500 tokens
    #>

    Write-Verbose "Extracting TypeScript interfaces from: $ProjectPath"

    $models = @()
    $pattern = '(interface|type)\s+(\w+)\s*{'

    $files = Get-ChildItem -Path $ProjectPath -Include "*.ts" -Recurse -File -ErrorAction SilentlyContinue `
        | Where-Object { $_.FullName -notmatch 'node_modules|test|spec|dist|build' } `
        | Select-Object -First 50

    foreach ($file in $files) {
        try {
            $content = Get-Content $file.FullName -Raw

            $matches = [regex]::Matches($content, $pattern)

            foreach ($match in $matches) {
                $kind = $match.Groups[1].Value
                $modelName = $match.Groups[2].Value
                $lines = $content -split "`n"
                $matchLine = ($content.Substring(0, $match.Index) -split "`n").Count

                # Extract fields
                $fields = @()
                $braceCount = 0
                $started = $false
                for ($i = $matchLine; $i -lt [Math]::Min($lines.Count, $matchLine + 30); $i++) {
                    $line = $lines[$i]

                    if ($line -match '{') { $braceCount++; $started = $true }
                    if ($line -match '}') { $braceCount--; if ($braceCount -eq 0) { break } }

                    if ($started -and $line -match '^\s*(\w+)(\?)?:\s*(.+?);?$') {
                        $fieldName = $matches[1]
                        $optional = $matches[2]
                        $fieldType = $matches[3] -replace '\s+', ''
                        $fields += [PSCustomObject]@{
                            name = $fieldName
                            type = $fieldType
                            optional = [bool]$optional
                        }
                    }
                }

                $models += [PSCustomObject]@{
                    name = $modelName
                    kind = $kind
                    file = $file.FullName.Replace($ProjectPath, "").TrimStart('\', '/')
                    line = $matchLine + 1
                    fields = $fields
                    confidence = "high"
                }

                if ($models.Count -ge $MaxModels) {
                    Write-Warning "  Reached max models limit ($MaxModels)"
                    return $models
                }
            }
        } catch {
            Write-Verbose "  Failed to parse file: $($file.Name) - $_"
        }
    }

    Write-Verbose "  Found $($models.Count) TypeScript interfaces/types"
    return $models
}

function Extract-ProjectModels {
    param(
        [string]$ProjectPath,
        [string]$Technology,
        [int]$MaxModels
    )

    <#
    .SYNOPSIS
    Extract data models based on technology
    #>

    Write-Verbose "Extracting models for technology: $Technology"

    $models = switch ($Technology) {
        "python" { Find-PydanticModels -ProjectPath $ProjectPath -MaxModels $MaxModels }
        "nodejs" { Find-TypeScriptInterfaces -ProjectPath $ProjectPath -MaxModels $MaxModels }
        default {
            Write-Warning "No model extractor for technology: $Technology"
            @()
        }
    }

    return $models
}

#endregion

#region Spec Generation Functions

function New-APISpecification {
    param(
        [PSCustomObject]$Metadata,
        [array]$Endpoints
    )

    <#
    .SYNOPSIS
    Generate API specification from extracted endpoints
    #>

    $spec = @"
# $($Metadata.name) - Existing API Specification

⚠️  **Auto-Generated from Existing Code**

This specification was reverse-engineered from the existing implementation.
Confidence: HIGH for structure, MEDIUM for business logic, LOW for requirements.

**Please review and enhance with:**
- Business context and purpose
- User scenarios and use cases
- Non-functional requirements
- Error handling specifications
- Authentication/authorization details

---

## Overview

- **Framework:** $($Metadata.framework)
- **Technology:** $($Metadata.technology)
- **Location:** ``$($Metadata.path)``
- **Total Endpoints Detected:** $($Endpoints.Count)

---

## API Endpoints

"@

    foreach ($endpoint in $Endpoints) {
        $spec += @"

### $($endpoint.method) $($endpoint.path)

**Location:** ``$($endpoint.file):$($endpoint.line)``
**Confidence:** $($endpoint.confidence)

"@

        if ($endpoint.request_model) {
            $spec += "**Request Model:** ``$($endpoint.request_model)```n"
        }

        if ($endpoint.response_model) {
            $spec += "**Response Model:** ``$($endpoint.response_model)```n"
        }

        if ($endpoint.handler) {
            $spec += "**Handler:** ``$($endpoint.handler)()```n"
        }

        $spec += @"

**Purpose:** *(Inferred - Please document)*

**Request:**
- Method: $($endpoint.method)
- Path: $($endpoint.path)
- Parameters: *(To be documented)*

**Response:**
- Success (200): *(To be documented)*
- Errors: *(To be documented)*

**Example:**
``````http
$($endpoint.method) $($endpoint.path) HTTP/1.1
Host: api.example.com
Content-Type: application/json

# Request body example needed
``````

---

"@
    }

    $spec += @"

## Next Steps

1. **Review** each endpoint and add business context
2. **Document** request/response schemas
3. **Add** authentication requirements
4. **Specify** error handling
5. **Define** rate limiting and quotas
6. **Create** test scenarios

---

**Status:** Reverse-engineered - Requires review and enhancement

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

    return $spec
}

function New-ModelSpecification {
    param(
        [PSCustomObject]$Metadata,
        [array]$Models
    )

    <#
    .SYNOPSIS
    Generate data model specification
    #>

    $spec = @"
# $($Metadata.name) - Data Models

⚠️  **Auto-Generated from Existing Code**

Data models extracted from codebase.
Confidence: HIGH for structure, MEDIUM for relationships, LOW for business rules.

---

## Overview

- **Technology:** $($Metadata.technology)
- **Location:** ``$($Metadata.path)``
- **Total Models Detected:** $($Models.Count)

---

## Models

"@

    foreach ($model in $Models) {
        $spec += @"

### $($model.name)

**Location:** ``$($model.file):$($model.line)``
**Confidence:** $($model.confidence)

"@

        if ($model.kind) {
            $spec += "**Kind:** $($model.kind)`n`n"
        }

        if ($model.fields -and $model.fields.Count -gt 0) {
            $spec += "**Fields:**`n`n"
            $spec += "| Field | Type | Optional | Description |`n"
            $spec += "|-------|------|----------|-------------|`n"

            foreach ($field in $model.fields) {
                $optional = if ($field.optional) { "Yes" } else { "No" }
                $spec += "| ``$($field.name)`` | ``$($field.type)`` | $optional | *(To be documented)* |`n"
            }

            $spec += "`n"
        }

        $spec += @"
**Purpose:** *(To be documented)*

**Relationships:** *(To be documented)*

**Validation Rules:** *(To be documented)*

---

"@
    }

    $spec += @"

## Next Steps

1. **Document** purpose and business context for each model
2. **Define** relationships between models
3. **Specify** validation rules and constraints
4. **Add** indexes and performance considerations
5. **Document** lifecycle and state transitions

---

**Status:** Reverse-engineered - Requires review and enhancement

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

    return $spec
}

function New-ExistingCodeReadme {
    param(
        [PSCustomObject]$Metadata,
        [int]$EndpointCount,
        [int]$ModelCount
    )

    <#
    .SYNOPSIS
    Generate README for 001-existing-code feature
    #>

    $readme = @"
# 001 - Existing Code (Reverse Engineered)

⚠️  **Auto-Generated Specification**

This feature represents the existing implementation, reverse-engineered from code.

---

## Overview

This specification was automatically generated by analyzing the existing codebase.
It provides a starting point for understanding the current system.

**Framework:** $($Metadata.framework)
**Technology:** $($Metadata.technology)
**Location:** ``$($Metadata.path)``

---

## Extracted Information

"@

    if ($EndpointCount -gt 0) {
        $readme += "- **API Endpoints:** $EndpointCount detected (see ``api-spec.md``)`n"
    }

    if ($ModelCount -gt 0) {
        $readme += "- **Data Models:** $ModelCount detected (see ``models.md``)`n"
    }

    $readme += @"

---

## Confidence Levels

**HIGH** - Structure and syntax accurately extracted
- API paths and methods
- Data model fields and types
- File locations

**MEDIUM** - Inferred from context
- Request/response formats
- Model relationships
- Handler logic

**LOW** - Requires human input
- Business requirements
- User scenarios
- Non-functional requirements
- Validation rules

---

## Next Steps

### 1. Review Generated Specs

``````bash
# Review API specification
cat api-spec.md

# Review data models
cat models.md
``````

### 2. Enhance with Business Context

- Add purpose and rationale for each endpoint
- Document user scenarios
- Specify error handling
- Define validation rules
- Add authentication/authorization requirements

### 3. Validate Against Reality

- Compare with actual API behavior
- Test endpoints
- Verify data models
- Check for missing functionality

### 4. Use as Foundation

This reverse-engineered spec serves as a baseline for:
- Understanding existing system
- Planning improvements
- Developing new features
- Onboarding new team members

---

## Files

- ``README.md`` - This file
- ``api-spec.md`` - API endpoints (auto-generated)
- ``models.md`` - Data models (auto-generated)

---

**Status:** Reverse-engineered baseline - Requires validation and enhancement

**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

    return $readme
}

#endregion

#region Main Execution Functions

function Invoke-ReverseEngineering {
    param(
        [string]$RepoRoot,
        [PSCustomObject]$Metadata,
        [bool]$ExtractAPIs,
        [bool]$ExtractModels,
        [int]$MaxEndpoints,
        [int]$MaxModels,
        [bool]$DryRun
    )

    <#
    .SYNOPSIS
    Perform reverse engineering for a single project
    #>

    Write-Host ""
    Write-Host "Reverse Engineering: $($Metadata.name)" -ForegroundColor Cyan
    Write-Host "  Framework: $($Metadata.framework)" -ForegroundColor Gray
    Write-Host "  Technology: $($Metadata.technology)" -ForegroundColor Gray
    Write-Host "  Path: $($Metadata.path)" -ForegroundColor Gray

    $projectPath = Join-Path $RepoRoot $Metadata.path

    if (-not (Test-Path $projectPath)) {
        Write-Error "  Project path not found: $projectPath"
        return $false
    }

    # Extract APIs
    $endpoints = @()
    if ($ExtractAPIs -and $Metadata.framework -and $Metadata.framework -ne "unknown") {
        Write-Host "  Extracting APIs..." -ForegroundColor Cyan
        $endpoints = Extract-ProjectAPIs -ProjectPath $projectPath -Framework $Metadata.framework -MaxEndpoints $MaxEndpoints
        Write-Host "    Found: $($endpoints.Count) endpoints" -ForegroundColor Green
    }

    # Extract Models
    $models = @()
    if ($ExtractModels) {
        Write-Host "  Extracting models..." -ForegroundColor Cyan
        $models = Extract-ProjectModels -ProjectPath $projectPath -Technology $Metadata.technology -MaxModels $MaxModels
        Write-Host "    Found: $($models.Count) models" -ForegroundColor Green
    }

    if ($endpoints.Count -eq 0 -and $models.Count -eq 0) {
        Write-Warning "  No APIs or models extracted"
        return $false
    }

    # Create 001-existing-code directory
    $specDir = Join-Path $RepoRoot "specs" "projects" $Metadata.id "001-existing-code"

    if (Test-Path $specDir) {
        if ($Force) {
            Write-Warning "  Overwriting existing specs (--force)"
        } else {
            Write-Warning "  Specs already exist (use --force to overwrite)"
            return $false
        }
    }

    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $specDir -Force | Out-Null
        Write-Verbose "  Created: $specDir"
    } else {
        Write-Host "  [DRY RUN] Would create: $specDir" -ForegroundColor Cyan
    }

    # Generate specifications
    if ($endpoints.Count -gt 0) {
        $apiSpec = New-APISpecification -Metadata $Metadata -Endpoints $endpoints
        $apiSpecFile = Join-Path $specDir "api-spec.md"

        if (-not $DryRun) {
            $apiSpec | Out-File $apiSpecFile -Encoding UTF8
            Write-Host "    Created: api-spec.md" -ForegroundColor Green
        } else {
            Write-Host "    [DRY RUN] Would create: api-spec.md ($($endpoints.Count) endpoints)" -ForegroundColor Cyan
        }
    }

    if ($models.Count -gt 0) {
        $modelSpec = New-ModelSpecification -Metadata $Metadata -Models $models
        $modelSpecFile = Join-Path $specDir "models.md"

        if (-not $DryRun) {
            $modelSpec | Out-File $modelSpecFile -Encoding UTF8
            Write-Host "    Created: models.md" -ForegroundColor Green
        } else {
            Write-Host "    [DRY RUN] Would create: models.md ($($models.Count) models)" -ForegroundColor Cyan
        }
    }

    # Generate README
    $readme = New-ExistingCodeReadme -Metadata $Metadata -EndpointCount $endpoints.Count -ModelCount $models.Count
    $readmeFile = Join-Path $specDir "README.md"

    if (-not $DryRun) {
        $readme | Out-File $readmeFile -Encoding UTF8
        Write-Host "    Created: README.md" -ForegroundColor Green
    } else {
        Write-Host "    [DRY RUN] Would create: README.md" -ForegroundColor Cyan
    }

    Write-Host "  ✓ Reverse engineering complete" -ForegroundColor Green

    return $true
}

#endregion

#region Main Script Logic

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Spec-Kit Reverse Engineering (Phase 4)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "** DRY RUN MODE - No files will be created **" -ForegroundColor Yellow
    Write-Host ""
}

# Load configuration
Write-Host "Loading configuration..." -ForegroundColor Cyan
$config = Get-SpeckitConfig -RepoRoot $repoRoot

# Determine what to extract
$extractAPIs = (-not $Models) -or $APIs  # Extract APIs by default, unless -Models only
$extractModels = (-not $APIs) -or $Models  # Extract models by default, unless -APIs only

Write-Host "  Extract APIs: $extractAPIs" -ForegroundColor Gray
Write-Host "  Extract Models: $extractModels" -ForegroundColor Gray
Write-Host "  Max Endpoints: $MaxEndpoints" -ForegroundColor Gray
Write-Host "  Max Models: $MaxModels" -ForegroundColor Gray
Write-Host ""

# Select projects
$projectsToProcess = @()

if ($All) {
    $projectsToProcess = $config.projects | Where-Object { $_.status -eq "onboarded" }
    Write-Host "Selected: All $($projectsToProcess.Count) onboarded projects" -ForegroundColor Green
} elseif ($Project) {
    $projectConfig = $config.projects | Where-Object { $_.id -eq $Project }
    if (-not $projectConfig) {
        throw "Project not found: $Project"
    }
    $projectsToProcess = @($projectConfig)
    Write-Host "Selected: Project '$Project'" -ForegroundColor Green
} else {
    throw "Must specify -Project <id> or -All"
}

Write-Host ""

# Process each project
$successCount = 0
$skipCount = 0

foreach ($projectConfig in $projectsToProcess) {
    # Load metadata
    $metadata = Get-ProjectMetadata -RepoRoot $repoRoot -ProjectId $projectConfig.id

    # Perform reverse engineering
    $result = Invoke-ReverseEngineering `
        -RepoRoot $repoRoot `
        -Metadata $metadata `
        -ExtractAPIs $extractAPIs `
        -ExtractModels $extractModels `
        -MaxEndpoints $MaxEndpoints `
        -MaxModels $MaxModels `
        -DryRun $DryRun

    if ($result) {
        $successCount++
    } else {
        $skipCount++
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Reverse Engineering Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results:" -ForegroundColor Green
Write-Host "  ✓ Successfully processed: $successCount" -ForegroundColor Green
if ($skipCount -gt 0) {
    Write-Host "  ⊘ Skipped: $skipCount" -ForegroundColor Yellow
}
Write-Host ""

if (-not $DryRun -and $successCount -gt 0) {
    Write-Host "Generated Files:" -ForegroundColor Green
    Write-Host "  specs/projects/{project-id}/001-existing-code/" -ForegroundColor Gray
    Write-Host "    ├── README.md           - Overview" -ForegroundColor Gray
    Write-Host "    ├── api-spec.md         - API endpoints" -ForegroundColor Gray
    Write-Host "    └── models.md           - Data models" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Review generated specifications" -ForegroundColor Gray
    Write-Host "  2. Add business context and requirements" -ForegroundColor Gray
    Write-Host "  3. Validate against actual behavior" -ForegroundColor Gray
    Write-Host "  4. Use as foundation for new features" -ForegroundColor Gray
    Write-Host ""
}

#endregion
