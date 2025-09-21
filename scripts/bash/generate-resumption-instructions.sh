#!/usr/bin/env bash
# Resumption Instructions Generator - Creates precise instructions to resume interrupted mvp-to-full execution
set -e

JSON_MODE=false
REASON=""
NEXT_SPECS=""
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --reason=*) REASON="${arg#*=}" ;;
        --next-specs=*) NEXT_SPECS="${arg#*=}" ;;
        --help|-h) 
            echo "Usage: $0 [--json] [--reason=<reason>] [--next-specs=<spec_list>]"
            echo "Generates resumption instructions for interrupted mvp-to-full execution"
            echo "  --reason: Reason for interruption (e.g., 'token_limit', 'manual_stop')"
            echo "  --next-specs: Comma-separated list of remaining specs to process"
            exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "ERROR: Not in a git repository. Run this script from within a git repository." >&2
    exit 1
fi

# Default reason if not provided
if [ -z "$REASON" ]; then
    REASON="execution_interrupted"
fi

# Analyze current project state
echo "🔍 Analyzing current project state..." >&2

# Find the spec-kit directory - it could be the repo itself or a sibling directory
SPEC_KIT_DIR=""
if [ -f "$REPO_ROOT/.specify/scripts/bash/analyze-spec-completion.sh" ]; then
    SPEC_KIT_DIR="$REPO_ROOT/.specify"
elif [ -f "$REPO_ROOT/scripts/bash/analyze-spec-completion.sh" ]; then
    SPEC_KIT_DIR="$REPO_ROOT"
elif [ -f "$REPO_ROOT/../spec-kit/scripts/bash/analyze-spec-completion.sh" ]; then
    SPEC_KIT_DIR="$REPO_ROOT/../spec-kit"
else
    echo "ERROR: Cannot find spec-kit scripts. Ensure spec-kit is available." >&2
    exit 1
fi

SPEC_ANALYSIS=$("$SPEC_KIT_DIR/scripts/bash/analyze-spec-completion.sh" --json)
PROJECT_STATE=$("$REPO_ROOT/.specify/scripts/bash/analyze-project-state.sh" --json)

# Extract key information
INCOMPLETE_SPECS=$(echo "$SPEC_ANALYSIS" | jq -r '.specs[] | select(.status == "incomplete" or .status == "partially_complete") | .spec_name')
IN_PROGRESS_SPECS=$(echo "$SPEC_ANALYSIS" | jq -r '.specs[] | select(.status == "implementation_in_progress") | .spec_name')
READY_SPECS=$(echo "$SPEC_ANALYSIS" | jq -r '.specs[] | select(.status == "ready_for_implementation") | .spec_name')

# Determine next action based on current state
NEXT_ACTION=""
PRIORITY_SPEC=""
RESUMPTION_CONTEXT=""

if [ -n "$IN_PROGRESS_SPECS" ]; then
    PRIORITY_SPEC=$(echo "$IN_PROGRESS_SPECS" | head -n1)
    NEXT_ACTION="continue_implementation"
    RESUMPTION_CONTEXT="Continue implementing tasks in spec: $PRIORITY_SPEC"
elif [ -n "$INCOMPLETE_SPECS" ]; then
    PRIORITY_SPEC=$(echo "$INCOMPLETE_SPECS" | head -n1)
    NEXT_ACTION="complete_spec_artifacts"
    RESUMPTION_CONTEXT="Complete missing artifacts in spec: $PRIORITY_SPEC"
elif [ -n "$READY_SPECS" ]; then
    PRIORITY_SPEC=$(echo "$READY_SPECS" | head -n1)
    NEXT_ACTION="start_implementation"
    RESUMPTION_CONTEXT="Begin implementation of spec: $PRIORITY_SPEC"
else
    NEXT_ACTION="continue_planning"
    RESUMPTION_CONTEXT="Continue creating new specs from remaining features"
fi

# Get the specific missing artifacts for priority spec
MISSING_ARTIFACTS=""
if [ -n "$PRIORITY_SPEC" ]; then
    MISSING_ARTIFACTS=$(echo "$SPEC_ANALYSIS" | jq -r ".specs[] | select(.spec_name == \"$PRIORITY_SPEC\") | .missing_artifacts[]" | tr '\n' ',' | sed 's/,$//')
fi

# Generate timestamp
TIMESTAMP=$(date -Iseconds)

# Create resumption instructions
if $JSON_MODE; then
    cat << EOF
{
  "interruption_timestamp": "$TIMESTAMP",
  "interruption_reason": "$REASON",
  "next_action": "$NEXT_ACTION",
  "priority_spec": "$PRIORITY_SPEC",
  "missing_artifacts": "$MISSING_ARTIFACTS",
  "resumption_context": "$RESUMPTION_CONTEXT",
  "resumption_command": "Start a new chat and use this prompt: '/mvp-to-full Resume interrupted execution from $TIMESTAMP. $RESUMPTION_CONTEXT. Current state analysis: $SPEC_ANALYSIS'",
  "current_state": $SPEC_ANALYSIS,
  "project_state": $PROJECT_STATE
}
EOF
else
    cat << EOF
=== RESUMPTION INSTRUCTIONS ===
Generated: $TIMESTAMP
Reason: $REASON

🚀 TO RESUME IN NEW CHAT WINDOW:

1. Copy this EXACT command and paste in new chat:

   /mvp-to-full Resume interrupted execution from $TIMESTAMP. $RESUMPTION_CONTEXT.

2. Include this state context:

   Current incomplete specs: $(echo "$INCOMPLETE_SPECS" | tr '\n' ' ')
   Specs in progress: $(echo "$IN_PROGRESS_SPECS" | tr '\n' ' ')
   Ready for implementation: $(echo "$READY_SPECS" | tr '\n' ' ')

3. Priority Action: $NEXT_ACTION
   Focus Spec: $PRIORITY_SPEC
   $([ -n "$MISSING_ARTIFACTS" ] && echo "Missing artifacts: $MISSING_ARTIFACTS")

4. The system will automatically:
   - Detect existing spec folders and their completion status
   - Continue from the exact interruption point
   - Avoid creating duplicate numbered specs
   - Complete missing artifacts before starting new specs

=== DETAILED STATE ANALYSIS ===
$(echo "$SPEC_ANALYSIS" | jq -r '.specs[] | "Spec: \(.spec_name) | Status: \(.status) | Completion: \(.completion_percentage)% | Tasks: \(.task_completion)"')

EOF
fi