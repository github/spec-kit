#!/usr/bin/env bash

# Reverse Engineer Script (Bash) - Phase 4
# Extract APIs and models from existing code

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

REPO_ROOT=$(get_repo_root) || die "Not in a git repository"
SPECKIT_DIR="$REPO_ROOT/.speckit"
SPECS_DIR="$REPO_ROOT/specs"
CONFIG_FILE="$SPECKIT_DIR/config.json"

FLAG_PROJECT=""
FLAG_ALL=false
FLAG_APIS=true
FLAG_MODELS=true
FLAG_MAX_ENDPOINTS=50
FLAG_MAX_MODELS=20
FLAG_FORCE=false
FLAG_DRY_RUN=false

show_help() {
    cat <<EOF
Usage: reverse-engineer.sh [OPTIONS]

Extract APIs and data models from existing code.

OPTIONS:
  --project=<id>           Reverse engineer specific project
  --all                    Reverse engineer all projects
  --apis                   Extract API endpoints (default: true)
  --models                 Extract data models (default: true)
  --max-endpoints=<n>      Maximum endpoints (default: 50)
  --max-models=<n>         Maximum models (default: 20)
  --force                  Force regeneration
  --dry-run                Show what would happen
  --help, -h               Show this help message

EXAMPLES:
  # Reverse engineer specific project
  ./reverse-engineer.sh --project=api

  # All projects
  ./reverse-engineer.sh --all

  # APIs only
  ./reverse-engineer.sh --all --apis --no-models

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --project=*) FLAG_PROJECT="${1#*=}"; shift ;;
        --all) FLAG_ALL=true; shift ;;
        --apis) FLAG_APIS=true; shift ;;
        --models) FLAG_MODELS=true; shift ;;
        --no-apis) FLAG_APIS=false; shift ;;
        --no-models) FLAG_MODELS=false; shift ;;
        --max-endpoints=*) FLAG_MAX_ENDPOINTS="${1#*=}"; shift ;;
        --max-models=*) FLAG_MAX_MODELS="${1#*=}"; shift ;;
        --force) FLAG_FORCE=true; shift ;;
        --dry-run) FLAG_DRY_RUN=true; shift ;;
        --help|-h) show_help ;;
        *) die "Unknown option: $1" ;;
    esac
done

find_express_endpoints() {
    local project_path="$1"
    local max_endpoints="$2"

    local -a endpoints=()

    # Pattern: app.get('/path', ...) or router.post('/path', ...)
    local files
    files=$(find "$project_path" -type f \( -name "*.js" -o -name "*.ts" \) 2>/dev/null || true)

    while IFS= read -r file; do
        if [[ -z "$file" ]]; then continue; fi

        # Extract HTTP method and path
        local matches
        matches=$(grep -E "(app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]" "$file" 2>/dev/null || true)

        while IFS= read -r match; do
            if [[ -z "$match" ]]; then continue; fi

            local method path
            method=$(echo "$match" | sed -E 's/.*\.(get|post|put|delete|patch).*/\U\1/')
            path=$(echo "$match" | sed -E "s/.*['\"]([^'\"]+)['\"].*/\1/")

            endpoints+=("$method|$path|$file")

            if [[ ${#endpoints[@]} -ge $max_endpoints ]]; then
                break 2
            fi
        done <<< "$matches"
    done <<< "$files"

    printf '%s\n' "${endpoints[@]}"
}

find_fastapi_endpoints() {
    local project_path="$1"
    local max_endpoints="$2"

    local -a endpoints=()

    local files
    files=$(find "$project_path" -type f -name "*.py" 2>/dev/null || true)

    while IFS= read -r file; do
        if [[ -z "$file" ]]; then continue; fi

        local matches
        matches=$(grep -E "@(app|router)\.(get|post|put|delete|patch)\s*\(" "$file" 2>/dev/null || true)

        while IFS= read -r match; do
            if [[ -z "$match" ]]; then continue; fi

            local method path
            method=$(echo "$match" | sed -E 's/.*@.*\.(get|post|put|delete|patch).*/\U\1/')
            path=$(echo "$match" | sed -E "s/.*['\"]([^'\"]+)['\"].*/\1/")

            endpoints+=("$method|$path|$file")

            if [[ ${#endpoints[@]} -ge $max_endpoints ]]; then
                break 2
            fi
        done <<< "$matches"
    done <<< "$files"

    printf '%s\n' "${endpoints[@]}"
}

find_gin_endpoints() {
    local project_path="$1"
    local max_endpoints="$2"

    local -a endpoints=()

    local files
    files=$(find "$project_path" -type f -name "*.go" 2>/dev/null || true)

    while IFS= read -r file; do
        if [[ -z "$file" ]]; then continue; fi

        local matches
        matches=$(grep -E "\.(GET|POST|PUT|DELETE|PATCH)\s*\(" "$file" 2>/dev/null || true)

        while IFS= read -r match; do
            if [[ -z "$match" ]]; then continue; fi

            local method path
            method=$(echo "$match" | sed -E 's/.*\.(GET|POST|PUT|DELETE|PATCH).*/\1/')
            path=$(echo "$match" | sed -E "s/.*['\"]([^'\"]+)['\"].*/\1/")

            endpoints+=("$method|$path|$file")

            if [[ ${#endpoints[@]} -ge $max_endpoints ]]; then
                break 2
            fi
        done <<< "$matches"
    done <<< "$files"

    printf '%s\n' "${endpoints[@]}"
}

generate_api_spec() {
    local project_id="$1"
    local project_path="$2"
    local framework="$3"
    local endpoints="$4"

    local output_file="$SPECS_DIR/projects/$project_id/001-existing-code/api-spec.md"

    if [[ "$FLAG_DRY_RUN" == "true" ]]; then
        write_info "[DRY RUN] Would generate: $output_file"
        return
    fi

    ensure_dir "$(dirname "$output_file")"

    cat > "$output_file" <<EOAPI
# API Specification (Reverse Engineered)

**Project:** $project_id
**Framework:** $framework
**Generated:** $(get_timestamp)
**Confidence:** MEDIUM (extracted from code patterns)

---

## Endpoints

EOAPI

    while IFS='|' read -r method path file; do
        if [[ -z "$method" ]]; then continue; fi

        cat >> "$output_file" <<EOEP

### $method $path

**Source:** \`$file\`
**Confidence:** MEDIUM

EOEP
    done <<< "$endpoints"

    cat >> "$output_file" <<EOFOOTER

---

**Note:** This specification was automatically extracted from existing code.
Review and verify all endpoints before relying on this documentation.
EOFOOTER

    write_success "  Generated: $output_file"
}

reverse_engineer_project() {
    local project_json="$1"

    local project_id project_name project_path technology framework

    project_id=$(echo "$project_json" | jq -r '.id')
    project_name=$(echo "$project_json" | jq -r '.name')
    project_path=$(echo "$project_json" | jq -r '.path')
    technology=$(echo "$project_json" | jq -r '.technology // "unknown"')
    framework=$(echo "$project_json" | jq -r '.framework // "Unknown"')

    write_progress "Reverse Engineering: $project_name"
    write_info "  Framework: $framework"

    local full_path="$REPO_ROOT/$project_path"

    if [[ ! -d "$full_path" ]]; then
        write_warning "  Project path not found: $full_path"
        return
    fi

    # Extract APIs
    if [[ "$FLAG_APIS" == "true" ]]; then
        write_info "  Extracting API endpoints..."

        local endpoints=""
        case "$framework" in
            Express|Next.js)
                endpoints=$(find_express_endpoints "$full_path" "$FLAG_MAX_ENDPOINTS")
                ;;
            FastAPI|Flask|Django)
                endpoints=$(find_fastapi_endpoints "$full_path" "$FLAG_MAX_ENDPOINTS")
                ;;
            Gin|Fiber|Echo)
                endpoints=$(find_gin_endpoints "$full_path" "$FLAG_MAX_ENDPOINTS")
                ;;
        esac

        if [[ -n "$endpoints" ]]; then
            local count
            count=$(echo "$endpoints" | wc -l | tr -d ' ')
            write_info "  Found $count endpoints"
            generate_api_spec "$project_id" "$project_path" "$framework" "$endpoints"
        else
            write_warning "  No endpoints found"
        fi
    fi

    write_success "  ✓ Reverse engineering complete"
}

main() {
    write_header "================================"
    write_header " Spec-Kit: Reverse Engineering (Phase 4)"
    write_header "================================"

    if [[ "$FLAG_ALL" == "false" ]] && [[ -z "$FLAG_PROJECT" ]]; then
        die "Must specify --all or --project=<id>"
    fi

    if [[ ! -f "$CONFIG_FILE" ]]; then
        die "Spec-kit not initialized. Run onboard.sh first"
    fi

    local projects
    projects=$(jq -r '.projects[]' "$CONFIG_FILE")

    write_step_header "Reverse engineering projects..."

    while IFS= read -r project; do
        if [[ -z "$project" ]]; then continue; fi

        local project_id
        project_id=$(echo "$project" | jq -r '.id')

        if [[ "$FLAG_ALL" == "false" ]] && [[ "$project_id" != "$FLAG_PROJECT" ]]; then
            continue
        fi

        reverse_engineer_project "$project"
    done <<< "$projects"

    write_header "================================"
    write_header " Reverse Engineering Complete!"
    write_header "================================"
}

main
