#!/usr/bin/env bash
# Manage git worktrees for spec-kit parallel development workflows
# Part of GitHub Spec Kit - https://github.com/github/spec-kit

set -e

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Constants
WORKTREE_BASE_DIR=".worktrees"

# ============================================================================
# Foundational Utility Functions
# ============================================================================

# ensure_worktree_gitignore
# Adds .worktrees/ to .gitignore if not already present
# Usage: ensure_worktree_gitignore
ensure_worktree_gitignore() {
	local repo_root
	repo_root=$(get_repo_root)
	local gitignore="$repo_root/.gitignore"

	# Create .gitignore if it doesn't exist
	if [[ ! -f "$gitignore" ]]; then
		cat > "$gitignore" <<EOF
# Git worktrees (parallel development)
.worktrees/
EOF
		return 0
	fi

	# Check if .worktrees/ is already in .gitignore
	if grep -q "^\.worktrees/" "$gitignore" 2>/dev/null || \
	   grep -q "^\.worktrees$" "$gitignore" 2>/dev/null || \
	   grep -q "^/\.worktrees/" "$gitignore" 2>/dev/null; then
		return 0
	fi

	# Add .worktrees/ to .gitignore
	echo "" >> "$gitignore"
	echo "# Git worktrees (parallel development)" >> "$gitignore"
	echo ".worktrees/" >> "$gitignore"
}

# get_worktree_status
# Checks if a worktree is active, stale, or orphaned
# Usage: get_worktree_status <branch_name>
# Returns: "active" | "stale" | "orphaned" | "none"
get_worktree_status() {
	local branch_name="$1"
	local repo_root
	repo_root=$(get_repo_root)
	local worktree_path="$repo_root/$WORKTREE_BASE_DIR/$branch_name"

	# Check if worktree directory exists
	if [[ ! -d "$worktree_path" ]]; then
		echo "none"
		return 0
	fi

	# Check if git knows about this worktree
	local git_knows=false
	if git worktree list --porcelain 2>/dev/null | grep -q "^worktree $worktree_path$"; then
		git_knows=true
	fi

	# Check if branch exists
	local branch_exists=false
	if git show-ref --verify --quiet "refs/heads/$branch_name" 2>/dev/null; then
		branch_exists=true
	fi

	# Determine status
	if [[ "$git_knows" == true ]] && [[ "$branch_exists" == true ]]; then
		echo "active"
	elif [[ "$git_knows" == true ]] && [[ "$branch_exists" == false ]]; then
		echo "stale"
	elif [[ "$git_knows" == false ]] && [[ -d "$worktree_path" ]]; then
		echo "orphaned"
	else
		echo "none"
	fi
}

# calculate_disk_usage
# Calculates human-readable disk usage for a worktree
# Usage: calculate_disk_usage <path>
# Returns: Human-readable size (e.g., "150M", "2.3G")
calculate_disk_usage() {
	local path="$1"

	if [[ ! -d "$path" ]]; then
		echo "0B"
		return 0
	fi

	# Use du -sh for human-readable output
	if command -v du >/dev/null 2>&1; then
		du -sh "$path" 2>/dev/null | awk '{print $1}' || echo "0B"
	else
		echo "N/A"
	fi
}

# ============================================================================
# User Story 1: Automatic Worktree Creation Functions
# ============================================================================

# prompt_conflict_resolution
# Prompts user when worktree already exists with options: stop, cleanup, skip
# Usage: prompt_conflict_resolution <branch_name>
# Returns: "stop" | "cleanup" | "skip"
prompt_conflict_resolution() {
	local branch_name="$1"

	echo "[specify] Worktree already exists for branch '$branch_name'" >&2
	echo "" >&2
	echo "Choose action:" >&2
	echo "  1) Stop - Cancel operation with error" >&2
	echo "  2) Cleanup - Remove old worktree and create fresh" >&2
	echo "  3) Skip - Keep existing worktree, continue" >&2
	echo "" >&2
	read -p "Enter choice (1-3): " choice >&2

	case "$choice" in
		1)
			echo "stop"
			;;
		2)
			echo "cleanup"
			;;
		3)
			echo "skip"
			;;
		*)
			echo "[specify] Invalid choice. Defaulting to stop." >&2
			echo "stop"
			;;
	esac
}

# create_worktree
# Creates a git worktree for the specified branch
# Usage: create_worktree <branch_name>
# Returns: 0 on success, 1 on error or stop
create_worktree() {
	local branch_name="$1"

	if [[ -z "$branch_name" ]]; then
		echo "[specify] Error: Branch name required" >&2
		return 1
	fi

	# Validate we're in a git repository (T021)
	local repo_root
	if ! repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
		echo "[specify] Error: Not in a git repository" >&2
		echo "[specify] Git worktrees require a git repository" >&2
		return 1
	fi

	# Validate branch follows spec-kit naming convention ###-feature-name (T019)
	if [[ ! "$branch_name" =~ ^[0-9]{3}- ]]; then
		echo "[specify] Error: Invalid branch name: $branch_name" >&2
		echo "[specify] Spec-kit worktrees require branches named like: 001-feature-name" >&2
		return 1
	fi

	# Error if on main branch (T020)
	if [[ "$branch_name" == "main" ]] || [[ "$branch_name" == "master" ]]; then
		echo "[specify] Error: Cannot create worktree for main/master branch" >&2
		echo "[specify] Worktrees are for feature branches only (###-feature-name)" >&2
		return 1
	fi
	local worktree_path="$repo_root/$WORKTREE_BASE_DIR/$branch_name"

	# Ensure .gitignore contains .worktrees/
	ensure_worktree_gitignore

	# Create .worktrees/ directory if it doesn't exist
	mkdir -p "$repo_root/$WORKTREE_BASE_DIR"

	# Check if worktree already exists
	if [[ -d "$worktree_path" ]]; then
		local action
		action=$(prompt_conflict_resolution "$branch_name")

		case "$action" in
			stop)
				echo "[specify] Worktree creation cancelled" >&2
				return 1
				;;
			cleanup)
				echo "[specify] Removing existing worktree..." >&2
				# Try to remove via git first
				git worktree remove "$worktree_path" --force 2>/dev/null || true
				# Clean up directory if it still exists
				rm -rf "$worktree_path"
				;;
			skip)
				echo "[specify] Keeping existing worktree at: $worktree_path" >&2
				return 0
				;;
		esac
	fi

	# Create the worktree
	echo "[specify] Creating worktree for branch '$branch_name'..." >&2
	if git worktree add "$worktree_path" "$branch_name" 2>&1; then
		echo "[specify] Worktree created at: $worktree_path" >&2
		echo "[specify] Ready for parallel development!" >&2
		return 0
	else
		echo "[specify] Error: Failed to create worktree" >&2
		return 1
	fi
}

# ============================================================================
# User Story 3: List Worktrees Functions
# ============================================================================

# list_worktrees
# Lists all git worktrees with status, path, and disk usage
# Usage: list_worktrees
# Returns: 0 on success, 1 on error
list_worktrees() {
	local repo_root
	if ! repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
		echo "[specify] Error: Not in a git repository" >&2
		return 1
	fi

	# Parse git worktree list --porcelain (T025)
	local worktrees_raw
	worktrees_raw=$(git worktree list --porcelain 2>/dev/null)

	if [[ -z "$worktrees_raw" ]]; then
		echo "[specify] No worktrees found" >&2
		return 0
	fi

	# Get current branch for highlighting (T028)
	local current_branch
	current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

	# Parse worktrees and build output
	local worktree_count=0
	local total_size_bytes=0
	local output_lines=()

	# Add table header
	output_lines+=("┌─────────────────────────────┬──────────────────────────────────────────┬────────────┬──────────────┐")
	output_lines+=("│ Branch                      │ Path                                     │ Status     │ Disk Usage   │")
	output_lines+=("├─────────────────────────────┼──────────────────────────────────────────┼────────────┼──────────────┤")

	# Process each worktree entry
	local worktree_path=""
	local branch_name=""

	while IFS= read -r line; do
		if [[ "$line" =~ ^worktree\ (.+)$ ]]; then
			worktree_path="${BASH_REMATCH[1]}"
		elif [[ "$line" =~ ^branch\ refs/heads/(.+)$ ]]; then
			branch_name="${BASH_REMATCH[1]}"

			# Skip main repo worktree (not in .worktrees/)
			if [[ ! "$worktree_path" =~ $WORKTREE_BASE_DIR ]]; then
				worktree_path=""
				branch_name=""
				continue
			fi

			# Detect status (T026)
			local status
			local branch_exists=false
			if git show-ref --verify --quiet "refs/heads/$branch_name" 2>/dev/null; then
				branch_exists=true
				status="active"
			else
				status="stale"
			fi

			# Calculate disk usage
			local disk_usage
			disk_usage=$(calculate_disk_usage "$worktree_path")

			# Highlight current branch (T028)
			local branch_display="$branch_name"
			if [[ "$branch_name" == "$current_branch" ]]; then
				branch_display="→ $branch_name"
			fi

			# Format row with proper padding
			local branch_col=$(printf "%-27s" "$branch_display")
			local path_col=$(printf "%-40s" "${worktree_path/$repo_root\//}")
			local status_col=$(printf "%-10s" "$status")
			local size_col=$(printf "%-12s" "$disk_usage")

			output_lines+=("│ $branch_col │ $path_col │ $status_col │ $size_col │")

			worktree_count=$((worktree_count + 1))

			# Reset for next entry
			worktree_path=""
			branch_name=""
		fi
	done <<< "$worktrees_raw"

	# Handle no worktrees found (T030)
	if [[ $worktree_count -eq 0 ]]; then
		echo "[specify] No spec-kit worktrees found in $WORKTREE_BASE_DIR/" >&2
		return 0
	fi

	# Add table footer
	output_lines+=("└─────────────────────────────┴──────────────────────────────────────────┴────────────┴──────────────┘")

	# Calculate total disk usage (T029)
	local total_disk_usage
	total_disk_usage=$(calculate_disk_usage "$repo_root/$WORKTREE_BASE_DIR")
	output_lines+=("")
	output_lines+=("Total worktrees: $worktree_count")
	output_lines+=("Total disk usage: $total_disk_usage")

	# Print all output
	for line in "${output_lines[@]}"; do
		echo "$line"
	done

	return 0
}

# ============================================================================
# User Story 4: Remove Specific Worktree Functions
# ============================================================================

# check_uncommitted_changes
# Checks if a worktree has uncommitted changes
# Usage: check_uncommitted_changes <worktree_path>
# Returns: 0 if changes exist, 1 if clean
check_uncommitted_changes() {
	local worktree_path="$1"

	if [[ ! -d "$worktree_path" ]]; then
		return 1
	fi

	# Run git status --porcelain in the worktree directory
	local status_output
	status_output=$(cd "$worktree_path" && git status --porcelain 2>/dev/null)

	if [[ -n "$status_output" ]]; then
		# Uncommitted changes exist
		return 0
	else
		# Clean worktree
		return 1
	fi
}

# remove_worktree
# Removes a specific worktree with safety checks
# Usage: remove_worktree [branch_name]
# If no branch_name provided, shows interactive selection menu
# Returns: 0 on success, 1 on error or cancellation
remove_worktree() {
	local branch_name="$1"
	local repo_root

	if ! repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
		echo "[specify] Error: Not in a git repository" >&2
		return 1
	fi

	# T036: Interactive selection menu when no branch argument provided
	if [[ -z "$branch_name" ]]; then
		# Get list of worktrees (exclude main repo)
		local worktrees_raw
		worktrees_raw=$(git worktree list --porcelain 2>/dev/null)

		if [[ -z "$worktrees_raw" ]]; then
			echo "[specify] No worktrees found" >&2
			return 0
		fi

		# Build array of branches with worktrees
		local -a branches=()
		local worktree_path=""
		while IFS= read -r line; do
			if [[ "$line" =~ ^worktree\ (.+)$ ]]; then
				worktree_path="${BASH_REMATCH[1]}"
			elif [[ "$line" =~ ^branch\ refs/heads/(.+)$ ]]; then
				local branch="${BASH_REMATCH[1]}"
				# Only include worktrees in .worktrees/
				if [[ "$worktree_path" =~ $WORKTREE_BASE_DIR ]]; then
					branches+=("$branch")
				fi
				worktree_path=""
			fi
		done <<< "$worktrees_raw"

		if [[ ${#branches[@]} -eq 0 ]]; then
			echo "[specify] No spec-kit worktrees found" >&2
			return 0
		fi

		# Show interactive menu
		echo "[specify] Select worktree to remove:" >&2
		echo "" >&2
		local i=1
		for branch in "${branches[@]}"; do
			echo "  $i) $branch" >&2
			i=$((i + 1))
		done
		echo "  0) Cancel" >&2
		echo "" >&2
		read -p "Enter choice (0-$((${#branches[@]}))): " choice >&2

		if [[ "$choice" == "0" ]] || [[ -z "$choice" ]]; then
			echo "[specify] Removal cancelled" >&2
			return 1
		fi

		if [[ "$choice" =~ ^[0-9]+$ ]] && [[ "$choice" -ge 1 ]] && [[ "$choice" -le ${#branches[@]} ]]; then
			branch_name="${branches[$((choice - 1))]}"
		else
			echo "[specify] Error: Invalid choice" >&2
			return 1
		fi
	fi

	local worktree_path="$repo_root/$WORKTREE_BASE_DIR/$branch_name"

	# Validate worktree exists
	if [[ ! -d "$worktree_path" ]]; then
		echo "[specify] Error: Worktree not found at: $worktree_path" >&2
		return 1
	fi

	# Calculate disk usage before removal (T039)
	local disk_usage
	disk_usage=$(calculate_disk_usage "$worktree_path")

	# T037: Check for uncommitted changes and prompt for confirmation
	if check_uncommitted_changes "$worktree_path"; then
		echo "[specify] Warning: Worktree '$branch_name' has uncommitted changes!" >&2
		echo "" >&2
		echo "Uncommitted files:" >&2
		(cd "$worktree_path" && git status --short 2>/dev/null) >&2
		echo "" >&2
		read -p "Are you sure you want to remove this worktree? (yes/no): " confirm >&2

		if [[ "$confirm" != "yes" ]]; then
			echo "[specify] Removal cancelled" >&2
			return 1
		fi
	fi

	# T040: Validation - do NOT delete feature branch or specs directory
	echo "[specify] Removing worktree for branch '$branch_name'..." >&2
	echo "[specify] Note: Feature branch and specs directory will be preserved" >&2

	# T038: Execute git worktree remove followed by directory cleanup
	if git worktree remove "$worktree_path" --force 2>&1; then
		# Cleanup directory if it still exists
		if [[ -d "$worktree_path" ]]; then
			rm -rf "$worktree_path"
		fi

		# T039: Display disk space reclaimed
		echo "[specify] Worktree removed successfully" >&2
		echo "[specify] Disk space reclaimed: $disk_usage" >&2
		return 0
	else
		echo "[specify] Error: Failed to remove worktree" >&2
		echo "[specify] Try: git worktree prune" >&2
		return 1
	fi
}

# ============================================================================
# User Story 5: Clean Up Stale Worktrees Functions
# ============================================================================

# cleanup_stale_worktrees
# Detects and batch-removes all stale worktrees
# Usage: cleanup_stale_worktrees
# Returns: 0 on success, 1 on error
cleanup_stale_worktrees() {
	local repo_root
	if ! repo_root=$(git rev-parse --show-toplevel 2>/dev/null); then
		echo "[specify] Error: Not in a git repository" >&2
		return 1
	fi

	# T046: Detect stale worktrees (branch deleted OR directory exists but not in git worktree list)
	local worktrees_raw
	worktrees_raw=$(git worktree list --porcelain 2>/dev/null)

	# Arrays to track stale worktrees
	local -a stale_branches=()
	local -a stale_paths=()
	local -a stale_sizes=()

	# Check git-tracked worktrees for deleted branches
	local worktree_path=""
	local branch_name=""

	while IFS= read -r line; do
		if [[ "$line" =~ ^worktree\ (.+)$ ]]; then
			worktree_path="${BASH_REMATCH[1]}"
		elif [[ "$line" =~ ^branch\ refs/heads/(.+)$ ]]; then
			branch_name="${BASH_REMATCH[1]}"

			# Skip main repo worktree
			if [[ ! "$worktree_path" =~ $WORKTREE_BASE_DIR ]]; then
				worktree_path=""
				branch_name=""
				continue
			fi

			# Check if branch still exists
			if ! git show-ref --verify --quiet "refs/heads/$branch_name" 2>/dev/null; then
				# Branch deleted - this is a stale worktree
				stale_branches+=("$branch_name")
				stale_paths+=("$worktree_path")
				stale_sizes+=("$(calculate_disk_usage "$worktree_path")")
			fi

			worktree_path=""
			branch_name=""
		fi
	done <<< "$worktrees_raw"

	# Check for orphaned directories (exist but not tracked by git)
	local worktree_base="$repo_root/$WORKTREE_BASE_DIR"
	if [[ -d "$worktree_base" ]]; then
		for dir in "$worktree_base"/*; do
			if [[ -d "$dir" ]]; then
				local dir_name=$(basename "$dir")
				# Check if this directory is tracked by git
				local is_tracked=false
				while IFS= read -r line; do
					if [[ "$line" =~ ^worktree\ (.+)$ ]]; then
						if [[ "${BASH_REMATCH[1]}" == "$dir" ]]; then
							is_tracked=true
							break
						fi
					fi
				done <<< "$worktrees_raw"

				# If not tracked, it's orphaned
				if [[ "$is_tracked" == false ]]; then
					stale_branches+=("$dir_name (orphaned)")
					stale_paths+=("$dir")
					stale_sizes+=("$(calculate_disk_usage "$dir")")
				fi
			fi
		done
	fi

	# T052: Handle case when no stale worktrees exist
	if [[ ${#stale_branches[@]} -eq 0 ]]; then
		echo "[specify] No stale worktrees found" >&2
		return 0
	fi

	# T047: Display list of detected stale worktrees with paths and disk usage
	echo "[specify] Stale worktrees detected:" >&2
	echo "" >&2
	for i in "${!stale_branches[@]}"; do
		echo "  $((i + 1)). ${stale_branches[$i]}" >&2
		echo "     Path: ${stale_paths[$i]}" >&2
		echo "     Disk usage: ${stale_sizes[$i]}" >&2
		echo "" >&2
	done

	# Calculate total disk usage
	local total_size
	total_size=$(calculate_disk_usage "$worktree_base")
	echo "Total stale worktree disk usage: $total_size" >&2
	echo "" >&2

	# T048: Prompt for batch confirmation before removal
	read -p "Remove all stale worktrees? (Y/N): " confirm >&2

	if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
		echo "[specify] Cleanup cancelled" >&2
		return 0
	fi

	# T049: Loop through stale worktrees calling git worktree remove on each
	local removed_count=0
	local skipped_count=0
	local total_reclaimed=0

	echo "" >&2
	echo "[specify] Removing stale worktrees..." >&2

	for i in "${!stale_paths[@]}"; do
		local path="${stale_paths[$i]}"
		local branch="${stale_branches[$i]}"

		# T050: Skip locked or in-use worktrees with warning message
		if git worktree remove "$path" --force 2>/dev/null; then
			# Cleanup directory if it still exists
			if [[ -d "$path" ]]; then
				rm -rf "$path"
			fi
			echo "  ✓ Removed: $branch" >&2
			removed_count=$((removed_count + 1))
		else
			echo "  ✗ Skipped: $branch (locked or in use)" >&2
			skipped_count=$((skipped_count + 1))
		fi
	done

	# T051: Calculate and display total disk space reclaimed after cleanup
	echo "" >&2
	echo "[specify] Cleanup complete!" >&2
	echo "  Removed: $removed_count worktree(s)" >&2
	if [[ $skipped_count -gt 0 ]]; then
		echo "  Skipped: $skipped_count worktree(s)" >&2
	fi
	echo "  Total disk space reclaimed: $total_size" >&2

	return 0
}

# Functions will be implemented below as per tasks.md
