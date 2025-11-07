#!/usr/bin/env bash
set -euo pipefail

# Workflow Status Script
# Detects current feature state and provides status information

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Parse arguments
OUTPUT_JSON=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            OUTPUT_JSON=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)

# Detect current feature
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
FEATURE_NUM=""
FEATURE_NAME=""

if [[ $CURRENT_BRANCH =~ ^([0-9]+)-(.+)$ ]]; then
    FEATURE_NUM="${BASH_REMATCH[1]}"
    FEATURE_NAME="${BASH_REMATCH[2]}"
fi

# Detect specs directory
SPECS_DIR="$REPO_ROOT/specs"
FEATURE_DIR=""
if [[ -n "$FEATURE_NUM" ]] && [[ -d "$SPECS_DIR/$FEATURE_NUM-$FEATURE_NAME" ]]; then
    FEATURE_DIR="$SPECS_DIR/$FEATURE_NUM-$FEATURE_NAME"
fi

# Check file existence
CONSTITUTION_EXISTS=false
SPEC_EXISTS=false
PLAN_EXISTS=false
TASKS_EXISTS=false
IMPLEMENTATION_EXISTS=false

[[ -f "$REPO_ROOT/memory/constitution.md" ]] && CONSTITUTION_EXISTS=true

if [[ -n "$FEATURE_DIR" ]]; then
    [[ -f "$FEATURE_DIR/spec.md" ]] && SPEC_EXISTS=true
    [[ -f "$FEATURE_DIR/plan.md" ]] && PLAN_EXISTS=true
    [[ -f "$FEATURE_DIR/tasks.md" ]] && TASKS_EXISTS=true
fi

# Check for implementation files (src/, any source code files)
if [[ -d "$REPO_ROOT/src" ]] || [[ -n "$(find "$REPO_ROOT" -maxdepth 3 -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.cs" -o -name "*.rs" \) 2>/dev/null | head -1)" ]]; then
    IMPLEMENTATION_EXISTS=true
fi

# Calculate task completion
TOTAL_TASKS=0
COMPLETED_TASKS=0
COMPLETION_PERCENTAGE=0

if [[ -f "$FEATURE_DIR/tasks.md" ]]; then
    TOTAL_TASKS=$(grep -cE '^\s*- \[[ Xx]\]' "$FEATURE_DIR/tasks.md" || echo "0")
    COMPLETED_TASKS=$(grep -cE '^\s*- \[[Xx]\]' "$FEATURE_DIR/tasks.md" || echo "0")
    if [[ $TOTAL_TASKS -gt 0 ]]; then
        COMPLETION_PERCENTAGE=$((COMPLETED_TASKS * 100 / TOTAL_TASKS))
    fi
fi

# Determine phase
PHASE="0"
PHASE_NAME="Setup"
NEXT_COMMAND=""
EXPLANATION=""

if ! $CONSTITUTION_EXISTS; then
    PHASE="0"
    PHASE_NAME="Setup"
    NEXT_COMMAND="/speckit.constitution"
    EXPLANATION="Establish project principles and development guidelines that will guide all subsequent development."
elif [[ -z "$FEATURE_DIR" ]]; then
    PHASE="1"
    PHASE_NAME="Ready for Feature"
    NEXT_COMMAND="/speckit.specify [feature description]"
    EXPLANATION="Create a new feature specification. Describe what you want to build in plain language."
elif $SPEC_EXISTS && ! $PLAN_EXISTS; then
    PHASE="2"
    PHASE_NAME="Specification Complete"
    NEXT_COMMAND="/speckit.plan [tech stack]"
    EXPLANATION="Create a technical implementation plan. Specify your tech stack (e.g., 'Next.js 14, PostgreSQL, Prisma')."
elif $PLAN_EXISTS && ! $TASKS_EXISTS; then
    PHASE="3"
    PHASE_NAME="Planning Complete"
    NEXT_COMMAND="/speckit.tasks"
    EXPLANATION="Generate a detailed task breakdown from your implementation plan."
elif $TASKS_EXISTS && [[ $COMPLETION_PERCENTAGE -eq 0 ]]; then
    PHASE="4"
    PHASE_NAME="Ready for Implementation"
    NEXT_COMMAND="/speckit.implement"
    EXPLANATION="Execute all tasks and build your feature according to the plan."
elif $TASKS_EXISTS && [[ $COMPLETION_PERCENTAGE -gt 0 ]] && [[ $COMPLETION_PERCENTAGE -lt 100 ]]; then
    PHASE="5"
    PHASE_NAME="Implementation in Progress"
    NEXT_COMMAND="/speckit.implement"
    EXPLANATION="Continue implementation. Current progress: ${COMPLETION_PERCENTAGE}%"
elif $TASKS_EXISTS && [[ $COMPLETION_PERCENTAGE -eq 100 ]]; then
    PHASE="6"
    PHASE_NAME="Implementation Complete"
    NEXT_COMMAND="/speckit.document"
    EXPLANATION="Generate documentation for your completed feature."
fi

# Calculate token budget (approximate)
TOKEN_BUDGET_USED=0
TOKEN_BUDGET_TOTAL=200

if [[ -n "$FEATURE_DIR" ]]; then
    if [[ -f "$FEATURE_DIR/spec.md" ]]; then
        SPEC_WORDS=$(wc -w < "$FEATURE_DIR/spec.md" 2>/dev/null || echo "0")
        TOKEN_BUDGET_USED=$((TOKEN_BUDGET_USED + SPEC_WORDS * 4 / 3))
    fi
    if [[ -f "$FEATURE_DIR/plan.md" ]]; then
        PLAN_WORDS=$(wc -w < "$FEATURE_DIR/plan.md" 2>/dev/null || echo "0")
        TOKEN_BUDGET_USED=$((TOKEN_BUDGET_USED + PLAN_WORDS * 4 / 3))
    fi
    if [[ -f "$FEATURE_DIR/tasks.md" ]]; then
        TASKS_WORDS=$(wc -w < "$FEATURE_DIR/tasks.md" 2>/dev/null || echo "0")
        TOKEN_BUDGET_USED=$((TOKEN_BUDGET_USED + TASKS_WORDS * 4 / 3))
    fi
fi

TOKEN_PERCENTAGE=0
if [[ $TOKEN_BUDGET_TOTAL -gt 0 ]]; then
    TOKEN_PERCENTAGE=$((TOKEN_BUDGET_USED * 100 / TOKEN_BUDGET_TOTAL))
fi

# Check validation status
VALIDATION_STATUS="not_run"
SPEC_VALIDATION="not_run"
PLAN_VALIDATION="not_run"

# Spec quality score (simple heuristic)
SPEC_QUALITY=0
if $SPEC_EXISTS && [[ -f "$FEATURE_DIR/spec.md" ]]; then
    SPEC_SIZE=$(wc -c < "$FEATURE_DIR/spec.md")
    CLARIFICATIONS=$(grep -c "\[NEEDS CLARIFICATION" "$FEATURE_DIR/spec.md" 2>/dev/null || echo "0")
    MANDATORY_SECTIONS=0
    grep -q "## User Scenarios" "$FEATURE_DIR/spec.md" && MANDATORY_SECTIONS=$((MANDATORY_SECTIONS + 1))
    grep -q "## Requirements" "$FEATURE_DIR/spec.md" && MANDATORY_SECTIONS=$((MANDATORY_SECTIONS + 1))
    grep -q "## Success Criteria" "$FEATURE_DIR/spec.md" && MANDATORY_SECTIONS=$((MANDATORY_SECTIONS + 1))

    # Simple quality score: size + sections - clarifications
    if [[ $SPEC_SIZE -gt 2000 ]] && [[ $MANDATORY_SECTIONS -eq 3 ]] && [[ $CLARIFICATIONS -eq 0 ]]; then
        SPEC_QUALITY=10
    elif [[ $SPEC_SIZE -gt 1000 ]] && [[ $MANDATORY_SECTIONS -ge 2 ]]; then
        SPEC_QUALITY=7
    elif [[ $MANDATORY_SECTIONS -gt 0 ]]; then
        SPEC_QUALITY=5
    else
        SPEC_QUALITY=3
    fi
fi

# Count checklists
CHECKLISTS_TOTAL=0
CHECKLISTS_COMPLETE=0
if [[ -d "$FEATURE_DIR/checklists" ]]; then
    for checklist in "$FEATURE_DIR/checklists"/*.md; do
        [[ -f "$checklist" ]] || continue
        CHECKLISTS_TOTAL=$((CHECKLISTS_TOTAL + 1))
        INCOMPLETE=$(grep -cE '^\s*- \[ \]' "$checklist" 2>/dev/null || echo "0")
        if [[ $INCOMPLETE -eq 0 ]]; then
            CHECKLISTS_COMPLETE=$((CHECKLISTS_COMPLETE + 1))
        fi
    done
fi

# Output JSON
if $OUTPUT_JSON; then
    cat <<EOF
{
  "feature_number": "$FEATURE_NUM",
  "feature_name": "$FEATURE_NAME",
  "branch": "$CURRENT_BRANCH",
  "phase": "$PHASE",
  "phase_name": "$PHASE_NAME",
  "next_command": "$NEXT_COMMAND",
  "explanation": "$EXPLANATION",
  "constitution_exists": $CONSTITUTION_EXISTS,
  "spec_exists": $SPEC_EXISTS,
  "plan_exists": $PLAN_EXISTS,
  "tasks_exists": $TASKS_EXISTS,
  "implementation_exists": $IMPLEMENTATION_EXISTS,
  "total_tasks": $TOTAL_TASKS,
  "completed_tasks": $COMPLETED_TASKS,
  "completion_percentage": $COMPLETION_PERCENTAGE,
  "token_budget_used": $TOKEN_BUDGET_USED,
  "token_budget_total": $TOKEN_BUDGET_TOTAL,
  "token_percentage": $TOKEN_PERCENTAGE,
  "spec_quality": $SPEC_QUALITY,
  "validation_status": "$VALIDATION_STATUS",
  "checklists_total": $CHECKLISTS_TOTAL,
  "checklists_complete": $CHECKLISTS_COMPLETE,
  "feature_dir": "$FEATURE_DIR",
  "specs_dir": "$SPECS_DIR"
}
EOF
else
    # Human-readable output
    echo "Status information:"
    echo "  Feature: $FEATURE_NUM-$FEATURE_NAME"
    echo "  Branch: $CURRENT_BRANCH"
    echo "  Phase: $PHASE - $PHASE_NAME"
    echo "  Progress: $COMPLETION_PERCENTAGE%"
    echo "  Next: $NEXT_COMMAND"
fi
