<#
.SYNOPSIS
    Scan a Next.js / TypeScript web app repository and emit an inventory
    used by /speckit.constitution.scan to draft a properly-structured
    constitution.

.DESCRIPTION
    Mirrors scripts/bash/scan-repo.sh. Outputs JSON by default; pass -Text
    for a human-readable summary.

.PARAMETER Root
    Repository root to scan. Defaults to the .specify-aware repo root or
    git toplevel; falls back to the current working directory.

.PARAMETER Text
    Emit a human-readable summary instead of JSON.

.PARAMETER Json
    Emit JSON (default).
#>

[CmdletBinding()]
param(
    [string]$Root,
    [switch]$Text,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$MdHeadBytes = if ($env:SPECKIT_SCAN_MD_HEAD_BYTES) { [int]$env:SPECKIT_SCAN_MD_HEAD_BYTES } else { 4096 }
$MdMaxFiles  = if ($env:SPECKIT_SCAN_MAX_MD_FILES)  { [int]$env:SPECKIT_SCAN_MAX_MD_FILES  } else { 200 }

# ---- Resolve repo root --------------------------------------------------------

function Resolve-RepoRoot {
    param([string]$Hint)
    if ($Hint) {
        $p = (Resolve-Path -LiteralPath $Hint -ErrorAction Stop).Path
        return $p
    }
    # Walk upward for a .specify directory
    $dir = (Get-Location).Path
    while ($dir) {
        if (Test-Path -LiteralPath (Join-Path $dir '.specify') -PathType Container) {
            return $dir
        }
        $parent = Split-Path -Parent $dir
        if (-not $parent -or $parent -eq $dir) { break }
        $dir = $parent
    }
    # Git fallback
    try {
        $top = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $top) { return $top.Trim() }
    } catch { }
    return (Get-Location).Path
}

$RepoRoot = Resolve-RepoRoot -Hint $Root
Push-Location -LiteralPath $RepoRoot
try {

# ---- Helpers ------------------------------------------------------------------

$IgnoreDirNames = @(
    'node_modules','.git','.next','.turbo','.vercel','dist','build','out',
    'coverage','.cache','.specify','.yarn','.pnpm-store'
)

function Test-PathIgnored {
    param([string]$Path)
    foreach ($seg in ($Path -split '[\\/]+')) {
        if ($IgnoreDirNames -contains $seg) { return $true }
    }
    return $false
}

function Find-Files {
    param(
        [string[]]$Include,
        [string]$RootDir = '.'
    )
    Get-ChildItem -LiteralPath $RootDir -Recurse -File -Include $Include -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $rel = Resolve-Path -LiteralPath $_.FullName -Relative
            -not (Test-PathIgnored -Path $rel)
        }
}

function Test-FirstExisting {
    param([string[]]$Candidates)
    foreach ($c in $Candidates) {
        if (Test-Path -LiteralPath $c -PathType Leaf) { return $c }
    }
    return $null
}

function Get-StrippedJson {
    param([string]$Text)
    # Strip // line and /* block */ comments and trailing commas (tsconfig-style)
    $t = [regex]::Replace($Text, '/\*.*?\*/', '', 'Singleline')
    $t = [regex]::Replace($t, '(?m)^\s*//.*$', '')
    $t = [regex]::Replace($t, ',(\s*[}\]])', '$1')
    return $t
}

# ---- package.json -------------------------------------------------------------

$PkgInventory = @{ present = $false }
if (Test-Path -LiteralPath 'package.json' -PathType Leaf) {
    try {
        $raw = Get-Content -LiteralPath 'package.json' -Raw -Encoding UTF8
        $pkg = $raw | ConvertFrom-Json -ErrorAction Stop

        $deps     = @{}
        $devdeps  = @{}
        $peerdeps = @{}
        if ($pkg.PSObject.Properties['dependencies'])     { $pkg.dependencies.PSObject.Properties     | ForEach-Object { $deps[$_.Name]     = $_.Value } }
        if ($pkg.PSObject.Properties['devDependencies'])  { $pkg.devDependencies.PSObject.Properties  | ForEach-Object { $devdeps[$_.Name]  = $_.Value } }
        if ($pkg.PSObject.Properties['peerDependencies']) { $pkg.peerDependencies.PSObject.Properties | ForEach-Object { $peerdeps[$_.Name] = $_.Value } }
        $all = @{}
        foreach ($d in @($deps,$devdeps,$peerdeps)) { foreach ($k in $d.Keys) { $all[$k] = $d[$k] } }

        function Has { param([string]$n) return $all.ContainsKey($n) }

        $scripts = @()
        if ($pkg.PSObject.Properties['scripts']) {
            $scripts = $pkg.scripts.PSObject.Properties.Name | Sort-Object
        }

        $signals = [ordered]@{
            has_next                  = (Has 'next')
            has_react                 = (Has 'react')
            has_typescript            = (Has 'typescript')
            has_eslint                = (Has 'eslint')
            has_prettier              = (Has 'prettier')
            has_biome                 = (Has '@biomejs/biome')
            has_vitest                = (Has 'vitest')
            has_jest                  = (Has 'jest')
            has_playwright            = (($all.Keys | Where-Object { $_ -like '@playwright/*' -or $_ -eq 'playwright' }).Count -gt 0)
            has_cypress               = (Has 'cypress')
            has_testing_library_react = (Has '@testing-library/react')
            has_zod                   = (Has 'zod')
            has_valibot               = (Has 'valibot')
            has_yup                   = (Has 'yup')
            has_prisma                = ((Has 'prisma') -or (Has '@prisma/client'))
            has_drizzle               = (Has 'drizzle-orm')
            has_kysely                = (Has 'kysely')
            has_authjs                = (($all.Keys | Where-Object { $_ -like 'next-auth*' -or $_ -like '@auth/*' }).Count -gt 0)
            has_clerk                 = (($all.Keys | Where-Object { $_ -like '@clerk/*' }).Count -gt 0)
            has_lucia                 = (Has 'lucia')
            has_tailwind              = (Has 'tailwindcss')
            has_rate_limit            = ((Has '@upstash/ratelimit') -or (Has 'express-rate-limit'))
            has_argon2                = ((Has 'argon2') -or (Has '@node-rs/argon2'))
            has_bcrypt                = ((Has 'bcrypt') -or (Has 'bcryptjs'))
            has_pino                  = (Has 'pino')
            has_winston               = (Has 'winston')
            has_otel                  = (($all.Keys | Where-Object { $_ -like '@opentelemetry/*' }).Count -gt 0)
            has_sentry                = (($all.Keys | Where-Object { $_ -like '@sentry/*' }).Count -gt 0)
            has_husky                 = (Has 'husky')
            has_lint_staged           = (Has 'lint-staged')
        }

        $engines = $null
        if ($pkg.PSObject.Properties['engines']) {
            $engines = @{}
            $pkg.engines.PSObject.Properties | ForEach-Object { $engines[$_.Name] = $_.Value }
        }

        $PkgInventory = [ordered]@{
            present         = $true
            name            = $pkg.name
            version         = $pkg.version
            private         = [bool]($pkg.PSObject.Properties['private'] -and $pkg.private)
            type            = $pkg.type
            engines         = $engines
            package_manager = $pkg.packageManager
            scripts         = $scripts
            dep_count       = $deps.Count
            devdep_count    = $devdeps.Count
            peer_count      = $peerdeps.Count
            next_version    = if ($deps['next'])      { $deps['next'] }      else { $devdeps['next'] }
            react_version   = if ($deps['react'])     { $deps['react'] }     else { $devdeps['react'] }
            ts_version      = if ($deps['typescript']){ $deps['typescript'] }else { $devdeps['typescript'] }
            node_engine     = if ($engines) { $engines['node'] } else { $null }
            signals         = $signals
        }
    } catch {
        $PkgInventory = @{ present = $true; error = "failed to parse package.json: $($_.Exception.Message)" }
    }
}

# ---- tsconfig.json ------------------------------------------------------------

$TsConfigInventory = @{ present = $false }
$TsConfigPath = Test-FirstExisting @('tsconfig.json','tsconfig.base.json')
if ($TsConfigPath) {
    try {
        $raw = Get-Content -LiteralPath $TsConfigPath -Raw -Encoding UTF8
        $clean = Get-StrippedJson -Text $raw
        $cfg = $clean | ConvertFrom-Json -ErrorAction Stop
        $co = if ($cfg.PSObject.Properties['compilerOptions']) { $cfg.compilerOptions } else { $null }
        $TsConfigInventory = [ordered]@{
            present                       = $true
            path                          = $TsConfigPath
            extends                       = $cfg.extends
            strict                        = if ($co) { $co.strict } else { $null }
            noUncheckedIndexedAccess      = if ($co) { $co.noUncheckedIndexedAccess } else { $null }
            noImplicitOverride            = if ($co) { $co.noImplicitOverride } else { $null }
            exactOptionalPropertyTypes    = if ($co) { $co.exactOptionalPropertyTypes } else { $null }
            noImplicitAny                 = if ($co) { $co.noImplicitAny } else { $null }
            noUnusedLocals                = if ($co) { $co.noUnusedLocals } else { $null }
            noUnusedParameters            = if ($co) { $co.noUnusedParameters } else { $null }
            target                        = if ($co) { $co.target } else { $null }
            module                        = if ($co) { $co.module } else { $null }
            moduleResolution              = if ($co) { $co.moduleResolution } else { $null }
            jsx                           = if ($co) { $co.jsx } else { $null }
            paths_count                   = if ($co -and $co.PSObject.Properties['paths']) { ($co.paths.PSObject.Properties | Measure-Object).Count } else { 0 }
        }
    } catch {
        $TsConfigInventory = @{ present = $true; path = $TsConfigPath; error = "parse failed: $($_.Exception.Message)" }
    }
}

# ---- Next.js & structure ------------------------------------------------------

$NextConfigFile = Test-FirstExisting @('next.config.ts','next.config.mjs','next.config.js','next.config.cjs')
$HasAppDir   = (Test-Path -LiteralPath 'app' -PathType Container) -or (Test-Path -LiteralPath 'src/app' -PathType Container)
$HasPagesDir = (Test-Path -LiteralPath 'pages' -PathType Container) -or (Test-Path -LiteralPath 'src/pages' -PathType Container)
$HasMiddleware = [bool](Test-FirstExisting @('middleware.ts','middleware.js','src/middleware.ts','src/middleware.js'))

$RouteHandlerCount = 0
if ($HasAppDir) {
    $RouteHandlerCount = (Find-Files -Include @('route.ts','route.tsx','route.js') | Measure-Object).Count
}

# Scan for "use client" / "use server" pragmas
$SourceFiles = Find-Files -Include @('*.ts','*.tsx','*.js','*.jsx')
$UseClientCount = 0
$UseServerCount = 0
$ServerOnlyCount = 0
$ClientOnlyCount = 0
foreach ($f in $SourceFiles) {
    try {
        $head = Get-Content -LiteralPath $f.FullName -TotalCount 5 -ErrorAction SilentlyContinue
        if (-not $head) { continue }
        $joined = ($head -join "`n")
        if ($joined -match "^\s*['""]use client['""]") { $UseClientCount++ }
        if ($joined -match "^\s*['""]use server['""]") { $UseServerCount++ }
        $full = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
        if ($full) {
            # Match both `import 'server-only'` and `import x from 'server-only'`
            if ($full -match "(?m)^\s*import\s+(?:[^'""]+\s+from\s+)?['""]server-only['""]") { $ServerOnlyCount++ }
            if ($full -match "(?m)^\s*import\s+(?:[^'""]+\s+from\s+)?['""]client-only['""]") { $ClientOnlyCount++ }
        }
    } catch { }
}

$HasDal = $false
foreach ($d in @('lib/dal','src/lib/dal','server/dal','src/server/dal','data/dal','src/data/dal')) {
    if (Test-Path -LiteralPath $d -PathType Container) { $HasDal = $true; break }
}

# ---- Tooling ------------------------------------------------------------------

$HasEslint  = [bool](Test-FirstExisting @('.eslintrc','.eslintrc.json','.eslintrc.js','.eslintrc.cjs','eslint.config.js','eslint.config.mjs','eslint.config.cjs','eslint.config.ts'))
$HasPrettier= [bool](Test-FirstExisting @('.prettierrc','.prettierrc.json','.prettierrc.js','.prettierrc.cjs','prettier.config.js','prettier.config.cjs','prettier.config.mjs','.prettierrc.yaml','.prettierrc.yml'))
$HasBiome   = [bool](Test-FirstExisting @('biome.json','biome.jsonc'))
$HasEditorConfig = Test-Path -LiteralPath '.editorconfig' -PathType Leaf
$HasHusky   = Test-Path -LiteralPath '.husky' -PathType Container

$CiWorkflows = @()
if (Test-Path -LiteralPath '.github/workflows' -PathType Container) {
    $CiWorkflows = Get-ChildItem -LiteralPath '.github/workflows' -File -Include '*.yml','*.yaml' -ErrorAction SilentlyContinue |
        ForEach-Object { ".github/workflows/" + $_.Name } | Sort-Object
}

$EnvFiles = @()
foreach ($f in @('.env.example','.env.sample','.env.template','.env.local.example')) {
    if (Test-Path -LiteralPath $f -PathType Leaf) { $EnvFiles += $f }
}

$NodeVersionFile = $null
$NodeVersionValue = $null
if (Test-Path -LiteralPath '.nvmrc' -PathType Leaf) {
    $NodeVersionFile = '.nvmrc'
    $NodeVersionValue = (Get-Content -LiteralPath '.nvmrc' -TotalCount 1 -ErrorAction SilentlyContinue).Trim()
} elseif (Test-Path -LiteralPath '.node-version' -PathType Leaf) {
    $NodeVersionFile = '.node-version'
    $NodeVersionValue = (Get-Content -LiteralPath '.node-version' -TotalCount 1 -ErrorAction SilentlyContinue).Trim()
} elseif (Test-Path -LiteralPath '.tool-versions' -PathType Leaf) {
    $NodeVersionFile = '.tool-versions'
    $match = Select-String -LiteralPath '.tool-versions' -Pattern '^node\s+(\S+)' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($match) { $NodeVersionValue = $match.Matches[0].Groups[1].Value }
}

$HasTestsDir = $false
foreach ($d in @('__tests__','tests','test','e2e')) {
    $found = Get-ChildItem -Path . -Recurse -Directory -Filter $d -Force -ErrorAction SilentlyContinue |
        Where-Object { -not (Test-PathIgnored -Path (Resolve-Path -LiteralPath $_.FullName -Relative)) }
    if ($found) { $HasTestsDir = $true; break }
}

$HasGit = $false
$GitRemoteUrl = $null
$GitDefaultBranch = $null
try {
    git rev-parse --is-inside-work-tree 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $HasGit = $true
        $remote = git remote get-url origin 2>$null
        if ($LASTEXITCODE -eq 0 -and $remote) { $GitRemoteUrl = $remote.Trim() }
        $defaultRef = git symbolic-ref --short refs/remotes/origin/HEAD 2>$null
        if ($LASTEXITCODE -eq 0 -and $defaultRef) {
            $GitDefaultBranch = ($defaultRef -replace '^origin/','').Trim()
        }
    }
} catch { }

$HasConstitution = Test-Path -LiteralPath '.specify/memory/constitution.md' -PathType Leaf

# ---- Markdown inventory -------------------------------------------------------

$AllMd = Find-Files -Include @('*.md','*.mdx') |
    Sort-Object { (Resolve-Path -LiteralPath $_.FullName -Relative) -replace '^\.[\\/]','' }
$MdTotal = ($AllMd | Measure-Object).Count

$KnownDocs = @()
foreach ($f in @('README.md','README.MD','ARCHITECTURE.md','CONTRIBUTING.md','SECURITY.md',
                 'CODE_OF_CONDUCT.md','CHANGELOG.md','AGENTS.md','CLAUDE.md','GEMINI.md',
                 '.github/copilot-instructions.md')) {
    if (Test-Path -LiteralPath $f -PathType Leaf) { $KnownDocs += $f }
}

function Get-MdSummary {
    param([System.IO.FileInfo]$File)
    $rel = (Resolve-Path -LiteralPath $File.FullName -Relative) -replace '^\.[\\/]',''
    $info = [ordered]@{ path = $rel; size = $File.Length }
    try {
        $stream = [System.IO.File]::Open($File.FullName, 'Open', 'Read', 'ReadWrite')
        try {
            $buf = New-Object byte[] $MdHeadBytes
            $read = $stream.Read($buf, 0, $MdHeadBytes)
        } finally {
            $stream.Dispose()
        }
        $text = [System.Text.Encoding]::UTF8.GetString($buf, 0, $read)
        $headings = New-Object System.Collections.ArrayList
        $excerpt = ''
        foreach ($line in ($text -split "`r?`n")) {
            if ($headings.Count -ge 25) { break }
            if ($line -match '^(#{1,6})\s+(.*\S)\s*$') {
                [void]$headings.Add([ordered]@{ level = $Matches[1].Length; text = $Matches[2].Substring(0, [Math]::Min(200,$Matches[2].Length)) })
            } elseif (-not $excerpt) {
                $trim = $line.Trim()
                if ($trim -and -not $trim.StartsWith('#') -and -not $trim.StartsWith('<!--')) {
                    $excerpt = $trim.Substring(0, [Math]::Min(300,$trim.Length))
                }
            }
        }
        $info.headings = @($headings)
        $info.excerpt = $excerpt
    } catch {
        $info.error = "read failed: $($_.Exception.Message)"
    }
    return $info
}

$MdListed = @()
$idx = 0
foreach ($f in $AllMd) {
    if ($idx -ge $MdMaxFiles) { break }
    $MdListed += Get-MdSummary -File $f
    $idx++
}
$MdTruncated = $MdTotal -gt $MdMaxFiles

# ---- Output -------------------------------------------------------------------

$Result = [ordered]@{
    schema_version = '1.0'
    repo_root      = $RepoRoot
    package_json   = $PkgInventory
    tsconfig       = $TsConfigInventory
    nextjs = [ordered]@{
        config_file         = $NextConfigFile
        has_app_dir         = $HasAppDir
        has_pages_dir       = $HasPagesDir
        has_middleware      = $HasMiddleware
        route_handler_count = $RouteHandlerCount
    }
    directives = [ordered]@{
        use_client_files     = $UseClientCount
        use_server_files     = $UseServerCount
        server_only_imports  = $ServerOnlyCount
        client_only_imports  = $ClientOnlyCount
    }
    data_access = [ordered]@{
        has_dal_directory = $HasDal
    }
    tooling = [ordered]@{
        eslint        = $HasEslint
        prettier      = $HasPrettier
        biome         = $HasBiome
        editorconfig  = $HasEditorConfig
        husky         = $HasHusky
        ci_workflows  = $CiWorkflows
    }
    environment = [ordered]@{
        env_example_files = $EnvFiles
        node_version_file = $NodeVersionFile
        node_version      = $NodeVersionValue
    }
    testing = [ordered]@{
        has_tests_directory = $HasTestsDir
    }
    git = [ordered]@{
        is_repo         = $HasGit
        origin_url      = $GitRemoteUrl
        default_branch  = $GitDefaultBranch
    }
    constitution = [ordered]@{
        exists = $HasConstitution
        path   = '.specify/memory/constitution.md'
    }
    markdown = [ordered]@{
        total      = $MdTotal
        listed     = $MdListed.Count
        truncated  = $MdTruncated
        known_docs = $KnownDocs
        files      = $MdListed
    }
}

if ($Text) {
    Write-Output "Repo root:           $RepoRoot"
    Write-Output ("package.json:        " + ($(if ($PkgInventory.present) {'present'} else {'absent'})))
    Write-Output ("tsconfig.json:       " + ($(if ($TsConfigInventory.present) {'present'} else {'absent'})))
    Write-Output ("next.config:         " + ($(if ($NextConfigFile) {$NextConfigFile} else {'absent'})))
    Write-Output "App Router (app/):   $HasAppDir"
    Write-Output "Pages Router:        $HasPagesDir"
    Write-Output "middleware:          $HasMiddleware"
    Write-Output "route handlers:      $RouteHandlerCount"
    Write-Output "use client files:    $UseClientCount"
    Write-Output "use server files:    $UseServerCount"
    Write-Output "server-only imports: $ServerOnlyCount"
    Write-Output "client-only imports: $ClientOnlyCount"
    Write-Output "DAL directory:       $HasDal"
    Write-Output "ESLint:              $HasEslint"
    Write-Output "Prettier:            $HasPrettier"
    Write-Output "Biome:               $HasBiome"
    Write-Output "Husky:               $HasHusky"
    Write-Output ("CI workflows:        " + ($CiWorkflows -join ' '))
    Write-Output ("Env example files:   " + ($EnvFiles -join ' '))
    Write-Output ("Node version:        " + ($(if ($NodeVersionValue) {$NodeVersionValue} else {'unknown'})) + " (from " + ($(if ($NodeVersionFile) {$NodeVersionFile} else {'no file'})) + ")")
    Write-Output "Tests directory:     $HasTestsDir"
    Write-Output "Git repository:      $HasGit"
    Write-Output "Constitution file:   $HasConstitution"
    Write-Output "Markdown files:      $MdTotal"
    if ($KnownDocs.Count -gt 0) {
        Write-Output "Known docs:"
        foreach ($d in $KnownDocs) { Write-Output "  - $d" }
    }
} else {
    $Result | ConvertTo-Json -Depth 8
}

} finally {
    Pop-Location
}
