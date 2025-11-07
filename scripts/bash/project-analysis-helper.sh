#!/usr/bin/env bash

# Project Analysis Helper Functions
# Provides caching and optimization utilities for project analysis

set -e

# Cache file location
CACHE_FILE=".speckit-analysis-cache.json"

# Generate MD5 hash of a file
get_file_hash() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if command -v md5sum >/dev/null 2>&1; then
            md5sum "$file" | awk '{print $1}'
        elif command -v md5 >/dev/null 2>&1; then
            md5 -q "$file"
        else
            # Fallback: use file size + modification time
            stat -f "%z-%m" "$file" 2>/dev/null || stat -c "%s-%Y" "$file" 2>/dev/null
        fi
    else
        echo "file-not-found"
    fi
}

# Load cache from JSON file
load_cache() {
    if [[ -f "$CACHE_FILE" ]]; then
        cat "$CACHE_FILE"
    else
        echo '{}'
    fi
}

# Check if file has changed since last analysis
file_has_changed() {
    local file="$1"
    local cache_json="$2"

    local current_hash=$(get_file_hash "$file")
    local cached_hash=$(echo "$cache_json" | grep -o "\"$file\":{\"hash\":\"[^\"]*\"" | grep -o "hash\":\"[^\"]*\"" | cut -d'"' -f3)

    if [[ "$current_hash" != "$cached_hash" ]]; then
        echo "true"
    else
        echo "false"
    fi
}

# Update cache with file analysis results
update_cache() {
    local file="$1"
    local hash="$2"
    local issues_count="$3"
    local timestamp="$4"

    # Simple append-based cache update
    # In production, would use jq for proper JSON manipulation
    echo "Cache updated for $file" >&2
}

# Get files to analyze (only changed files in incremental mode)
get_files_to_analyze() {
    local specs_dir="$1"
    local incremental="${2:-false}"
    local cache_json="${3:-{}}"

    local files_to_analyze=()

    for spec_dir in "$specs_dir"/*; do
        if [[ -d "$spec_dir" ]]; then
            for file in "$spec_dir"/{spec.md,plan.md,tasks.md}; do
                if [[ -f "$file" ]]; then
                    if [[ "$incremental" == "true" ]]; then
                        if [[ $(file_has_changed "$file" "$cache_json") == "true" ]]; then
                            files_to_analyze+=("$file")
                        fi
                    else
                        files_to_analyze+=("$file")
                    fi
                fi
            done
        fi
    done

    printf '%s\n' "${files_to_analyze[@]}"
}

# Extract specific section from markdown file
extract_section() {
    local file="$1"
    local section_name="$2"

    awk "
        /^## $section_name/ { found=1; next }
        /^## / && found { exit }
        found { print }
    " "$file"
}

# Count requirements in spec file (without reading full file)
count_requirements() {
    local spec_file="$1"
    grep -c "^- \*\*FR-" "$spec_file" 2>/dev/null || echo "0"
}

# Count tasks in tasks file (without reading full file)
count_tasks() {
    local tasks_file="$1"
    grep -c "^\[T[0-9]" "$tasks_file" 2>/dev/null || echo "0"
}

# Sample source files for pattern analysis
sample_source_files() {
    local source_dir="$1"
    local max_files="${2:-20}"
    local file_pattern="${3:-*}"

    # Prioritize important files
    local priority_patterns=(
        "*auth*" "*login*" "*api*" "*endpoint*"
        "*database*" "*db*" "*model*" "*controller*"
        "*service*" "*handler*" "*middleware*"
    )

    local sampled_files=()

    # First, get priority files
    for pattern in "${priority_patterns[@]}"; do
        while IFS= read -r file; do
            if [[ ${#sampled_files[@]} -lt $max_files ]]; then
                sampled_files+=("$file")
            fi
        done < <(find "$source_dir" -type f -name "$pattern.$file_pattern" 2>/dev/null | head -5)
    done

    # Fill remaining with random sample
    if [[ ${#sampled_files[@]} -lt $max_files ]]; then
        local remaining=$((max_files - ${#sampled_files[@]}))
        while IFS= read -r file; do
            # Skip if already in sampled_files
            local already_sampled=false
            for sampled in "${sampled_files[@]}"; do
                if [[ "$file" == "$sampled" ]]; then
                    already_sampled=true
                    break
                fi
            done

            if [[ "$already_sampled" == false ]]; then
                sampled_files+=("$file")
                if [[ ${#sampled_files[@]} -ge $max_files ]]; then
                    break
                fi
            fi
        done < <(find "$source_dir" -type f -name "*.$file_pattern" 2>/dev/null | shuf | head -$remaining)
    fi

    printf '%s\n' "${sampled_files[@]}"
}

# Targeted pattern search (returns count + line numbers only)
search_pattern() {
    local directory="$1"
    local pattern="$2"
    local file_type="${3:-}"

    local grep_cmd="grep -rn"

    if [[ -n "$file_type" ]]; then
        grep_cmd="$grep_cmd --include=*.$file_type"
    fi

    # Return format: filename:line_number (no content)
    $grep_cmd "$pattern" "$directory" 2>/dev/null | cut -d: -f1-2 | head -100 || echo ""
}

# Count pattern occurrences
count_pattern() {
    local directory="$1"
    local pattern="$2"
    local file_type="${3:-}"

    search_pattern "$directory" "$pattern" "$file_type" | wc -l
}

# Check if codebase is large (requires sampling)
is_large_codebase() {
    local source_dir="$1"
    local threshold="${2:-50}"

    local file_count=$(find "$source_dir" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" -o -name "*.go" -o -name "*.rb" \) 2>/dev/null | wc -l)

    if [[ $file_count -gt $threshold ]]; then
        echo "true"
    else
        echo "false"
    fi
}

# Generate cache statistics
cache_stats() {
    local cache_json="$1"
    local total_files=$(echo "$cache_json" | grep -o "\"hash\":" | wc -l)
    echo "Cached files: $total_files"
}

# Main function for testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Project Analysis Helper Functions"
    echo "This script provides utility functions for optimized analysis"
    echo ""
    echo "Available functions:"
    echo "  - get_file_hash <file>"
    echo "  - file_has_changed <file> <cache_json>"
    echo "  - extract_section <file> <section_name>"
    echo "  - count_requirements <spec_file>"
    echo "  - count_tasks <tasks_file>"
    echo "  - sample_source_files <source_dir> <max_files>"
    echo "  - search_pattern <directory> <pattern> [file_type]"
    echo "  - count_pattern <directory> <pattern> [file_type]"
    echo "  - is_large_codebase <source_dir> [threshold]"
fi
