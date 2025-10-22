# Version management script for Specify CLI

param(
    [Parameter(Position=0, HelpMessage="Command to execute: current, bump, set, validate, tag")]
    [ValidateSet("current", "bump", "set", "validate", "tag", "help")]
    [string]$Command = "help",
    
    [Parameter(Position=1, HelpMessage="Argument for command (e.g., bump type or version number)")]
    [string]$Argument,
    
    [Parameter(HelpMessage="Show what would be done without making changes")]
    [switch]$DryRun,
    
    [Parameter(HelpMessage="Custom commit/tag message")]
    [string]$Message
)

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Get script and repo paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

# Files to update
$pyprojectFile = Join-Path $repoRoot "pyproject.toml"
$changelogFile = Join-Path $repoRoot "CHANGELOG.md"
$initFile = Join-Path $repoRoot "src\specify_cli\__init__.py"

# Help function
function Show-Help {
    Write-Host @"
Version management for Specify CLI

USAGE:
    .\version-manager.ps1 [COMMAND] [ARGUMENT] [OPTIONS]

COMMANDS:
    current             Show current version
    bump <TYPE>         Bump version (TYPE: major, minor, patch)
    set <VERSION>       Set specific version (e.g., 1.2.3)
    validate            Validate version consistency across files
    tag                 Create git tag for current version
    help                Show this help message
    
OPTIONS:
    -DryRun             Show what would be done without making changes
    -Message <MSG>      Custom commit/tag message

EXAMPLES:
    .\version-manager.ps1 current                     # Show current version
    .\version-manager.ps1 bump patch                  # Bump patch version (0.0.20 -> 0.0.21)
    .\version-manager.ps1 bump minor                  # Bump minor version (0.0.20 -> 0.1.0)
    .\version-manager.ps1 bump major                  # Bump major version (0.0.20 -> 1.0.0)
    .\version-manager.ps1 set 1.0.0                   # Set version to 1.0.0
    .\version-manager.ps1 validate                    # Check version consistency
    .\version-manager.ps1 tag -Message "Release v0.0.21"  # Create git tag

"@
}

# Get current version from pyproject.toml
function Get-CurrentVersion {
    if (!(Test-Path $pyprojectFile)) {
        Write-ColorOutput Red "Error: pyproject.toml not found at $pyprojectFile"
        exit 1
    }
    
    $content = Get-Content $pyprojectFile -Raw
    if ($content -match 'version = "([^"]+)"') {
        return $matches[1]
    }
    
    Write-ColorOutput Red "Error: Could not find version in pyproject.toml"
    exit 1
}

# Parse version into components
function Parse-Version {
    param([string]$Version)
    
    $parts = $Version.Split('.')
    return @{
        Major = [int]$parts[0]
        Minor = [int]$parts[1]
        Patch = [int]$parts[2]
    }
}

# Bump version
function Get-BumpedVersion {
    param(
        [string]$BumpType,
        [string]$CurrentVersion
    )
    
    $parts = Parse-Version $CurrentVersion
    
    switch ($BumpType.ToLower()) {
        "major" {
            $parts.Major++
            $parts.Minor = 0
            $parts.Patch = 0
        }
        "minor" {
            $parts.Minor++
            $parts.Patch = 0
        }
        "patch" {
            $parts.Patch++
        }
        default {
            Write-ColorOutput Red "Error: Invalid bump type '$BumpType'"
            Write-Host "Valid types: major, minor, patch"
            exit 1
        }
    }
    
    return "$($parts.Major).$($parts.Minor).$($parts.Patch)"
}

# Update version in file
function Update-VersionInFile {
    param(
        [string]$FilePath,
        [string]$OldVersion,
        [string]$NewVersion,
        [bool]$IsDryRun
    )
    
    if (!(Test-Path $FilePath)) {
        Write-ColorOutput Yellow "Warning: File not found: $FilePath"
        return $false
    }
    
    if ($IsDryRun) {
        Write-ColorOutput Blue "Would update $FilePath`: $OldVersion -> $NewVersion"
        return $true
    }
    
    $content = Get-Content $FilePath -Raw
    
    # Different patterns for different files
    switch -Wildcard ($FilePath) {
        "*pyproject.toml" {
            $content = $content -replace "version = `"$OldVersion`"", "version = `"$NewVersion`""
        }
        "*__init__.py" {
            if ($content -match "__version__") {
                $content = $content -replace "__version__ = `"$OldVersion`"", "__version__ = `"$NewVersion`""
            }
        }
        "*CHANGELOG.md" {
            # Add new version section at the top (after header)
            $date = Get-Date -Format "yyyy-MM-dd"
            $newSection = @"

## [$NewVersion] - $date

### Added
- New features in this release

### Changed
- Changes in this release

### Fixed
- Bug fixes in this release

"@
            # Insert after first ## heading
            $content = $content -replace "(## \[)", "$newSection`$1"
        }
    }
    
    Set-Content -Path $FilePath -Value $content -NoNewline
    Write-ColorOutput Green "✓ Updated $FilePath"
    return $true
}

# Validate version consistency
function Test-VersionConsistency {
    Write-ColorOutput Blue "Validating version consistency..."
    
    $pyprojectVersion = Get-CurrentVersion
    $issues = 0
    
    Write-Host "pyproject.toml: $pyprojectVersion"
    
    # Check __init__.py if it has __version__
    if (Test-Path $initFile) {
        $initContent = Get-Content $initFile -Raw
        if ($initContent -match '__version__ = "([^"]+)"') {
            $initVersion = $matches[1]
            Write-Host "__init__.py: $initVersion"
            
            if ($initVersion -ne $pyprojectVersion) {
                Write-ColorOutput Red "✗ Version mismatch in __init__.py"
                $issues++
            }
        }
    }
    
    # Check CHANGELOG.md
    if (Test-Path $changelogFile) {
        $changelogContent = Get-Content $changelogFile -Raw
        if ($changelogContent -match "\[\Q$pyprojectVersion\E\]") {
            Write-ColorOutput Green "✓ CHANGELOG.md has entry for $pyprojectVersion"
        }
        else {
            Write-ColorOutput Yellow "! CHANGELOG.md missing entry for $pyprojectVersion"
            $issues++
        }
    }
    
    if ($issues -eq 0) {
        Write-ColorOutput Green "✓ All versions are consistent"
        return $true
    }
    else {
        Write-ColorOutput Red "✗ Found $issues version inconsistencies"
        return $false
    }
}

# Create git tag
function New-GitTag {
    param(
        [string]$CustomMessage,
        [bool]$IsDryRun
    )
    
    $version = Get-CurrentVersion
    $tag = "v$version"
    
    if (!$CustomMessage) {
        $CustomMessage = "Release v$version"
    }
    
    # Check if tag exists
    $existingTag = git tag -l $tag 2>$null
    if ($existingTag) {
        Write-ColorOutput Yellow "Warning: Tag $tag already exists"
        return $false
    }
    
    if ($IsDryRun) {
        Write-ColorOutput Blue "Would create tag: $tag"
        Write-ColorOutput Blue "Message: $CustomMessage"
        return $true
    }
    
    git tag -a $tag -m $CustomMessage
    Write-ColorOutput Green "✓ Created tag $tag"
    Write-ColorOutput Yellow "Push with: git push origin $tag"
    return $true
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "current" {
        $version = Get-CurrentVersion
        Write-Host "Current version: $version"
    }
    
    "bump" {
        if (!$Argument) {
            $Argument = "patch"
        }
        
        $currentVersion = Get-CurrentVersion
        $newVersion = Get-BumpedVersion -BumpType $Argument -CurrentVersion $currentVersion
        
        Write-ColorOutput Yellow "Bumping version: $currentVersion -> $newVersion"
        
        # Update all files
        Update-VersionInFile -FilePath $pyprojectFile -OldVersion $currentVersion -NewVersion $newVersion -IsDryRun $DryRun
        Update-VersionInFile -FilePath $initFile -OldVersion $currentVersion -NewVersion $newVersion -IsDryRun $DryRun
        Update-VersionInFile -FilePath $changelogFile -OldVersion $currentVersion -NewVersion $newVersion -IsDryRun $DryRun
        
        if (!$DryRun) {
            Write-ColorOutput Green "✓ Version bumped to $newVersion"
            Write-ColorOutput Yellow "Don't forget to commit these changes!"
        }
    }
    
    "set" {
        if (!$Argument) {
            Write-ColorOutput Red "Error: Version required"
            Write-Host "Usage: .\version-manager.ps1 set VERSION"
            exit 1
        }
        
        # Validate version format
        if ($Argument -notmatch '^\d+\.\d+\.\d+$') {
            Write-ColorOutput Red "Error: Invalid version format '$Argument'"
            Write-Host "Expected format: MAJOR.MINOR.PATCH (e.g., 1.0.0)"
            exit 1
        }
        
        $currentVersion = Get-CurrentVersion
        $newVersion = $Argument
        
        Write-ColorOutput Yellow "Setting version: $currentVersion -> $newVersion"
        
        # Update all files
        Update-VersionInFile -FilePath $pyprojectFile -OldVersion $currentVersion -NewVersion $newVersion -IsDryRun $DryRun
        Update-VersionInFile -FilePath $initFile -OldVersion $currentVersion -NewVersion $newVersion -IsDryRun $DryRun
        Update-VersionInFile -FilePath $changelogFile -OldVersion $currentVersion -NewVersion $newVersion -IsDryRun $DryRun
        
        if (!$DryRun) {
            Write-ColorOutput Green "✓ Version set to $newVersion"
            Write-ColorOutput Yellow "Don't forget to commit these changes!"
        }
    }
    
    "validate" {
        Test-VersionConsistency
    }
    
    "tag" {
        New-GitTag -CustomMessage $Message -IsDryRun $DryRun
    }
    
    "help" {
        Show-Help
    }
    
    default {
        Write-ColorOutput Red "Error: Unknown command '$Command'"
        Write-Host ""
        Show-Help
        exit 1
    }
}
