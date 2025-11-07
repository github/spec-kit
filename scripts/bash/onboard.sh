#!/usr/bin/env bash

# Onboard Script (Bash) - Phase 3
# Non-invasive onboarding of discovered projects

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

REPO_ROOT=$(get_repo_root) || die "Not in a git repository"
SPECKIT_DIR="$REPO_ROOT/.speckit"
SPECS_DIR="$REPO_ROOT/specs"
CONFIG_FILE="$SPECKIT_DIR/config.json"
CACHE_DIR="$SPECKIT_DIR/cache"
DISCOVERY_CACHE="$CACHE_DIR/discovery.json"
METADATA_DIR="$SPECKIT_DIR/metadata"
TEMPLATES_DIR="$REPO_ROOT/templates"

FLAG_ALL=false
FLAG_PROJECTS=""
FLAG_FROM_DISCOVERY=false
FLAG_CONSTITUTION="universal"
FLAG_FORCE=false
FLAG_DRY_RUN=false
FLAG_JSON=false

show_help() {
    cat <<EOF
Usage: onboard.sh [OPTIONS]

Onboard discovered projects by creating parallel .speckit/ structure.

OPTIONS:
  --all                    Onboard all discovered projects
  --projects=<ids>         Onboard specific projects (comma-separated)
  --from-discovery         Use discovery cache
  --constitution=<type>    Constitution type (universal, microservices)
  --force                  Re-onboard already onboarded projects
  --dry-run                Show what would happen
  --json                   Output JSON format
  --help, -h               Show this help message

EXAMPLES:
  # Onboard all projects
  ./onboard.sh --all --from-discovery

  # Onboard specific projects
  ./onboard.sh --projects="api,frontend"

  # Microservices constitution
  ./onboard.sh --all --constitution=microservices

  # Dry run
  ./onboard.sh --all --dry-run

EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --all) FLAG_ALL=true; shift ;;
        --projects=*) FLAG_PROJECTS="${1#*=}"; shift ;;
        --from-discovery) FLAG_FROM_DISCOVERY=true; shift ;;
        --constitution=*) FLAG_CONSTITUTION="${1#*=}"; shift ;;
        --force) FLAG_FORCE=true; shift ;;
        --dry-run) FLAG_DRY_RUN=true; shift ;;
        --json) FLAG_JSON=true; shift ;;
        --help|-h) show_help ;;
        *) die "Unknown option: $1" ;;
    esac
done

initialize_speckit_structure() {
    write_step_header "Step 1: Initializing spec-kit structure..."

    for dir in "$SPECKIT_DIR" "$METADATA_DIR" "$CACHE_DIR" "$SPECS_DIR" "$SPECS_DIR/projects"; do
        if [[ "$FLAG_DRY_RUN" == "true" ]]; then
            write_info "[DRY RUN] Would create: $dir"
        else
            ensure_dir "$dir"
            write_success "Created: $dir"
        fi
    done
}

get_discovery_results() {
    if [[ ! -f "$DISCOVERY_CACHE" ]]; then
        die "Discovery cache not found. Run project-analysis.sh --discover first"
    fi

    if ! validate_json_file "$DISCOVERY_CACHE"; then
        die "Invalid discovery cache format"
    fi

    jq -r '.projects[]' "$DISCOVERY_CACHE"
}

get_speckit_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        cat "$CONFIG_FILE"
    else
        cat <<EOF
{
  "version": "1.0",
  "initialized_at": "$(get_iso_timestamp)",
  "repo_root": "$REPO_ROOT",
  "projects": [],
  "constitution": {
    "type": "$FLAG_CONSTITUTION",
    "path": "constitution.md"
  }
}
EOF
    fi
}

copy_constitution_template() {
    write_step_header "Step 4: Setting up constitution..."

    local source="$TEMPLATES_DIR/constitution-$FLAG_CONSTITUTION.md"
    local dest="$SPECS_DIR/constitution.md"

    if [[ ! -f "$source" ]]; then
        write_warning "Constitution template not found: $source"
        return
    fi

    if [[ "$FLAG_DRY_RUN" == "true" ]]; then
        write_info "[DRY RUN] Would copy: $source -> $dest"
    else
        cp "$source" "$dest"
        write_success "Created constitution: $dest ($FLAG_CONSTITUTION)"
    fi
}

onboard_project() {
    local project_json="$1"

    local project_id project_name project_path project_type

    project_id=$(echo "$project_json" | jq -r '.id')
    project_name=$(echo "$project_json" | jq -r '.name')
    project_path=$(echo "$project_json" | jq -r '.path')
    project_type=$(echo "$project_json" | jq -r '.type // "unknown"')

    write_progress "Onboarding: $project_name"
    write_info "  ID: $project_id"
    write_info "  Path: $project_path"
    write_info "  Type: $project_type"

    # Create spec directory
    local spec_dir="$SPECS_DIR/projects/$project_id"
    if [[ "$FLAG_DRY_RUN" == "true" ]]; then
        write_info "[DRY RUN] Would create: $spec_dir"
    else
        ensure_dir "$spec_dir"
    fi

    # Save metadata
    local metadata_file="$METADATA_DIR/$project_id.json"
    if [[ "$FLAG_DRY_RUN" == "true" ]]; then
        write_info "[DRY RUN] Would save: $metadata_file"
    else
        echo "$project_json" | jq '. + {"onboarded_at": "'$(get_iso_timestamp)'"}' > "$metadata_file"
    fi

    # Create README
    local readme_file="$spec_dir/README.md"
    if [[ "$FLAG_DRY_RUN" == "true" ]]; then
        write_info "[DRY RUN] Would create: $readme_file"
    else
        cat > "$readme_file" <<EOREADME
# $project_name

**Type:** $project_type
**Path:** \`$project_path\`
**Onboarded:** $(get_timestamp)

## Overview

This project was automatically onboarded by Spec-Kit.

## Getting Started

\`\`\`bash
cd $project_path
\`\`\`

## Specifications

- Add new feature specs in numbered directories (e.g., \`002-new-feature/\`)
- Use \`/speckit.reverse-engineer\` to extract existing APIs and models

## Links

- [Constitution](../../constitution.md)
- [Project Catalog](../../../docs/PROJECT-CATALOG.md)
EOREADME
    fi

    write_success "  ✓ Onboarded successfully"
}

main() {
    write_header "================================"
    write_header " Spec-Kit Onboarding (Phase 3)"
    write_header "================================"

    if [[ "$FLAG_ALL" == "false" ]] && [[ -z "$FLAG_PROJECTS" ]]; then
        die "Must specify --all or --projects=<ids>"
    fi

    initialize_speckit_structure

    write_step_header "Step 2: Loading discovery results..."
    local projects
    projects=$(get_discovery_results)
    local project_count
    project_count=$(echo "$projects" | jq -s 'length')
    write_success "Found $project_count projects"

    write_step_header "Step 3: Loading configuration..."
    local config
    config=$(get_speckit_config)

    copy_constitution_template

    write_step_header "Step 5: Onboarding projects..."

    local -a onboarded=()
    while IFS= read -r project; do
        local project_id
        project_id=$(echo "$project" | jq -r '.id')

        if [[ "$FLAG_ALL" == "false" ]] && ! echo "$FLAG_PROJECTS" | grep -q "$project_id"; then
            continue
        fi

        onboard_project "$project"
        onboarded+=("$project")
    done <<< "$projects"

    write_step_header "Step 6: Saving configuration..."

    if [[ "$FLAG_DRY_RUN" == "false" ]]; then
        local onboarded_json
        onboarded_json=$(printf '%s\n' "${onboarded[@]}" | jq -s .)

        echo "$config" | jq --argjson projects "$onboarded_json" '.projects = $projects' > "$CONFIG_FILE"
        write_success "Configuration saved: $CONFIG_FILE"
    fi

    write_header "================================"
    write_header " Onboarding Complete!"
    write_header "================================"

    write_progress "Total Onboarded: ${#onboarded[@]}"

    if [[ "$FLAG_JSON" == "true" ]]; then
        printf '%s\n' "${onboarded[@]}" | jq -s '{success: true, onboarded: length, projects: .}'
    fi
}

main
