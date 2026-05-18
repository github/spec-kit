<#
.SYNOPSIS
    Audit a TypeScript / Next.js codebase against the behavioral directives
    in the project constitution. PowerShell mirror of audit-codebase.sh.

.DESCRIPTION
    Emits a JSON report of findings with file:line locations, rule metadata,
    and remediation hints. Companion command: /speckit.audit (and
    /speckit.audit.deep, which layers tsc/eslint/npm-audit/LLM analysis on
    top of this script).

.PARAMETER Root
    Repository root (default: auto-detected via .specify or git).

.PARAMETER Paths
    Limit scan to these paths (comma-separated, relative to root).

.PARAMETER Rules
    Run only these rule IDs (comma-separated).

.PARAMETER Sections
    Run only these sections (comma-separated: TS, FE, BE, SEC, PERF, INFRA).

.PARAMETER Severity
    Minimum severity to include (critical|high|medium|low).

.PARAMETER MaxFindingsPerRule
    Cap findings per rule (default: 50).

.PARAMETER Text
    Emit human-readable summary instead of JSON.

.PARAMETER Json
    Emit JSON (default).

.PARAMETER ListRules
    Print rule catalog as JSON and exit.
#>

[CmdletBinding()]
param(
    [string]$Root,
    [string]$Paths,
    [string]$Rules,
    [string]$Sections,
    [ValidateSet('critical','high','medium','low')]
    [string]$Severity = 'low',
    [int]$MaxFindingsPerRule = 0,
    [switch]$Text,
    [switch]$Json,
    [switch]$ListRules
)

$ErrorActionPreference = 'Stop'
if ($MaxFindingsPerRule -le 0) {
    $MaxFindingsPerRule = if ($env:SPECKIT_AUDIT_MAX_PER_RULE) { [int]$env:SPECKIT_AUDIT_MAX_PER_RULE } else { 50 }
}
$SnippetMax = 200

# ---- Resolve repo root --------------------------------------------------------

function Resolve-RepoRoot {
    param([string]$Hint)
    if ($Hint) {
        return (Resolve-Path -LiteralPath $Hint -ErrorAction Stop).Path
    }
    $dir = (Get-Location).Path
    while ($dir) {
        if (Test-Path -LiteralPath (Join-Path $dir '.specify') -PathType Container) { return $dir }
        $parent = Split-Path -Parent $dir
        if (-not $parent -or $parent -eq $dir) { break }
        $dir = $parent
    }
    try {
        $top = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $top) { return $top.Trim() }
    } catch { }
    return (Get-Location).Path
}

$RepoRoot = Resolve-RepoRoot -Hint $Root
Push-Location -LiteralPath $RepoRoot
try {

# ---- Rule catalog -------------------------------------------------------------

$RuleCatalog = @(
    @{ id='TS.COMPILER.strict-missing';                       severity='critical'; section='TypeScript / Compiler & Project Config'; phase='P1'; scope='Both'; directive='Enable strict: true from day one'; remediation='Set "strict": true in tsconfig.json compilerOptions.' }
    @{ id='TS.COMPILER.no-unchecked-indexed-access-missing';  severity='critical'; section='TypeScript / Compiler & Project Config'; phase='P1'; scope='Both'; directive='Enable noUncheckedIndexedAccess'; remediation='Set "noUncheckedIndexedAccess": true in tsconfig.json.' }
    @{ id='TS.COMPILER.exact-optional-missing';               severity='critical'; section='TypeScript / Compiler & Project Config'; phase='P1'; scope='Both'; directive='Enable exactOptionalPropertyTypes'; remediation='Set "exactOptionalPropertyTypes": true to separate absent from explicitly undefined.' }
    @{ id='TS.COMPILER.no-implicit-override-missing';         severity='high';     section='TypeScript / Compiler & Project Config'; phase='P1'; scope='Both'; directive='Enable noImplicitOverride'; remediation='Set "noImplicitOverride": true in tsconfig.json.' }
    @{ id='TS.COMPILER.no-fallthrough-cases-missing';         severity='high';     section='TypeScript / Compiler & Project Config'; phase='P1'; scope='Both'; directive='Enable noFallthroughCasesInSwitch'; remediation='Set "noFallthroughCasesInSwitch": true in tsconfig.json.' }
    @{ id='TS.COMPILER.no-implicit-returns-missing';          severity='high';     section='TypeScript / Compiler & Project Config'; phase='P1'; scope='Both'; directive='Enable noImplicitReturns'; remediation='Set "noImplicitReturns": true in tsconfig.json.' }
    @{ id='TS.COMPILER.force-consistent-casing-missing';      severity='high';     section='TypeScript / Compiler & Project Config'; phase='P1'; scope='Both'; directive='Enable forceConsistentCasingInFileNames'; remediation='Set "forceConsistentCasingInFileNames": true to prevent case-sensitivity bugs across OSs.' }
    @{ id='TS.TYPE.any-usage';                                severity='critical'; section='TypeScript / Type System Discipline'; phase='P1'; scope='Both'; directive='Ban any; use unknown for untrusted data and narrow before use'; remediation="Replace 'any' with 'unknown' and narrow at the use site, or define a precise type." }
    @{ id='TS.TYPE.ts-ignore';                                severity='critical'; section='TypeScript / Type System Discipline'; phase='P2'; scope='Both'; directive='Ban @ts-ignore; require @ts-expect-error with a justification'; remediation='Replace @ts-ignore with @ts-expect-error and add a comment explaining why.' }
    @{ id='TS.TYPE.unchecked-as-cast';                        severity='critical'; section='TypeScript / Type System Discipline'; phase='P1'; scope='Both'; directive="Never cast with 'as' to bypass the checker"; remediation="Use a type guard, satisfies, or schema parsing. 'as const' and 'as unknown' are exempt." }
    @{ id='TS.TYPE.untyped-catch';                            severity='high';     section='TypeScript / Type System Discipline'; phase='P2'; scope='Both'; directive='Narrow errors in catch with instanceof Error or a typed union'; remediation='Declare catch (e: unknown) and narrow via instanceof Error or a typed error union.' }
    @{ id='BE.DAL.missing-server-only';                       severity='critical'; section='Backend Patterns'; phase='P2'; scope='BE'; directive='Mark server-only modules so client imports fail the build'; remediation="Add ""import 'server-only';"" at the top of every DAL/server module." }
    @{ id='BE.ENV.direct-process-env-outside-validator';      severity='high';     section='Backend Patterns'; phase='P2'; scope='BE'; directive='Read env through a single typed module; fail boot if missing/invalid'; remediation='Centralize process.env reads in an env.ts (or lib/env.ts) module that validates with a schema.' }
    @{ id='FE.RSC.use-client-at-page-or-layout';              severity='critical'; section='Frontend Behaviors'; phase='P1'; scope='FE'; directive="Push 'use client' boundaries as deep as possible"; remediation='Move "use client" to the smallest interactive leaf; keep page.tsx and layout.tsx as Server Components.' }
    @{ id='FE.IMG.raw-img-tag';                               severity='high';     section='Frontend Behaviors'; phase='P3'; scope='FE'; directive='Use next/image with proper sizes for non-test images'; remediation='Replace <img> with next/image and set sizes; mark the LCP image priority=true.' }
    @{ id='FE.LINK.raw-anchor-internal';                      severity='medium';   section='Frontend Behaviors'; phase='P2'; scope='FE'; directive='Use <Link> for in-app navigation to benefit from prefetching'; remediation='Replace <a href="/..."> with <Link href="/..."> from next/link for internal routes.' }
    @{ id='FE.METADATA.missing-generate-metadata';            severity='medium';   section='Frontend Behaviors'; phase='P2'; scope='FE'; directive='Define generateMetadata or static metadata per route for SEO'; remediation='Export a static `metadata` or `generateMetadata` from this page.tsx.' }
    @{ id='SEC.SESSION.localstorage-auth';                    severity='critical'; section='Security Behaviors'; phase='P2'; scope='Both'; directive='Store sessions in httpOnly cookies, never localStorage'; remediation='Move session/token storage to httpOnly+Secure+SameSite cookies. localStorage is XSS-readable.' }
    @{ id='SEC.XSS.dangerously-set';                          severity='high';     section='Security Behaviors'; phase='P2'; scope='FE'; directive='Sanitize/encode user-generated content before rendering'; remediation='Pass content through a sanitizer (e.g. DOMPurify) or render as text; avoid dangerouslySetInnerHTML.' }
    @{ id='SEC.SECRET.public-env-prefix';                     severity='critical'; section='Security Behaviors'; phase='P2'; scope='Both'; directive='Never put secrets behind the public env var prefix'; remediation='Rename NEXT_PUBLIC_*SECRET/TOKEN/KEY/PASSWORD to a server-only env var (drop the NEXT_PUBLIC_ prefix).' }
    @{ id='SEC.SQL.template-literal-query';                   severity='high';     section='Security Behaviors'; phase='P2'; scope='BE'; directive='Use parameterized queries everywhere; ban string-concatenated SQL'; remediation='Use parameterized queries / query builder bindings; never interpolate user input into SQL strings.' }
    @{ id='PERF.LOG.console-log-in-source';                   severity='medium';   section='Performance Behaviors'; phase='P3'; scope='Both'; directive='Use structured logging; avoid console.log in production source'; remediation='Replace console.log with a structured logger; if intentional, use console.warn/console.error explicitly.' }
    @{ id='INFRA.CI.missing-typecheck-job';                   severity='high';     section='Infrastructure & Operations'; phase='P1'; scope='Both'; directive='CI runs typecheck on every PR; failures block merge'; remediation="Add a CI job that runs 'tsc --noEmit' (or 'npm run typecheck') on PRs and protected branches." }
)

if ($ListRules) {
    @{ schema_version='1.0'; rules=$RuleCatalog } | ConvertTo-Json -Depth 6
    return
}

# ---- Helpers ------------------------------------------------------------------

$SevRank = @{ critical = 4; high = 3; medium = 2; low = 1 }
$MinRank = $SevRank[$Severity]

$RuleFilter    = if ($Rules)    { ($Rules    -split ',' | Where-Object { $_ }) } else { @() }
$SectionFilter = if ($Sections) { ($Sections -split ',' | Where-Object { $_ } | ForEach-Object { $_.ToUpper() }) } else { @() }

function Test-RuleEnabled {
    param([string]$RuleId)
    if ($RuleFilter -and $RuleFilter.Count -gt 0 -and ($RuleFilter -notcontains $RuleId)) { return $false }
    if ($SectionFilter -and $SectionFilter.Count -gt 0) {
        $sec = ($RuleId -split '\.', 2)[0].ToUpper()
        if ($SectionFilter -notcontains $sec) { return $false }
    }
    return $true
}

function Test-SeverityPasses {
    param([string]$Sev)
    return $SevRank[$Sev] -ge $MinRank
}

function Format-Snippet {
    param([string]$Text)
    if (-not $Text) { return '' }
    $t = $Text.Trim()
    if ($t.Length -gt $SnippetMax) { $t = $t.Substring(0, $SnippetMax) + '...' }
    return $t
}

$Findings = [System.Collections.ArrayList]::new()
$PerRuleCount = @{}

function Add-Finding {
    param([string]$RuleId, [string]$Severity, [string]$File, [int]$Line, [string]$Snippet)
    if (-not (Test-SeverityPasses -Sev $Severity)) { return }
    $count = $PerRuleCount[$RuleId]
    if ($count -eq $null) { $count = 0 }
    if ($count -ge $MaxFindingsPerRule) { return }
    [void]$Findings.Add([ordered]@{
        rule_id  = $RuleId
        severity = $Severity
        file     = $File
        line     = $Line
        snippet  = (Format-Snippet -Text $Snippet)
    })
    $PerRuleCount[$RuleId] = $count + 1
}

# ---- File enumeration ---------------------------------------------------------

$IgnoreDirNames = @(
    'node_modules','.git','.next','.turbo','.vercel','dist','build','out',
    'coverage','.cache','.specify','.yarn','.pnpm-store','.swc'
)

function Test-PathIgnored {
    param([string]$Path)
    foreach ($seg in ($Path -split '[\\/]+')) {
        if ($IgnoreDirNames -contains $seg) { return $true }
    }
    return $false
}

$ScanRoots = if ($Paths) { ($Paths -split ',' | Where-Object { $_ }) } else { @('.') }
$AllFiles = New-Object System.Collections.ArrayList
$SourceExts = @('.ts','.tsx','.js','.jsx','.mjs','.cjs')

foreach ($r in $ScanRoots) {
    if (-not (Test-Path -LiteralPath $r)) {
        Write-Warning "[audit] path '$r' does not exist; skipping"
        continue
    }
    Get-ChildItem -LiteralPath $r -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $SourceExts -contains $_.Extension.ToLower() -and
            -not (Test-PathIgnored -Path ((Resolve-Path -LiteralPath $_.FullName -Relative) -replace '^\.[\\/]',''))
        } | ForEach-Object {
            $rel = (Resolve-Path -LiteralPath $_.FullName -Relative) -replace '^\.[\\/]',''
            [void]$AllFiles.Add($rel)
        }
}

$AllFiles = [System.Collections.ArrayList]@($AllFiles | Sort-Object -Unique)
$FilesScanned = $AllFiles.Count

function Get-FilesMatching {
    param([string]$Pattern)
    return $AllFiles | Where-Object { $_ -match $Pattern }
}

function Get-FilesExcluding {
    param([string]$Pattern)
    return $AllFiles | Where-Object { $_ -notmatch $Pattern }
}

$NoiseFilter = '(__tests__/|/test/|/tests/|\.test\.|\.spec\.|\.stories\.|/scripts/|/storybook/)'

function Get-ProdFiles { return $AllFiles | Where-Object { $_ -notmatch $NoiseFilter } }

# ---- Helper: scan files with a regex -----------------------------------------

function Invoke-RegexScan {
    param(
        [string]$RuleId,
        [string]$Severity,
        [string]$Pattern,
        [string[]]$Files
    )
    if (-not (Test-RuleEnabled -RuleId $RuleId)) { return }
    if (-not $Files -or $Files.Count -eq 0) { return }
    foreach ($f in $Files) {
        try {
            $matches = Select-String -LiteralPath $f -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue
        } catch { continue }
        if (-not $matches) { continue }
        foreach ($m in $matches) {
            if ($PerRuleCount[$RuleId] -ge $MaxFindingsPerRule) { break }
            Add-Finding -RuleId $RuleId -Severity $Severity -File $f -Line $m.LineNumber -Snippet $m.Line
        }
    }
}

# ---- Compiler rules -----------------------------------------------------------

function Read-TsConfigFlags {
    $path = $null
    foreach ($c in @('tsconfig.json','tsconfig.base.json')) {
        if (Test-Path -LiteralPath $c -PathType Leaf) { $path = $c; break }
    }
    if (-not $path) { return $null }
    try {
        $raw = Get-Content -LiteralPath $path -Raw -Encoding UTF8
        # strip comments + trailing commas
        $raw = [regex]::Replace($raw, '/\*.*?\*/', '', 'Singleline')
        $raw = [regex]::Replace($raw, '(?m)^\s*//.*$', '')
        $raw = [regex]::Replace($raw, ',(\s*[}\]])', '$1')
        $cfg = $raw | ConvertFrom-Json -ErrorAction Stop
        $co = if ($cfg.PSObject.Properties['compilerOptions']) { $cfg.compilerOptions } else { $null }
        $flags = [ordered]@{ path = $path }
        foreach ($k in @('strict','noUncheckedIndexedAccess','exactOptionalPropertyTypes',
                         'noImplicitOverride','noFallthroughCasesInSwitch',
                         'noImplicitReturns','forceConsistentCasingInFileNames')) {
            $v = if ($co -and $co.PSObject.Properties[$k]) { $co.$k } else { $null }
            $flags[$k] = $v
        }
        return $flags
    } catch { return $null }
}

function Eval-CompilerRules {
    $flags = Read-TsConfigFlags
    if (-not $flags) {
        foreach ($r in @('TS.COMPILER.strict-missing','TS.COMPILER.no-unchecked-indexed-access-missing','TS.COMPILER.exact-optional-missing')) {
            if (Test-RuleEnabled -RuleId $r) {
                Add-Finding -RuleId $r -Severity 'critical' -File 'tsconfig.json' -Line 0 -Snippet 'tsconfig.json not found or unparseable'
            }
        }
        return
    }
    $checks = @(
        @{ rule='TS.COMPILER.strict-missing';                      key='strict';                          sev='critical' }
        @{ rule='TS.COMPILER.no-unchecked-indexed-access-missing'; key='noUncheckedIndexedAccess';        sev='critical' }
        @{ rule='TS.COMPILER.exact-optional-missing';              key='exactOptionalPropertyTypes';      sev='critical' }
        @{ rule='TS.COMPILER.no-implicit-override-missing';        key='noImplicitOverride';              sev='high' }
        @{ rule='TS.COMPILER.no-fallthrough-cases-missing';        key='noFallthroughCasesInSwitch';      sev='high' }
        @{ rule='TS.COMPILER.no-implicit-returns-missing';         key='noImplicitReturns';               sev='high' }
        @{ rule='TS.COMPILER.force-consistent-casing-missing';     key='forceConsistentCasingInFileNames'; sev='high' }
    )
    foreach ($c in $checks) {
        if (-not (Test-RuleEnabled -RuleId $c.rule)) { continue }
        $val = $flags[$c.key]
        if ($val -ne $true) {
            $repr = if ($null -eq $val) { 'absent' } else { $val.ToString().ToLower() }
            Add-Finding -RuleId $c.rule -Severity $c.sev -File $flags.path -Line 0 `
                -Snippet ("compilerOptions.{0} = {1} (expected true)" -f $c.key, $repr)
        }
    }
}

# ---- Run rules ----------------------------------------------------------------

Eval-CompilerRules

# TS.TYPE.any-usage
$tsFiles = Get-FilesMatching '\.(ts|tsx)$'
Invoke-RegexScan -RuleId 'TS.TYPE.any-usage' -Severity 'critical' `
    -Pattern '(:\s*any\b)|(<\s*any\s*[,>])|(\bArray<\s*any\s*>)|(\bas\s+any\b)|(:\s*Promise<any>)' `
    -Files $tsFiles

# TS.TYPE.ts-ignore
$srcFiles = Get-FilesMatching '\.(ts|tsx|js|jsx)$'
Invoke-RegexScan -RuleId 'TS.TYPE.ts-ignore' -Severity 'critical' -Pattern '@ts-ignore' -Files $srcFiles

# TS.TYPE.unchecked-as-cast (PowerShell supports lookaround natively)
if (Test-RuleEnabled -RuleId 'TS.TYPE.unchecked-as-cast') {
    foreach ($f in $tsFiles) {
        try {
            $ms = Select-String -LiteralPath $f -Pattern '\bas\s+(?!(?:const|unknown)\b)[A-Z][A-Za-z0-9_]*' -AllMatches -ErrorAction SilentlyContinue
        } catch { continue }
        if (-not $ms) { continue }
        foreach ($m in $ms) {
            if ($PerRuleCount['TS.TYPE.unchecked-as-cast'] -ge $MaxFindingsPerRule) { break }
            Add-Finding -RuleId 'TS.TYPE.unchecked-as-cast' -Severity 'critical' -File $f -Line $m.LineNumber -Snippet $m.Line
        }
    }
}

# TS.TYPE.untyped-catch
Invoke-RegexScan -RuleId 'TS.TYPE.untyped-catch' -Severity 'high' `
    -Pattern 'catch\s*\(\s*[A-Za-z_$][A-Za-z0-9_$]*\s*\)' -Files $tsFiles

# BE.DAL.missing-server-only
if (Test-RuleEnabled -RuleId 'BE.DAL.missing-server-only') {
    $dalFiles = $AllFiles | Where-Object { $_ -match '(^|/)(src/)?(lib|server|data)/dal/.*\.(ts|tsx)$' }
    foreach ($f in $dalFiles) {
        $content = Get-Content -LiteralPath $f -Raw -ErrorAction SilentlyContinue
        if (-not ($content -match "(?m)^\s*import\s+(?:[^'""]+\s+from\s+)?['""]server-only['""]")) {
            Add-Finding -RuleId 'BE.DAL.missing-server-only' -Severity 'critical' -File $f -Line 1 -Snippet "DAL module missing import 'server-only'"
        }
    }
}

# BE.ENV.direct-process-env-outside-validator
if (Test-RuleEnabled -RuleId 'BE.ENV.direct-process-env-outside-validator') {
    $envExclude = '(^|/)(env|environment|config)\.(ts|tsx|js|mjs|cjs)$|(^|/)(lib|src/lib|server|src/server)/env(\.|/)'
    $candidates = Get-ProdFiles | Where-Object { $_ -match '\.(ts|tsx|js|jsx|mjs|cjs)$' -and $_ -notmatch $envExclude }
    Invoke-RegexScan -RuleId 'BE.ENV.direct-process-env-outside-validator' -Severity 'high' `
        -Pattern 'process\.env\.[A-Z_][A-Z0-9_]*' -Files $candidates
}

# FE.RSC.use-client-at-page-or-layout
if (Test-RuleEnabled -RuleId 'FE.RSC.use-client-at-page-or-layout') {
    $roots = $AllFiles | Where-Object { $_ -match '(^|/)(src/)?app/.*/(page|layout|template)\.(tsx?|jsx?)$' }
    foreach ($f in $roots) {
        $lines = Get-Content -LiteralPath $f -TotalCount 5 -ErrorAction SilentlyContinue
        if (-not $lines) { continue }
        $firstNonEmpty = ($lines | Where-Object { $_.Trim() } | Select-Object -First 1)
        if ($firstNonEmpty -and $firstNonEmpty -match "^\s*['""]use client['""]") {
            Add-Finding -RuleId 'FE.RSC.use-client-at-page-or-layout' -Severity 'critical' -File $f -Line 1 -Snippet $firstNonEmpty
        }
    }
}

# FE.IMG.raw-img-tag
if (Test-RuleEnabled -RuleId 'FE.IMG.raw-img-tag') {
    $prodTsx = Get-ProdFiles | Where-Object { $_ -match '\.(tsx|jsx)$' }
    Invoke-RegexScan -RuleId 'FE.IMG.raw-img-tag' -Severity 'high' -Pattern '<img\s' -Files $prodTsx
}

# FE.LINK.raw-anchor-internal
if (Test-RuleEnabled -RuleId 'FE.LINK.raw-anchor-internal') {
    $appTsx = Get-ProdFiles | Where-Object { $_ -match '(^|/)(src/)?app/.*\.(tsx|jsx)$' }
    Invoke-RegexScan -RuleId 'FE.LINK.raw-anchor-internal' -Severity 'medium' `
        -Pattern '<a\s[^>]*href=["'']/[^/"'']' -Files $appTsx
}

# FE.METADATA.missing-generate-metadata
if (Test-RuleEnabled -RuleId 'FE.METADATA.missing-generate-metadata') {
    $pages = $AllFiles | Where-Object { $_ -match '(^|/)(src/)?app/.*/page\.(tsx|jsx|ts|js)$' }
    foreach ($f in $pages) {
        $content = Get-Content -LiteralPath $f -Raw -ErrorAction SilentlyContinue
        if (-not ($content -match 'export\s+(const|let|var|async\s+function|function)\s+(metadata|generateMetadata)\b')) {
            Add-Finding -RuleId 'FE.METADATA.missing-generate-metadata' -Severity 'medium' -File $f -Line 1 -Snippet 'page module exports no `metadata` or `generateMetadata`'
        }
    }
}

# SEC.SESSION.localstorage-auth
Invoke-RegexScan -RuleId 'SEC.SESSION.localstorage-auth' -Severity 'critical' `
    -Pattern 'localStorage\.(setItem|getItem)\s*\(\s*["''](session|token|auth|jwt|access|refresh|bearer)' `
    -Files $srcFiles

# SEC.XSS.dangerously-set
$tsxFiles = Get-FilesMatching '\.(tsx|jsx)$'
Invoke-RegexScan -RuleId 'SEC.XSS.dangerously-set' -Severity 'high' -Pattern 'dangerouslySetInnerHTML' -Files $tsxFiles

# SEC.SECRET.public-env-prefix — source code
Invoke-RegexScan -RuleId 'SEC.SECRET.public-env-prefix' -Severity 'critical' `
    -Pattern 'NEXT_PUBLIC_[A-Z0-9_]*(SECRET|TOKEN|KEY|PASSWORD|PASSWD|PRIVATE)[A-Z0-9_]*' -Files $srcFiles

# SEC.SECRET.public-env-prefix — .env files
if (Test-RuleEnabled -RuleId 'SEC.SECRET.public-env-prefix') {
    foreach ($e in @('.env','.env.local','.env.production','.env.development','.env.example','.env.sample','.env.template')) {
        if (-not (Test-Path -LiteralPath $e -PathType Leaf)) { continue }
        try {
            $ms = Select-String -LiteralPath $e -Pattern '^NEXT_PUBLIC_[A-Z0-9_]*(SECRET|TOKEN|KEY|PASSWORD|PASSWD|PRIVATE)' -AllMatches -ErrorAction SilentlyContinue
        } catch { continue }
        if (-not $ms) { continue }
        foreach ($m in $ms) {
            if ($PerRuleCount['SEC.SECRET.public-env-prefix'] -ge $MaxFindingsPerRule) { break }
            Add-Finding -RuleId 'SEC.SECRET.public-env-prefix' -Severity 'critical' -File $e -Line $m.LineNumber -Snippet $m.Line
        }
    }
}

# SEC.SQL.template-literal-query
Invoke-RegexScan -RuleId 'SEC.SQL.template-literal-query' -Severity 'high' `
    -Pattern '`[^`]*\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b[^`]*\$\{' `
    -Files $srcFiles

# PERF.LOG.console-log-in-source
if (Test-RuleEnabled -RuleId 'PERF.LOG.console-log-in-source') {
    Invoke-RegexScan -RuleId 'PERF.LOG.console-log-in-source' -Severity 'medium' `
        -Pattern '\bconsole\.log\s*\(' -Files (Get-ProdFiles)
}

# INFRA.CI.missing-typecheck-job
if (Test-RuleEnabled -RuleId 'INFRA.CI.missing-typecheck-job') {
    $ciDir = '.github/workflows'
    if (-not (Test-Path -LiteralPath $ciDir -PathType Container)) {
        Add-Finding -RuleId 'INFRA.CI.missing-typecheck-job' -Severity 'high' -File $ciDir -Line 0 -Snippet 'no CI workflow directory found'
    } else {
        $workflows = Get-ChildItem -LiteralPath $ciDir -File -Include '*.yml','*.yaml' -ErrorAction SilentlyContinue
        $foundTc = $false
        foreach ($wf in $workflows) {
            $c = Get-Content -LiteralPath $wf.FullName -Raw -ErrorAction SilentlyContinue
            if ($c -match '\b(tsc|typecheck|type-check|type:check)\b') { $foundTc = $true; break }
        }
        if (-not $foundTc) {
            Add-Finding -RuleId 'INFRA.CI.missing-typecheck-job' -Severity 'high' -File $ciDir -Line 0 -Snippet 'no workflow references tsc or a typecheck script'
        }
    }
}

# ---- Aggregate & emit ---------------------------------------------------------

$RuleMeta = @{}
foreach ($r in $RuleCatalog) { $RuleMeta[$r.id] = $r }

foreach ($fnd in $Findings) {
    $m = $RuleMeta[$fnd.rule_id]
    if ($m) {
        $fnd.section     = $m.section
        $fnd.phase       = $m.phase
        $fnd.scope       = $m.scope
        $fnd.directive   = $m.directive
        $fnd.remediation = $m.remediation
    }
}

$BySeverity = @{ critical = 0; high = 0; medium = 0; low = 0 }
$BySection = @{}
$ByRule = @{}
foreach ($f in $Findings) {
    $BySeverity[$f.severity] = $BySeverity[$f.severity] + 1
    $sec = ($f.section -split ' ', 2)[0]
    if (-not $sec) { $sec = 'unknown' }
    if (-not $BySection.ContainsKey($sec)) { $BySection[$sec] = 0 }
    $BySection[$sec] += 1
    if (-not $ByRule.ContainsKey($f.rule_id)) { $ByRule[$f.rule_id] = 0 }
    $ByRule[$f.rule_id] += 1
}

$Result = [ordered]@{
    schema_version = '1.0'
    command        = 'audit'
    scanned_at     = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    repo_root      = $RepoRoot
    scope = [ordered]@{
        files_scanned   = $FilesScanned
        paths_included  = if ($Paths) { @($ScanRoots) } else { $null }
        extensions      = $SourceExts
        min_severity    = $Severity
        max_per_rule    = $MaxFindingsPerRule
    }
    summary = [ordered]@{
        rules_evaluated     = $RuleCatalog.Count
        rules_with_findings = $ByRule.Keys.Count
        findings_total      = $Findings.Count
        by_severity         = $BySeverity
        by_section          = $BySection
        by_rule             = $ByRule
    }
    rules    = $RuleCatalog
    findings = @($Findings)
}

if ($Text) {
    Write-Output ("speckit audit — {0}" -f $RepoRoot)
    Write-Output ("Files scanned: {0}" -f $FilesScanned)
    Write-Output ("Min severity:  {0}" -f $Severity)
    Write-Output ''
    if ($Findings.Count -eq 0) {
        Write-Output '  (no findings)'
    } else {
        $grouped = $Findings | Group-Object rule_id | Sort-Object Name
        foreach ($g in $grouped) {
            Write-Output ("  {0,-55} {1,3} finding(s)" -f $g.Name, $g.Count)
        }
    }
    Write-Output ''
    Write-Output ("Total findings: {0}" -f $Findings.Count)
} else {
    $Result | ConvertTo-Json -Depth 8
}

} finally {
    Pop-Location
}
