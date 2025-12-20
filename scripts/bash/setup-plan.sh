#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --help|-h) 
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0 
            ;;
        *) 
            ARGS+=("$arg") 
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
eval $(get_feature_paths)

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Detect if this is an RDF-first feature
IS_RDF_FEATURE=false
if [[ -d "$ONTOLOGY_DIR" ]] && [[ -f "$GGEN_CONFIG" ]]; then
    IS_RDF_FEATURE=true
fi

if $IS_RDF_FEATURE; then
    # RDF-First Architecture: Create plan.ttl source and link template
    echo "Detected RDF-first feature, setting up TTL-based plan..."

    # Ensure ontology and templates directories exist
    mkdir -p "$ONTOLOGY_DIR"
    mkdir -p "$TEMPLATES_DIR"
    mkdir -p "$GENERATED_DIR"

    # Copy plan.ttl template from RDF helpers
    PLAN_TTL_TEMPLATE="$REPO_ROOT/.specify/templates/rdf-helpers/plan.ttl.template"
    if [[ -f "$PLAN_TTL_TEMPLATE" ]]; then
        # Extract feature name from branch for placeholder replacement
        FEATURE_NAME=$(basename "$FEATURE_DIR")

        # Copy template and replace FEATURE-NAME placeholder
        sed "s/FEATURE-NAME/$FEATURE_NAME/g" "$PLAN_TTL_TEMPLATE" > "$IMPL_PLAN_TTL"
        echo "Created plan.ttl from template at $IMPL_PLAN_TTL"
    else
        echo "Warning: Plan TTL template not found at $PLAN_TTL_TEMPLATE"
        touch "$IMPL_PLAN_TTL"
    fi

    # Create symlink to plan.tera template (if not exists)
    PLAN_TERA_TARGET="$REPO_ROOT/.specify/templates/plan.tera"
    PLAN_TERA_LINK="$TEMPLATES_DIR/plan.tera"
    if [[ -f "$PLAN_TERA_TARGET" ]] && [[ ! -e "$PLAN_TERA_LINK" ]]; then
        ln -s "$PLAN_TERA_TARGET" "$PLAN_TERA_LINK"
        echo "Created symlink to plan.tera template"
    fi

    # Note: plan.md generation would be done by ggen render (not this script)
    echo "Note: Run 'ggen render templates/plan.tera ontology/plan.ttl > generated/plan.md' to generate markdown"
else
    # Legacy Feature: Copy markdown template
    echo "Detected legacy feature, setting up MD-based plan..."

    TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"
    if [[ -f "$TEMPLATE" ]]; then
        cp "$TEMPLATE" "$IMPL_PLAN_LEGACY"
        echo "Copied plan template to $IMPL_PLAN_LEGACY"
    else
        echo "Warning: Plan template not found at $TEMPLATE"
        # Create a basic plan file if template doesn't exist
        touch "$IMPL_PLAN_LEGACY"
    fi
fi

# Output results
if $JSON_MODE; then
    if $IS_RDF_FEATURE; then
        printf '{"IS_RDF_FEATURE":%s,"FEATURE_SPEC_TTL":"%s","IMPL_PLAN_TTL":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","ONTOLOGY_DIR":"%s","GENERATED_DIR":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
            "$IS_RDF_FEATURE" "$FEATURE_SPEC_TTL" "$IMPL_PLAN_TTL" "$FEATURE_SPEC" "$IMPL_PLAN" "$ONTOLOGY_DIR" "$GENERATED_DIR" "$FEATURE_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
    else
        printf '{"IS_RDF_FEATURE":%s,"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
            "$IS_RDF_FEATURE" "$FEATURE_SPEC_LEGACY" "$IMPL_PLAN_LEGACY" "$FEATURE_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
    fi
else
    if $IS_RDF_FEATURE; then
        echo "# RDF-First Feature"
        echo "FEATURE_SPEC_TTL: $FEATURE_SPEC_TTL"
        echo "IMPL_PLAN_TTL: $IMPL_PLAN_TTL"
        echo "FEATURE_SPEC (generated): $FEATURE_SPEC"
        echo "IMPL_PLAN (generated): $IMPL_PLAN"
        echo "ONTOLOGY_DIR: $ONTOLOGY_DIR"
        echo "GENERATED_DIR: $GENERATED_DIR"
    else
        echo "# Legacy Feature"
        echo "FEATURE_SPEC: $FEATURE_SPEC_LEGACY"
        echo "IMPL_PLAN: $IMPL_PLAN_LEGACY"
    fi
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi

