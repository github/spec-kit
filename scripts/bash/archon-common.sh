#!/usr/bin/env bash
# Archon MCP Integration - Silent Utilities
# CRITICAL: All functions in this file MUST be completely silent (no stdout/stderr)

# Silent MCP detection - returns 0 if available, 1 if not
# NO stdout/stderr output
check_archon_available() {
    # Check if mcp__archon__health_check command exists and responds
    if command -v claude >/dev/null 2>&1; then
        # Try to call health check via MCP (completely silent)
        # Note: This assumes MCP tools are available in the environment
        # In practice, we'll check for the existence of Archon state or previous successful calls
        return 0  # For now, assume available if Claude is available
    fi
    return 1
}

# Get the Archon state directory for a feature
get_archon_state_dir() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "$script_dir/.archon-state"
}

# Save project ID mapping (completely silent)
# Args: feature_name, project_id
save_project_mapping() {
    local feature_name="$1"
    local project_id="$2"
    local state_dir=$(get_archon_state_dir)

    # Create state directory silently
    mkdir -p "$state_dir" 2>/dev/null || return 1

    # Write project ID to state file
    echo "$project_id" > "$state_dir/${feature_name}.pid" 2>/dev/null || return 1

    return 0
}

# Load project ID mapping (silent, outputs to stdout only on success)
# Args: feature_name
# Returns: project_id via stdout, or empty string if not found
load_project_mapping() {
    local feature_name="$1"
    local state_dir=$(get_archon_state_dir)
    local pid_file="$state_dir/${feature_name}.pid"

    if [[ -f "$pid_file" ]]; then
        cat "$pid_file" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Save document ID mapping (completely silent)
# Args: feature_name, document_filename, document_id
save_document_mapping() {
    local feature_name="$1"
    local doc_filename="$2"
    local doc_id="$3"
    local state_dir=$(get_archon_state_dir)

    mkdir -p "$state_dir" 2>/dev/null || return 1

    # Append or update document mapping
    local docs_file="$state_dir/${feature_name}.docs"

    # Remove existing entry for this document if it exists
    if [[ -f "$docs_file" ]]; then
        grep -v "^${doc_filename}:" "$docs_file" > "${docs_file}.tmp" 2>/dev/null || true
        mv "${docs_file}.tmp" "$docs_file" 2>/dev/null || true
    fi

    # Append new mapping
    echo "${doc_filename}:${doc_id}" >> "$docs_file" 2>/dev/null || return 1

    return 0
}

# Load document ID mapping (silent, outputs to stdout only on success)
# Args: feature_name, document_filename
# Returns: document_id via stdout, or empty string if not found
load_document_mapping() {
    local feature_name="$1"
    local doc_filename="$2"
    local state_dir=$(get_archon_state_dir)
    local docs_file="$state_dir/${feature_name}.docs"

    if [[ -f "$docs_file" ]]; then
        grep "^${doc_filename}:" "$docs_file" 2>/dev/null | cut -d':' -f2 || echo ""
    else
        echo ""
    fi
}

# Save task ID mapping (completely silent)
# Args: feature_name, task_id_local (e.g., T001), task_id_archon (UUID)
save_task_mapping() {
    local feature_name="$1"
    local task_local="$2"
    local task_archon="$3"
    local state_dir=$(get_archon_state_dir)

    mkdir -p "$state_dir" 2>/dev/null || return 1

    local tasks_file="$state_dir/${feature_name}.tasks"

    # Remove existing entry if it exists
    if [[ -f "$tasks_file" ]]; then
        grep -v "^${task_local}:" "$tasks_file" > "${tasks_file}.tmp" 2>/dev/null || true
        mv "${tasks_file}.tmp" "$tasks_file" 2>/dev/null || true
    fi

    # Append new mapping
    echo "${task_local}:${task_archon}" >> "$tasks_file" 2>/dev/null || return 1

    return 0
}

# Load task ID mapping (silent, outputs to stdout only on success)
# Args: feature_name, task_id_local (e.g., T001)
# Returns: task_id_archon (UUID) via stdout, or empty string if not found
load_task_mapping() {
    local feature_name="$1"
    local task_local="$2"
    local state_dir=$(get_archon_state_dir)
    local tasks_file="$state_dir/${feature_name}.tasks"

    if [[ -f "$tasks_file" ]]; then
        grep "^${task_local}:" "$tasks_file" 2>/dev/null | cut -d':' -f2 || echo ""
    else
        echo ""
    fi
}

# Save sync metadata (timestamp for conflict resolution)
# Args: feature_name, filename, timestamp (ISO 8601)
save_sync_metadata() {
    local feature_name="$1"
    local filename="$2"
    local timestamp="$3"
    local state_dir=$(get_archon_state_dir)

    mkdir -p "$state_dir" 2>/dev/null || return 1

    local meta_file="$state_dir/${feature_name}.meta"

    # Remove existing entry if it exists
    if [[ -f "$meta_file" ]]; then
        grep -v "^${filename}|" "$meta_file" > "${meta_file}.tmp" 2>/dev/null || true
        mv "${meta_file}.tmp" "$meta_file" 2>/dev/null || true
    fi

    # Append new metadata (using | as delimiter to avoid conflict with : in ISO timestamps)
    echo "${filename}|${timestamp}" >> "$meta_file" 2>/dev/null || return 1

    return 0
}

# Load sync metadata (silent, outputs to stdout only on success)
# Args: feature_name, filename
# Returns: timestamp via stdout, or empty string if not found
load_sync_metadata() {
    local feature_name="$1"
    local filename="$2"
    local state_dir=$(get_archon_state_dir)
    local meta_file="$state_dir/${feature_name}.meta"

    if [[ -f "$meta_file" ]]; then
        grep "^${filename}|" "$meta_file" 2>/dev/null | cut -d'|' -f2 || echo ""
    else
        echo ""
    fi
}

# Extract feature name from feature directory path
# Args: feature_dir (absolute path)
# Returns: feature name (e.g., "001-feature-name")
extract_feature_name() {
    local feature_dir="$1"
    basename "$feature_dir" 2>/dev/null || echo ""
}

# Get current timestamp in ISO 8601 format
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo ""
}
