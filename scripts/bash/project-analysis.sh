#!/usr/bin/env bash

# Project Analysis Script (Bash)
#
# This script performs comprehensive project analysis against all SpecKit specifications
# to verify whether the project meets defined expectations.
#
# It also supports Universal Adoption features: discovering existing projects in any codebase.
#
# Usage: ./project-analysis.sh [OPTIONS]
#
# OPTIONS:
#   --json               Output in JSON format
#   --check-patterns     Enable code pattern analysis (Security, DRY, KISS, SOLID)
#   --discover           Discover all projects in repository (Universal Adoption)
#   --deep-analysis      Parse dependency files for detailed technology info (Phase 2)
#   --cached             Use cached discovery results (0 tokens!)
#   --force              Force rescan, ignore cache
#   --help, -h           Show help message

set -euo pipefail

# ============================================================================
# Script Directory and Imports
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

# ============================================================================
# Configuration
# ============================================================================

REPO_ROOT=$(get_repo_root) || die "Not in a git repository"
SPECKIT_DIR="$REPO_ROOT/.speckit"
CACHE_DIR="$SPECKIT_DIR/cache"
DISCOVERY_CACHE="$CACHE_DIR/discovery.json"

FLAG_JSON=false
FLAG_CHECK_PATTERNS=false
FLAG_DISCOVER=false
FLAG_DEEP_ANALYSIS=false
FLAG_CACHED=false
FLAG_FORCE=false

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    cat <<EOF
Usage: project-analysis.sh [OPTIONS]

Perform comprehensive project analysis against all SpecKit specifications.

OPTIONS:
  --json               Output in JSON format
  --check-patterns     Enable code pattern analysis (Security, DRY, KISS, SOLID)
  --discover           Discover all projects in repository (Universal Adoption)
  --deep-analysis      Parse dependency files for detailed technology info (Phase 2)
  --cached             Use cached discovery results (0 tokens!)
  --force              Force rescan, ignore cache
  --help, -h           Show this help message

EXAMPLES:
  # Basic project analysis (existing specs)
  ./project-analysis.sh --json

  # Analysis with pattern checking
  ./project-analysis.sh --json --check-patterns

  # Discover all projects (Universal Adoption - Phase 1)
  ./project-analysis.sh --discover --json

  # Discover with deep analysis (Phase 2: frameworks, versions, dependencies)
  ./project-analysis.sh --discover --deep-analysis --json

  # Use cached discovery (0 tokens!)
  ./project-analysis.sh --discover --cached --json

  # Force rescan with deep analysis
  ./project-analysis.sh --discover --deep-analysis --force --json

EOF
    exit 0
}

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            FLAG_JSON=true
            shift
            ;;
        --check-patterns)
            FLAG_CHECK_PATTERNS=true
            shift
            ;;
        --discover)
            FLAG_DISCOVER=true
            shift
            ;;
        --deep-analysis)
            FLAG_DEEP_ANALYSIS=true
            shift
            ;;
        --cached)
            FLAG_CACHED=true
            shift
            ;;
        --force)
            FLAG_FORCE=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

# ============================================================================
# Universal Adoption - Project Discovery Functions (Phase 1)
# ============================================================================

get_project_indicators() {
    # Returns list of file indicators for different project types
    cat <<'EOF'
package.json|nodejs|1
requirements.txt|python|1
pyproject.toml|python|1
go.mod|go|1
Cargo.toml|rust|1
pom.xml|java|1
build.gradle|java|1
*.csproj|csharp|1
*.sln|csharp|2
Gemfile|ruby|1
composer.json|php|1
CMakeLists.txt|cpp|1
EOF
}

find_projects() {
    # Discover all projects in repository
    # Returns: Array of project paths
    local repo_root="$1"
    local deep_analysis="${2:-false}"

    write_step_header "Scanning repository for projects..."

    local -a projects=()
    local indicators
    indicators=$(get_project_indicators)

    # Find all indicator files
    while IFS='|' read -r pattern type priority; do
        write_info "Searching for $pattern files..."

        local files
        if [[ "$pattern" == *"*"* ]]; then
            # Glob pattern
            files=$(find "$repo_root" -type f -name "$pattern" 2>/dev/null || true)
        else
            # Exact name
            files=$(find "$repo_root" -type f -name "$pattern" 2>/dev/null || true)
        fi

        while IFS= read -r file; do
            if [[ -n "$file" ]]; then
                local project_dir
                project_dir=$(dirname "$file")
                projects+=("$project_dir|$type|$pattern")
            fi
        done <<< "$files"
    done <<< "$indicators"

    # Remove duplicates and sort
    printf '%s\n' "${projects[@]}" | sort -u
}

identify_project_type() {
    # Identify project type based on indicator files
    local project_path="$1"

    # Priority order: nodejs > python > go > rust > java > etc.
    if [[ -f "$project_path/package.json" ]]; then
        echo "nodejs"
    elif [[ -f "$project_path/go.mod" ]]; then
        echo "go"
    elif [[ -f "$project_path/requirements.txt" ]] || [[ -f "$project_path/pyproject.toml" ]]; then
        echo "python"
    elif [[ -f "$project_path/Cargo.toml" ]]; then
        echo "rust"
    elif [[ -f "$project_path/pom.xml" ]] || [[ -f "$project_path/build.gradle" ]]; then
        echo "java"
    elif [[ -f "$project_path/"*.csproj ]]; then
        echo "csharp"
    elif [[ -f "$project_path/Gemfile" ]]; then
        echo "ruby"
    elif [[ -f "$project_path/composer.json" ]]; then
        echo "php"
    elif [[ -f "$project_path/CMakeLists.txt" ]]; then
        echo "cpp"
    else
        echo "unknown"
    fi
}

get_project_name() {
    # Extract project name from path
    local project_path="$1"
    basename "$project_path"
}

get_project_metadata() {
    # Get basic project metadata (no deep analysis)
    local project_path="$1"
    local project_type="$2"
    local indicator_file="$3"

    local project_name
    project_name=$(get_project_name "$project_path")

    local rel_path
    rel_path=$(get_relative_path "$REPO_ROOT" "$project_path")

    local size
    size=$(get_dir_size "$project_path")

    local file_count
    file_count=$(count_files "$project_path")

    local last_modified
    if [[ -f "$project_path/$indicator_file" ]]; then
        last_modified=$(get_file_mtime "$project_path/$indicator_file")
        last_modified=$(date -u -d "@$last_modified" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -r "$last_modified" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")
    else
        last_modified="unknown"
    fi

    # Generate JSON
    cat <<EOF
{
  "id": "$(echo "$rel_path" | tr '/' '-' | tr -d '.'))",
  "name": "$project_name",
  "path": "$rel_path",
  "type": "$project_type",
  "technology": "$project_type",
  "indicator_file": "$indicator_file",
  "size_bytes": $size,
  "file_count": $file_count,
  "last_modified": "$last_modified"
}
EOF
}

compute_cache_hash() {
    # Compute MD5 hash of all indicator file paths for cache validation
    local repo_root="$1"

    local indicators
    indicators=$(get_project_indicators)

    local -a files=()

    while IFS='|' read -r pattern type priority; do
        local found_files
        if [[ "$pattern" == *"*"* ]]; then
            found_files=$(find "$repo_root" -type f -name "$pattern" 2>/dev/null || true)
        else
            found_files=$(find "$repo_root" -type f -name "$pattern" 2>/dev/null || true)
        fi

        while IFS= read -r file; do
            if [[ -n "$file" ]]; then
                files+=("$file")
            fi
        done <<< "$found_files"
    done <<< "$indicators"

    # Sort and hash
    if command -v md5sum &> /dev/null; then
        printf '%s\n' "${files[@]}" | sort | md5sum | awk '{print $1}' || echo "none"
    elif command -v md5 &> /dev/null; then
        printf '%s\n' "${files[@]}" | sort | md5 -r | awk '{print $1}' || echo "none"
    else
        echo "none"
    fi
}

is_discovery_cache_valid() {
    # Check if discovery cache is still valid
    if [[ "$FLAG_FORCE" == "true" ]]; then
        return 1
    fi

    if [[ ! -f "$DISCOVERY_CACHE" ]]; then
        return 1
    fi

    # Validate JSON
    if ! validate_json_file "$DISCOVERY_CACHE"; then
        return 1
    fi

    # Check hash
    local cached_hash
    cached_hash=$(jq -r '.cache_hash // "none"' "$DISCOVERY_CACHE")

    local current_hash
    current_hash=$(compute_cache_hash "$REPO_ROOT")

    if [[ "$cached_hash" != "$current_hash" ]]; then
        return 1
    fi

    return 0
}

# ============================================================================
# Phase 2: Deep Technology Detection
# ============================================================================

get_nodejs_details() {
    # Parse package.json for Node.js details
    local project_path="$1"
    local pkg_json="$project_path/package.json"

    if [[ ! -f "$pkg_json" ]]; then
        echo "{}"
        return
    fi

    local framework="Unknown"
    local runtime_version="Unknown"
    local build_tools=()
    local test_frameworks=()
    local key_deps=()

    # Parse dependencies
    local all_deps
    all_deps=$(jq -r '(.dependencies // {}) + (.devDependencies // {}) | keys[]' "$pkg_json" 2>/dev/null || true)

    # Detect framework
    if echo "$all_deps" | grep -q "^express$"; then
        framework="Express"
    elif echo "$all_deps" | grep -q "^next$"; then
        framework="Next.js"
    elif echo "$all_deps" | grep -q "^react$"; then
        framework="React"
    elif echo "$all_deps" | grep -q "^vue$"; then
        framework="Vue.js"
    elif echo "$all_deps" | grep -q "^@angular/core$"; then
        framework="Angular"
    elif echo "$all_deps" | grep -q "^fastify$"; then
        framework="Fastify"
    elif echo "$all_deps" | grep -q "^nestjs$"; then
        framework="NestJS"
    fi

    # Runtime version
    runtime_version=$(jq -r '.engines.node // "Unknown"' "$pkg_json" 2>/dev/null || echo "Unknown")

    # Build tools
    if echo "$all_deps" | grep -q "typescript"; then
        build_tools+=("typescript")
    fi
    if echo "$all_deps" | grep -q "webpack"; then
        build_tools+=("webpack")
    fi
    if echo "$all_deps" | grep -q "vite"; then
        build_tools+=("vite")
    fi
    if echo "$all_deps" | grep -q "babel"; then
        build_tools+=("babel")
    fi

    # Test frameworks
    if echo "$all_deps" | grep -q "jest"; then
        test_frameworks+=("jest")
    fi
    if echo "$all_deps" | grep -q "mocha"; then
        test_frameworks+=("mocha")
    fi
    if echo "$all_deps" | grep -q "vitest"; then
        test_frameworks+=("vitest")
    fi

    # Key dependencies (top 5)
    mapfile -t key_deps < <(echo "$all_deps" | head -5)

    # Generate JSON
    local build_tools_json
    build_tools_json=$(printf '%s\n' "${build_tools[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    local test_frameworks_json
    test_frameworks_json=$(printf '%s\n' "${test_frameworks[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    local key_deps_json
    key_deps_json=$(printf '%s\n' "${key_deps[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "framework": "$framework",
  "runtime": "nodejs",
  "runtime_version": "$runtime_version",
  "build_tools": $build_tools_json,
  "test_frameworks": $test_frameworks_json,
  "key_dependencies": $key_deps_json
}
EOF
}

get_python_details() {
    # Parse requirements.txt or pyproject.toml for Python details
    local project_path="$1"

    local framework="Unknown"
    local runtime_version="Unknown"
    local build_tools=()
    local test_frameworks=()
    local key_deps=()

    # Try requirements.txt
    if [[ -f "$project_path/requirements.txt" ]]; then
        local reqs
        reqs=$(cat "$project_path/requirements.txt")

        # Detect framework
        if echo "$reqs" | grep -qi "^fastapi"; then
            framework="FastAPI"
        elif echo "$reqs" | grep -qi "^flask"; then
            framework="Flask"
        elif echo "$reqs" | grep -qi "^django"; then
            framework="Django"
        fi

        # Test frameworks
        if echo "$reqs" | grep -qi "^pytest"; then
            test_frameworks+=("pytest")
        fi
        if echo "$reqs" | grep -qi "^unittest"; then
            test_frameworks+=("unittest")
        fi

        # Key dependencies
        mapfile -t key_deps < <(echo "$reqs" | grep -v "^#" | grep -v "^$" | head -5)
    fi

    # Try pyproject.toml
    if [[ -f "$project_path/pyproject.toml" ]]; then
        # Basic parsing (would need toml parser for full support)
        if grep -qi "fastapi" "$project_path/pyproject.toml"; then
            framework="FastAPI"
        elif grep -qi "flask" "$project_path/pyproject.toml"; then
            framework="Flask"
        elif grep -qi "django" "$project_path/pyproject.toml"; then
            framework="Django"
        fi
    fi

    # Generate JSON
    local build_tools_json
    build_tools_json=$(printf '%s\n' "${build_tools[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    local test_frameworks_json
    test_frameworks_json=$(printf '%s\n' "${test_frameworks[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    local key_deps_json
    key_deps_json=$(printf '%s\n' "${key_deps[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "framework": "$framework",
  "runtime": "python",
  "runtime_version": "$runtime_version",
  "build_tools": $build_tools_json,
  "test_frameworks": $test_frameworks_json,
  "key_dependencies": $key_deps_json
}
EOF
}

get_go_details() {
    # Parse go.mod for Go details
    local project_path="$1"
    local go_mod="$project_path/go.mod"

    if [[ ! -f "$go_mod" ]]; then
        echo "{}"
        return
    fi

    local framework="Unknown"
    local runtime_version="Unknown"
    local build_tools=()
    local test_frameworks=()
    local key_deps=()

    # Parse go version
    runtime_version=$(grep -E "^go [0-9.]+" "$go_mod" | awk '{print $2}' || echo "Unknown")

    # Parse dependencies
    local deps
    deps=$(grep -E "^\s+[a-z]" "$go_mod" | awk '{print $1}' || true)

    # Detect framework
    if echo "$deps" | grep -q "github.com/gin-gonic/gin"; then
        framework="Gin"
    elif echo "$deps" | grep -q "github.com/gofiber/fiber"; then
        framework="Fiber"
    elif echo "$deps" | grep -q "github.com/labstack/echo"; then
        framework="Echo"
    fi

    # Key dependencies
    mapfile -t key_deps < <(echo "$deps" | head -5)

    # Generate JSON
    local build_tools_json
    build_tools_json=$(printf '%s\n' "${build_tools[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    local test_frameworks_json
    test_frameworks_json=$(printf '%s\n' "${test_frameworks[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    local key_deps_json
    key_deps_json=$(printf '%s\n' "${key_deps[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]")

    cat <<EOF
{
  "framework": "$framework",
  "runtime": "go",
  "runtime_version": "$runtime_version",
  "build_tools": $build_tools_json,
  "test_frameworks": $test_frameworks_json,
  "key_dependencies": $key_deps_json
}
EOF
}

enrich_project_with_deep_analysis() {
    # Enrich project metadata with deep technology detection
    local project_json="$1"

    local project_path
    project_path=$(echo "$project_json" | jq -r '.path')
    local full_path="$REPO_ROOT/$project_path"

    local technology
    technology=$(echo "$project_json" | jq -r '.technology')

    local details="{}"

    case "$technology" in
        nodejs)
            details=$(get_nodejs_details "$full_path")
            ;;
        python)
            details=$(get_python_details "$full_path")
            ;;
        go)
            details=$(get_go_details "$full_path")
            ;;
        *)
            details="{}"
            ;;
    esac

    # Merge details into project JSON
    echo "$project_json" | jq --argjson details "$details" '. + $details'
}

# ============================================================================
# Main Discovery Logic
# ============================================================================

run_discovery() {
    write_header "================================"
    write_header " Spec-Kit: Project Discovery"
    write_header "================================"

    # Check cache
    if [[ "$FLAG_CACHED" == "true" ]]; then
        write_step_header "Checking cache..."

        if is_discovery_cache_valid; then
            write_success "Using cached discovery results"
            cat "$DISCOVERY_CACHE"
            return 0
        else
            write_warning "Cache invalid or not found, running discovery"
        fi
    fi

    # Step 1: Find projects
    write_step_header "Step 1: Discovering projects..."
    local projects
    projects=$(find_projects "$REPO_ROOT" "$FLAG_DEEP_ANALYSIS")

    if [[ -z "$projects" ]]; then
        write_warning "No projects found"
        echo '{"projects": [], "total": 0}'
        return 0
    fi

    local project_count
    project_count=$(echo "$projects" | wc -l | tr -d ' ')
    write_success "Found $project_count potential projects"

    # Step 2: Process each project
    write_step_header "Step 2: Analyzing projects..."

    local -a project_jsons=()

    while IFS='|' read -r project_dir project_type indicator; do
        if [[ -z "$project_dir" ]]; then
            continue
        fi

        local project_name
        project_name=$(get_project_name "$project_dir")

        write_info "Analyzing: $project_name"

        local metadata
        metadata=$(get_project_metadata "$project_dir" "$project_type" "$indicator")

        # Deep analysis (Phase 2)
        if [[ "$FLAG_DEEP_ANALYSIS" == "true" ]]; then
            metadata=$(enrich_project_with_deep_analysis "$metadata")
        fi

        project_jsons+=("$metadata")
    done <<< "$projects"

    # Step 3: Generate output
    write_step_header "Step 3: Generating output..."

    local cache_hash
    cache_hash=$(compute_cache_hash "$REPO_ROOT")

    local timestamp
    timestamp=$(get_iso_timestamp)

    # Build JSON array
    local projects_json="["
    local first=true
    for pj in "${project_jsons[@]}"; do
        if [[ "$first" == "true" ]]; then
            projects_json+="$pj"
            first=false
        else
            projects_json+=", $pj"
        fi
    done
    projects_json+="]"

    local output
    output=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "repo_root": "$REPO_ROOT",
  "total_projects": ${#project_jsons[@]},
  "deep_analysis_enabled": $FLAG_DEEP_ANALYSIS,
  "cache_hash": "$cache_hash",
  "projects": $projects_json
}
EOF
)

    # Save cache
    ensure_dir "$CACHE_DIR"
    echo "$output" > "$DISCOVERY_CACHE"
    write_success "Cache saved to: $DISCOVERY_CACHE"

    # Output result
    if [[ "$FLAG_JSON" == "true" ]]; then
        echo "$output" | jq .
    else
        write_header "================================"
        write_header " Discovery Complete!"
        write_header "================================"
        echo ""
        write_progress "Total Projects: ${#project_jsons[@]}"
        write_progress "Deep Analysis: $FLAG_DEEP_ANALYSIS"
        write_progress "Cache File: $DISCOVERY_CACHE"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    if [[ "$FLAG_DISCOVER" == "true" ]]; then
        run_discovery
    else
        die "Non-discovery mode not yet implemented in Bash version. Use PowerShell version or specify --discover"
    fi
}

# Run main function
main
