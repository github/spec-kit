#!/usr/bin/env bash

# Project Catalog Script (Bash) - Phase 5
# Generate unified project catalog

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

REPO_ROOT=$(get_repo_root) || die "Not in a git repository"
SPECKIT_DIR="$REPO_ROOT/.speckit"
SPECS_DIR="$REPO_ROOT/specs"
CONFIG_FILE="$SPECKIT_DIR/config.json"
CACHE_DIR="$SPECKIT_DIR/cache"
CATALOG_CACHE="$CACHE_DIR/catalog.json"

FLAG_OUTPUT="docs/PROJECT-CATALOG.md"
FLAG_INCLUDE_APIS=true
FLAG_INCLUDE_DEPS=true
FLAG_JSON=false
FLAG_FORCE=false

show_help() {
    cat <<EOF
Usage: project-catalog.sh [OPTIONS]

Generate unified project catalog with cross-project search and API indexing.

OPTIONS:
  --output=<file>          Output file (default: docs/PROJECT-CATALOG.md)
  --no-apis                Exclude API endpoint index
  --no-dependencies        Exclude dependency analysis
  --json                   Output JSON format
  --force                  Force regeneration (ignore cache)
  --help, -h               Show this help message

EXAMPLES:
  # Generate default catalog
  ./project-catalog.sh

  # Custom output location
  ./project-catalog.sh --output=catalog.md

  # Minimal catalog (save tokens)
  ./project-catalog.sh --no-apis --no-dependencies

  # JSON output
  ./project-catalog.sh --json

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --output=*) FLAG_OUTPUT="${1#*=}"; shift ;;
        --no-apis) FLAG_INCLUDE_APIS=false; shift ;;
        --no-dependencies) FLAG_INCLUDE_DEPS=false; shift ;;
        --json) FLAG_JSON=true; shift ;;
        --force) FLAG_FORCE=true; shift ;;
        --help|-h) show_help ;;
        *) die "Unknown option: $1" ;;
    esac
done

get_api_endpoints() {
    local projects="$1"

    local -a endpoints=()

    while IFS= read -r project; do
        if [[ -z "$project" ]]; then continue; fi

        local project_id
        project_id=$(echo "$project" | jq -r '.id')

        local api_spec="$SPECS_DIR/projects/$project_id/001-existing-code/api-spec.md"

        if [[ ! -f "$api_spec" ]]; then
            continue
        fi

        # Extract endpoints: ### METHOD /path
        local matches
        matches=$(grep -E "^### (GET|POST|PUT|DELETE|PATCH) " "$api_spec" 2>/dev/null || true)

        while IFS= read -r match; do
            if [[ -z "$match" ]]; then continue; fi

            local method path
            method=$(echo "$match" | awk '{print $2}')
            path=$(echo "$match" | awk '{print $3}')

            endpoints+=("$project_id|$method|$path")
        done <<< "$matches"
    done <<< "$projects"

    printf '%s\n' "${endpoints[@]}"
}

generate_markdown_catalog() {
    local projects="$1"
    local project_count="$2"
    local api_count="$3"

    cat <<EOHEADER
# Project Catalog

**Generated:** $(get_timestamp)
**Total Projects:** $project_count
**API Endpoints:** $api_count

---

## Quick Navigation

| Project | Type | Technology | Status | Spec Dir |
|---------|------|------------|--------|----------|
EOHEADER

    while IFS= read -r project; do
        if [[ -z "$project" ]]; then continue; fi

        local id name path type tech status
        id=$(echo "$project" | jq -r '.id')
        name=$(echo "$project" | jq -r '.name')
        path=$(echo "$project" | jq -r '.path')
        type=$(echo "$project" | jq -r '.type // "unknown"')
        tech=$(echo "$project" | jq -r '.technology // "unknown"')
        status=$(echo "$project" | jq -r '.status // "onboarded"')

        echo "| [$name](specs/projects/$id) | $type | $tech | $status | \`specs/projects/$id\` |"
    done <<< "$projects"

    cat <<EOSECTION

---

## Technology Matrix

### Languages

EOSECTION

    # Group by technology
    local techs
    techs=$(echo "$projects" | jq -r '.technology // "unknown"' | sort | uniq -c | sort -rn)

    while IFS= read -r line; do
        if [[ -z "$line" ]]; then continue; fi

        local count tech
        count=$(echo "$line" | awk '{print $1}')
        tech=$(echo "$line" | awk '{print $2}')

        echo "- **$tech** ($count projects)"
    done <<< "$techs"

    if [[ "$FLAG_INCLUDE_APIS" == "true" ]]; then
        cat <<EOAPISECTION

---

## API Endpoint Index

EOAPISECTION

        local endpoints
        endpoints=$(get_api_endpoints "$projects")

        if [[ -n "$endpoints" ]]; then
            local current_project=""

            while IFS='|' read -r project_id method path; do
                if [[ -z "$project_id" ]]; then continue; fi

                if [[ "$project_id" != "$current_project" ]]; then
                    if [[ -n "$current_project" ]]; then
                        echo ""
                    fi
                    echo "### $project_id"
                    echo ""
                    current_project="$project_id"
                fi

                echo "- **$method** \`$path\`"
            done <<< "$endpoints"
        else
            echo "No API endpoints found. Run reverse-engineer.sh first."
        fi
    fi

    cat <<EOFOOTER

---

## Search & Navigation

Use \`/speckit.find\` to search across projects:

\`\`\`bash
# Find API endpoints
/speckit.find --api "users"

# Find by technology
/speckit.find --tech nodejs

# Find by project
/speckit.find --project api
\`\`\`

---

_Generated by Spec-Kit Phase 5: Integration & Catalog_
EOFOOTER
}

generate_json_catalog() {
    local projects="$1"
    local project_count="$2"

    local projects_array
    projects_array=$(echo "$projects" | jq -s .)

    local endpoints_array="[]"
    if [[ "$FLAG_INCLUDE_APIS" == "true" ]]; then
        local endpoints
        endpoints=$(get_api_endpoints "$projects")

        if [[ -n "$endpoints" ]]; then
            endpoints_array=$(while IFS='|' read -r project_id method path; do
                jq -n --arg pid "$project_id" --arg m "$method" --arg p "$path" \
                    '{project_id: $pid, method: $m, path: $p}'
            done <<< "$endpoints" | jq -s .)
        fi
    fi

    jq -n \
        --arg ts "$(get_iso_timestamp)" \
        --argjson pc "$project_count" \
        --argjson projects "$projects_array" \
        --argjson endpoints "$endpoints_array" \
        '{
            generated_at: $ts,
            total_projects: $pc,
            total_apis: ($endpoints | length),
            projects: $projects,
            api_index: $endpoints
        }'
}

main() {
    write_header "================================"
    write_header " Spec-Kit: Project Catalog (Phase 5)"
    write_header "================================"

    write_step_header "Step 1: Loading spec-kit configuration..."

    if [[ ! -f "$CONFIG_FILE" ]]; then
        die "Spec-kit not initialized. Run onboard.sh first"
    fi

    local projects
    projects=$(jq -r '.projects[]' "$CONFIG_FILE")
    local project_count
    project_count=$(echo "$projects" | jq -s 'length')
    write_success "Loaded $project_count projects"

    write_step_header "Step 2: Indexing API endpoints..."
    local endpoints
    endpoints=$(get_api_endpoints "$projects")
    local api_count
    api_count=$(echo "$endpoints" | wc -l | tr -d ' ')
    write_success "Indexed $api_count API endpoints"

    write_step_header "Step 3: Generating catalog..."

    if [[ "$FLAG_JSON" == "true" ]]; then
        generate_json_catalog "$projects" "$project_count"
        write_success "Generated JSON catalog"
    else
        local catalog
        catalog=$(generate_markdown_catalog "$projects" "$project_count" "$api_count")

        ensure_dir "$(dirname "$FLAG_OUTPUT")"
        echo "$catalog" > "$FLAG_OUTPUT"

        write_success "Catalog saved to: $FLAG_OUTPUT"

        local token_estimate
        token_estimate=$(($(echo "$catalog" | wc -c | tr -d ' ') / 4))

        if [[ $token_estimate -lt 1000 ]]; then
            write_success "Token estimate: ~$token_estimate tokens ✓ Optimized"
        else
            write_warning "Token estimate: ~$token_estimate tokens (consider --no-apis or --no-dependencies)"
        fi
    fi

    write_header "================================"
    write_header " Catalog Complete!"
    write_header "================================"

    write_progress "Projects: $project_count"
    write_progress "API Endpoints: $api_count"

    if [[ "$FLAG_JSON" == "false" ]]; then
        write_progress "Output: $FLAG_OUTPUT"
    fi
}

main
