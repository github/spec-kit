param(
    [switch]$Json,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: token-budget.ps1 [-Json] [-Help]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json      Output in JSON format"
    Write-Host "  -Help      Show this help message"
    Write-Host ""
    Write-Host "Description:"
    Write-Host "  Estimates token usage for the current session based on file sizes"
    Write-Host "  and provides recommendations for token optimization."
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Get repository root
$RepoRoot = Get-RepoRoot
$SpecsDir = Join-Path $RepoRoot "specs"
$ConstitutionFile = Join-Path $RepoRoot "memory\constitution.md"

# Default budget for Claude Sonnet
$TotalBudget = 200000

# Function to estimate tokens from file size
function Estimate-Tokens {
    param(
        [string]$FilePath,
        [string]$FileType
    )

    if (-not (Test-Path $FilePath)) {
        return 0
    }

    # Get file size in bytes
    $Bytes = (Get-Item $FilePath).Length

    # Estimate characters (roughly 1 byte = 1 char for ASCII/UTF-8)
    $Chars = $Bytes

    # Convert to tokens: chars / 4 * multiplier
    # Base: 1 token ≈ 4 characters
    $BaseTokens = [Math]::Floor($Chars / 4)

    # Apply multipliers based on file type
    switch ($FileType) {
        "markdown" {
            # Markdown has formatting overhead
            return [Math]::Floor($BaseTokens * 1.1)
        }
        "code" {
            # Code files are dense
            return $BaseTokens
        }
        "json" {
            # JSON is structured/compressed in context
            return [Math]::Floor($BaseTokens * 0.9)
        }
        default {
            return $BaseTokens
        }
    }
}

# Estimate tokens for specs
$SpecsTokens = 0
$SpecBreakdown = @{}

if (Test-Path $SpecsDir) {
    $SpecDirs = Get-ChildItem -Path $SpecsDir -Directory | Sort-Object Name

    foreach ($SpecDir in $SpecDirs) {
        $SpecName = $SpecDir.Name
        $SpecTotal = 0

        # spec.md
        $SpecFile = Join-Path $SpecDir.FullName "spec.md"
        if (Test-Path $SpecFile) {
            $Tokens = Estimate-Tokens -FilePath $SpecFile -FileType "markdown"
            $SpecTotal += $Tokens
        }

        # plan.md (weight: 0.9, often partially referenced)
        $PlanFile = Join-Path $SpecDir.FullName "plan.md"
        if (Test-Path $PlanFile) {
            $Tokens = Estimate-Tokens -FilePath $PlanFile -FileType "markdown"
            $Tokens = [Math]::Floor($Tokens * 0.9)
            $SpecTotal += $Tokens
        }

        # tasks.md (weight: 0.8, scanned not fully read)
        $TasksFile = Join-Path $SpecDir.FullName "tasks.md"
        if (Test-Path $TasksFile) {
            $Tokens = Estimate-Tokens -FilePath $TasksFile -FileType "markdown"
            $Tokens = [Math]::Floor($Tokens * 0.8)
            $SpecTotal += $Tokens
        }

        # ai-doc.md
        $AiDocFile = Join-Path $SpecDir.FullName "ai-doc.md"
        if (Test-Path $AiDocFile) {
            $Tokens = Estimate-Tokens -FilePath $AiDocFile -FileType "markdown"
            $SpecTotal += $Tokens
        }

        # quick-ref.md
        $QuickRefFile = Join-Path $SpecDir.FullName "quick-ref.md"
        if (Test-Path $QuickRefFile) {
            $Tokens = Estimate-Tokens -FilePath $QuickRefFile -FileType "markdown"
            $SpecTotal += $Tokens
        }

        $SpecsTokens += $SpecTotal

        if ($SpecTotal -gt 0) {
            $SpecBreakdown[$SpecName] = $SpecTotal
        }
    }
}

# Estimate constitution tokens
$ConstitutionTokens = 0
if (Test-Path $ConstitutionFile) {
    $ConstitutionTokens = Estimate-Tokens -FilePath $ConstitutionFile -FileType "markdown"
}

# Estimate conversation tokens (rough heuristic)
$ConversationTokens = 20000

# Estimate code context
$CodeContextTokens = 0

# Calculate session total
$SessionTokens = $ConversationTokens + $SpecsTokens + $ConstitutionTokens + $CodeContextTokens
$RemainingTokens = $TotalBudget - $SessionTokens
$UsagePercent = [Math]::Floor(($SessionTokens * 100) / $TotalBudget)

# Determine status
if ($UsagePercent -lt 40) {
    $Status = "healthy"
    $StatusIcon = "✓"
} elseif ($UsagePercent -lt 60) {
    $Status = "moderate"
    $StatusIcon = "⚠️"
} elseif ($UsagePercent -lt 80) {
    $Status = "high"
    $StatusIcon = "⚠️"
} else {
    $Status = "critical"
    $StatusIcon = "🚨"
}

# Generate recommendations
$Recommendations = @()
if ($UsagePercent -lt 40) {
    $Recommendations += "You have plenty of budget remaining"
    $Recommendations += "Safe to proceed with planning and implementation"
    $Recommendations += "No optimization needed at this stage"
} elseif ($UsagePercent -lt 60) {
    $Recommendations += "Moderate token usage detected"
    $Recommendations += "Consider using quick-ref.md instead of full ai-doc.md (saves ~2K per feature)"
    $Recommendations += "Use /speckit.analyze --summary for quick checks (90% faster)"
    $Recommendations += "Continue monitoring usage"
} elseif ($UsagePercent -lt 80) {
    $Recommendations += "High token usage - optimization recommended"
    $Recommendations += "Run /speckit.prune to compress session (saves 40-60K tokens)"
    $Recommendations += "Use /speckit.analyze --incremental (70-90% faster)"
    $Recommendations += "Load only essential specs/docs"
    $Recommendations += "Budget may be tight for implementation"
} else {
    $Recommendations += "CRITICAL: Token budget nearly exhausted"
    $Recommendations += "IMMEDIATE: Run /speckit.prune NOW to free up space"
    $Recommendations += "Use summary modes for all analysis"
    $Recommendations += "Consider starting fresh session for implementation"
    $Recommendations += "Estimated remaining capacity: 1-2 major operations"
}

# Format numbers with K suffix
function Format-Tokens {
    param([int]$Num)

    if ($Num -ge 1000) {
        return "$([Math]::Floor($Num / 1000))K"
    } else {
        return "$Num"
    }
}

# Output results
if ($Json) {
    # JSON output
    $Output = @{
        session_tokens = $SessionTokens
        total_budget = $TotalBudget
        remaining_tokens = $RemainingTokens
        usage_percentage = $UsagePercent
        breakdown = @{
            conversation = $ConversationTokens
            specs = $SpecBreakdown
            constitution = $ConstitutionTokens
            code_context = $CodeContextTokens
        }
        status = $Status
        recommendations = $Recommendations
    }

    $Output | ConvertTo-Json -Depth 10
} else {
    # Human-readable output
    Write-Host "Token Budget Status"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Current Session: ~$(Format-Tokens $SessionTokens) tokens used"
    Write-Host "Remaining: ~$(Format-Tokens $RemainingTokens) tokens ($((100 - $UsagePercent))% available)"
    Write-Host ""
    Write-Host "Breakdown:"
    Write-Host "  Conversation: $(Format-Tokens $ConversationTokens) (estimated)"

    if ($SpecsTokens -gt 0) {
        Write-Host "  Specifications: $(Format-Tokens $SpecsTokens)"
        foreach ($SpecName in ($SpecBreakdown.Keys | Sort-Object)) {
            $SpecTotal = $SpecBreakdown[$SpecName]
            Write-Host "    • $SpecName: $(Format-Tokens $SpecTotal)"
        }
    }

    if ($ConstitutionTokens -gt 0) {
        Write-Host "  Constitution: $(Format-Tokens $ConstitutionTokens)"
    }

    if ($CodeContextTokens -gt 0) {
        Write-Host "  Code context: $(Format-Tokens $CodeContextTokens)"
    }

    Write-Host ""
    Write-Host "Status: $StatusIcon $Status"

    Write-Host ""
    if ($UsagePercent -lt 40) {
        Write-Host "💡 Recommendations:"
    } elseif ($UsagePercent -lt 60) {
        Write-Host "💡 Recommendations:"
    } elseif ($UsagePercent -lt 80) {
        Write-Host "⚠️  Recommendations:"
    } else {
        Write-Host "🚨 IMMEDIATE ACTIONS REQUIRED:"
    }

    foreach ($Rec in $Recommendations) {
        Write-Host "  • $Rec"
    }

    # Show optimization options if usage is moderate or higher
    if ($UsagePercent -ge 40) {
        Write-Host ""
        Write-Host "🔧 Optimization Options:"
        if ($UsagePercent -ge 60) {
            Write-Host "  /speckit.prune              - Compress session (save ~40-50K tokens)"
        }
        Write-Host "  /speckit.analyze --summary  - Quick analysis (90% faster)"
        Write-Host "  /speckit.analyze --incremental - Smart analysis (70% faster)"
        Write-Host ""
        Write-Host "  Load quick refs:"

        $SpecDirs = Get-ChildItem -Path $SpecsDir -Directory | Select-Object -First 3
        foreach ($SpecDir in $SpecDirs) {
            $QuickRefFile = Join-Path $SpecDir.FullName "quick-ref.md"
            if (Test-Path $QuickRefFile) {
                $SpecName = $SpecDir.Name
                Write-Host "    cat specs\$SpecName\quick-ref.md (~200 tokens)"
            }
        }
    }
}
