#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *) echo "ERROR: Unknown option '$arg'" >&2; exit 1 ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths
_paths_output=$(get_feature_paths) || { echo "ERROR: Failed to resolve feature paths" >&2; exit 1; }
eval "$_paths_output"
unset _paths_output

# Validate branch
# If feature.json pins an existing feature directory, branch naming is not required.
if ! feature_json_matches_feature_dir "$REPO_ROOT" "$FEATURE_DIR"; then
    check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1
fi

# Validate prerequisites
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /speckit.specify first to create the feature structure." >&2
    exit 1
fi

if [[ ! -f "$IMPL_PLAN" ]]; then
    echo "ERROR: plan.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit.plan first to create the implementation plan." >&2
    exit 1
fi

# Build available docs list
docs=()
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")
if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi
[[ -f "$QUICKSTART" ]] && docs+=("quickstart.md")

# Resolve tasks template through override stack
TASKS_TEMPLATE=$(resolve_template "tasks-template" "$REPO_ROOT") || true
if [[ -z "$TASKS_TEMPLATE" ]] || [[ ! -f "$TASKS_TEMPLATE" ]]; then
    echo "ERROR: Could not resolve required tasks-template from the template override stack for $REPO_ROOT" >&2
    echo "Template 'tasks-template' was not found in any supported location (overrides, presets, extensions, or shared core). Add an override at .specify/templates/tasks-template.md, or run 'specify init' / reinstall shared infra to restore the shared core template." >&2
    exit 1
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        if [[ ${#docs[@]} -eq 0 ]]; then
            json_docs="[]"
        else
            json_docs=$(printf '%s\n' "${docs[@]}" | jq -R . | jq -s .)
        fi
        jq -cn \
            --arg feature_dir "$FEATURE_DIR" \
            --argjson docs "$json_docs" \
            --arg tasks_template "${TASKS_TEMPLATE:-}" \
            '{FEATURE_DIR:$feature_dir,AVAILABLE_DOCS:$docs,TASKS_TEMPLATE:$tasks_template}'
    else
        if [[ ${#docs[@]} -eq 0 ]]; then
            json_docs="[]"
        else
            json_docs=$(for d in "${docs[@]}"; do printf '"%s",' "$(json_escape "$d")"; done)
            json_docs="[${json_docs%,}]"
        fi
        printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":%s,"TASKS_TEMPLATE":"%s"}\n' \
            "$(json_escape "$FEATURE_DIR")" "$json_docs" "$(json_escape "${TASKS_TEMPLATE:-}")"
    fi
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "TASKS_TEMPLATE: ${TASKS_TEMPLATE:-not found}"
    echo "AVAILABLE_DOCS:"
    check_file "$RESEARCH" "research.md"
    check_file "$DATA_MODEL" "data-model.md"
    check_dir "$CONTRACTS_DIR" "contracts/"
    check_file "$QUICKSTART" "quickstart.md"
fi
