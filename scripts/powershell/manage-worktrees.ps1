# Manage git worktrees for spec-kit parallel development workflows
# Part of GitHub Spec Kit - https://github.com/github/spec-kit

$ErrorActionPreference = "Stop"

# Source common utilities
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$scriptDir/common.ps1"

# Constants
$WORKTREE_BASE_DIR = ".worktrees"

# ============================================================================
# Foundational Utility Functions
# ============================================================================

# ensure_worktree_gitignore
# Adds .worktrees/ to .gitignore if not already present
# Usage: ensure_worktree_gitignore
function ensure_worktree_gitignore {
	$repoRoot = Get-RepoRoot
	$gitignorePath = Join-Path $repoRoot ".gitignore"

	# Create .gitignore if it doesn't exist
	if (-not (Test-Path $gitignorePath)) {
		@"
# Git worktrees (parallel development)
.worktrees/
"@ | Out-File -FilePath $gitignorePath -Encoding UTF8
		return
	}

	# Check if .worktrees/ is already in .gitignore
	$content = Get-Content $gitignorePath -Raw
	if ($content -match '(^|\n)\.worktrees/?(\r?\n|$)' -or $content -match '(^|\n)/\.worktrees/?(\r?\n|$)') {
		return
	}

	# Add .worktrees/ to .gitignore
	@"

# Git worktrees (parallel development)
.worktrees/
"@ | Out-File -FilePath $gitignorePath -Append -Encoding UTF8
}

# get_worktree_status
# Checks if a worktree is active, stale, or orphaned
# Usage: get_worktree_status <branch_name>
# Returns: "active" | "stale" | "orphaned" | "none"
function get_worktree_status {
	param([string]$branchName)

	$repoRoot = Get-RepoRoot
	$worktreePath = Join-Path $repoRoot "$WORKTREE_BASE_DIR\$branchName"

	# Check if worktree directory exists
	if (-not (Test-Path $worktreePath)) {
		return "none"
	}

	# Check if git knows about this worktree
	$gitKnows = $false
	try {
		$worktreeList = git worktree list --porcelain 2>$null
		if ($worktreeList -match "worktree $([regex]::Escape($worktreePath))") {
			$gitKnows = $true
		}
	} catch {
		# git worktree list failed, treat as not known
	}

	# Check if branch exists
	$branchExists = $false
	try {
		git show-ref --verify --quiet "refs/heads/$branchName" 2>$null
		if ($LASTEXITCODE -eq 0) {
			$branchExists = $true
		}
	} catch {
		# Branch doesn't exist
	}

	# Determine status
	if ($gitKnows -and $branchExists) {
		return "active"
	} elseif ($gitKnows -and -not $branchExists) {
		return "stale"
	} elseif (-not $gitKnows -and (Test-Path $worktreePath)) {
		return "orphaned"
	} else {
		return "none"
	}
}

# calculate_disk_usage
# Calculates human-readable disk usage for a worktree
# Usage: calculate_disk_usage <path>
# Returns: Human-readable size (e.g., "150M", "2.3G")
function calculate_disk_usage {
	param([string]$path)

	if (-not (Test-Path $path)) {
		return "0B"
	}

	try {
		$size = (Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue |
			Measure-Object -Property Length -Sum).Sum

		if ($null -eq $size -or $size -eq 0) {
			return "0B"
		}

		# Convert to human-readable format
		if ($size -lt 1KB) {
			return "$($size)B"
		} elseif ($size -lt 1MB) {
			return "$([math]::Round($size / 1KB, 1))K"
		} elseif ($size -lt 1GB) {
			return "$([math]::Round($size / 1MB, 1))M"
		} else {
			return "$([math]::Round($size / 1GB, 2))G"
		}
	} catch {
		return "N/A"
	}
}

# ============================================================================
# User Story 1: Automatic Worktree Creation Functions
# ============================================================================

# prompt_conflict_resolution
# Prompts user when worktree already exists with options: stop, cleanup, skip
# Usage: prompt_conflict_resolution <branch_name>
# Returns: "stop" | "cleanup" | "skip"
function prompt_conflict_resolution {
	param([string]$branchName)

	Write-Host "[specify] Worktree already exists for branch '$branchName'" -ForegroundColor Yellow
	Write-Host ""
	Write-Host "Choose action:"
	Write-Host "  1) Stop - Cancel operation with error"
	Write-Host "  2) Cleanup - Remove old worktree and create fresh"
	Write-Host "  3) Skip - Keep existing worktree, continue"
	Write-Host ""
	$choice = Read-Host "Enter choice (1-3)"

	switch ($choice) {
		"1" { return "stop" }
		"2" { return "cleanup" }
		"3" { return "skip" }
		default {
			Write-Host "[specify] Invalid choice. Defaulting to stop." -ForegroundColor Yellow
			return "stop"
		}
	}
}

# create_worktree
# Creates a git worktree for the specified branch
# Usage: create_worktree <branch_name>
# Returns: $true on success, $false on error or stop
function create_worktree {
	param([string]$branchName)

	if ([string]::IsNullOrEmpty($branchName)) {
		Write-Host "[specify] Error: Branch name required" -ForegroundColor Red
		return $false
	}

	# Validate we're in a git repository (T022)
	$repoRoot = $null
	try {
		$repoRoot = git rev-parse --show-toplevel 2>$null
		if ($LASTEXITCODE -ne 0) {
			throw "Not a git repository"
		}
	} catch {
		Write-Host "[specify] Error: Not in a git repository" -ForegroundColor Red
		Write-Host "[specify] Git worktrees require a git repository" -ForegroundColor Red
		return $false
	}

	# Validate branch follows spec-kit naming convention ###-feature-name (T022)
	if ($branchName -notmatch '^\d{3}-') {
		Write-Host "[specify] Error: Invalid branch name: $branchName" -ForegroundColor Red
		Write-Host "[specify] Spec-kit worktrees require branches named like: 001-feature-name" -ForegroundColor Red
		return $false
	}

	# Error if on main branch (T023)
	if ($branchName -eq "main" -or $branchName -eq "master") {
		Write-Host "[specify] Error: Cannot create worktree for main/master branch" -ForegroundColor Red
		Write-Host "[specify] Worktrees are for feature branches only (###-feature-name)" -ForegroundColor Red
		return $false
	}
	$worktreePath = Join-Path $repoRoot "$WORKTREE_BASE_DIR\$branchName"

	# Ensure .gitignore contains .worktrees/
	ensure_worktree_gitignore

	# Create .worktrees/ directory if it doesn't exist
	$worktreeBaseDir = Join-Path $repoRoot $WORKTREE_BASE_DIR
	if (-not (Test-Path $worktreeBaseDir)) {
		New-Item -ItemType Directory -Path $worktreeBaseDir -Force | Out-Null
	}

	# Check if worktree already exists
	if (Test-Path $worktreePath) {
		$action = prompt_conflict_resolution $branchName

		switch ($action) {
			"stop" {
				Write-Host "[specify] Worktree creation cancelled" -ForegroundColor Yellow
				return $false
			}
			"cleanup" {
				Write-Host "[specify] Removing existing worktree..." -ForegroundColor Yellow
				# Try to remove via git first
				try {
					git worktree remove $worktreePath --force 2>$null
				} catch {
					# Ignore errors
				}
				# Clean up directory if it still exists
				if (Test-Path $worktreePath) {
					Remove-Item -Path $worktreePath -Recurse -Force -ErrorAction SilentlyContinue
				}
			}
			"skip" {
				Write-Host "[specify] Keeping existing worktree at: $worktreePath" -ForegroundColor Green
				return $true
			}
		}
	}

	# Create the worktree
	Write-Host "[specify] Creating worktree for branch '$branchName'..." -ForegroundColor Cyan
	try {
		$output = git worktree add $worktreePath $branchName 2>&1
		if ($LASTEXITCODE -eq 0) {
			Write-Host "[specify] Worktree created at: $worktreePath" -ForegroundColor Green
			Write-Host "[specify] Ready for parallel development!" -ForegroundColor Green
			return $true
		} else {
			Write-Host "[specify] Error: Failed to create worktree" -ForegroundColor Red
			Write-Host $output -ForegroundColor Red
			return $false
		}
	} catch {
		Write-Host "[specify] Error: Failed to create worktree - $_" -ForegroundColor Red
		return $false
	}
}

# ============================================================================
# User Story 3: List Worktrees Functions
# ============================================================================

# list_worktrees
# Lists all git worktrees with status, path, and disk usage
# Usage: list_worktrees
# Returns: $true on success, $false on error
function list_worktrees {
	try {
		$repoRoot = git rev-parse --show-toplevel 2>$null
		if ($LASTEXITCODE -ne 0) {
			Write-Host "[specify] Error: Not in a git repository" -ForegroundColor Red
			return $false
		}
	} catch {
		Write-Host "[specify] Error: Not in a git repository" -ForegroundColor Red
		return $false
	}

	# Parse git worktree list --porcelain (T031)
	$worktreesRaw = git worktree list --porcelain 2>$null
	if ([string]::IsNullOrEmpty($worktreesRaw)) {
		Write-Host "[specify] No worktrees found" -ForegroundColor Yellow
		return $true
	}

	# Get current branch for highlighting (T031)
	$currentBranch = git rev-parse --abbrev-ref HEAD 2>$null

	# Parse worktrees and build output
	$worktreeCount = 0
	$outputLines = @()

	# Add table header
	$outputLines += "┌─────────────────────────────┬──────────────────────────────────────────┬────────────┬──────────────┐"
	$outputLines += "│ Branch                      │ Path                                     │ Status     │ Disk Usage   │"
	$outputLines += "├─────────────────────────────┼──────────────────────────────────────────┼────────────┼──────────────┤"

	# Process each worktree entry
	$worktreePath = ""
	$branchName = ""

	foreach ($line in $worktreesRaw -split "`n") {
		$line = $line.Trim()
		if ($line -match '^worktree (.+)$') {
			$worktreePath = $matches[1]
		}
		elseif ($line -match '^branch refs/heads/(.+)$') {
			$branchName = $matches[1]

			# Skip main repo worktree (not in .worktrees/)
			if ($worktreePath -notmatch [regex]::Escape($WORKTREE_BASE_DIR)) {
				$worktreePath = ""
				$branchName = ""
				continue
			}

			# Detect status (T031)
			$status = "active"
			try {
				git show-ref --verify --quiet "refs/heads/$branchName" 2>$null
				if ($LASTEXITCODE -ne 0) {
					$status = "stale"
				}
			} catch {
				$status = "stale"
			}

			# Calculate disk usage
			$diskUsage = calculate_disk_usage $worktreePath

			# Highlight current branch (T031)
			$branchDisplay = $branchName
			if ($branchName -eq $currentBranch) {
				$branchDisplay = "→ $branchName"
			}

			# Format row with proper padding
			$branchCol = $branchDisplay.PadRight(27).Substring(0, [Math]::Min(27, $branchDisplay.Length)).PadRight(27)
			$pathRel = $worktreePath -replace [regex]::Escape("$repoRoot\"), ""
			$pathCol = $pathRel.PadRight(40).Substring(0, [Math]::Min(40, $pathRel.Length)).PadRight(40)
			$statusCol = $status.PadRight(10)
			$sizeCol = $diskUsage.PadRight(12)

			$outputLines += "│ $branchCol │ $pathCol │ $statusCol │ $sizeCol │"

			$worktreeCount++

			# Reset for next entry
			$worktreePath = ""
			$branchName = ""
		}
	}

	# Handle no worktrees found (T031)
	if ($worktreeCount -eq 0) {
		Write-Host "[specify] No spec-kit worktrees found in $WORKTREE_BASE_DIR/" -ForegroundColor Yellow
		return $true
	}

	# Add table footer
	$outputLines += "└─────────────────────────────┴──────────────────────────────────────────┴────────────┴──────────────┘"

	# Calculate total disk usage (T031)
	$totalDiskUsage = calculate_disk_usage (Join-Path $repoRoot $WORKTREE_BASE_DIR)
	$outputLines += ""
	$outputLines += "Total worktrees: $worktreeCount"
	$outputLines += "Total disk usage: $totalDiskUsage"

	# Print all output
	foreach ($line in $outputLines) {
		Write-Host $line
	}

	return $true
}

# ============================================================================
# User Story 4: Remove Specific Worktree Functions
# ============================================================================

# check_uncommitted_changes
# Checks if a worktree has uncommitted changes
# Usage: check_uncommitted_changes <worktree_path>
# Returns: $true if changes exist, $false if clean
function check_uncommitted_changes {
	param([string]$worktreePath)

	if (-not (Test-Path $worktreePath)) {
		return $false
	}

	# Run git status --porcelain in the worktree directory
	try {
		Push-Location $worktreePath
		$statusOutput = git status --porcelain 2>$null
		Pop-Location

		if (-not [string]::IsNullOrEmpty($statusOutput)) {
			# Uncommitted changes exist
			return $true
		} else {
			# Clean worktree
			return $false
		}
	} catch {
		Pop-Location
		return $false
	}
}

# remove_worktree
# Removes a specific worktree with safety checks
# Usage: remove_worktree [branch_name]
# If no branch_name provided, shows interactive selection menu
# Returns: $true on success, $false on error or cancellation
function remove_worktree {
	param([string]$branchName = "")

	try {
		$repoRoot = git rev-parse --show-toplevel 2>$null
		if ($LASTEXITCODE -ne 0) {
			Write-Host "[specify] Error: Not in a git repository" -ForegroundColor Red
			return $false
		}
	} catch {
		Write-Host "[specify] Error: Not in a git repository" -ForegroundColor Red
		return $false
	}

	# T042: Interactive selection menu when no branch argument provided
	if ([string]::IsNullOrEmpty($branchName)) {
		# Get list of worktrees (exclude main repo)
		$worktreesRaw = git worktree list --porcelain 2>$null
		if ([string]::IsNullOrEmpty($worktreesRaw)) {
			Write-Host "[specify] No worktrees found" -ForegroundColor Yellow
			return $true
		}

		# Build array of branches with worktrees
		$branches = @()
		$worktreePath = ""
		foreach ($line in $worktreesRaw -split "`n") {
			$line = $line.Trim()
			if ($line -match '^worktree (.+)$') {
				$worktreePath = $matches[1]
			}
			elseif ($line -match '^branch refs/heads/(.+)$') {
				$branch = $matches[1]
				# Only include worktrees in .worktrees/
				if ($worktreePath -match [regex]::Escape($WORKTREE_BASE_DIR)) {
					$branches += $branch
				}
				$worktreePath = ""
			}
		}

		if ($branches.Count -eq 0) {
			Write-Host "[specify] No spec-kit worktrees found" -ForegroundColor Yellow
			return $true
		}

		# Show interactive menu
		Write-Host "[specify] Select worktree to remove:" -ForegroundColor Cyan
		Write-Host ""
		for ($i = 0; $i -lt $branches.Count; $i++) {
			Write-Host "  $($i + 1)) $($branches[$i])"
		}
		Write-Host "  0) Cancel"
		Write-Host ""
		$choice = Read-Host "Enter choice (0-$($branches.Count))"

		if ($choice -eq "0" -or [string]::IsNullOrEmpty($choice)) {
			Write-Host "[specify] Removal cancelled" -ForegroundColor Yellow
			return $false
		}

		$choiceNum = 0
		if ([int]::TryParse($choice, [ref]$choiceNum) -and $choiceNum -ge 1 -and $choiceNum -le $branches.Count) {
			$branchName = $branches[$choiceNum - 1]
		} else {
			Write-Host "[specify] Error: Invalid choice" -ForegroundColor Red
			return $false
		}
	}

	$worktreePath = Join-Path $repoRoot "$WORKTREE_BASE_DIR\$branchName"

	# Validate worktree exists
	if (-not (Test-Path $worktreePath)) {
		Write-Host "[specify] Error: Worktree not found at: $worktreePath" -ForegroundColor Red
		return $false
	}

	# Calculate disk usage before removal (T042)
	$diskUsage = calculate_disk_usage $worktreePath

	# T042: Check for uncommitted changes and prompt for confirmation
	if (check_uncommitted_changes $worktreePath) {
		Write-Host "[specify] Warning: Worktree '$branchName' has uncommitted changes!" -ForegroundColor Yellow
		Write-Host ""
		Write-Host "Uncommitted files:" -ForegroundColor Yellow
		Push-Location $worktreePath
		git status --short 2>$null | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
		Pop-Location
		Write-Host ""
		$confirm = Read-Host "Are you sure you want to remove this worktree? (yes/no)"

		if ($confirm -ne "yes") {
			Write-Host "[specify] Removal cancelled" -ForegroundColor Yellow
			return $false
		}
	}

	# T042: Validation - do NOT delete feature branch or specs directory
	Write-Host "[specify] Removing worktree for branch '$branchName'..." -ForegroundColor Cyan
	Write-Host "[specify] Note: Feature branch and specs directory will be preserved" -ForegroundColor Cyan

	# T042: Execute git worktree remove followed by directory cleanup
	try {
		$output = git worktree remove $worktreePath --force 2>&1
		if ($LASTEXITCODE -eq 0) {
			# Cleanup directory if it still exists
			if (Test-Path $worktreePath) {
				Remove-Item -Path $worktreePath -Recurse -Force -ErrorAction SilentlyContinue
			}

			# T042: Display disk space reclaimed
			Write-Host "[specify] Worktree removed successfully" -ForegroundColor Green
			Write-Host "[specify] Disk space reclaimed: $diskUsage" -ForegroundColor Green
			return $true
		} else {
			Write-Host "[specify] Error: Failed to remove worktree" -ForegroundColor Red
			Write-Host "[specify] Try: git worktree prune" -ForegroundColor Red
			Write-Host $output -ForegroundColor Red
			return $false
		}
	} catch {
		Write-Host "[specify] Error: Failed to remove worktree - $_" -ForegroundColor Red
		Write-Host "[specify] Try: git worktree prune" -ForegroundColor Red
		return $false
	}
}

# ============================================================================
# User Story 5: Clean Up Stale Worktrees Functions
# ============================================================================

# cleanup_stale_worktrees
# Detects and batch-removes all stale worktrees
# Usage: cleanup_stale_worktrees
# Returns: $true on success, $false on error
function cleanup_stale_worktrees {
	try {
		$repoRoot = git rev-parse --show-toplevel 2>$null
		if ($LASTEXITCODE -ne 0) {
			Write-Host "[specify] Error: Not in a git repository" -ForegroundColor Red
			return $false
		}
	} catch {
		Write-Host "[specify] Error: Not in a git repository" -ForegroundColor Red
		return $false
	}

	# T053: Detect stale worktrees (branch deleted OR directory exists but not in git worktree list)
	$worktreesRaw = git worktree list --porcelain 2>$null

	# Arrays to track stale worktrees
	$staleBranches = @()
	$stalePaths = @()
	$staleSizes = @()

	# Check git-tracked worktrees for deleted branches
	$worktreePath = ""
	$branchName = ""

	foreach ($line in $worktreesRaw -split "`n") {
		$line = $line.Trim()
		if ($line -match '^worktree (.+)$') {
			$worktreePath = $matches[1]
		}
		elseif ($line -match '^branch refs/heads/(.+)$') {
			$branchName = $matches[1]

			# Skip main repo worktree
			if ($worktreePath -notmatch [regex]::Escape($WORKTREE_BASE_DIR)) {
				$worktreePath = ""
				$branchName = ""
				continue
			}

			# Check if branch still exists
			try {
				git show-ref --verify --quiet "refs/heads/$branchName" 2>$null
				if ($LASTEXITCODE -ne 0) {
					# Branch deleted - this is a stale worktree
					$staleBranches += $branchName
					$stalePaths += $worktreePath
					$staleSizes += (calculate_disk_usage $worktreePath)
				}
			} catch {
				# Branch deleted
				$staleBranches += $branchName
				$stalePaths += $worktreePath
				$staleSizes += (calculate_disk_usage $worktreePath)
			}

			$worktreePath = ""
			$branchName = ""
		}
	}

	# Check for orphaned directories (exist but not tracked by git)
	$worktreeBase = Join-Path $repoRoot $WORKTREE_BASE_DIR
	if (Test-Path $worktreeBase) {
		$dirs = Get-ChildItem -Path $worktreeBase -Directory -ErrorAction SilentlyContinue
		foreach ($dir in $dirs) {
			$dirPath = $dir.FullName
			$dirName = $dir.Name

			# Check if this directory is tracked by git
			$isTracked = $false
			foreach ($line in $worktreesRaw -split "`n") {
				$line = $line.Trim()
				if ($line -match '^worktree (.+)$') {
					if ($matches[1] -eq $dirPath) {
						$isTracked = $true
						break
					}
				}
			}

			# If not tracked, it's orphaned
			if (-not $isTracked) {
				$staleBranches += "$dirName (orphaned)"
				$stalePaths += $dirPath
				$staleSizes += (calculate_disk_usage $dirPath)
			}
		}
	}

	# T053: Handle case when no stale worktrees exist
	if ($staleBranches.Count -eq 0) {
		Write-Host "[specify] No stale worktrees found" -ForegroundColor Yellow
		return $true
	}

	# T053: Display list of detected stale worktrees with paths and disk usage
	Write-Host "[specify] Stale worktrees detected:" -ForegroundColor Yellow
	Write-Host ""
	for ($i = 0; $i -lt $staleBranches.Count; $i++) {
		Write-Host "  $($i + 1). $($staleBranches[$i])"
		Write-Host "     Path: $($stalePaths[$i])"
		Write-Host "     Disk usage: $($staleSizes[$i])"
		Write-Host ""
	}

	# Calculate total disk usage
	$totalSize = calculate_disk_usage $worktreeBase
	Write-Host "Total stale worktree disk usage: $totalSize"
	Write-Host ""

	# T053: Prompt for batch confirmation before removal
	$confirm = Read-Host "Remove all stale worktrees? (Y/N)"

	if ($confirm -notmatch '^[Yy]$') {
		Write-Host "[specify] Cleanup cancelled" -ForegroundColor Yellow
		return $true
	}

	# T053: Loop through stale worktrees calling git worktree remove on each
	$removedCount = 0
	$skippedCount = 0

	Write-Host ""
	Write-Host "[specify] Removing stale worktrees..." -ForegroundColor Cyan

	for ($i = 0; $i -lt $stalePaths.Count; $i++) {
		$path = $stalePaths[$i]
		$branch = $staleBranches[$i]

		# T053: Skip locked or in-use worktrees with warning message
		try {
			$output = git worktree remove $path --force 2>&1
			if ($LASTEXITCODE -eq 0) {
				# Cleanup directory if it still exists
				if (Test-Path $path) {
					Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
				}
				Write-Host "  ✓ Removed: $branch" -ForegroundColor Green
				$removedCount++
			} else {
				Write-Host "  ✗ Skipped: $branch (locked or in use)" -ForegroundColor Yellow
				$skippedCount++
			}
		} catch {
			Write-Host "  ✗ Skipped: $branch (locked or in use)" -ForegroundColor Yellow
			$skippedCount++
		}
	}

	# T053: Calculate and display total disk space reclaimed after cleanup
	Write-Host ""
	Write-Host "[specify] Cleanup complete!" -ForegroundColor Green
	Write-Host "  Removed: $removedCount worktree(s)"
	if ($skippedCount -gt 0) {
		Write-Host "  Skipped: $skippedCount worktree(s)"
	}
	Write-Host "  Total disk space reclaimed: $totalSize"

	return $true
}

# Functions will be implemented below as per tasks.md
