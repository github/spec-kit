#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false

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
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root)
ARCH_DIR="$REPO_ROOT/.specify/memory"
ARCH_FILE="$ARCH_DIR/architecture.md"
SCENARIO_VIEW="$ARCH_DIR/architecture-scenario-view.md"
LOGICAL_VIEW="$ARCH_DIR/architecture-logical-view.md"
PROCESS_VIEW="$ARCH_DIR/architecture-process-view.md"
DEVELOPMENT_VIEW="$ARCH_DIR/architecture-development-view.md"
PHYSICAL_VIEW="$ARCH_DIR/architecture-physical-view.md"

mkdir -p "$ARCH_DIR"

copy_template_if_missing() {
    local template_name="$1"
    local destination="$2"

    if [[ -f "$destination" ]]; then
        return 0
    fi

    local template
    template=$(resolve_template "$template_name" "$REPO_ROOT") || true
    if [[ -n "$template" ]] && [[ -f "$template" ]]; then
        cp "$template" "$destination"
        echo "Copied $template_name template to $destination"
    else
        echo "Warning: $template_name template not found"
        touch "$destination"
    fi
}

copy_template_if_missing "architecture-template" "$ARCH_FILE"
copy_template_if_missing "architecture-scenario-template" "$SCENARIO_VIEW"
copy_template_if_missing "architecture-logical-template" "$LOGICAL_VIEW"
copy_template_if_missing "architecture-process-template" "$PROCESS_VIEW"
copy_template_if_missing "architecture-development-template" "$DEVELOPMENT_VIEW"
copy_template_if_missing "architecture-physical-template" "$PHYSICAL_VIEW"

if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg arch_file "$ARCH_FILE" \
            --arg arch_dir "$ARCH_DIR" \
            --arg scenario_view "$SCENARIO_VIEW" \
            --arg logical_view "$LOGICAL_VIEW" \
            --arg process_view "$PROCESS_VIEW" \
            --arg development_view "$DEVELOPMENT_VIEW" \
            --arg physical_view "$PHYSICAL_VIEW" \
            '{ARCH_FILE:$arch_file,ARCH_DIR:$arch_dir,SCENARIO_VIEW:$scenario_view,LOGICAL_VIEW:$logical_view,PROCESS_VIEW:$process_view,DEVELOPMENT_VIEW:$development_view,PHYSICAL_VIEW:$physical_view}'
    else
        printf '{"ARCH_FILE":"%s","ARCH_DIR":"%s","SCENARIO_VIEW":"%s","LOGICAL_VIEW":"%s","PROCESS_VIEW":"%s","DEVELOPMENT_VIEW":"%s","PHYSICAL_VIEW":"%s"}\n' \
            "$(json_escape "$ARCH_FILE")" \
            "$(json_escape "$ARCH_DIR")" \
            "$(json_escape "$SCENARIO_VIEW")" \
            "$(json_escape "$LOGICAL_VIEW")" \
            "$(json_escape "$PROCESS_VIEW")" \
            "$(json_escape "$DEVELOPMENT_VIEW")" \
            "$(json_escape "$PHYSICAL_VIEW")"
    fi
else
    echo "ARCH_FILE: $ARCH_FILE"
    echo "ARCH_DIR: $ARCH_DIR"
    echo "SCENARIO_VIEW: $SCENARIO_VIEW"
    echo "LOGICAL_VIEW: $LOGICAL_VIEW"
    echo "PROCESS_VIEW: $PROCESS_VIEW"
    echo "DEVELOPMENT_VIEW: $DEVELOPMENT_VIEW"
    echo "PHYSICAL_VIEW: $PHYSICAL_VIEW"
fi
