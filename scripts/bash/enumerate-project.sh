#!/usr/bin/env bash
#
# enumerate-project.sh - Enumerate all files in a project for AI analysis
#
# Usage:
#   ./enumerate-project.sh --project PATH [--output FILE] [--max-size BYTES]
#
# This script performs a full recursive scan of a project directory and outputs
# a JSON manifest of all files with metadata. AI will use this to decide what
# to include/exclude and how to read each file.
#

set -euo pipefail

# Script metadata
SCRIPT_VERSION="1.0.1"
SCRIPT_NAME="enumerate-project.sh"

# Default values
PROJECT_PATH=""
OUTPUT_FILE=""
MAX_FILE_SIZE=$((10 * 1024 * 1024))  # 10MB default
SCAN_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Colors for output (if not outputting JSON to stdout)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Platform-specific command (detected once at startup)
STAT_SIZE_CMD=""

# Progress reporting flag
SHOW_PROGRESS=false

# Check dependencies
check_dependencies() {
    local missing=0

    if ! command -v jq &> /dev/null; then
        echo "ERROR: jq is required but not installed" >&2
        echo "" >&2
        echo "Why jq? It prevents JSON injection vulnerabilities (security requirement)" >&2
        echo "" >&2
        echo "Installation options:" >&2
        echo "  • Standard: sudo apt-get install jq  OR  brew install jq" >&2
        echo "  • Corporate/Air-gapped: Download portable jq binary" >&2
        echo "    https://github.com/jqlang/jq/releases" >&2
        echo "    (Single file, no installation needed - just place in PATH)" >&2
        echo "  • Alternative: Use PowerShell version (scripts/powershell/enumerate-project.ps1)" >&2
        echo "    (No external dependencies)" >&2
        missing=1
    fi

    if ! command -v find &> /dev/null; then
        echo "ERROR: find command is required" >&2
        missing=1
    fi

    if [[ $missing -eq 1 ]]; then
        exit 1
    fi
}

# Detect platform and set stat command (run once at startup)
detect_platform() {
    # Create temp file to test stat command
    local test_file="${BASH_SOURCE[0]}"

    if stat -f %z "$test_file" &>/dev/null 2>&1; then
        STAT_SIZE_CMD="stat -f %z"  # macOS/BSD
    elif stat -c %s "$test_file" &>/dev/null 2>&1; then
        STAT_SIZE_CMD="stat -c %s"   # Linux/GNU
    else
        echo "ERROR: Cannot determine stat command for this platform" >&2
        exit 1
    fi
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project)
                if [[ -z "${2:-}" ]]; then
                    echo "ERROR: --project requires a path argument" >&2
                    exit 1
                fi
                PROJECT_PATH="$2"
                shift 2
                ;;
            --output)
                if [[ -z "${2:-}" ]]; then
                    echo "ERROR: --output requires a path argument" >&2
                    exit 1
                fi
                OUTPUT_FILE="$2"
                SHOW_PROGRESS=true
                shift 2
                ;;
            --max-size)
                if [[ -z "${2:-}" ]]; then
                    echo "ERROR: --max-size requires a numeric argument" >&2
                    exit 1
                fi
                # Validate numeric input
                if ! [[ "$2" =~ ^[0-9]+$ ]]; then
                    echo "ERROR: --max-size must be a positive integer (bytes)" >&2
                    echo "Received: $2" >&2
                    exit 1
                fi
                MAX_FILE_SIZE="$2"
                shift 2
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 --project PATH [OPTIONS]

Enumerate all files in a project directory for AI analysis.

Required Arguments:
  --project PATH       Path to project root directory

Optional Arguments:
  --output FILE        Output JSON file (default: stdout)
  --max-size BYTES     Maximum file size to include (default: 10485760 = 10MB)
  -h, --help          Show this help message

Output Format:
  JSON object with project structure, file metadata, and statistics

Examples:
  # Scan current directory, output to stdout
  $0 --project .

  # Scan project, save to file
  $0 --project /path/to/legacy --output manifest.json

  # Scan with custom size limit (50MB)
  $0 --project . --output manifest.json --max-size 52428800

Dependencies:
  - jq (required for JSON generation)
  - find (standard utility)

EOF
                exit 0
                ;;
            *)
                echo "Unknown option: $1" >&2
                echo "Use --help for usage information" >&2
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$PROJECT_PATH" ]]; then
        echo "ERROR: --project is required" >&2
        echo "Use --help for usage information" >&2
        exit 1
    fi

    # Validate project path
    if [[ ! -d "$PROJECT_PATH" ]]; then
        echo "ERROR: Project path does not exist or is not a directory: $PROJECT_PATH" >&2
        exit 1
    fi

    # Convert to absolute path
    PROJECT_PATH=$(cd "$PROJECT_PATH" && pwd)
}

# Progress logging (only if output goes to file and stderr is TTY)
log_progress() {
    if [[ "$SHOW_PROGRESS" == "true" ]] && [[ -t 2 ]]; then
        echo -e "${BLUE}ℹ${NC} $1" >&2
    fi
}

log_success() {
    if [[ "$SHOW_PROGRESS" == "true" ]] && [[ -t 2 ]]; then
        echo -e "${GREEN}✓${NC} $1" >&2
    fi
}

# Get file category based on extension
get_category() {
    local ext="$1"

    case "$ext" in
        # Code files
        js|ts|jsx|tsx|mjs|cjs) echo "code" ;;
        cs|fs|vb) echo "code" ;;
        java|kt|scala|groovy) echo "code" ;;
        py|pyw|pyx) echo "code" ;;
        rb|rake|gemspec) echo "code" ;;
        go) echo "code" ;;
        rs) echo "code" ;;
        php|phtml) echo "code" ;;
        c|cpp|cc|cxx|h|hpp) echo "code" ;;
        swift|m|mm) echo "code" ;;

        # Markup and styles
        html|htm|xhtml) echo "markup" ;;
        css|scss|sass|less) echo "style" ;;
        vue|svelte) echo "component" ;;

        # Configuration
        json|yaml|yml|toml|ini|conf|config) echo "config" ;;
        xml|plist) echo "config" ;;
        env|properties) echo "config" ;;

        # Build and project files
        csproj|sln|fsproj|vbproj) echo "project" ;;
        gradle|pom) echo "project" ;;
        gemfile|rakefile) echo "project" ;;
        lock) echo "lockfile" ;;

        # Database
        sql|psql|mysql) echo "database" ;;

        # Scripts
        sh|bash|zsh|fish) echo "script" ;;
        ps1|psm1|psd1) echo "script" ;;
        bat|cmd) echo "script" ;;

        # Documentation
        md|markdown|txt|rst|adoc) echo "documentation" ;;

        # Data
        csv|tsv|dat) echo "data" ;;

        # Binary/compiled
        dll|exe|so|dylib|a|o|obj|pdb) echo "binary" ;;
        class|jar|war|ear) echo "binary" ;;
        pyc|pyo) echo "binary" ;;

        # Images
        jpg|jpeg|png|gif|svg|ico|webp|bmp) echo "image" ;;

        # Archives
        zip|tar|gz|bz2|xz|7z|rar) echo "archive" ;;

        # Default
        *)
            if [[ -z "$ext" ]]; then
                echo "no_extension"
            else
                echo "other"
            fi
            ;;
    esac
}

# Detect if file is binary by checking for null bytes
# Returns: "true" or "false"
is_binary() {
    local filepath="$1"

    # Read first 8KB and count null bytes
    local null_count
    null_count=$(head -c 8192 "$filepath" 2>/dev/null | tr -cd '\000' | wc -c | tr -d ' ')

    if [[ -z "$null_count" ]] || [[ "$null_count" -eq 0 ]]; then
        echo "false"
    else
        echo "true"
    fi
}

# Extract file extension properly
get_extension() {
    local filepath="$1"
    local basename="${filepath##*/}"

    # Handle dotfiles without extension (.gitignore)
    if [[ "$basename" == .* ]] && [[ ! "$basename" =~ \..+\. ]] && [[ "$basename" != *.* || "$basename" == .* ]]; then
        echo ""
        return
    fi

    # Extract extension
    if [[ "$basename" =~ \. ]]; then
        local ext="${basename##*.}"
        echo ".${ext}"
    else
        echo ""
    fi
}

# Main enumeration function - streams JSON output
enumerate_files() {
    log_progress "Starting full recursive scan of: $PROJECT_PATH"

    local file_count=0
    local total_size=0
    local binary_count=0
    local oversized_count=0
    local error_count=0

    declare -A category_counts
    declare -A extension_counts
    declare -A largest_files  # key="size:path", stores top 10

    # Start JSON output
    if [[ -n "$OUTPUT_FILE" ]]; then
        exec 3>"$OUTPUT_FILE"
    else
        exec 3>&1
    fi

    # Output JSON header
    jq -n \
        --arg project "$PROJECT_PATH" \
        --arg scanner "bash-${BASH_VERSION}" \
        --arg version "$SCRIPT_VERSION" \
        --arg start "$SCAN_START" \
        --argjson max_size "$MAX_FILE_SIZE" \
        '{
            scan_info: {
                project_path: $project,
                scanner: $scanner,
                script_version: $version,
                scan_start: $start,
                scan_end: null,
                max_file_size_bytes: $max_size
            },
            files: [' >&3

    local first_file=true

    # Enumerate all files
    while IFS= read -r -d '' filepath; do
        ((file_count++))

        # Show progress every 100 files
        if [[ $((file_count % 100)) -eq 0 ]]; then
            log_progress "Scanned $file_count files..."
        fi

        # Get relative path
        local rel_path="${filepath#$PROJECT_PATH/}"

        # Get file size (using platform-specific command)
        local size=0
        if [[ -f "$filepath" ]]; then
            size=$($STAT_SIZE_CMD "$filepath" 2>/dev/null || echo 0)
        fi

        ((total_size += size))

        # Get extension
        local ext
        ext=$(get_extension "$filepath")
        local ext_for_category="${ext#.}"  # Remove leading dot for category lookup

        # Get category
        local category
        category=$(get_category "$ext_for_category")

        # Update counters
        ((category_counts[$category]=${category_counts[$category]:-0} + 1))
        if [[ -n "$ext" ]]; then
            ((extension_counts[$ext]=${extension_counts[$ext]:-0} + 1))
        fi

        # Track largest files (keep top 10)
        if [[ ${#largest_files[@]} -lt 10 ]]; then
            largest_files["$size:$filepath"]="$rel_path"
        else
            # Check if this file is larger than smallest in top 10
            local smallest_key=$(printf '%s\n' "${!largest_files[@]}" | sort -n | head -1)
            local smallest_size="${smallest_key%%:*}"
            if [[ $size -gt $smallest_size ]]; then
                unset "largest_files[$smallest_key]"
                largest_files["$size:$filepath"]="$rel_path"
            fi
        fi

        # Determine file properties
        local readable="true"
        local is_binary_file="false"
        local size_category="normal"
        local skip_reason=""

        # Check readability
        if [[ ! -r "$filepath" ]]; then
            readable="false"
            skip_reason="permission_denied"
            ((error_count++))
        # Check size before doing binary detection (CRITICAL FIX)
        elif [[ $size -gt $MAX_FILE_SIZE ]]; then
            size_category="oversized"
            skip_reason="exceeds_max_size"
            ((oversized_count++))
        # Check if binary by extension first
        elif [[ "$category" == "binary" ]] || [[ "$category" == "image" ]] || [[ "$category" == "archive" ]]; then
            is_binary_file="true"
            ((binary_count++))
        # Only now check binary by content (after size check!)
        elif [[ -f "$filepath" ]] && [[ -r "$filepath" ]]; then
            is_binary_file=$(is_binary "$filepath")
            if [[ "$is_binary_file" == "true" ]]; then
                ((binary_count++))
            fi
        fi

        # Determine size category for readable files
        if [[ "$size_category" != "oversized" ]] && [[ "$readable" == "true" ]]; then
            if [[ $size -lt 10240 ]]; then
                size_category="tiny"      # < 10KB
            elif [[ $size -lt 102400 ]]; then
                size_category="small"     # < 100KB
            elif [[ $size -lt 1048576 ]]; then
                size_category="medium"    # < 1MB
            else
                size_category="large"     # 1MB - 10MB
            fi
        fi

        # Output JSON for this file (using jq for safety - CRITICAL FIX)
        if [[ "$first_file" == "true" ]]; then
            first_file=false
        else
            echo "," >&3
        fi

        jq -n \
            --arg path "$rel_path" \
            --arg abs_path "$filepath" \
            --argjson size "$size" \
            --arg ext "$ext" \
            --arg cat "$category" \
            --arg size_cat "$size_category" \
            --argjson is_bin "$is_binary_file" \
            --argjson read "$readable" \
            --arg skip "$skip_reason" \
            '{
                path: $path,
                absolute_path: $abs_path,
                size_bytes: $size,
                extension: $ext,
                category: $cat,
                size_category: $size_cat,
                is_binary: $is_bin,
                readable: $read,
                skip_reason: $skip
            }' | tr -d '\n' >&3

    done < <(find "$PROJECT_PATH" -type f -print0 2>/dev/null)

    log_success "Scanned $file_count files"

    # Close files array
    echo "]," >&3

    # Build statistics
    local scan_end=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Convert category_counts to JSON
    local cat_json="{"
    local first=true
    for cat in "${!category_counts[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            cat_json+=","
        fi
        cat_json+="\"$cat\":${category_counts[$cat]}"
    done
    cat_json+="}"

    # Convert extension_counts to JSON
    local ext_json="{"
    first=true
    for ext in "${!extension_counts[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            ext_json+=","
        fi
        # Escape extension for JSON
        ext_json+="$(jq -n --arg e "$ext" '$e'):${extension_counts[$ext]}"
    done
    ext_json+="}"

    # Build largest files array
    echo "\"statistics\": {" >&3
    jq -n \
        --argjson total "$file_count" \
        --argjson size "$total_size" \
        --argjson binary "$binary_count" \
        --argjson oversized "$oversized_count" \
        --argjson errors "$error_count" \
        --argjson by_cat "$cat_json" \
        --argjson by_ext "$ext_json" \
        '{
            total_files: $total,
            total_size_bytes: $size,
            binary_files: $binary,
            oversized_files: $oversized,
            unreadable_files: $errors,
            by_category: $by_cat,
            by_extension: $by_ext,
            largest_files: []
        }' | head -n -1 | tail -n +2 >&3  # Remove outer braces

    # Add largest files
    echo "," >&3
    echo "\"largest_files\": [" >&3
    first=true
    for key in $(printf '%s\n' "${!largest_files[@]}" | sort -rn | head -10); do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo "," >&3
        fi
        local size="${key%%:*}"
        local path="${largest_files[$key]}"
        jq -n \
            --arg p "$path" \
            --argjson s "$size" \
            '{path: $p, size_bytes: $s}' | tr -d '\n' >&3
    done
    echo "]" >&3
    echo "}" >&3  # Close statistics

    # Update scan_end in scan_info
    echo "}" >&3  # Close root object

    # Close file descriptor
    exec 3>&-

    # Fix scan_end timestamp using jq (update in place)
    if [[ -n "$OUTPUT_FILE" ]]; then
        local temp_file="${OUTPUT_FILE}.tmp"
        jq --arg end "$scan_end" '.scan_info.scan_end = $end' "$OUTPUT_FILE" > "$temp_file"
        mv "$temp_file" "$OUTPUT_FILE"
    fi
}

# Main execution
main() {
    check_dependencies
    detect_platform
    parse_arguments "$@"
    enumerate_files

    log_success "Enumeration complete"
    if [[ -n "$OUTPUT_FILE" ]]; then
        log_success "Output: $OUTPUT_FILE"
    fi
}

main "$@"
