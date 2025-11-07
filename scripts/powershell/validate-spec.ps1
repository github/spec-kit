param(
    [switch]$Json,
    [switch]$Current,
    [switch]$Spec,
    [switch]$Plan,
    [switch]$Tasks,
    [switch]$All,
    [switch]$Constitution,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: validate-spec.ps1 [-Json] [mode]"
    Write-Host ""
    Write-Host "Modes:"
    Write-Host "  -Current        Validate current feature (default)"
    Write-Host "  -Spec           Validate only spec.md"
    Write-Host "  -Plan           Validate only plan.md"
    Write-Host "  -Tasks          Validate only tasks.md"
    Write-Host "  -All            Validate all features"
    Write-Host "  -Constitution   Validate constitution.md"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json           Output in JSON format"
    exit 0
}

# Source common functions
. "$PSScriptRoot\common.ps1"

# Get repository root
$RepoRoot = Get-RepoRoot
$SpecsDir = Join-Path $RepoRoot "specs"
$ConstitutionFile = Join-Path $RepoRoot "memory\constitution.md"

# Determine validation mode
$ValidateMode = "current"
if ($Spec) { $ValidateMode = "spec" }
elseif ($Plan) { $ValidateMode = "plan" }
elseif ($Tasks) { $ValidateMode = "tasks" }
elseif ($All) { $ValidateMode = "all" }
elseif ($Constitution) { $ValidateMode = "constitution" }

# Validate a single file
function Validate-File {
    param(
        [string]$FilePath,
        [string]$FileType
    )

    $Issues = @()

    if (-not (Test-Path $FilePath)) {
        return @{
            exists = $false
            complete = $false
            issues = @("File not found")
        }
    }

    # Check file size
    $Size = (Get-Item $FilePath).Length
    $MinSize = 100

    $Content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue

    switch ($FileType) {
        "spec" {
            $MinSize = 500
            # Check for required sections
            if ($Content -notmatch "## User Scenarios") {
                $Issues += "Missing User Scenarios section"
            }
            if ($Content -notmatch "## Functional Requirements") {
                $Issues += "Missing Functional Requirements section"
            }
            # Check for placeholders
            if ($Content -match "TODO|TBD|FIXME|XXX") {
                $Issues += "Contains TODO/TBD placeholders"
            }
        }
        "plan" {
            $MinSize = 300
            if ($Content -notmatch "## Technology Stack|## Tech Stack") {
                $Issues += "Missing Technology Stack section"
            }
            if ($Content -notmatch "## Project Structure") {
                $Issues += "Missing Project Structure section"
            }
        }
        "tasks" {
            $MinSize = 200
            $TaskCount = ([regex]::Matches($Content, "^[-0-9]", [System.Text.RegularExpressions.RegexOptions]::Multiline)).Count
            if ($TaskCount -lt 5) {
                $Issues += "Only $TaskCount tasks found (minimum 5 recommended)"
            }
        }
        "constitution" {
            $MinSize = 300
            if ($Content -notmatch "## Principles|# Principles") {
                $Issues += "Missing Principles section"
            }
        }
    }

    if ($Size -lt $MinSize) {
        $Issues += "File too short ($Size bytes, minimum $MinSize)"
    }

    $Complete = $Issues.Count -eq 0

    return @{
        exists = $true
        complete = $Complete
        issues = $Issues
    }
}

# Validate single feature
function Validate-Feature {
    param([string]$FeatureDir)

    $FeatureName = Split-Path $FeatureDir -Leaf

    $SpecResult = Validate-File -FilePath (Join-Path $FeatureDir "spec.md") -FileType "spec"
    $PlanResult = Validate-File -FilePath (Join-Path $FeatureDir "plan.md") -FileType "plan"
    $TasksResult = Validate-File -FilePath (Join-Path $FeatureDir "tasks.md") -FileType "tasks"

    # Determine overall status
    $Status = "success"
    if (-not $SpecResult.complete) { $Status = "error" }
    elseif (-not $PlanResult.complete -or -not $TasksResult.complete) { $Status = "warning" }

    return @{
        feature = $FeatureName
        validations = @{
            spec = $SpecResult
            plan = $PlanResult
            tasks = $TasksResult
        }
        status = $Status
    }
}

# Main validation logic
$Results = @()

if ($ValidateMode -eq "constitution") {
    # Validate constitution only
    $Result = Validate-File -FilePath $ConstitutionFile -FileType "constitution"

    if ($Json) {
        @{
            constitution = $Result
        } | ConvertTo-Json -Depth 10
    } else {
        Write-Host "Constitution Validation"
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if ($Result.exists) {
            if ($Result.complete) {
                Write-Host "✓ Constitution is valid"
            } else {
                Write-Host "⚠️  Constitution has issues:"
                foreach ($Issue in $Result.issues) {
                    Write-Host "  • $Issue"
                }
            }
        } else {
            Write-Host "✗ Constitution file not found"
        }
    }
} elseif ($ValidateMode -eq "all") {
    # Validate all features
    if (Test-Path $SpecsDir) {
        $FeatureDirs = Get-ChildItem -Path $SpecsDir -Directory | Sort-Object Name

        foreach ($FeatureDir in $FeatureDirs) {
            $Results += Validate-Feature -FeatureDir $FeatureDir.FullName
        }
    }

    if ($Json) {
        @{
            features = $Results
            total = $Results.Count
            success = ($Results | Where-Object { $_.status -eq "success" }).Count
            warnings = ($Results | Where-Object { $_.status -eq "warning" }).Count
            errors = ($Results | Where-Object { $_.status -eq "error" }).Count
        } | ConvertTo-Json -Depth 10
    } else {
        Write-Host "Project Validation"
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Write-Host ""
        Write-Host "Total features: $($Results.Count)"
        Write-Host "Success: $(($Results | Where-Object { $_.status -eq 'success' }).Count)"
        Write-Host "Warnings: $(($Results | Where-Object { $_.status -eq 'warning' }).Count)"
        Write-Host "Errors: $(($Results | Where-Object { $_.status -eq 'error' }).Count)"
        Write-Host ""

        foreach ($Result in $Results) {
            $StatusIcon = if ($Result.status -eq "success") { "✓" } elseif ($Result.status -eq "warning") { "⚠️" } else { "✗" }
            Write-Host "$StatusIcon $($Result.feature)"

            if ($Result.validations.spec.issues.Count -gt 0) {
                Write-Host "  Spec issues:"
                foreach ($Issue in $Result.validations.spec.issues) {
                    Write-Host "    • $Issue"
                }
            }
            if ($Result.validations.plan.issues.Count -gt 0) {
                Write-Host "  Plan issues:"
                foreach ($Issue in $Result.validations.plan.issues) {
                    Write-Host "    • $Issue"
                }
            }
            if ($Result.validations.tasks.issues.Count -gt 0) {
                Write-Host "  Tasks issues:"
                foreach ($Issue in $Result.validations.tasks.issues) {
                    Write-Host "    • $Issue"
                }
            }
        }
    }
} else {
    # Validate current feature
    $CurrentBranch = Get-CurrentBranch
    $FeatureDir = Find-FeatureDirByPrefix -RepoRoot $RepoRoot -BranchName $CurrentBranch

    if (-not $FeatureDir) {
        Write-Host "Error: Could not determine current feature from branch name" -ForegroundColor Red
        exit 1
    }

    $Result = Validate-Feature -FeatureDir $FeatureDir

    if ($Json) {
        $Result | ConvertTo-Json -Depth 10
    } else {
        Write-Host "Feature Validation: $($Result.feature)"
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        Write-Host ""

        $StatusIcon = if ($Result.status -eq "success") { "✓" } elseif ($Result.status -eq "warning") { "⚠️" } else { "✗" }
        Write-Host "Status: $StatusIcon $($Result.status)"
        Write-Host ""

        # Spec validation
        Write-Host "spec.md:"
        if ($Result.validations.spec.complete) {
            Write-Host "  ✓ Valid"
        } else {
            Write-Host "  ✗ Issues found:"
            foreach ($Issue in $Result.validations.spec.issues) {
                Write-Host "    • $Issue"
            }
        }

        # Plan validation
        Write-Host ""
        Write-Host "plan.md:"
        if ($Result.validations.plan.complete) {
            Write-Host "  ✓ Valid"
        } else {
            Write-Host "  ⚠️  Issues found:"
            foreach ($Issue in $Result.validations.plan.issues) {
                Write-Host "    • $Issue"
            }
        }

        # Tasks validation
        Write-Host ""
        Write-Host "tasks.md:"
        if ($Result.validations.tasks.complete) {
            Write-Host "  ✓ Valid"
        } else {
            Write-Host "  ⚠️  Issues found:"
            foreach ($Issue in $Result.validations.tasks.issues) {
                Write-Host "    • $Issue"
            }
        }

        if ($Result.status -ne "success") {
            Write-Host ""
            Write-Host "💡 Recommendation: Address issues before proceeding with /speckit.implement"
        }
    }
}
