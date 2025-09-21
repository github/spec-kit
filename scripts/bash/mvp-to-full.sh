#!/usr/bin/env bash
# MVP to Full Product Orchestrator
set -e

JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) 
            echo "Usage: $0 [--json] <project_description>"
            echo "Orchestrates MVP to Full Product development workflow"
            exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

PROJECT_DESCRIPTION="${ARGS[*]}"
if [ -z "$PROJECT_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] <project_description>" >&2
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "ERROR: Not in a git repository. Run this script from within a git repository." >&2
    exit 1
fi
SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Analyze project state (brownfield vs greenfield)
echo "🔍 Analyzing project state..." >&2
PROJECT_STATE_RESULT=$("$REPO_ROOT/.specify/scripts/bash/analyze-project-state.sh" --json)
PROJECT_TYPE=$(echo "$PROJECT_STATE_RESULT" | jq -r '.project_type')
echo "📊 Project type detected: $PROJECT_TYPE" >&2

# Create MVP plan file if it doesn't exist
MVP_PLAN_FILE="$REPO_ROOT/mvp-plan.md"
if [ ! -f "$MVP_PLAN_FILE" ]; then
    if [ -f "$REPO_ROOT/templates/mvp-plan-template.md" ]; then
        cp "$REPO_ROOT/templates/mvp-plan-template.md" "$MVP_PLAN_FILE"
    else
        cat > "$MVP_PLAN_FILE" << 'EOF'
# MVP to Full Product Plan

**Project**: [PROJECT_NAME]
**Description**: $PROJECT_DESCRIPTION

## MVP Features (Priority 1)
- [ ] Core Feature 1
- [ ] Core Feature 2
- [ ] Basic Auth

## Full Product Features (Priority 2)
- [ ] Advanced Feature 1
- [ ] Analytics
- [ ] Advanced Auth

## Full Product Features (Priority 3)  
- [ ] Premium Features
- [ ] Integrations
- [ ] Admin Panel

## Dependencies
```
MVP Features -> Full Product P2 -> Full Product P3
```

## Execution Plan
1. Analyze and identify specific features from project description
2. Create dependency graph
3. Execute workflow for each feature in order
EOF
    fi
fi

# Generate execution plan with project state awareness
EXECUTION_PLAN="$REPO_ROOT/execution-plan.json"
cat > "$EXECUTION_PLAN" << EOF
{
  "project_description": "$PROJECT_DESCRIPTION",
  "project_type": "$PROJECT_TYPE", 
  "project_state": $PROJECT_STATE_RESULT,
  "mvp_plan_file": "$MVP_PLAN_FILE",
  "specs_directory": "$SPECS_DIR",
  "features": [],
  "dependencies": {},
  "execution_order": [],
  "status": "initialized"
}
EOF

if $JSON_MODE; then
    printf '{"MVP_PLAN_FILE":"%s","EXECUTION_PLAN":"%s","SPECS_DIR":"%s","PROJECT_TYPE":"%s","PROJECT_STATE":%s,"STATUS":"ready_for_analysis"}\n' "$MVP_PLAN_FILE" "$EXECUTION_PLAN" "$SPECS_DIR" "$PROJECT_TYPE" "$PROJECT_STATE_RESULT"
else
    echo "MVP_PLAN_FILE: $MVP_PLAN_FILE"
    echo "EXECUTION_PLAN: $EXECUTION_PLAN"
    echo "SPECS_DIR: $SPECS_DIR"
    echo "PROJECT_TYPE: $PROJECT_TYPE"
    echo "STATUS: ready_for_analysis"
fi