#!/usr/bin/env bash

# Consolidated prerequisite checking script
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --require-tasks     Require tasks.md to exist (for implementation phase)
#   --include-tasks     Include tasks.md in AVAILABLE_DOCS list
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...", "FEATURE_SPEC_TTL":"...", "IMPL_PLAN_TTL":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: FEATURE_DIR:... \n TTL_SOURCES: ... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... \n TTL paths ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            ;;
        --include-tasks)
            INCLUDE_TASKS=true
            ;;
        --paths-only)
            PATHS_ONLY=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: check-prerequisites.sh [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for implementation phase)
  --include-tasks     Include tasks.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  ./check-prerequisites.sh --json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  ./check-prerequisites.sh --json --require-tasks --include-tasks
  
  # Get feature paths only (no validation)
  ./check-prerequisites.sh --paths-only
  
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths and validate branch
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # Minimal JSON paths payload (no validation performed) - RDF-first architecture
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","FEATURE_DIR":"%s","FEATURE_SPEC_TTL":"%s","IMPL_PLAN_TTL":"%s","TASKS_TTL":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s","ONTOLOGY_DIR":"%s","GENERATED_DIR":"%s","GGEN_CONFIG":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$FEATURE_DIR" "$FEATURE_SPEC_TTL" "$IMPL_PLAN_TTL" "$TASKS_TTL" "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS" "$ONTOLOGY_DIR" "$GENERATED_DIR" "$GGEN_CONFIG"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "FEATURE_DIR: $FEATURE_DIR"
        echo ""
        echo "# RDF-First Architecture: TTL sources (source of truth)"
        echo "FEATURE_SPEC_TTL: $FEATURE_SPEC_TTL"
        echo "IMPL_PLAN_TTL: $IMPL_PLAN_TTL"
        echo "TASKS_TTL: $TASKS_TTL"
        echo ""
        echo "# Generated artifacts (NEVER edit manually)"
        echo "FEATURE_SPEC: $FEATURE_SPEC"
        echo "IMPL_PLAN: $IMPL_PLAN"
        echo "TASKS: $TASKS"
        echo ""
        echo "# RDF infrastructure"
        echo "ONTOLOGY_DIR: $ONTOLOGY_DIR"
        echo "GENERATED_DIR: $GENERATED_DIR"
        echo "GGEN_CONFIG: $GGEN_CONFIG"
    fi
    exit 0
fi

# Validate required directories and files
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /speckit.specify first to create the feature structure." >&2
    exit 1
fi

# RDF-First Architecture: Check for TTL sources first, fall back to legacy MD
# Detect feature format (RDF-first vs. legacy)
IS_RDF_FEATURE=false
if [[ -d "$ONTOLOGY_DIR" ]] && [[ -f "$GGEN_CONFIG" ]]; then
    IS_RDF_FEATURE=true
fi

if $IS_RDF_FEATURE; then
    # RDF-first feature: Validate TTL sources
    if [[ ! -f "$IMPL_PLAN_TTL" ]] && [[ ! -f "$IMPL_PLAN_LEGACY" ]]; then
        echo "ERROR: plan.ttl not found in $ONTOLOGY_DIR (and no legacy plan.md)" >&2
        echo "Run /speckit.plan first to create the implementation plan." >&2
        exit 1
    fi

    # Check for tasks.ttl if required
    if $REQUIRE_TASKS && [[ ! -f "$TASKS_TTL" ]] && [[ ! -f "$TASKS_LEGACY" ]]; then
        echo "ERROR: tasks.ttl not found in $ONTOLOGY_DIR (and no legacy tasks.md)" >&2
        echo "Run /speckit.tasks first to create the task list." >&2
        exit 1
    fi
else
    # Legacy feature: Check for MD files
    if [[ ! -f "$IMPL_PLAN_LEGACY" ]]; then
        echo "ERROR: plan.md not found in $FEATURE_DIR" >&2
        echo "Run /speckit.plan first to create the implementation plan." >&2
        exit 1
    fi

    # Check for tasks.md if required
    if $REQUIRE_TASKS && [[ ! -f "$TASKS_LEGACY" ]]; then
        echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
        echo "Run /speckit.tasks first to create the task list." >&2
        exit 1
    fi
fi

# Build list of available documents (both TTL sources and MD artifacts)
docs=()
ttl_sources=()

if $IS_RDF_FEATURE; then
    # RDF-first feature: List TTL sources and generated artifacts
    [[ -f "$FEATURE_SPEC_TTL" ]] && ttl_sources+=("ontology/feature-content.ttl")
    [[ -f "$IMPL_PLAN_TTL" ]] && ttl_sources+=("ontology/plan.ttl")
    [[ -f "$TASKS_TTL" ]] && ttl_sources+=("ontology/tasks.ttl")

    # Generated artifacts (for reference only)
    [[ -f "$FEATURE_SPEC" ]] && docs+=("generated/spec.md")
    [[ -f "$IMPL_PLAN" ]] && docs+=("generated/plan.md")
    [[ -f "$TASKS" ]] && docs+=("generated/tasks.md")
else
    # Legacy feature: List MD files as primary
    [[ -f "$FEATURE_SPEC_LEGACY" ]] && docs+=("spec.md")
    [[ -f "$IMPL_PLAN_LEGACY" ]] && docs+=("plan.md")
    if $INCLUDE_TASKS && [[ -f "$TASKS_LEGACY" ]]; then
        docs+=("tasks.md")
    fi
fi

# Always check these optional docs (same for RDF and legacy)
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")

# Check contracts directory (only if it exists and has files)
if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi

[[ -f "$QUICKSTART" ]] && docs+=("quickstart.md")

# Output results
if $JSON_MODE; then
    # Build JSON array of TTL sources
    if [[ ${#ttl_sources[@]} -eq 0 ]]; then
        json_ttl="[]"
    else
        json_ttl=$(printf '"%s",' "${ttl_sources[@]}")
        json_ttl="[${json_ttl%,}]"
    fi

    # Build JSON array of documents
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi

    # Output with RDF-first architecture fields
    printf '{"FEATURE_DIR":"%s","IS_RDF_FEATURE":%s,"TTL_SOURCES":%s,"AVAILABLE_DOCS":%s,"FEATURE_SPEC_TTL":"%s","IMPL_PLAN_TTL":"%s","TASKS_TTL":"%s","ONTOLOGY_DIR":"%s","GENERATED_DIR":"%s","GGEN_CONFIG":"%s"}\n' \
        "$FEATURE_DIR" "$IS_RDF_FEATURE" "$json_ttl" "$json_docs" "$FEATURE_SPEC_TTL" "$IMPL_PLAN_TTL" "$TASKS_TTL" "$ONTOLOGY_DIR" "$GENERATED_DIR" "$GGEN_CONFIG"
else
    # Text output
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo ""

    if $IS_RDF_FEATURE; then
        echo "# RDF-First Feature (source of truth: TTL files)"
        echo "TTL_SOURCES:"
        check_file "$FEATURE_SPEC_TTL" "  ontology/feature-content.ttl"
        check_file "$IMPL_PLAN_TTL" "  ontology/plan.ttl"
        check_file "$TASKS_TTL" "  ontology/tasks.ttl"
        echo ""
        echo "GENERATED_ARTIFACTS (NEVER edit manually):"
        check_file "$FEATURE_SPEC" "  generated/spec.md"
        check_file "$IMPL_PLAN" "  generated/plan.md"
        check_file "$TASKS" "  generated/tasks.md"
        echo ""
        echo "RDF_INFRASTRUCTURE:"
        check_dir "$ONTOLOGY_DIR" "  ontology/"
        check_dir "$GENERATED_DIR" "  generated/"
        check_file "$GGEN_CONFIG" "  ggen.toml"
        check_file "$SCHEMA_TTL" "  ontology/spec-kit-schema.ttl (symlink)"
        echo ""
    else
        echo "# Legacy Feature (source of truth: MD files)"
        echo "AVAILABLE_DOCS:"
        check_file "$FEATURE_SPEC_LEGACY" "  spec.md"
        check_file "$IMPL_PLAN_LEGACY" "  plan.md"
        if $INCLUDE_TASKS; then
            check_file "$TASKS_LEGACY" "  tasks.md"
        fi
        echo ""
    fi

    # Show status of optional documents (same for RDF and legacy)
    echo "OPTIONAL_DOCS:"
    check_file "$RESEARCH" "  research.md"
    check_file "$DATA_MODEL" "  data-model.md"
    check_dir "$CONTRACTS_DIR" "  contracts/"
    check_file "$QUICKSTART" "  quickstart.md"
fi
