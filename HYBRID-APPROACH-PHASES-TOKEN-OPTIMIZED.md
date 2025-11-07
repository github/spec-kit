# Hybrid Approach: Token-Optimized Implementation Phases (Windows-First)

**Vision:** Implement Universal Adoption by extending existing capabilities with extreme focus on token efficiency

**Core Principle:** Every feature must operate within token budget constraints, using caching, progressive disclosure, and lazy loading

**Platform Strategy:** **Windows/PowerShell First**, Bash/Linux Later

**Date:** 2025-11-07 (Updated)

---

## Platform Implementation Strategy

### Windows-First Approach

**Rationale:**
- Focus on complete PowerShell (.ps1) implementation first
- Validate all features on Windows platform
- Achieve full functionality before porting
- Bash (.sh) port in final phase after Windows is proven

**Implementation Order:**
1. **Phases 1-5:** PowerShell implementation only (Weeks 1-10)
2. **Phase 6:** Bash/Linux port (Weeks 11-12)

**Benefits:**
- ✅ Faster time-to-value (one platform fully working)
- ✅ Clear validation before duplication
- ✅ Easier to maintain during development
- ✅ Windows users get features immediately

---

## Token Optimization Philosophy

### The Problem

**Without optimization, Universal Adoption could consume massive tokens:**

```
Scenario: Discover 10 projects in existing codebase

Naive Approach:
- Load all project files: 50,000 lines × 0.25 tokens/char × 80 chars/line = 1M tokens
- Parse all code: 500K tokens
- Extract APIs from all: 200K tokens
- Generate all specs: 300K tokens
Total: 2M+ tokens (UNACCEPTABLE)
```

### The Solution

**Token-optimized approach (target: < 10K tokens per operation):**

```
Optimized Approach:
- Discover projects (metadata only): 500 tokens
- Cache discoveries: 0 tokens on subsequent runs
- Lazy load per project: Only when accessed (2K tokens each)
- Progressive spec generation: One at a time (3K tokens each)
- Quick-refs first: 200 tokens vs 2,400 tokens
Total: 500-3,000 tokens typical operation (99.7% savings)
```

### Token Budget Targets

| Operation | Target | Maximum | Optimization Strategy |
|-----------|--------|---------|----------------------|
| Project Discovery | 500 tokens | 1,000 tokens | Metadata only, no code reads |
| Single Project Analysis | 2,000 tokens | 5,000 tokens | Progressive disclosure, sampling |
| API Extraction | 1,500 tokens | 3,000 tokens | Targeted searches, no full file reads |
| Spec Generation | 3,000 tokens | 8,000 tokens | Template-based, cached extractions |
| Project Catalog View | 500 tokens | 1,000 tokens | From cache, no live analysis |
| Full Repo Onboarding | 5,000 tokens | 10,000 tokens | Metadata only, defer deep analysis |

**Key Constraint:** No single operation should exceed 10K tokens

---

## Phase 1: Token-Optimized Discovery Engine (Weeks 1-2) 🪟 PowerShell

### Goal
Scan repository and detect all projects using **metadata-only approach** (no code reading)

### Implementation: PowerShell Only

#### 1.1 Extend `project-analysis.ps1` with `-Discover` Parameter

**Location:** `scripts/powershell/project-analysis.ps1`

**New functionality:**
```powershell
# Command usage
/speckit.project-analysis --discover

# PowerShell script invocation
.\scripts\powershell\project-analysis.ps1 -Json -Discover

# Options:
-Discover              # Metadata-only discovery
-Cached               # Use cached results (0 tokens!)
-Force                # Force rescan (ignore cache)
-Json                 # JSON output for tooling
```

**Token Optimization Techniques:**

##### A. Metadata-Only Scanning (Primary Strategy)

**Don't read files, just check existence and metadata:**

```powershell
# ❌ BAD: Reading files (500 tokens per file)
Get-Content "package.json"

# ✅ GOOD: Just check existence and size (10 tokens)
if (Test-Path "package.json") {
    $size = (Get-Item "package.json").Length
    Write-Output "Found: package.json ($size bytes)"
}
```

**Discovery workflow (PowerShell):**

```powershell
# 1. Find project indicators (file existence only)
$indicators = @(
    "package.json",
    "requirements.txt",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "*.csproj",
    "*.sln"
)

$projectFiles = @()
foreach ($indicator in $indicators) {
    $found = Get-ChildItem -Path . -Filter $indicator -Recurse -ErrorAction SilentlyContinue `
        | Where-Object { $_.FullName -notmatch "(node_modules|venv|\.git|build|dist)" }
    $projectFiles += $found
}
# Result: List of paths (50-100 tokens for 10 projects)

# 2. Classify by indicator type
$projects = @()
foreach ($file in $projectFiles) {
    $type = switch ($file.Name) {
        "package.json"     { "nodejs" }
        "requirements.txt" { "python" }
        "go.mod"          { "go" }
        "Cargo.toml"      { "rust" }
        "pom.xml"         { "java" }
        { $_ -like "*.csproj" } { "csharp" }
        { $_ -like "*.sln" }    { "csharp" }
        default           { "unknown" }
    }

    $projects += @{
        Path = $file.DirectoryName
        Type = $type
        Indicator = $file.Name
    }
}
# Result: Project type mapping (100 tokens)

# 3. Detect project structure (directory names only)
$directories = Get-ChildItem -Directory | Select-Object -ExpandProperty Name
# Result: Directory structure (50 tokens)

# 4. Generate discovery cache
$cache = @{
    version = "1.0"
    scanned_at = Get-Date -Format "o"
    projects = $projects
} | ConvertTo-Json -Depth 10
$cache | Out-File ".speckit\cache\discovery.json" -Encoding UTF8
# Result: JSON metadata (300 tokens)
```

**Total: ~500 tokens for discovery**

##### B. Aggressive Caching

**Cache discovery results to `.speckit\cache\discovery.json`:**

```json
{
  "version": "1.0",
  "scanned_at": "2025-11-07T10:00:00Z",
  "repo_root": "C:\\Users\\user\\repo",
  "cache_hash": "abc123...",
  "projects": [
    {
      "id": "services-api",
      "path": "services\\api",
      "type": "backend-api",
      "technology": "nodejs",
      "framework": "express",
      "indicators": {
        "package_json": true,
        "dockerfile": true,
        "src_dir": true
      },
      "size_bytes": 145000,
      "file_count": 87,
      "last_modified": "2025-11-06T15:30:00Z"
    }
  ]
}
```

**Cache invalidation (PowerShell):**

```powershell
# Compute cache hash from directory structure
$indicators = Get-ChildItem -Recurse -Include "package.json","requirements.txt" `
    | Sort-Object FullName `
    | Select-Object -ExpandProperty FullName

$hashInput = $indicators -join "`n"
$hash = Get-FileHash -InputStream ([System.IO.MemoryStream]::new([System.Text.Encoding]::UTF8.GetBytes($hashInput))) -Algorithm MD5

# Compare with cached hash
$cacheFile = ".speckit\cache\discovery.json"
if (Test-Path $cacheFile) {
    $cached = Get-Content $cacheFile | ConvertFrom-Json
    if ($cached.cache_hash -eq $hash.Hash) {
        Write-Host "✓ Using cached discovery (0 tokens!)" -ForegroundColor Green
        Get-Content $cacheFile
        exit 0
    }
}
```

**Token savings: 100% on subsequent runs (0 tokens!)**

##### C. Lazy Framework Detection

**Don't detect framework during discovery - defer until needed:**

```powershell
# During discovery: Just detect language
$type = "nodejs"  # From package.json existence

# Later, when user requests analysis:
# /speckit.analyze --project=services-api
# THEN detect framework (progressive disclosure)
```

**Token savings: Defer 1,000 tokens per project until needed**

##### D. Exclude Common Directories

**Skip directories that won't have projects:**

```powershell
$excludePatterns = @(
    "node_modules",
    "venv",
    ".git",
    "build",
    "dist",
    "__pycache__",
    ".next",
    "target",
    "bin",
    "obj",
    "packages"  # NuGet packages
)

# Filter results
$projectFiles = $projectFiles | Where-Object {
    $path = $_.FullName
    $excluded = $false
    foreach ($pattern in $excludePatterns) {
        if ($path -match [regex]::Escape($pattern)) {
            $excluded = $true
            break
        }
    }
    -not $excluded
}
# 99% token reduction by not scanning these
```

#### 1.2 Output Format

**Concise discovery report (< 1,000 tokens):**

```markdown
# Project Discovery Report

**Scanned:** C:\Users\user\my-repo
**Cache:** Fresh scan (cache will be used on next run)
**Projects Found:** 7

## Quick Summary

| # | Name | Type | Tech | Path | Size |
|---|------|------|------|------|------|
| 1 | API Backend | Backend | Go | services\api | 145KB |
| 2 | User Service | Backend | Python | services\user | 98KB |
| 3 | Frontend | Frontend | React | frontend\ | 234KB |
| 4 | Mobile | Mobile | RN | mobile\ | 189KB |
| 5 | Legacy | Monolith | Django | legacy\ | 567KB |
| 6 | Shared Lib | Library | Python | libs\common | 23KB |
| 7 | CLI | CLI Tool | Rust | cli\ | 45KB |

## Next Steps

```powershell
# View detailed info for a project
/speckit.project-analysis --project=services-api

# Onboard all projects
/speckit.onboard --all

# Onboard specific projects
/speckit.onboard --projects=services-api,frontend
```

**Subsequent runs (from cache):**
```
✓ Using cached discovery (0 tokens)
✓ Last scan: 2 hours ago
✓ Projects: 7 (unchanged)

Tip: Use --force to rescan
```

#### 1.3 PowerShell Script Structure

**File:** `scripts/powershell/project-analysis.ps1`

```powershell
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Discover,
    [switch]$Cached,
    [switch]$Force,
    [switch]$CheckPatterns,
    [int]$SampleSize = 20
)

# Import common functions
. "$PSScriptRoot\common.ps1"

# Main discovery function
function Invoke-ProjectDiscovery {
    param(
        [bool]$UseCache = $true,
        [bool]$ForceRescan = $false
    )

    # Check cache first (unless force)
    if ($UseCache -and -not $ForceRescan) {
        $cached = Get-CachedDiscovery
        if ($cached) {
            return $cached
        }
    }

    # Perform discovery
    $projects = Find-Projects

    # Cache results
    Save-DiscoveryCache -Projects $projects

    return $projects
}

# Execute based on parameters
if ($Discover) {
    $results = Invoke-ProjectDiscovery -UseCache $Cached -ForceRescan $Force

    if ($Json) {
        $results | ConvertTo-Json -Depth 10
    } else {
        Format-DiscoveryReport -Projects $results
    }
}
```

### Token Budget: Phase 1 (PowerShell)

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Initial discovery scan | 500 | Metadata only, no file reads |
| Cached discovery | 0 | Cache hit (100% savings) |
| Display report | 500 | Concise table format |
| **Total (first run)** | **1,000** | ✅ Under budget |
| **Total (cached)** | **0-500** | ✅ Near-zero cost |

---

## Phase 2: Lightweight Project Analysis (Weeks 3-4) 🪟 PowerShell

### Goal
Analyze individual projects **on-demand** with token-efficient techniques

### Implementation: PowerShell Only

#### 2.1 Progressive Disclosure

**Load information incrementally, only what's needed:**

**Level 1: Metadata (50 tokens) - PowerShell**
```powershell
# Quick metadata
$metadata = @{
    id = "services-api"
    type = "backend-api"
    language = "go"
    size = "145KB"
} | ConvertTo-Json
```

**Level 2: Structure (200 tokens) - PowerShell**
```powershell
# Directory structure
$structure = @{
    entry_point = "cmd\api\main.go"
    directories = (Get-ChildItem -Directory | Select-Object -ExpandProperty Name)
    config_files = (Get-ChildItem -Include ".env.example","config.yaml" -Recurse | Select-Object -ExpandProperty Name)
} | ConvertTo-Json
```

**Level 3: Deep Analysis (2,000 tokens) - PowerShell**
```powershell
# Full analysis with sampling
$analysis = @{
    api_endpoints = Get-ApiEndpoints -SampleSize $SampleSize
    data_models = Get-DataModels -SampleSize $SampleSize
    dependencies = Get-Dependencies
} | ConvertTo-Json -Depth 10
```

**Usage:**
```powershell
# Quick check (50 tokens)
/speckit.info --project=services-api

# Structure view (200 tokens)
/speckit.info --project=services-api --structure

# Full analysis (2,000 tokens)
/speckit.analyze --project=services-api
```

#### 2.2 Targeted Extraction (No Full File Reads)

**Use Select-String (PowerShell grep) instead of loading entire files:**

**❌ Bad (Token-Heavy):**
```powershell
# Read entire file
Get-Content src\handlers\user.go  # 5,000 tokens

# Parse in AI
"Find all API endpoints in this file..."
```

**✅ Good (Token-Efficient):**
```powershell
# Extract only endpoints with Select-String
Select-String -Path "src\handlers\*.go" -Pattern "router\.(GET|POST|PUT|DELETE)" `
    | Select-Object LineNumber, Line, Filename

# Result:
# src\handlers\user.go:45: router.GET("/users"
# src\handlers\user.go:67: router.POST("/users"
# 50 tokens vs 5,000 tokens (99% savings)
```

**Extraction patterns by framework (PowerShell):**

**FastAPI (Python):**
```powershell
# Find API endpoints
Select-String -Path "src\*.py" -Pattern "@app\.(get|post|put|delete)" -AllMatches

# Find models
Select-String -Path "src\*.py" -Pattern "class.*BaseModel"

# Token cost: ~100 tokens (vs 10K for reading all files)
```

**Express (Node.js):**
```powershell
# Find API endpoints
Select-String -Path "src\*.js","src\*.ts" -Pattern "(app|router)\.(get|post|put|delete)"

# Token cost: ~100 tokens
```

**ASP.NET Core (C#):**
```powershell
# Find API endpoints
Select-String -Path "*.cs" -Pattern "\[Http(Get|Post|Put|Delete)\]"

# Find controllers
Select-String -Path "*.cs" -Pattern "class.*Controller.*:"

# Token cost: ~100 tokens
```

**Gin (Go):**
```powershell
# Find API endpoints
Select-String -Path "*.go" -Pattern "router\.(GET|POST|PUT|DELETE)"

# Token cost: ~100 tokens
```

**Django (Python):**
```powershell
# Find URL patterns
Select-String -Path "*urls.py" -Pattern "path\("

# Token cost: ~50 tokens
```

#### 2.3 Sampling Strategy for Large Projects

**For projects with >100 files, use statistical sampling:**

```powershell
# Instead of analyzing all files
$totalFiles = (Get-ChildItem -Path src -Recurse -Include "*.py").Count
Write-Host "Total files: $totalFiles"

# Analyze sample
$sampleSize = 20
$sample = Get-ChildItem -Path src -Recurse -Include "*.py" `
    | Get-Random -Count $sampleSize

foreach ($file in $sample) {
    Analyze-File -Path $file.FullName
}

# Note in report:
Write-Host "Analyzed $sampleSize of $totalFiles files ($(($sampleSize/$totalFiles*100).ToString('F1'))% sample)"

# Token cost: 2,000 tokens (vs 50,000 for all files = 96% savings)
```

**Sampling prioritization (PowerShell):**

```powershell
# 1. Entry points (highest priority)
$entryPoints = @("main.py", "index.js", "main.go", "Program.cs", "Startup.cs")
$priority1 = Get-ChildItem -Recurse -Include $entryPoints

# 2. API/route files
$apiPatterns = @("*controller*.cs", "*handler*.go", "*route*.js", "*view*.py")
$priority2 = Get-ChildItem -Recurse | Where-Object {
    $name = $_.Name.ToLower()
    $apiPatterns | Where-Object { $name -like $_ }
}

# 3. Model files
$modelPatterns = @("*model*.cs", "*model*.go", "*entity*.py")
$priority3 = Get-ChildItem -Recurse | Where-Object {
    $name = $_.Name.ToLower()
    $modelPatterns | Where-Object { $name -like $_ }
}

# 4. Largest files
$priority4 = Get-ChildItem -Recurse -File `
    | Sort-Object Length -Descending `
    | Select-Object -First 5

# 5. Recently modified
$priority5 = Get-ChildItem -Recurse -File `
    | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMonths(-1) } `
    | Sort-Object LastWriteTime -Descending `
    | Select-Object -First 5

# Combine and deduplicate
$sampled = @($priority1) + @($priority2) + @($priority3) + @($priority4) + @($priority5) `
    | Select-Object -Unique `
    | Select-Object -First $sampleSize
```

#### 2.4 Quick-Refs for Projects

**Generate ultra-compact project summaries (200 tokens):**

**PowerShell generation:**

```powershell
function New-ProjectQuickRef {
    param(
        [Parameter(Mandatory)]
        [PSCustomObject]$Project
    )

    $quickRef = @"
# $($Project.Name) Quick Reference

**Type:** $($Project.Type)
**Tech:** $($Project.Technology) + $($Project.Framework)
**Path:** $($Project.Path)

**Entry:** $($Project.EntryPoint)
**Endpoints:** $($Project.EndpointCount) ($($Project.TopEndpoints -join ', ')...)
**Models:** $($Project.Models -join ', ') ($($Project.ModelCount) total)

**Dependencies:**
- Internal: $($Project.InternalDeps -join ', ')
- External: $($Project.TopExternalDeps -join ', ')

**Config:** $($Project.ConfigVars -join ', ')

[Full Analysis →](./analysis.md)
"@

    $quickRef | Out-File "specs\projects\$($Project.Id)\quick-ref.md" -Encoding UTF8
}

# Token cost: 200 tokens (vs 2,400 for full analysis = 92% savings)
```

### Token Budget: Phase 2 (PowerShell)

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Quick info (metadata) | 50 | From cache |
| Structure view | 200 | Directory listing only |
| API extraction (Select-String) | 100-300 | Targeted search, no file reads |
| Model extraction (Select-String) | 100-300 | Targeted search |
| Quick-ref generation | 200 | Template-based |
| Full analysis (sampling) | 2,000 | Sample 20 files, extrapolate |
| **Total (typical)** | **1,000-2,000** | ✅ Under budget |
| **Total (full analysis)** | **3,000-5,000** | ✅ Under maximum |

---

## Phase 3: Token-Efficient Reverse Engineering (Weeks 5-7) 🪟 PowerShell

### Goal
Generate specs from existing code using template-driven approach with minimal token usage

### Implementation: PowerShell Only

#### 3.1 Template-Based Generation

**PowerShell workflow:**

```powershell
# 1. Extract structured data (PowerShell script, 0 AI tokens)
function Get-EndpointData {
    param([string]$ProjectPath)

    $endpoints = Select-String -Path "$ProjectPath\*.go" -Pattern "router\.(GET|POST|PUT|DELETE)" `
        | ForEach-Object {
            @{
                Method = $_.Matches[0].Groups[1].Value
                Line = $_.Line
                File = $_.Filename
                LineNumber = $_.LineNumber
            }
        }

    return $endpoints | ConvertTo-Json
}

$endpointsJson = Get-EndpointData -ProjectPath "services\api"
# Result: endpoints.json (500 tokens)

# 2. Fill template (PowerShell, 0 AI tokens)
function Fill-SpecTemplate {
    param(
        [string]$TemplatePath,
        [PSCustomObject]$Data
    )

    $template = Get-Content $TemplatePath -Raw

    # Replace placeholders
    $template = $template -replace '\{PROJECT_NAME\}', $Data.Name
    $template = $template -replace '\{ENDPOINTS\}', ($Data.Endpoints | ConvertTo-Json)
    # ... more replacements

    return $template
}

$specDraft = Fill-SpecTemplate -TemplatePath "templates\spec-template.md" -Data $data
# Result: spec-draft.md (2,000 tokens)

# 3. AI refinement (minimal tokens)
# AI sees: template + extracted data
# Task: "Add context and business purpose"
# Tokens: 2,000 input + 1,000 output = 3,000 total
```

**Token savings: 85% (3K vs 20K)**

#### 3.2 Incremental Spec Generation (PowerShell)

**Generate specs one section at a time:**

```powershell
# Step 1: API Endpoints (500 tokens)
$apiSection = Get-ApiEndpoints | Format-SpecSection -SectionType "API"
# AI task: "Format these endpoints in spec format"
# Input: 300 tokens (raw extraction)
# Output: 200 tokens (formatted section)
# Total: 500 tokens

# Step 2: Data Models (500 tokens)
$modelSection = Get-DataModels | Format-SpecSection -SectionType "Models"
# AI task: "Format these models in spec format"
# Total: 500 tokens

# Step 3: User Scenarios (1,500 tokens)
# This requires inference
# AI task: "Based on these endpoints and models, infer user scenarios"
# Input: API endpoints (200) + Models (200) = 400 tokens
# Output: User scenarios (1,000 tokens)
# Total: 1,500 tokens

# Step 4: Combine (100 tokens)
$sections = @($apiSection, $modelSection, $scenariosSection)
$fullSpec = $sections -join "`n`n"
$fullSpec | Out-File "specs\projects\api\spec.md" -Encoding UTF8
# AI task: "Quick coherence check"
# Total: 100 tokens
```

**Total: 2,600 tokens (incremental) vs 8,000 tokens (monolithic)**

#### 3.3 Confidence-Based Generation

**Only generate what we're confident about:**

```powershell
function Add-ConfidenceMarker {
    param(
        [string]$Content,
        [ValidateSet("High", "Medium", "Low")]
        [string]$Confidence
    )

    $marker = switch ($Confidence) {
        "High"   { "### ✅ High Confidence" }
        "Medium" { "### ⚠️ Medium Confidence" }
        "Low"    { "### ❓ Low Confidence - NEEDS REVIEW" }
    }

    return "$marker`n`n$Content"
}

# Usage
$endpoint = @"
GET /api/v1/users
- **Source:** handlers\user.go:45
- **Purpose:** List all users
- **Extracted:** Request/response from code
"@

$marked = Add-ConfidenceMarker -Content $endpoint -Confidence "High"
```

**Token optimization:**
- High confidence: Full generation (500 tokens)
- Medium confidence: Basic generation + flag (300 tokens)
- Low confidence: Placeholder + skip details (50 tokens)

**Savings: 50% by not elaborating on uncertain items**

### Token Budget: Phase 3 (PowerShell)

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Extract endpoints (PowerShell) | 300 | Script, no AI |
| Extract models (PowerShell) | 300 | Script, no AI |
| Generate API section | 500 | Template + AI format |
| Generate model section | 500 | Template + AI format |
| Infer user scenarios | 1,500 | AI inference needed |
| Generate quick-ref | 200 | Template-based |
| Coherence check | 100 | AI review |
| **Total per project** | **3,000-4,000** | ✅ Under budget |
| **7 projects (parallel)** | **3,000-4,000** | ✅ Isolated contexts |

---

## Phase 4: Non-Invasive Onboarding (Weeks 8-9) 🪟 PowerShell

### Goal
Set up spec-kit structure without modifying existing code, using cached data

### Implementation: PowerShell Only

#### 4.1 Metadata-Only Onboarding

**Create structure from cached discovery (near-zero tokens):**

```powershell
# /speckit.onboard --all

# Process:
# 1. Load discovery cache (0 tokens - from disk)
$discovery = Get-Content ".speckit\cache\discovery.json" | ConvertFrom-Json

# 2. Create directories (0 tokens - PowerShell operations)
foreach ($project in $discovery.projects) {
    New-Item -ItemType Directory -Path "specs\projects\$($project.id)" -Force | Out-Null
    New-Item -ItemType Directory -Path ".speckit\metadata" -Force | Out-Null
}

# 3. Generate config files (100 tokens - template filling)
$config = @{
    version = "1.0"
    mode = "universal"
    projects = $discovery.projects
} | ConvertTo-Json -Depth 10
$config | Out-File ".speckit.config.json" -Encoding UTF8

# 4. Create README (200 tokens - project list)
$readme = "# Projects`n`n" + ($discovery.projects | ForEach-Object { "- $($_.name)" }) -join "`n"
$readme | Out-File "docs\PROJECTS.md" -Encoding UTF8

# Total: 300 tokens for onboarding entire repo!
```

**Directory creation (no AI needed):**

```powershell
# Read from cache
$projects = (Get-Content ".speckit\cache\discovery.json" | ConvertFrom-Json).projects

# Create structure
foreach ($project in $projects) {
    $projectDir = "specs\projects\$($project.id)"
    New-Item -ItemType Directory -Path $projectDir -Force | Out-Null

    # Copy template (no AI, 0 tokens)
    Copy-Item "templates\project-quick-ref-template.md" "$projectDir\quick-ref.md"

    # Fill placeholders (no AI, PowerShell)
    $quickRef = Get-Content "$projectDir\quick-ref.md" -Raw
    $quickRef = $quickRef -replace '\{PROJECT_NAME\}', $project.name
    $quickRef = $quickRef -replace '\{PROJECT_TYPE\}', $project.type
    $quickRef | Out-File "$projectDir\quick-ref.md" -Encoding UTF8
}
```

#### 4.2 Lazy Spec Generation

**Don't generate all specs during onboarding - only create placeholders:**

```powershell
# PowerShell placeholder generation
$placeholder = @"
# $projectName

This project has been discovered but not yet analyzed.

**Quick Actions:**

``````powershell
# Analyze this project
/speckit.analyze --project=$projectId

# Reverse engineer spec
/speckit.reverse-engineer --project=$projectId

# View quick info
/speckit.info --project=$projectId
``````

**Status:** 🔍 Discovered, not analyzed
**Last Modified:** $(Get-Date -Format 'yyyy-MM-dd')
"@

$placeholder | Out-File "specs\projects\$projectId\README.md" -Encoding UTF8

# Token cost: 50 tokens per project placeholder
```

### Token Budget: Phase 4 (PowerShell)

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Load cached discovery | 0 | From disk |
| Create directory structure | 0 | PowerShell operations |
| Generate config files | 100 | Template filling |
| Create project READMEs | 50 × 7 = 350 | Simple placeholders |
| Generate platform README | 200 | Project list |
| **Total (metadata only)** | **650** | ✅ Minimal |
| **With analysis (optional)** | **+3,000** | Per project, on-demand |

---

## Phase 5: Unified Project Catalog (Week 10) 🪟 PowerShell

### Goal
Generate navigable catalog from cached metadata (near-zero tokens)

### Implementation: PowerShell Only

#### 5.1 Cache-Driven Catalog

**Generate entirely from cached data:**

```powershell
# /speckit.project-catalog

# Process:
# 1. Load discovery cache (0 tokens)
$discovery = Get-Content ".speckit\cache\discovery.json" | ConvertFrom-Json

# 2. Load project metadata (0 tokens)
$metadata = @{}
foreach ($project in $discovery.projects) {
    $metaFile = ".speckit\metadata\$($project.id).json"
    if (Test-Path $metaFile) {
        $metadata[$project.id] = Get-Content $metaFile | ConvertFrom-Json
    }
}

# 3. Generate catalog from template (200 tokens)
$catalog = @"
# Project Catalog

**Total Projects:** $($discovery.projects.Count)
**Last Updated:** $(Get-Date -Format 'yyyy-MM-dd HH:mm')

"@

foreach ($project in $discovery.projects) {
    $catalog += @"

## $($project.name)
**Type:** $($project.type) | **Tech:** $($project.technology) | **Path:** $($project.path)

[Quick Ref](../specs/projects/$($project.id)/quick-ref.md) (200 tokens)
[Full Analysis](../specs/projects/$($project.id)/analysis.md) (2,400 tokens)

"@
}

$catalog | Out-File "docs\PROJECT-CATALOG.md" -Encoding UTF8

# No live analysis needed!
# Token cost: ~200 tokens (just formatting)
```

#### 5.2 Lazy Dependency Graph

**Don't compute graph during catalog generation - compute on demand:**

```powershell
# Catalog generation (200 tokens)
.\New-ProjectCatalog.ps1

# Dependency graph (only when requested, 1,000 tokens)
.\New-ProjectCatalog.ps1 -ShowDependencies

# Visual graph (only when requested, 2,000 tokens)
.\New-ProjectCatalog.ps1 -Graph -Format Mermaid
```

### Token Budget: Phase 5 (PowerShell)

| Activity | Tokens | Optimization |
|----------|--------|--------------|
| Load cached discovery | 0 | From disk |
| Load project metadata | 0 | From disk |
| Generate catalog table | 200 | Template-based |
| Link to quick-refs | 0 | Static links |
| **Total (basic catalog)** | **200** | ✅ Ultra-efficient |
| **With dependencies** | **+1,000** | On-demand only |
| **With visual graph** | **+2,000** | On-demand only |

---

## Phase 6: Bash/Linux Port (Weeks 11-12) 🐧 Bash

### Goal
Port all PowerShell functionality to Bash for Linux/macOS support

### Implementation Strategy

**Direct port of PowerShell scripts to Bash equivalents:**

#### 6.1 Script Mapping

| PowerShell Script | Bash Script | Complexity |
|-------------------|-------------|------------|
| `project-analysis.ps1` | `project-analysis.sh` | Medium |
| Discovery functions | Direct translation | Low |
| Caching logic | JSON via `jq` | Medium |
| Extraction (Select-String) | `grep -r` | Low |
| Template filling | `sed`/`awk` | Low |
| JSON handling | `jq` | Low |

#### 6.2 Port Approach

**For each PowerShell script:**

1. **Copy PowerShell logic to Bash**
2. **Translate cmdlets:**
   - `Get-ChildItem` → `find` / `ls`
   - `Select-String` → `grep`
   - `ConvertTo-Json` → `jq`
   - `Test-Path` → `[ -f ]` / `[ -d ]`
   - `New-Item` → `mkdir` / `touch`

3. **Test on Linux/macOS**
4. **Ensure feature parity**

**Example translation:**

```powershell
# PowerShell
$files = Get-ChildItem -Path . -Filter "*.py" -Recurse `
    | Where-Object { $_.FullName -notmatch "venv" }
```

```bash
# Bash equivalent
files=$(find . -name "*.py" -type f | grep -v "venv")
```

#### 6.3 Validation

**Ensure both platforms work identically:**

- ✅ Same discovery results
- ✅ Same caching behavior
- ✅ Same token usage
- ✅ Same output format
- ✅ Same command interface

### Token Budget: Phase 6 (Bash Port)

| Activity | Tokens | Note |
|----------|--------|------|
| Translation (no AI needed) | 0 | Direct port |
| Testing/validation | 0 | Manual |
| Documentation updates | 500 | Update examples |
| **Total** | **500** | ✅ Minimal |

---

## Implementation Timeline

| Phase | Duration | Platform | Token Budget | Deliverable |
|-------|----------|----------|--------------|-------------|
| **Phase 1** | 2 weeks | 🪟 PowerShell | 1,000 | Discovery + Caching |
| **Phase 2** | 2 weeks | 🪟 PowerShell | 5,000 | Analysis + Extraction |
| **Phase 3** | 3 weeks | 🪟 PowerShell | 4,000 | Reverse Engineering |
| **Phase 4** | 2 weeks | 🪟 PowerShell | 1,000 | Non-Invasive Setup |
| **Phase 5** | 1 week | 🪟 PowerShell | 200 | Project Catalog |
| **Phase 6** | 2 weeks | 🐧 Bash | 500 | Linux/macOS Port |
| **TOTAL** | **12 weeks** | **Both** | **~11K** | **Universal Adoption** |

---

## Platform Support Matrix

| Phase | Windows (PowerShell) | Linux/macOS (Bash) |
|-------|---------------------|-------------------|
| Phases 1-5 | ✅ Full support | ❌ Not yet |
| Phase 6 | ✅ Full support | ✅ Full support |

---

## Success Metrics

### Token Efficiency Targets (Same for Both Platforms)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Discovery operation | < 1,000 tokens | Actual token count |
| Cached discovery | < 100 tokens | Cache hit ratio |
| Single project analysis | < 5,000 tokens | With sampling |
| Spec generation | < 4,000 tokens | Template-driven |
| Catalog generation | < 500 tokens | From cache |
| Daily typical usage | < 5,000 tokens | User workflow |
| Full repo onboarding | < 10,000 tokens | One-time cost |

---

## Next Steps

1. ✅ Review Windows-first approach
2. ✅ Approve PowerShell implementation priority
3. ⏳ Implement Phase 1 (PowerShell Discovery)
4. ⏳ Measure actual token usage on Windows
5. ⏳ Complete Phases 2-5 on Windows
6. ⏳ Port to Bash (Phase 6)

---

**Status:** Windows-first implementation plan ready
**Key Achievement:** Focus on complete PowerShell implementation before Bash port, ensuring quality and validation on one platform first
