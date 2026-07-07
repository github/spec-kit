#!/usr/bin/env bash
# AI Team extension: shared helpers for handoff spec sync.

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.specify" ]] || [[ -d "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

handoff_spec_repo_root() {
    _find_project_root "$SCRIPT_DIR" || pwd
}

handoff_spec_load_core() {
    local repo_root="$1"
    # shellcheck source=/dev/null
    source "$repo_root/.specify/scripts/bash/common.sh"
}

resolve_effective_spec() {
    local feature_dir="$1"
    local override_file="${2:-spec.override.md}"
    local override="$feature_dir/$override_file"
    if [[ -f "$override" ]]; then
        echo "$override"
    else
        echo "$feature_dir/spec.md"
    fi
}

_override_file_name() {
    local repo_root="$1"
    local config="$repo_root/.specify/extensions/ai-team/ai-team-config.yml"
    local name="spec.override.md"
    if [[ -f "$config" ]]; then
        local parsed
        parsed=$(grep -E 'private_handoff_override_file:' "$config" 2>/dev/null | head -1 | sed 's/.*private_handoff_override_file:[[:space:]]*//' | tr -d ' "\r' || true)
        [[ -n "$parsed" ]] && name="$parsed"
    fi
    echo "$name"
}

_extract_https_url() {
    local raw="$1"
    local url=""
    if [[ "$raw" =~ (https://[^[:space:]\"\'\>]+) ]]; then
        url="${BASH_REMATCH[1]}"
        url="${url%/}"
    fi
    [[ "$url" == https://* ]] && echo "$url"
}

_parse_url_from_text() {
    local text="$1"
    local key value url
    for key in handoff_requirement_url published_requirement_url; do
        if [[ "$text" =~ ${key}[[:space:]]*=[[:space:]]*(https://[^[:space:]\"\'\>]+) ]]; then
            url="${BASH_REMATCH[1]}"
            url="${url%/}"
            echo "$url"
            return 0
        fi
    done
    while IFS= read -r line; do
        for key in handoff_requirement_url published_requirement_url; do
            if [[ "$line" =~ ^[[:space:]]*${key}:[[:space:]]*(https://[^[:space:]\"\'\#]+) ]]; then
                url="${BASH_REMATCH[1]}"
                url="${url%/}"
                echo "$url"
                return 0
            fi
        done
    done <<< "$text"
    return 1
}

_read_url_from_spec_frontmatter() {
    local spec_file="$1"
    [[ -f "$spec_file" ]] || return 1
    _parse_url_from_text "$(head -40 "$spec_file")"
}

_read_url_from_task_context() {
    local repo_root="$1"
    local args_text="${2:-}"
    local task_id="" tasks_root="$repo_root/.specify/ai-team/tasks"
    if [[ "$args_text" =~ task_id=([^[:space:]\"\'\>]+) ]]; then
        task_id="${BASH_REMATCH[1]}"
    fi
    if [[ -n "$task_id" && -f "$tasks_root/$task_id/task-context.yml" ]]; then
        _parse_url_from_text "$(cat "$tasks_root/$task_id/task-context.yml")" && return 0
    fi
    if [[ -d "$tasks_root" ]]; then
        local ctx url
        for ctx in "$tasks_root"/*/task-context.yml; do
            [[ -f "$ctx" ]] || continue
            if url=$(_parse_url_from_text "$(cat "$ctx")"); then
                echo "$url"
                return 0
            fi
        done
    fi
    return 1
}

resolve_handoff_requirement_url() {
    local repo_root="$1"
    local args_text="${2:-}"
    local url=""

    url=$(_extract_https_url "${HANDOFF_REQUIREMENT_URL:-}") && { echo "$url"; return 0; }
    url=$(_extract_https_url "${PUBLISHED_REQUIREMENT_URL:-}") && { echo "$url"; return 0; }
    url=$(_parse_url_from_text "$args_text") && { echo "$url"; return 0; }
    url=$(_read_url_from_task_context "$repo_root" "$args_text") && { echo "$url"; return 0; }

    local feature_dir spec_file
    handoff_spec_load_core
    if _paths_output=$(get_feature_paths --no-persist 2>/dev/null); then
        eval "$_paths_output"
        spec_file="$FEATURE_SPEC"
        url=$(_read_url_from_spec_frontmatter "$spec_file") && { echo "$url"; return 0; }
    fi
    return 1
}

ensure_gitignore_pattern() {
    local repo_root="$1"
    local pattern="${2:-**/spec.override.md}"
    local gitignore="$repo_root/.gitignore"
    if [[ -f "$gitignore" ]] && grep -qxF "$pattern" "$gitignore" 2>/dev/null; then
        return 0
    fi
    {
        echo ""
        echo "# Spec Kit AI Team remote handoff cache (auto-generated)"
        echo "$pattern"
    } >> "$gitignore"
}

spec_is_pointer_only() {
    local spec_file="$1"
    [[ -f "$spec_file" ]] || return 1
    if grep -q '^spec_source:[[:space:]]*remote' "$spec_file" 2>/dev/null; then
        return 0
    fi
    if grep -q 'Remote Reference' "$spec_file" 2>/dev/null; then
        return 0
    fi
    return 1
}

write_spec_pointer() {
    local spec_file="$1"
    local url="$2"
    mkdir -p "$(dirname "$spec_file")"
    cat > "$spec_file" <<EOF
---
handoff_requirement_url: $url
spec_source: remote
---

# Feature Specification (Remote Reference)

**Handoff Requirement URL**: $url

**Local cache**: \`spec.override.md\` (gitignored, generated by \`speckit.ai-team.handoff-spec-sync\`)

> Do not edit this file for full requirement content. Re-run handoff sync or update the remote source.
EOF
}

fetch_remote_requirement() {
    local url="$1"
    local dest="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$dest"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$dest" "$url"
    else
        echo "ERROR: curl or wget required to fetch handoff requirement URL" >&2
        return 1
    fi
}

write_merged_override() {
    local override_file="$1"
    local url="$2"
    local spec_file="$3"
    local fetched_file="$4"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    {
        echo "# Effective Feature Specification (AI Team Handoff)"
        echo ""
        echo "**Source URL**: $url"
        echo "**Generated**: $timestamp"
        echo "**Public baseline**: \`spec.md\` (preserved unchanged)"
        echo ""
        echo "---"
        echo ""
    } > "$override_file"

    if [[ -f "$spec_file" ]] && ! spec_is_pointer_only "$spec_file"; then
        {
            echo "## Public baseline (from spec.md)"
            echo ""
            cat "$spec_file"
            echo ""
            echo "---"
            echo ""
            echo "## Handoff requirement (fetched)"
            echo ""
            cat "$fetched_file"
        } >> "$override_file"
    else
        {
            echo "## Handoff requirement (fetched)"
            echo ""
            cat "$fetched_file"
        } >> "$override_file"
    fi
}

emit_handoff_json() {
    local skipped="$1"
    local feature_dir="$2"
    local feature_spec="$3"
    local effective_spec="$4"
    local url="${5:-}"
    local bootstrapped="${6:-false}"

    if has_jq; then
        jq -cn \
            --argjson skipped "$skipped" \
            --arg feature_dir "$feature_dir" \
            --arg feature_spec "$feature_spec" \
            --arg effective_spec "$effective_spec" \
            --arg handoff_url "$url" \
            --argjson spec_bootstrapped "$bootstrapped" \
            '{SKIPPED:$skipped,FEATURE_DIR:$feature_dir,FEATURE_SPEC:$feature_spec,EFFECTIVE_SPEC:$effective_spec,HANDOFF_REQUIREMENT_URL:$handoff_url,SPEC_BOOTSTRAPPED:$spec_bootstrapped}'
    else
        printf '{"SKIPPED":%s,"FEATURE_DIR":"%s","FEATURE_SPEC":"%s","EFFECTIVE_SPEC":"%s","HANDOFF_REQUIREMENT_URL":"%s","SPEC_BOOTSTRAPPED":%s}\n' \
            "$skipped" \
            "$(json_escape "$feature_dir")" \
            "$(json_escape "$feature_spec")" \
            "$(json_escape "$effective_spec")" \
            "$(json_escape "$url")" \
            "$bootstrapped"
    fi
}
