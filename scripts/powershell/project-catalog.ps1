#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Phase 5: Integration & Catalog - Generate unified project catalog with cross-project search and API indexing.

.DESCRIPTION
    Generates a token-optimized unified catalog of all onboarded projects including:
    - Project overview with quick navigation
    - Technology matrix showing all frameworks/languages
    - API endpoint index from reverse-engineered specs
    - Cross-project search capabilities
    - Dependency visualization

    Token Budget: < 1,000 tokens for entire catalog

.PARAMETER Output
    Output file path for the catalog (default: docs/PROJECT-CATALOG.md)

.PARAMETER Format
    Output format: markdown (default), json, or html

.PARAMETER IncludeAPIs
    Include API endpoint index from reverse-engineered specs (default: true)

.PARAMETER IncludeDependencies
    Include dependency matrix (default: true)

.PARAMETER Json
    Output JSON format for programmatic use

.PARAMETER Force
    Force regeneration even if cache is valid

.EXAMPLE
    ./project-catalog.ps1
    Generates catalog at docs/PROJECT-CATALOG.md

.EXAMPLE
    ./project-catalog.ps1 -Output catalog.md -IncludeAPIs $false
    Generate catalog without API index

.EXAMPLE
    ./project-catalog.ps1 -Json
    Output JSON format for programmatic processing

.NOTES
    Phase: 5 (Integration & Catalog)
    Token Budget: < 1,000 tokens total
    Dependencies: Phase 3 (onboarding), Phase 4 (reverse engineering)
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$Output = "docs/PROJECT-CATALOG.md",

    [Parameter()]
    [ValidateSet("markdown", "json", "html")]
    [string]$Format = "markdown",

    [Parameter()]
    [bool]$IncludeAPIs = $true,

    [Parameter()]
    [bool]$IncludeDependencies = $true,

    [Parameter()]
    [switch]$Json,

    [Parameter()]
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================================
# Constants
# ============================================================================

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$REPO_ROOT = (Get-Item $SCRIPT_DIR).Parent.Parent.FullName
$SPECKIT_DIR = Join-Path $REPO_ROOT ".speckit"
$SPECS_DIR = Join-Path $REPO_ROOT "specs"
$CONFIG_FILE = Join-Path $SPECKIT_DIR "config.json"
$CACHE_DIR = Join-Path $SPECKIT_DIR "cache"
$CATALOG_CACHE = Join-Path $CACHE_DIR "catalog.json"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-StepHeader {
    param([string]$Message)
    Write-Host "`n$Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Gray
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  ⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

# ============================================================================
# Core Functions
# ============================================================================

function Get-SpeckitConfig {
    <#
    .SYNOPSIS
        Load spec-kit configuration
    #>
    if (-not (Test-Path $CONFIG_FILE)) {
        throw "Spec-kit not initialized. Run /speckit.onboard first."
    }

    $config = Get-Content $CONFIG_FILE -Raw | ConvertFrom-Json
    return $config
}

function Get-ProjectMetadata {
    <#
    .SYNOPSIS
        Load metadata for all projects
    #>
    param([object[]]$Projects)

    $metadataList = @()
    foreach ($project in $Projects) {
        $metadataFile = Join-Path $SPECKIT_DIR $project.metadata_file
        if (Test-Path $metadataFile) {
            $metadata = Get-Content $metadataFile -Raw | ConvertFrom-Json
            $metadataList += $metadata
        }
    }

    return $metadataList
}

function Get-ReverseEngineeredAPIs {
    <#
    .SYNOPSIS
        Extract all API endpoints from reverse-engineered specs
    #>
    param([object[]]$Projects)

    $apiIndex = @()

    foreach ($project in $Projects) {
        $apiSpecPath = Join-Path $SPECS_DIR "projects" $project.id "001-existing-code" "api-spec.md"

        if (-not (Test-Path $apiSpecPath)) {
            continue
        }

        # Parse API spec to extract endpoints
        $content = Get-Content $apiSpecPath -Raw

        # Extract endpoints using regex pattern
        # Pattern: ### METHOD /path/to/endpoint
        $endpointPattern = '###\s+(\w+)\s+(/[^\s\n]*)'
        $matches = [regex]::Matches($content, $endpointPattern)

        foreach ($match in $matches) {
            $method = $match.Groups[1].Value
            $path = $match.Groups[2].Value

            $apiIndex += [PSCustomObject]@{
                project_id = $project.id
                project_name = $project.name
                method = $method
                path = $path
                spec_file = "specs/projects/$($project.id)/001-existing-code/api-spec.md"
            }
        }
    }

    return $apiIndex
}

function Get-TechnologyMatrix {
    <#
    .SYNOPSIS
        Build technology matrix from project metadata
    #>
    param([object[]]$MetadataList)

    $matrix = @{
        languages = @{}
        frameworks = @{}
        databases = @{}
        build_tools = @{}
    }

    foreach ($metadata in $MetadataList) {
        # Languages
        if ($metadata.technology) {
            $lang = $metadata.technology
            if (-not $matrix.languages.ContainsKey($lang)) {
                $matrix.languages[$lang] = @()
            }
            $matrix.languages[$lang] += $metadata.id
        }

        # Frameworks
        if ($metadata.framework) {
            $fw = $metadata.framework
            if (-not $matrix.frameworks.ContainsKey($fw)) {
                $matrix.frameworks[$fw] = @()
            }
            $matrix.frameworks[$fw] += $metadata.id
        }

        # Build Tools
        if ($metadata.build_tools) {
            foreach ($tool in $metadata.build_tools) {
                if (-not $matrix.build_tools.ContainsKey($tool)) {
                    $matrix.build_tools[$tool] = @()
                }
                $matrix.build_tools[$tool] += $metadata.id
            }
        }
    }

    return $matrix
}

function Get-DependencyGraph {
    <#
    .SYNOPSIS
        Extract key dependencies across all projects
    #>
    param([object[]]$MetadataList)

    $dependencies = @{}

    foreach ($metadata in $MetadataList) {
        if ($metadata.key_dependencies) {
            foreach ($dep in $metadata.key_dependencies) {
                if (-not $dependencies.ContainsKey($dep)) {
                    $dependencies[$dep] = @()
                }
                $dependencies[$dep] += $metadata.id
            }
        }
    }

    # Sort by usage count
    $sorted = $dependencies.GetEnumerator() | Sort-Object { $_.Value.Count } -Descending

    return $sorted
}

function New-MarkdownCatalog {
    <#
    .SYNOPSIS
        Generate catalog in Markdown format
    #>
    param(
        [object]$Config,
        [object[]]$MetadataList,
        [object[]]$APIIndex,
        [object]$TechMatrix,
        [object[]]$Dependencies
    )

    $lines = @()

    # Header
    $lines += "# Project Catalog"
    $lines += ""
    $lines += "**Generated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $lines += "**Total Projects:** $($Config.projects.Count)"
    $lines += "**API Endpoints:** $($APIIndex.Count)"
    $lines += ""
    $lines += "---"
    $lines += ""

    # Quick Navigation
    $lines += "## Quick Navigation"
    $lines += ""
    $lines += "| Project | Type | Technology | Status | Spec Dir |"
    $lines += "|---------|------|------------|--------|----------|"

    foreach ($project in $Config.projects) {
        $metadata = $MetadataList | Where-Object { $_.id -eq $project.id }
        $type = if ($metadata) { $metadata.type } else { "unknown" }
        $tech = if ($metadata) { $metadata.technology } else { "unknown" }
        $status = if ($project.status) { $project.status } else { "unknown" }
        $specDir = "specs/$($project.spec_dir)"

        $lines += "| [$($project.name)]($specDir) | $type | $tech | $status | ``$specDir`` |"
    }

    $lines += ""
    $lines += "---"
    $lines += ""

    # Technology Matrix
    $lines += "## Technology Matrix"
    $lines += ""

    # Languages
    $lines += "### Languages"
    $lines += ""
    foreach ($entry in $TechMatrix.languages.GetEnumerator() | Sort-Object Name) {
        $projectCount = $entry.Value.Count
        $projectList = ($entry.Value | ForEach-Object { "``$_``" }) -join ", "
        $lines += "- **$($entry.Key)** ($projectCount): $projectList"
    }
    $lines += ""

    # Frameworks
    if ($TechMatrix.frameworks.Count -gt 0) {
        $lines += "### Frameworks"
        $lines += ""
        foreach ($entry in $TechMatrix.frameworks.GetEnumerator() | Sort-Object Name) {
            $projectCount = $entry.Value.Count
            $projectList = ($entry.Value | ForEach-Object { "``$_``" }) -join ", "
            $lines += "- **$($entry.Key)** ($projectCount): $projectList"
        }
        $lines += ""
    }

    # Build Tools
    if ($TechMatrix.build_tools.Count -gt 0) {
        $lines += "### Build Tools"
        $lines += ""
        foreach ($entry in $TechMatrix.build_tools.GetEnumerator() | Sort-Object Name) {
            $projectCount = $entry.Value.Count
            $projectList = ($entry.Value | ForEach-Object { "``$_``" }) -join ", "
            $lines += "- **$($entry.Key)** ($projectCount): $projectList"
        }
        $lines += ""
    }

    $lines += "---"
    $lines += ""

    # API Endpoint Index
    if ($IncludeAPIs -and $APIIndex.Count -gt 0) {
        $lines += "## API Endpoint Index"
        $lines += ""
        $lines += "Total endpoints: $($APIIndex.Count)"
        $lines += ""

        # Group by project
        $byProject = $APIIndex | Group-Object project_id

        foreach ($group in $byProject) {
            $projectName = ($group.Group | Select-Object -First 1).project_name
            $lines += "### $projectName"
            $lines += ""

            # Group by method
            $byMethod = $group.Group | Group-Object method | Sort-Object Name

            foreach ($methodGroup in $byMethod) {
                $lines += "**$($methodGroup.Name)**:"
                $lines += ""
                foreach ($endpoint in ($methodGroup.Group | Sort-Object path)) {
                    $lines += "- ``$($endpoint.path)``"
                }
                $lines += ""
            }
        }

        $lines += "---"
        $lines += ""
    }

    # Dependency Overview
    if ($IncludeDependencies -and $Dependencies.Count -gt 0) {
        $lines += "## Popular Dependencies"
        $lines += ""
        $lines += "Top dependencies used across projects:"
        $lines += ""

        # Show top 15 most common dependencies
        $topDeps = $Dependencies | Select-Object -First 15

        foreach ($dep in $topDeps) {
            $projectCount = $dep.Value.Count
            $projectList = ($dep.Value | ForEach-Object { "``$_``" }) -join ", "
            $lines += "- **$($dep.Key)** ($projectCount): $projectList"
        }

        $lines += ""
        $lines += "---"
        $lines += ""
    }

    # Project Details
    $lines += "## Project Details"
    $lines += ""

    foreach ($project in $Config.projects) {
        $metadata = $MetadataList | Where-Object { $_.id -eq $project.id }

        $lines += "### $($project.name)"
        $lines += ""
        $lines += "**ID:** ``$($project.id)``"
        $lines += "**Path:** ``$($project.path)``"
        $lines += "**Type:** $($metadata.type)"
        $lines += "**Technology:** $($metadata.technology)"

        if ($metadata.framework) {
            $lines += "**Framework:** $($metadata.framework)"
        }

        if ($metadata.runtime_version) {
            $lines += "**Runtime:** $($metadata.runtime) $($metadata.runtime_version)"
        }

        $lines += ""
        $lines += "**Specs:**"
        $lines += "- [README](specs/$($project.spec_dir)/README.md)"

        # Check for reverse-engineered specs
        $apiSpecPath = Join-Path $SPECS_DIR "projects" $project.id "001-existing-code" "api-spec.md"
        $modelsPath = Join-Path $SPECS_DIR "projects" $project.id "001-existing-code" "models.md"

        if (Test-Path $apiSpecPath) {
            $lines += "- [API Specification](specs/projects/$($project.id)/001-existing-code/api-spec.md)"
        }

        if (Test-Path $modelsPath) {
            $lines += "- [Data Models](specs/projects/$($project.id)/001-existing-code/models.md)"
        }

        $lines += ""
    }

    $lines += "---"
    $lines += ""

    # Footer
    $lines += "## Search & Navigation"
    $lines += ""
    $lines += "Use ``/speckit.find`` to search across projects:"
    $lines += ""
    $lines += "```bash"
    $lines += "# Find API endpoints"
    $lines += "/speckit.find --api ""users"""
    $lines += ""
    $lines += "# Find by technology"
    $lines += "/speckit.find --tech nodejs"
    $lines += ""
    $lines += "# Find by project"
    $lines += "/speckit.find --project api"
    $lines += "```"
    $lines += ""
    $lines += "---"
    $lines += ""
    $lines += "_Generated by Spec-Kit Phase 5: Integration & Catalog_"

    return $lines -join "`n"
}

function New-JsonCatalog {
    <#
    .SYNOPSIS
        Generate catalog in JSON format
    #>
    param(
        [object]$Config,
        [object[]]$MetadataList,
        [object[]]$APIIndex,
        [object]$TechMatrix,
        [object[]]$Dependencies
    )

    $catalog = @{
        generated_at = (Get-Date -Format 'o')
        total_projects = $Config.projects.Count
        total_apis = $APIIndex.Count
        projects = @()
        technology_matrix = @{
            languages = @{}
            frameworks = @{}
            build_tools = @{}
        }
        api_index = @()
        dependencies = @{}
    }

    # Projects
    foreach ($project in $Config.projects) {
        $metadata = $MetadataList | Where-Object { $_.id -eq $project.id }

        $projectData = @{
            id = $project.id
            name = $project.name
            path = $project.path
            type = $metadata.type
            technology = $metadata.technology
            framework = $metadata.framework
            status = $project.status
            spec_dir = "specs/$($project.spec_dir)"
        }

        $catalog.projects += $projectData
    }

    # Technology Matrix
    foreach ($entry in $TechMatrix.languages.GetEnumerator()) {
        $catalog.technology_matrix.languages[$entry.Key] = $entry.Value
    }
    foreach ($entry in $TechMatrix.frameworks.GetEnumerator()) {
        $catalog.technology_matrix.frameworks[$entry.Key] = $entry.Value
    }
    foreach ($entry in $TechMatrix.build_tools.GetEnumerator()) {
        $catalog.technology_matrix.build_tools[$entry.Key] = $entry.Value
    }

    # API Index
    $catalog.api_index = $APIIndex

    # Dependencies
    foreach ($dep in $Dependencies) {
        $catalog.dependencies[$dep.Key] = $dep.Value
    }

    return $catalog | ConvertTo-Json -Depth 10
}

function Save-CatalogCache {
    <#
    .SYNOPSIS
        Cache catalog data for fast regeneration
    #>
    param([object]$CatalogData)

    if (-not (Test-Path $CACHE_DIR)) {
        New-Item -ItemType Directory -Path $CACHE_DIR -Force | Out-Null
    }

    $cacheData = @{
        generated_at = (Get-Date -Format 'o')
        data = $CatalogData
    }

    $cacheData | ConvertTo-Json -Depth 10 | Set-Content $CATALOG_CACHE -Encoding UTF8
}

# ============================================================================
# Main Execution
# ============================================================================

function Main {
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host " Spec-Kit: Project Catalog (Phase 5)" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan

    # Step 1: Load configuration
    Write-StepHeader "Step 1: Loading spec-kit configuration..."
    $config = Get-SpeckitConfig
    Write-Success "Loaded $($config.projects.Count) projects"

    # Step 2: Load metadata
    Write-StepHeader "Step 2: Loading project metadata..."
    $metadataList = Get-ProjectMetadata -Projects $config.projects
    Write-Success "Loaded metadata for $($metadataList.Count) projects"

    # Step 3: Extract API endpoints
    $apiIndex = @()
    if ($IncludeAPIs) {
        Write-StepHeader "Step 3: Indexing API endpoints..."
        $apiIndex = Get-ReverseEngineeredAPIs -Projects $config.projects
        Write-Success "Indexed $($apiIndex.Count) API endpoints"
    }

    # Step 4: Build technology matrix
    Write-StepHeader "Step 4: Building technology matrix..."
    $techMatrix = Get-TechnologyMatrix -MetadataList $metadataList
    $langCount = $techMatrix.languages.Count
    $fwCount = $techMatrix.frameworks.Count
    Write-Success "Found $langCount languages, $fwCount frameworks"

    # Step 5: Extract dependencies
    $dependencies = @()
    if ($IncludeDependencies) {
        Write-StepHeader "Step 5: Analyzing dependencies..."
        $dependencies = Get-DependencyGraph -MetadataList $metadataList
        Write-Success "Found $($dependencies.Count) unique dependencies"
    }

    # Step 6: Generate catalog
    Write-StepHeader "Step 6: Generating catalog..."

    if ($Json) {
        $catalog = New-JsonCatalog -Config $config -MetadataList $metadataList -APIIndex $apiIndex -TechMatrix $techMatrix -Dependencies $dependencies
        Write-Output $catalog
        Write-Success "Generated JSON catalog"
    } else {
        $catalog = New-MarkdownCatalog -Config $config -MetadataList $metadataList -APIIndex $apiIndex -TechMatrix $techMatrix -Dependencies $dependencies

        # Ensure output directory exists
        $outputDir = Split-Path -Parent $Output
        if ($outputDir -and -not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }

        # Write catalog
        $catalog | Set-Content $Output -Encoding UTF8
        Write-Success "Catalog saved to: $Output"

        # Token estimation
        $tokenEstimate = [int]($catalog.Length / 4)
        $tokenStatus = if ($tokenEstimate -lt 1000) { "✓ Optimized" } else { "⚠ High" }
        Write-Info "Token estimate: ~$tokenEstimate tokens $tokenStatus"
    }

    # Step 7: Cache results
    Write-StepHeader "Step 7: Caching catalog data..."
    $catalogData = @{
        config = $config
        metadata = $metadataList
        apis = $apiIndex
        tech_matrix = $techMatrix
        dependencies = $dependencies
    }
    Save-CatalogCache -CatalogData $catalogData
    Write-Success "Cached catalog data"

    # Summary
    Write-Host "`n================================" -ForegroundColor Cyan
    Write-Host " Catalog Complete!" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Summary:" -ForegroundColor White
    Write-Host "  Projects: $($config.projects.Count)" -ForegroundColor White
    Write-Host "  API Endpoints: $($apiIndex.Count)" -ForegroundColor White
    Write-Host "  Languages: $($techMatrix.languages.Count)" -ForegroundColor White
    Write-Host "  Frameworks: $($techMatrix.frameworks.Count)" -ForegroundColor White

    if (-not $Json) {
        Write-Host ""
        Write-Host "Output: $Output" -ForegroundColor White
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor White
        Write-Host "  1. Review catalog: cat $Output" -ForegroundColor Gray
        Write-Host "  2. Search projects: /speckit.find --api 'endpoint'" -ForegroundColor Gray
        Write-Host "  3. Navigate to project: cd specs/projects/{project-id}" -ForegroundColor Gray
    }
}

# Run main function
try {
    Main
} catch {
    Write-Host "`n✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
