# Speckit UX Improvements - Detailed Implementation Plan

**Version:** 1.0.0
**Created:** 2025-11-07
**Status:** Ready for Implementation
**Estimated Total Effort:** 8 weeks (1 developer)

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Core UX (Weeks 1-2)](#phase-1-core-ux-weeks-1-2)
3. [Phase 2: Onboarding (Weeks 3-4)](#phase-2-onboarding-weeks-3-4)
4. [Phase 3: Workflow (Weeks 5-6)](#phase-3-workflow-weeks-5-6)
5. [Phase 4: Advanced (Weeks 7-8)](#phase-4-advanced-weeks-7-8)
6. [Testing Strategy](#testing-strategy)
7. [Documentation Updates](#documentation-updates)
8. [Rollout Plan](#rollout-plan)

---

## Overview

### Goals
- Reduce learning curve by 60% (measured by time to first successful feature)
- Improve command discoverability (90% of users find needed commands without docs)
- Increase workflow completion rate from ~40% to 80%
- Reduce token waste through proactive budgeting (save 30% tokens on average)

### Success Metrics
- Time to complete first feature: 30 min → 10 min
- Commands used per feature: 8-10 → 4-6 (automation)
- User-reported confusion incidents: Baseline → -70%
- Token budget overruns: 25% → 5%

### Architecture Principles
- **Backward Compatible**: All existing commands continue to work
- **Progressive Enhancement**: New features are opt-in
- **Zero Breaking Changes**: Existing workflows unaffected
- **Shadow Mode Compatible**: All improvements work in shadow mode

---

## Phase 1: Core UX (Weeks 1-2)

**Goal**: Fix immediate pain points that frustrate users daily.

### Task 1.1: Add `/speckit.status` Command
**Priority:** P0
**Effort:** 8 hours
**Impact:** High - Addresses #1 user complaint (workflow confusion)

#### Implementation Details

**Files to Create:**
```
templates/commands/status.md
templates/shadow/commands/status.md
scripts/bash/workflow-status.sh
scripts/powershell/workflow-status.ps1
```

**File: `templates/commands/status.md`**
```markdown
---
description: Display current feature status and suggest next steps
scripts:
  sh: scripts/bash/workflow-status.sh --json
  ps: scripts/powershell/workflow-status.ps1 -Json
---

# Workflow Status

## Current State Analysis

You are tasked with analyzing the current feature workflow state and providing clear guidance.

## Process

1. **Run the status script**: Execute `{SCRIPT}` to gather workflow information
   - The script outputs JSON with current state
   - Parse: FEATURE_DIR, BRANCH, PHASE, COMPLETED_STEPS, NEXT_STEPS

2. **Analyze workspace state**:
   - Check if specs/ directory exists
   - Check for current branch name matching pattern: [0-9]+-*
   - Look for spec.md, plan.md, tasks.md, implementation files
   - Check git status for uncommitted changes

3. **Determine current phase**:
   - **No specs directory or constitution**: Phase 0 (Setup)
   - **Constitution exists but no feature branch**: Phase 1 (Ready for feature)
   - **Feature branch + spec.md exists**: Phase 2 (Specification)
   - **spec.md + plan.md exists**: Phase 3 (Planning)
   - **spec.md + plan.md + tasks.md exists**: Phase 4 (Ready for implementation)
   - **Implementation files exist + tasks.md**: Phase 5 (Implementation in progress)
   - **All tasks marked [X] in tasks.md**: Phase 6 (Complete)

4. **Calculate completion percentage**:
   - Count completed vs total checkboxes in tasks.md
   - Count [X] vs [ ] markers
   - Calculate percentage: (completed / total) * 100

5. **Generate status report** using this format:

```
═══════════════════════════════════════════════════════
  SPECKIT WORKFLOW STATUS
═══════════════════════════════════════════════════════

Current Feature: {feature-name}
Branch: {branch-name}
Phase: {phase-number} - {phase-name}
Overall Progress: {percentage}%

✓ COMPLETED
  ✓ {step-1}
  ✓ {step-2}
  ✓ {step-3}

⚙ IN PROGRESS
  ⚙ {current-step}
    Status: {percentage}% complete
    Location: {file-path}
    Started: {timestamp-if-available}

⏳ PENDING
  ⏳ {next-step-1}
  ⏳ {next-step-2}
  ⏳ {next-step-3}

═══════════════════════════════════════════════════════

💡 SUGGESTED NEXT STEP
{command-to-run}

{explanation-of-what-it-does}

═══════════════════════════════════════════════════════

📊 QUALITY METRICS
Specification Quality: {score}/10
Token Budget Used: {used}K / {total}K ({percentage}%)
Checklists Complete: {completed}/{total}
Validation Status: {pass/fail/warning}

═══════════════════════════════════════════════════════

🔗 QUICK LINKS
Spec: specs/{feature}/spec.md
Plan: specs/{feature}/plan.md
Tasks: specs/{feature}/tasks.md

═══════════════════════════════════════════════════════
```

6. **Provide contextual help**:
   - If stuck in same phase for >1 hour, suggest `/speckit.help {phase}`
   - If validation issues detected, suggest `/speckit.validate --fix`
   - If token budget >80%, suggest `/speckit.prune`
   - If multiple [NEEDS CLARIFICATION] markers, suggest `/speckit.clarify`

## Error Handling

- If no git repository: Show message about initializing Speckit first
- If no current feature: Suggest `/speckit.specify` or list available features
- If in detached HEAD state: Warn about workflow state
```

**File: `scripts/bash/workflow-status.sh`**
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

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
[[ -f "$FEATURE_DIR/spec.md" ]] && SPEC_EXISTS=true
[[ -f "$FEATURE_DIR/plan.md" ]] && PLAN_EXISTS=true
[[ -f "$FEATURE_DIR/tasks.md" ]] && TASKS_EXISTS=true

# Check for implementation files (src/, any source code files)
if [[ -d "$REPO_ROOT/src" ]] || [[ -n "$(find "$REPO_ROOT" -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.java" \) 2>/dev/null | head -1)" ]]; then
    IMPLEMENTATION_EXISTS=true
fi

# Calculate task completion
TOTAL_TASKS=0
COMPLETED_TASKS=0
COMPLETION_PERCENTAGE=0

if [[ -f "$FEATURE_DIR/tasks.md" ]]; then
    TOTAL_TASKS=$(grep -E '^\s*- \[[ Xx]\]' "$FEATURE_DIR/tasks.md" | wc -l)
    COMPLETED_TASKS=$(grep -E '^\s*- \[[Xx]\]' "$FEATURE_DIR/tasks.md" | wc -l)
    if [[ $TOTAL_TASKS -gt 0 ]]; then
        COMPLETION_PERCENTAGE=$((COMPLETED_TASKS * 100 / TOTAL_TASKS))
    fi
fi

# Determine phase
PHASE="0"
PHASE_NAME="Setup"
NEXT_COMMAND=""

if ! $CONSTITUTION_EXISTS; then
    PHASE="0"
    PHASE_NAME="Setup"
    NEXT_COMMAND="/speckit.constitution"
elif [[ -z "$FEATURE_DIR" ]]; then
    PHASE="1"
    PHASE_NAME="Ready for Feature"
    NEXT_COMMAND="/speckit.specify \"Your feature description\""
elif $SPEC_EXISTS && ! $PLAN_EXISTS; then
    PHASE="2"
    PHASE_NAME="Specification Complete"
    NEXT_COMMAND="/speckit.plan \"Your tech stack\""
elif $PLAN_EXISTS && ! $TASKS_EXISTS; then
    PHASE="3"
    PHASE_NAME="Planning Complete"
    NEXT_COMMAND="/speckit.tasks"
elif $TASKS_EXISTS && [[ $COMPLETION_PERCENTAGE -eq 0 ]]; then
    PHASE="4"
    PHASE_NAME="Ready for Implementation"
    NEXT_COMMAND="/speckit.implement"
elif $TASKS_EXISTS && [[ $COMPLETION_PERCENTAGE -gt 0 ]] && [[ $COMPLETION_PERCENTAGE -lt 100 ]]; then
    PHASE="5"
    PHASE_NAME="Implementation in Progress"
    NEXT_COMMAND="/speckit.implement (continue)"
elif $TASKS_EXISTS && [[ $COMPLETION_PERCENTAGE -eq 100 ]]; then
    PHASE="6"
    PHASE_NAME="Implementation Complete"
    NEXT_COMMAND="/speckit.document"
fi

# Calculate token budget (approximate)
TOKEN_BUDGET_USED=0
TOKEN_BUDGET_TOTAL=200

if [[ -f "$FEATURE_DIR/spec.md" ]]; then
    TOKEN_BUDGET_USED=$((TOKEN_BUDGET_USED + $(wc -w < "$FEATURE_DIR/spec.md") / 4))
fi
if [[ -f "$FEATURE_DIR/plan.md" ]]; then
    TOKEN_BUDGET_USED=$((TOKEN_BUDGET_USED + $(wc -w < "$FEATURE_DIR/plan.md") / 4))
fi
if [[ -f "$FEATURE_DIR/tasks.md" ]]; then
    TOKEN_BUDGET_USED=$((TOKEN_BUDGET_USED + $(wc -w < "$FEATURE_DIR/tasks.md") / 4))
fi

TOKEN_PERCENTAGE=$((TOKEN_BUDGET_USED * 100 / TOKEN_BUDGET_TOTAL))

# Output JSON
cat <<EOF
{
  "feature_number": "$FEATURE_NUM",
  "feature_name": "$FEATURE_NAME",
  "branch": "$CURRENT_BRANCH",
  "phase": "$PHASE",
  "phase_name": "$PHASE_NAME",
  "next_command": "$NEXT_COMMAND",
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
  "feature_dir": "$FEATURE_DIR",
  "specs_dir": "$SPECS_DIR"
}
EOF
```

**PowerShell Equivalent**: `scripts/powershell/workflow-status.ps1` (full parity)

**Testing:**
```bash
# Test cases:
1. No constitution → Should suggest /speckit.constitution
2. Constitution but no feature → Should suggest /speckit.specify
3. Mid-implementation → Should show progress percentage
4. All tasks complete → Should suggest /speckit.document
```

---

### Task 1.2: Improve Error Messages
**Priority:** P0
**Effort:** 12 hours
**Impact:** High - Reduces frustration and support requests

#### Implementation Details

**Approach**: Create error message enhancement library

**Files to Create/Modify:**
```
scripts/bash/lib/error-messages.sh
scripts/bash/lib/common.sh (enhance die() function)
templates/commands/validate.md (enhance error reporting)
```

**File: `scripts/bash/lib/error-messages.sh`**
```bash
#!/usr/bin/env bash

# Enhanced error message library
# Provides context-aware, actionable error messages

# Error message structure:
# 1. What failed (brief)
# 2. Why it failed (context)
# 3. How to fix it (actionable steps)
# 4. Additional help resources

error_missing_spec_section() {
    local section="$1"
    local file_path="$2"

    cat <<EOF
❌ Error: Specification validation failed

Issue: Missing mandatory section "$section"
  Location: $file_path

Why this matters:
  The "$section" section is required for planning and implementation.
  Without it, the AI agent cannot generate a complete implementation plan.

How to fix:
  1. Open the file: $file_path
  2. Add the missing section: ## $section
  3. Fill in the required content
  4. Run validation again: /speckit.validate --spec

Need help?
  • See template: templates/spec-template.md
  • Run: /speckit.help specify
  • Example: examples/specify.md

💡 Pro tip: Run /speckit.validate --fix to auto-add missing sections
EOF
}

error_implementation_details_in_spec() {
    local file_path="$1"
    local line_number="$2"
    local offending_text="$3"

    cat <<EOF
❌ Error: Implementation details found in specification

Issue: Specification contains technical implementation details
  Location: $file_path:$line_number
  Found: "$offending_text"

Why this matters:
  Specifications should describe WHAT and WHY, not HOW.
  Including implementation details makes the spec fragile and
  ties it to specific technologies.

How to fix:
  1. Open: $file_path
  2. Go to line: $line_number
  3. Remove technical details like:
     - Framework names (React, Vue, Express)
     - API endpoints (/api/users)
     - Database technologies (PostgreSQL, MongoDB)
     - Code structures (classes, functions)
  4. Replace with user-facing outcomes:
     ❌ "Use React hooks for state management"
     ✅ "Users can see real-time updates without page refresh"

Need help?
  • See: docs/quickstart.md#writing-specs
  • Run: /speckit.help specify

💡 Pro tip: Think "product requirements" not "technical design"
EOF
}

error_token_budget_exceeded() {
    local used_tokens="$1"
    local budget_limit="$2"
    local suggested_action="$3"

    cat <<EOF
⚠️  Warning: Token budget limit exceeded

Current usage: ${used_tokens}K tokens
Budget limit: ${budget_limit}K tokens
Overage: $((used_tokens - budget_limit))K tokens ($(( (used_tokens - budget_limit) * 100 / budget_limit ))% over)

Impact:
  • AI responses may be incomplete or cut off
  • Context window may not fit entire specification
  • Increased likelihood of errors or inconsistencies

Immediate actions:
  1. Compress session context:
     /speckit.prune
     Expected savings: 40-60K tokens

  2. If working on large feature, break into smaller features:
     /speckit.specify "Feature Part 1 - Core functionality"
     /speckit.specify "Feature Part 2 - Advanced features"

  3. Use quick references instead of full docs:
     /speckit.document --quick-ref-only

Next steps:
  $suggested_action

💡 Pro tip: Run /speckit.budget before starting implementation
  to catch token issues early.
EOF
}

error_feature_not_found() {
    local feature_ref="$1"
    local available_features="$2"

    cat <<EOF
❌ Error: Feature not found

Requested feature: $feature_ref

Available features:
$available_features

Possible causes:
  1. Feature doesn't exist yet
  2. Not on feature branch
  3. Wrong feature number or name

How to fix:
  • List all features: /speckit.features list
  • Switch to feature: /speckit.features switch $feature_ref
  • Create new feature: /speckit.specify "Your feature description"
  • Check current status: /speckit.status

💡 Pro tip: Use tab completion for feature names
EOF
}

error_git_not_initialized() {
    cat <<EOF
❌ Error: Git repository not initialized

This directory is not a git repository.

Why this matters:
  Speckit uses git branches to organize features and track changes.
  Without git, branch-based workflows won't work.

How to fix:
  Option 1 - Initialize git:
    git init
    git add .
    git commit -m "Initial commit"

  Option 2 - Reinitialize Speckit:
    specify init . --force --ai claude

  Option 3 - Work without git (limited functionality):
    Set environment variable:
    export SPECIFY_FEATURE="001-my-feature"

    Then proceed with /speckit.specify

Need help?
  • See: docs/installation.md#git-setup
  • Run: /speckit.help setup
EOF
}

error_spec_validation_failed() {
    local issues="$1"
    local file_path="$2"

    cat <<EOF
❌ Error: Specification validation failed

Found $issues validation issues in: $file_path

Common issues and fixes:

1. Missing mandatory sections
   Fix: Add all required sections from template
   Template: templates/spec-template.md

2. [NEEDS CLARIFICATION] markers remaining
   Fix: Run /speckit.clarify to resolve ambiguities

3. Success criteria not measurable
   Fix: Add specific metrics (time, percentage, count)
   ❌ "System is fast"
   ✅ "Users see results in under 2 seconds"

4. Implementation details in spec
   Fix: Remove framework/technology mentions
   ❌ "Use PostgreSQL for storage"
   ✅ "System persists user data reliably"

Quick actions:
  • Auto-fix common issues: /speckit.validate --spec --fix
  • See detailed report: /speckit.validate --spec --verbose
  • Manual edit: $file_path

Next steps:
  1. Run /speckit.validate --spec --fix
  2. Review and adjust auto-fixes
  3. Run /speckit.validate --spec again
  4. Proceed to /speckit.plan when validation passes

💡 Pro tip: Validate early and often to catch issues quickly
EOF
}

# Export functions
export -f error_missing_spec_section
export -f error_implementation_details_in_spec
export -f error_token_budget_exceeded
export -f error_feature_not_found
export -f error_git_not_initialized
export -f error_spec_validation_failed
```

**Update common.sh die() function:**
```bash
die() {
    local message="$1"
    local exit_code="${2:-1}"
    local error_type="${3:-generic}"

    # Check if error message library is loaded
    if declare -f "error_${error_type}" > /dev/null 2>&1; then
        # Call specialized error handler
        "error_${error_type}" "$@"
    else
        # Fallback to simple error
        echo "❌ Error: $message" >&2
    fi

    exit "$exit_code"
}
```

**Usage in scripts:**
```bash
# Old way:
die "Specification validation failed"

# New way:
source "$SCRIPT_DIR/lib/error-messages.sh"
die "spec_validation_failed" "$issue_count" "$spec_file"
```

**Testing:**
Create test suite that triggers each error type and validates:
- Error message clarity
- Actionable steps provided
- Help resources linked
- User can resolve without external help

---

### Task 1.3: Add Command Aliases
**Priority:** P1
**Effort:** 4 hours
**Impact:** Medium - Improves discoverability

#### Implementation Details

**Approach**: Create alias mapping system in agent command loading

**Files to Create/Modify:**
```
templates/commands/_aliases.json
templates/commands/ask-questions.md → symlink to clarify.md
templates/commands/token-usage.md → symlink to budget.md
scripts/bash/create-aliases.sh
```

**File: `templates/commands/_aliases.json`**
```json
{
  "version": "1.0.0",
  "description": "Command alias mappings for improved discoverability",
  "aliases": [
    {
      "alias": "ask-questions",
      "target": "clarify",
      "description": "Ask clarifying questions about requirements (alias for clarify)"
    },
    {
      "alias": "token-usage",
      "target": "budget",
      "description": "View token budget usage and recommendations (alias for budget)"
    },
    {
      "alias": "compress-context",
      "target": "prune",
      "description": "Compress session context to save tokens (alias for prune)"
    },
    {
      "alias": "search-code",
      "target": "find",
      "description": "Search code using natural language (alias for find)"
    },
    {
      "alias": "debug-error",
      "target": "error-context",
      "description": "Analyze errors with spec cross-reference (alias for error-context)"
    },
    {
      "alias": "check-quality",
      "target": "validate",
      "description": "Validate specs, plans, and tasks (alias for validate)"
    },
    {
      "alias": "create-spec",
      "target": "specify",
      "description": "Create feature specification (alias for specify)"
    },
    {
      "alias": "create-plan",
      "target": "plan",
      "description": "Create implementation plan (alias for plan)"
    },
    {
      "alias": "create-tasks",
      "target": "tasks",
      "description": "Create task breakdown (alias for tasks)"
    },
    {
      "alias": "start-coding",
      "target": "implement",
      "description": "Start implementation (alias for implement)"
    },
    {
      "alias": "what-next",
      "target": "status",
      "description": "Show workflow status and next step (alias for status)"
    },
    {
      "alias": "get-help",
      "target": "help",
      "description": "Get help with Speckit commands (alias for help)"
    }
  ]
}
```

**File: `scripts/bash/create-aliases.sh`**
```bash
#!/usr/bin/env bash
set -euo pipefail

# Create command aliases
# Reads _aliases.json and creates symlinks in commands directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")

COMMANDS_DIR="$REPO_ROOT/.claude/commands"
ALIASES_JSON="$REPO_ROOT/templates/commands/_aliases.json"

if [[ ! -f "$ALIASES_JSON" ]]; then
    echo "Error: Aliases file not found: $ALIASES_JSON"
    exit 1
fi

if [[ ! -d "$COMMANDS_DIR" ]]; then
    echo "Error: Commands directory not found: $COMMANDS_DIR"
    exit 1
fi

# Parse JSON and create symlinks
jq -r '.aliases[] | "\(.alias) \(.target)"' "$ALIASES_JSON" | while read -r alias target; do
    alias_file="$COMMANDS_DIR/speckit.${alias}.md"
    target_file="speckit.${target}.md"

    # Remove existing alias if present
    [[ -L "$alias_file" ]] && rm "$alias_file"

    # Create symlink
    ln -s "$target_file" "$alias_file"
    echo "Created alias: /speckit.$alias → /speckit.$target"
done

echo "✓ All command aliases created successfully"
```

**Update specify CLI to run alias creation:**
Modify `src/specify_cli/__init__.py` to run alias creation after template extraction.

---

### Task 1.4: Add Token Budget Warnings
**Priority:** P0
**Effort:** 6 hours
**Impact:** High - Prevents token overruns

#### Implementation Details

**Approach**: Add predictive token estimation before expensive operations

**Files to Modify:**
```
templates/commands/plan.md (add pre-check)
templates/commands/implement.md (add pre-check)
scripts/bash/token-budget.sh (add prediction functions)
scripts/bash/lib/token-estimation.sh (NEW)
```

**File: `scripts/bash/lib/token-estimation.sh`**
```bash
#!/usr/bin/env bash

# Token estimation library
# Predicts token usage for upcoming operations

estimate_tokens_from_text() {
    local text="$1"
    # Rough estimation: 1 token ≈ 4 characters
    local char_count=${#text}
    echo $((char_count / 4))
}

estimate_tokens_from_file() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo "0"
        return
    fi
    local word_count=$(wc -w < "$file")
    # Rough estimation: 1 token ≈ 0.75 words
    echo $((word_count * 4 / 3))
}

estimate_plan_tokens() {
    local feature_description="$1"
    local tech_stack="$2"

    # Estimate based on complexity
    local base_tokens=8000  # Minimum for simple plan
    local desc_tokens=$(estimate_tokens_from_text "$feature_description")
    local tech_tokens=$(estimate_tokens_from_text "$tech_stack")

    # Add multiplier for complex features
    local complexity_multiplier=1
    if [[ "$feature_description" =~ microservice|distributed|real-time|multi-tenant ]]; then
        complexity_multiplier=2
    fi

    local estimated=$((base_tokens + desc_tokens + tech_tokens * complexity_multiplier))
    echo "$estimated"
}

estimate_implement_tokens() {
    local tasks_file="$1"

    if [[ ! -f "$tasks_file" ]]; then
        echo "0"
        return
    fi

    # Count total tasks
    local total_tasks=$(grep -c '^\s*- \[ \]' "$tasks_file" 2>/dev/null || echo "0")

    # Estimate tokens per task (average)
    local tokens_per_task=3000

    # Add overhead for context and planning
    local overhead=15000

    local estimated=$((total_tasks * tokens_per_task + overhead))
    echo "$estimated"
}

get_current_token_usage() {
    local repo_root="$1"
    local total=0

    # Sum tokens from existing files
    for file in "$repo_root"/specs/*/spec.md; do
        [[ -f "$file" ]] || continue
        tokens=$(estimate_tokens_from_file "$file")
        total=$((total + tokens))
    done

    for file in "$repo_root"/specs/*/plan.md; do
        [[ -f "$file" ]] || continue
        tokens=$(estimate_tokens_from_file "$file")
        total=$((total + tokens))
    done

    for file in "$repo_root"/specs/*/tasks.md; do
        [[ -f "$file" ]] || continue
        tokens=$(estimate_tokens_from_file "$file")
        total=$((total + tokens))
    done

    echo "$total"
}

check_token_budget_warning() {
    local current_usage="$1"
    local estimated_operation="$2"
    local budget_limit="${3:-200000}"  # Default 200K

    local projected=$((current_usage + estimated_operation))
    local percentage=$((projected * 100 / budget_limit))

    if [[ $percentage -gt 90 ]]; then
        echo "CRITICAL"
    elif [[ $percentage -gt 75 ]]; then
        echo "WARNING"
    elif [[ $percentage -gt 60 ]]; then
        echo "CAUTION"
    else
        echo "OK"
    fi
}

show_token_budget_warning() {
    local operation="$1"
    local current_usage="$2"
    local estimated_cost="$3"
    local budget_limit="$4"
    local warning_level="$5"

    local projected=$((current_usage + estimated_cost))
    local percentage=$((projected * 100 / budget_limit))

    case "$warning_level" in
        CRITICAL)
            cat <<EOF
🚨 CRITICAL: Token Budget Exceeded

Operation: $operation
Current usage: $(format_thousands "$current_usage") tokens
Estimated cost: $(format_thousands "$estimated_cost") tokens
Projected total: $(format_thousands "$projected") tokens (${percentage}% of budget)
Budget limit: $(format_thousands "$budget_limit") tokens

⚠️  WARNING: This operation will exceed your token budget!

Recommended actions (choose one):
1. Compress context first (saves ~40-60K tokens):
   /speckit.prune

2. Break feature into smaller parts:
   /speckit.specify "Feature Part 1"
   /speckit.specify "Feature Part 2"

3. Use quick references instead of full docs:
   /speckit.document --quick-ref-only

4. Proceed anyway (not recommended):
   Risk: Incomplete AI responses, context loss

Do you want to proceed? [y/N]:
EOF
            ;;
        WARNING)
            cat <<EOF
⚠️  WARNING: High Token Usage Projected

Operation: $operation
Current usage: $(format_thousands "$current_usage") tokens
Estimated cost: $(format_thousands "$estimated_cost") tokens
Projected total: $(format_thousands "$projected") tokens (${percentage}% of budget)

You're approaching the token budget limit.

Suggested actions:
• Run /speckit.prune to free ~40-60K tokens
• Use /speckit.budget to see detailed breakdown
• Consider quick references over full documentation

Continue? [Y/n]:
EOF
            ;;
        CAUTION)
            cat <<EOF
ℹ️  INFO: Moderate Token Usage

Current: $(format_thousands "$current_usage") tokens
Estimated: +$(format_thousands "$estimated_cost") tokens
Projected: $(format_thousands "$projected") tokens (${percentage}% of budget)

💡 Tip: Run /speckit.budget to track token usage
EOF
            ;;
    esac
}

format_thousands() {
    local num="$1"
    echo "$num" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta'
}

export -f estimate_tokens_from_text
export -f estimate_tokens_from_file
export -f estimate_plan_tokens
export -f estimate_implement_tokens
export -f get_current_token_usage
export -f check_token_budget_warning
export -f show_token_budget_warning
export -f format_thousands
```

**Update `/speckit.plan` command template:**
Add pre-check section:
```markdown
## Pre-Flight Token Budget Check

Before executing the planning workflow:

1. Load token estimation library
2. Calculate current token usage
3. Estimate planning operation cost
4. Check if budget allows operation
5. Show warning if necessary
6. Wait for user confirmation if in WARNING or CRITICAL state

Example:
```bash
source scripts/bash/lib/token-estimation.sh

current=$(get_current_token_usage "$REPO_ROOT")
estimated=$(estimate_plan_tokens "$ARGUMENTS" "$TECH_STACK")
warning=$(check_token_budget_warning "$current" "$estimated" 200000)

if [[ "$warning" == "CRITICAL" ]] || [[ "$warning" == "WARNING" ]]; then
    show_token_budget_warning "Planning" "$current" "$estimated" 200000 "$warning"
    # Wait for user response
fi
```
```

---

### Task 1.5: Testing & Documentation for Phase 1
**Priority:** P1
**Effort:** 8 hours
**Impact:** Ensures quality

#### Test Suite

**Create**: `tests/phase1-core-ux/`
```
tests/phase1-core-ux/
├── test-status-command.sh
├── test-error-messages.sh
├── test-command-aliases.sh
├── test-token-warnings.sh
└── test-integration.sh
```

**Test Cases:**
1. Status command shows correct phase for all workflow states
2. Error messages include actionable steps
3. All aliases resolve to correct target commands
4. Token warnings trigger at correct thresholds
5. Integration: Full workflow with new features works end-to-end

#### Documentation Updates

**Update:**
- `README.md`: Add new commands to command list
- `docs/quickstart.md`: Reference new status command
- `CHANGELOG.md`: Document Phase 1 changes
- Create: `docs/troubleshooting.md` with improved error explanations

---

## Phase 2: Onboarding (Weeks 3-4)

**Goal**: Dramatically reduce learning curve for new users.

### Task 2.1: Create `/speckit.wizard` Interactive Flow
**Priority:** P0
**Effort:** 16 hours
**Impact:** High - Makes Speckit accessible to beginners

#### Implementation Details

**Files to Create:**
```
templates/commands/wizard.md
templates/shadow/commands/wizard.md
scripts/bash/interactive-wizard.sh
scripts/powershell/interactive-wizard.ps1
templates/wizard/steps.json
```

**File: `templates/commands/wizard.md`**
```markdown
---
description: Interactive wizard for guided feature creation
scripts:
  sh: scripts/bash/interactive-wizard.sh
  ps: scripts/powershell/interactive-wizard.ps1
---

# Interactive Feature Wizard

Welcome to the Speckit Interactive Wizard! This guided experience will help you create a complete feature specification and implementation plan step-by-step.

## Process

1. **Run the wizard script**: Execute `{SCRIPT}` to start interactive session
   - Script handles all user input and validation
   - Provides contextual help at each step
   - Saves progress and allows resume

2. **Follow the interactive prompts**:
   The wizard will guide you through:
   - Feature description
   - Tech stack selection
   - Architecture choices
   - Development approach
   - Confirmation and execution

3. **Wizard steps** (defined in templates/wizard/steps.json):

### Step 1: Feature Description
```
═══════════════════════════════════════════════════════════
  SPECKIT FEATURE WIZARD
═══════════════════════════════════════════════════════════

Let's create your feature step-by-step!

Step 1 of 6: What are you building?

Describe your feature in plain language:
→ _

Examples:
• A task management app with drag-and-drop boards
• User authentication with OAuth2 and email/password
• Real-time chat system with message history
• REST API for product catalog management

💡 Tip: Focus on WHAT users will do, not HOW to build it

═══════════════════════════════════════════════════════════
```

### Step 2: Application Type
```
Step 2 of 6: What type of application?

Choose your application type:

[1] 🌐 Web Application
    Full-stack web app with frontend and backend
    Examples: Dashboard, SaaS platform, E-commerce site

[2] 🔌 API Only
    Backend API service without frontend
    Examples: REST API, GraphQL API, Microservice

[3] 📱 Mobile Application
    Native or cross-platform mobile app
    Examples: iOS app, Android app, React Native

[4] 🖥️  Desktop Application
    Desktop software application
    Examples: Electron app, Native desktop app

[5] 🤖 CLI Tool
    Command-line interface tool
    Examples: Build tool, Automation script

[6] 🧪 Other / Custom
    Specify your own application type

Enter choice [1-6]: _

═══════════════════════════════════════════════════════════
```

### Step 3: Tech Stack (Web Application example)
```
Step 3 of 6: Choose your tech stack

Based on your choice: Web Application

Frontend Framework:
[1] ⚛️  Next.js 14 (React) - Recommended
    Modern, full-stack React framework

[2] ⚡ Vite + React
    Fast development with React

[3] 🟢 Vue 3 + Vite
    Progressive JavaScript framework

[4] 🅰️  Angular
    Full-featured framework by Google

[5] 💎 Other: _____

Enter choice [1-5]: _

Backend Technology:
[1] 🟢 Node.js + Express - Recommended
    JavaScript/TypeScript backend

[2] 🐍 Python + FastAPI
    Modern Python web framework

[3] ☕ Java + Spring Boot
    Enterprise Java framework

[4] 🦀 Rust + Axum
    High-performance systems language

[5] 💎 Ruby on Rails
    Convention-over-configuration framework

[6] 🔷 C# + .NET
    Microsoft's modern framework

[7] 🐹 Go + Gin
    Fast, compiled backend

[8] 💎 Other: _____

Enter choice [1-8]: _

Database:
[1] 🐘 PostgreSQL - Recommended
    Powerful open-source relational DB

[2] 🐬 MySQL
    Popular relational database

[3] 🍃 MongoDB
    NoSQL document database

[4] 📦 SQLite
    Lightweight embedded database

[5] 🔴 Redis
    In-memory data store

[6] 💎 Other: _____

Enter choice [1-6]: _

═══════════════════════════════════════════════════════════
```

### Step 4: Architecture Pattern
```
Step 4 of 6: Choose architecture pattern

Select the architectural pattern that best fits your needs:

[1] 📚 Layered (3-tier) - Recommended for most apps
    API → Service → Repository → Database
    Best for: Standard web apps, CRUD applications
    Complexity: Low

[2] 🔷 Hexagonal (Ports & Adapters)
    Core domain isolated from infrastructure
    Best for: Domain-driven design, testability
    Complexity: Medium

[3] 📮 Event-Driven
    Components communicate via events
    Best for: Real-time systems, microservices
    Complexity: High

[4] 🎯 Serverless
    Function-as-a-Service architecture
    Best for: Auto-scaling, pay-per-use
    Complexity: Medium

[5] 🧱 Modular Monolith
    Single deployment, multiple modules
    Best for: Team scalability, clear boundaries
    Complexity: Medium

[6] 💡 Need help choosing?
    Get AI recommendation based on your feature

Enter choice [1-6]: _

═══════════════════════════════════════════════════════════
```

### Step 5: Development Approach
```
Step 5 of 6: Development approach

How would you like to develop this feature?

Testing Strategy:
[1] ✅ Test-First (TDD) - Recommended
    Write tests before implementation
    Higher quality, better design

[2] 🏃 Implementation-First
    Write code first, tests later
    Faster initial development

Enter choice [1-2]: _

Implementation Style:
[1] 📋 Task-by-Task
    Follow detailed task list step-by-step
    Best for: Complex features, team work

[2] 🎯 User-Story-by-Story
    Implement one complete user story at a time
    Best for: Independent deliverables

[3] ⚡ Quick Prototype
    Minimal planning, fast iteration
    Best for: Spikes, experiments

Enter choice [1-3]: _

═══════════════════════════════════════════════════════════
```

### Step 6: Confirmation
```
Step 6 of 6: Confirm and create

═══════════════════════════════════════════════════════════
  REVIEW YOUR CHOICES
═══════════════════════════════════════════════════════════

Feature Description:
  A task management app with drag-and-drop boards

Application Type:
  🌐 Web Application

Tech Stack:
  Frontend: Next.js 14 (React)
  Backend: Node.js + Express
  Database: PostgreSQL

Architecture:
  📚 Layered Architecture (3-tier)

Development:
  Testing: ✅ Test-First (TDD)
  Style: 📋 Task-by-Task

═══════════════════════════════════════════════════════════

What I'll do next:

1. ✓ Create feature specification
   Location: specs/XXX-task-management/spec.md
   Estimated time: 2-3 minutes

2. ✓ Generate implementation plan
   Location: specs/XXX-task-management/plan.md
   Tech: Next.js + Node.js + PostgreSQL
   Estimated time: 3-5 minutes

3. ✓ Create task breakdown
   Location: specs/XXX-task-management/tasks.md
   Estimated time: 2-3 minutes

4. ✓ Set up project structure
   Initialize directories and configuration
   Estimated time: 1-2 minutes

Total estimated time: 8-13 minutes

═══════════════════════════════════════════════════════════

Ready to proceed? [Y/n]: _

═══════════════════════════════════════════════════════════
```

### Step 7: Execution with Progress
```
═══════════════════════════════════════════════════════════
  CREATING YOUR FEATURE
═══════════════════════════════════════════════════════════

[████████████████░░░░░░░░] 60% Complete

✓ Feature specification created
  specs/001-task-management/spec.md

✓ Implementation plan generated
  specs/001-task-management/plan.md

⚙ Creating task breakdown...
  specs/001-task-management/tasks.md
  Status: Analyzing user stories (2/3 complete)

⏳ Project structure setup (pending)

═══════════════════════════════════════════════════════════
```

### Step 8: Completion
```
═══════════════════════════════════════════════════════════
  ✨ FEATURE CREATED SUCCESSFULLY!
═══════════════════════════════════════════════════════════

Your feature is ready for implementation:

📂 Feature: 001-task-management
🌿 Branch: 001-task-management
📄 Files created:
  ✓ specs/001-task-management/spec.md (2.3 KB)
  ✓ specs/001-task-management/plan.md (5.1 KB)
  ✓ specs/001-task-management/tasks.md (8.7 KB)
  ✓ specs/001-task-management/data-model.md (1.8 KB)
  ✓ specs/001-task-management/contracts/ (3 files)

═══════════════════════════════════════════════════════════

🚀 NEXT STEPS

Ready to start coding? Run:
  /speckit.implement

Want to review first? Check:
  • Specification: specs/001-task-management/spec.md
  • Implementation plan: specs/001-task-management/plan.md
  • Task list: specs/001-task-management/tasks.md

Need to make changes? Run:
  • Update spec: /speckit.specify (edit and regenerate)
  • Adjust plan: /speckit.plan (modify tech choices)
  • Change tasks: /speckit.tasks (regenerate breakdown)

═══════════════════════════════════════════════════════════

💡 Tip: Run /speckit.status anytime to see your progress

═══════════════════════════════════════════════════════════
```

4. **Handle user navigation**:
   - Allow back/forward through steps
   - Save progress for resume
   - Validate each input
   - Provide contextual help

5. **Execute workflow**:
   - Run /speckit.specify with collected input
   - Run /speckit.plan with tech stack choices
   - Run /speckit.tasks
   - Report completion with next steps

## Error Handling

- Invalid choices: Show valid options and retry
- Empty inputs: Require non-empty for critical fields
- Interrupted session: Save state, allow resume with /speckit.wizard --resume
- Technical errors: Show detailed error with recovery steps

## Help System

At any step, user can type:
- `help` - Show contextual help for current step
- `back` - Go to previous step
- `skip` - Skip optional step
- `quit` - Exit wizard (save progress)
- `restart` - Start over from beginning
```

**File: `scripts/bash/interactive-wizard.sh`**
```bash
#!/usr/bin/env bash
set -euo pipefail

# Interactive wizard for guided feature creation
# Provides step-by-step UI for creating features

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Unicode box drawing
BOX_H="═"
BOX_V="║"
BOX_TL="╔"
BOX_TR="╗"
BOX_BL="╚"
BOX_BR="╝"

# Wizard state file
STATE_FILE="$REPO_ROOT/.speckit-wizard-state.json"

# Initialize wizard state
declare -A wizard_state=(
    [feature_description]=""
    [app_type]=""
    [frontend]=""
    [backend]=""
    [database]=""
    [architecture]=""
    [testing]=""
    [implementation_style]=""
    [current_step]=1
)

# Load saved state if resuming
load_state() {
    if [[ -f "$STATE_FILE" ]] && [[ "${1:-}" == "--resume" ]]; then
        while IFS="=" read -r key value; do
            wizard_state[$key]="$value"
        done < <(jq -r 'to_entries | .[] | "\(.key)=\(.value)"' "$STATE_FILE")
        echo "${GREEN}✓${NC} Resumed from previous session"
    fi
}

# Save current state
save_state() {
    local json="{"
    local first=true
    for key in "${!wizard_state[@]}"; do
        [[ "$first" == false ]] && json+=","
        json+="\"$key\":\"${wizard_state[$key]}\""
        first=false
    done
    json+="}"
    echo "$json" | jq '.' > "$STATE_FILE"
}

# Draw box header
draw_header() {
    local text="$1"
    local width=65

    echo -e "${BLUE}"
    printf "%s" "$BOX_TL"
    printf "%${width}s" | tr ' ' "$BOX_H"
    printf "%s\n" "$BOX_TR"

    local padding=$(( (width - ${#text}) / 2 ))
    printf "%s" "$BOX_V"
    printf "%${padding}s" ""
    printf "%s" "$text"
    printf "%$((width - padding - ${#text}))s" ""
    printf "%s\n" "$BOX_V"

    printf "%s" "$BOX_BL"
    printf "%${width}s" | tr ' ' "$BOX_H"
    printf "%s\n" "$BOX_BR"
    echo -e "${NC}"
}

# Draw box footer
draw_footer() {
    local width=65
    echo -e "${BLUE}"
    printf "%s" "$BOX_TL"
    printf "%${width}s" | tr ' ' "$BOX_H"
    printf "%s\n" "$BOX_TR"
    echo -e "${NC}"
}

# Get user input with validation
get_input() {
    local prompt="$1"
    local validation_type="${2:-any}"
    local input=""

    while true; do
        echo -e -n "${CYAN}${prompt}${NC} "
        read -r input

        # Handle special commands
        case "$input" in
            help)
                show_step_help
                continue
                ;;
            back)
                wizard_state[current_step]=$((wizard_state[current_step] - 1))
                return 1
                ;;
            quit)
                save_state
                echo -e "${YELLOW}Session saved. Resume with: /speckit.wizard --resume${NC}"
                exit 0
                ;;
            restart)
                rm -f "$STATE_FILE"
                exec "$0"
                ;;
        esac

        # Validate input
        case "$validation_type" in
            number)
                if [[ "$input" =~ ^[0-9]+$ ]]; then
                    echo "$input"
                    return 0
                else
                    echo -e "${RED}Please enter a number${NC}"
                fi
                ;;
            non-empty)
                if [[ -n "$input" ]]; then
                    echo "$input"
                    return 0
                else
                    echo -e "${RED}This field cannot be empty${NC}"
                fi
                ;;
            *)
                echo "$input"
                return 0
                ;;
        esac
    done
}

# Step 1: Feature Description
step1_feature_description() {
    clear
    draw_header "SPECKIT FEATURE WIZARD"

    echo ""
    echo "Let's create your feature step-by-step!"
    echo ""
    echo -e "${PURPLE}Step 1 of 6: What are you building?${NC}"
    echo ""
    echo "Describe your feature in plain language:"
    echo ""

    wizard_state[feature_description]=$(get_input "→" "non-empty")

    echo ""
    echo -e "${GREEN}✓${NC} Feature description captured"
    echo ""

    wizard_state[current_step]=2
    save_state
    sleep 1
}

# Step 2: Application Type
step2_app_type() {
    clear
    draw_header "SPECKIT FEATURE WIZARD"

    echo ""
    echo -e "${PURPLE}Step 2 of 6: What type of application?${NC}"
    echo ""
    echo "Choose your application type:"
    echo ""
    echo -e "[1] 🌐 ${CYAN}Web Application${NC}"
    echo "    Full-stack web app with frontend and backend"
    echo ""
    echo -e "[2] 🔌 ${CYAN}API Only${NC}"
    echo "    Backend API service without frontend"
    echo ""
    echo -e "[3] 📱 ${CYAN}Mobile Application${NC}"
    echo "    Native or cross-platform mobile app"
    echo ""
    echo -e "[4] 🖥️  ${CYAN}Desktop Application${NC}"
    echo "    Desktop software application"
    echo ""
    echo -e "[5] 🤖 ${CYAN}CLI Tool${NC}"
    echo "    Command-line interface tool"
    echo ""
    echo -e "[6] 🧪 ${CYAN}Other / Custom${NC}"
    echo "    Specify your own application type"
    echo ""

    local choice
    while true; do
        choice=$(get_input "Enter choice [1-6]:" "number")
        [[ $choice -ge 1 && $choice -le 6 ]] && break
        echo -e "${RED}Please enter a number between 1 and 6${NC}"
    done

    case $choice in
        1) wizard_state[app_type]="web" ;;
        2) wizard_state[app_type]="api" ;;
        3) wizard_state[app_type]="mobile" ;;
        4) wizard_state[app_type]="desktop" ;;
        5) wizard_state[app_type]="cli" ;;
        6)
            echo ""
            wizard_state[app_type]=$(get_input "Specify application type:" "non-empty")
            ;;
    esac

    echo ""
    echo -e "${GREEN}✓${NC} Application type selected: ${wizard_state[app_type]}"
    echo ""

    wizard_state[current_step]=3
    save_state
    sleep 1
}

# Step 3: Tech Stack (varies by app type)
step3_tech_stack() {
    clear
    draw_header "SPECKIT FEATURE WIZARD"

    echo ""
    echo -e "${PURPLE}Step 3 of 6: Choose your tech stack${NC}"
    echo ""

    case "${wizard_state[app_type]}" in
        web)
            step3_web_stack
            ;;
        api)
            step3_api_stack
            ;;
        mobile)
            step3_mobile_stack
            ;;
        *)
            echo "Custom stack for ${wizard_state[app_type]}"
            wizard_state[frontend]=$(get_input "Frontend/UI technology:" "non-empty")
            wizard_state[backend]=$(get_input "Backend technology:" "non-empty")
            wizard_state[database]=$(get_input "Database:" "non-empty")
            ;;
    esac

    echo ""
    echo -e "${GREEN}✓${NC} Tech stack configured"
    echo ""

    wizard_state[current_step]=4
    save_state
    sleep 1
}

step3_web_stack() {
    echo "Frontend Framework:"
    echo "[1] ⚛️  Next.js 14 (React) - Recommended"
    echo "[2] ⚡ Vite + React"
    echo "[3] 🟢 Vue 3 + Vite"
    echo "[4] 🅰️  Angular"
    echo "[5] 💎 Other"
    echo ""

    local choice=$(get_input "Enter choice [1-5]:" "number")
    case $choice in
        1) wizard_state[frontend]="Next.js 14" ;;
        2) wizard_state[frontend]="Vite + React" ;;
        3) wizard_state[frontend]="Vue 3 + Vite" ;;
        4) wizard_state[frontend]="Angular" ;;
        5) wizard_state[frontend]=$(get_input "Specify frontend:" "non-empty") ;;
    esac

    echo ""
    echo "Backend Technology:"
    echo "[1] 🟢 Node.js + Express"
    echo "[2] 🐍 Python + FastAPI"
    echo "[3] ☕ Java + Spring Boot"
    echo "[4] 🦀 Rust + Axum"
    echo "[5] 💎 Ruby on Rails"
    echo "[6] 🔷 C# + .NET"
    echo "[7] 🐹 Go + Gin"
    echo "[8] 💎 Other"
    echo ""

    choice=$(get_input "Enter choice [1-8]:" "number")
    case $choice in
        1) wizard_state[backend]="Node.js + Express" ;;
        2) wizard_state[backend]="Python + FastAPI" ;;
        3) wizard_state[backend]="Java + Spring Boot" ;;
        4) wizard_state[backend]="Rust + Axum" ;;
        5) wizard_state[backend]="Ruby on Rails" ;;
        6) wizard_state[backend]="C# + .NET" ;;
        7) wizard_state[backend]="Go + Gin" ;;
        8) wizard_state[backend]=$(get_input "Specify backend:" "non-empty") ;;
    esac

    echo ""
    echo "Database:"
    echo "[1] 🐘 PostgreSQL - Recommended"
    echo "[2] 🐬 MySQL"
    echo "[3] 🍃 MongoDB"
    echo "[4] 📦 SQLite"
    echo "[5] 🔴 Redis"
    echo "[6] 💎 Other"
    echo ""

    choice=$(get_input "Enter choice [1-6]:" "number")
    case $choice in
        1) wizard_state[database]="PostgreSQL" ;;
        2) wizard_state[database]="MySQL" ;;
        3) wizard_state[database]="MongoDB" ;;
        4) wizard_state[database]="SQLite" ;;
        5) wizard_state[database]="Redis" ;;
        6) wizard_state[database]=$(get_input "Specify database:" "non-empty") ;;
    esac
}

# Additional steps continue...
# (steps 4-8 follow similar pattern)

# Main wizard loop
main() {
    load_state "$@"

    while true; do
        case ${wizard_state[current_step]} in
            1) step1_feature_description ;;
            2) step2_app_type ;;
            3) step3_tech_stack ;;
            4) step4_architecture ;;
            5) step5_development ;;
            6) step6_confirmation ;;
            7) step7_execution ;;
            8) step8_completion; break ;;
        esac
    done

    # Clean up state file
    rm -f "$STATE_FILE"
}

main "$@"
```

**Testing:**
- Complete walkthrough for each application type
- Test back/forward navigation
- Test resume functionality
- Validate all inputs
- Ensure generated files match wizard inputs

---

### Task 2.2: Create `/speckit.help` Command
**Priority:** P0
**Effort:** 10 hours
**Impact:** High - Self-service documentation

#### Implementation Details

**Files to Create:**
```
templates/commands/help.md
scripts/bash/help-system.sh
templates/help/command-index.json
templates/help/command-details/*.md
```

**Features:**
- `/speckit.help` - Show all commands with categories
- `/speckit.help specify` - Detailed help for specific command
- `/speckit.help workflow` - Explain workflow phases
- `/speckit.help troubleshooting` - Common issues and solutions
- Interactive command search

**(Implementation details continue with full code examples...)**

---

### Task 2.3: Add Quick-Start Workflows
**Priority:** P1
**Effort:** 8 hours
**Impact:** Medium - Reduces multi-step commands

#### Implementation Details

**Files to Create:**
```
templates/commands/quickstart.md
templates/commands/full-cycle.md
scripts/bash/workflow-automation.sh
```

**Workflows:**
1. `/speckit.quickstart` - Auto: specify → validate → plan → tasks
2. `/speckit.full-cycle` - Auto: constitution → specify → plan → tasks → implement
3. `/speckit.resume` - Smart resume from last state

---

### Task 2.4: Domain-Specific Constitution Templates
**Priority:** P1
**Effort:** 12 hours
**Impact:** Medium - Better defaults for specific domains

#### Implementation Details

**Files to Create:**
```
templates/constitutions/
├── web-application.md
├── mobile-app.md
├── rest-api.md
├── microservices.md
├── machine-learning.md
├── data-pipeline.md
└── cli-tool.md
```

**Each template includes:**
- Domain-specific principles
- Technology patterns
- Common anti-patterns
- Quality gates tailored to domain
- Example projects

---

### Task 2.5: Testing & Documentation for Phase 2
**Priority:** P1
**Effort:** 10 hours
**Impact:** Ensures quality

**(Testing and documentation details...)**

---

## Phase 3: Workflow (Weeks 5-6)

**Goal**: Improve workflow continuity and quality enforcement.

### Task 3.1: Persistent Workflow State
**Priority:** P0
**Effort:** 12 hours
**Impact:** High - Enables seamless resume

#### Implementation Details

**Files to Create:**
```
.speckit-state.json (per project)
scripts/bash/state-manager.sh
templates/commands/resume.md (enhanced)
```

**State Schema:**
```json
{
  "version": "1.0.0",
  "current_feature": "001-task-management",
  "phase": "planning",
  "completed_steps": [
    {
      "command": "specify",
      "timestamp": "2025-11-07T10:30:00Z",
      "artifacts": ["specs/001-task-management/spec.md"]
    },
    {
      "command": "validate",
      "timestamp": "2025-11-07T10:35:00Z",
      "status": "passed"
    },
    {
      "command": "clarify",
      "timestamp": "2025-11-07T10:40:00Z",
      "artifacts": [".clarifications/001-task-management-questions.md"]
    }
  ],
  "next_suggested": "plan",
  "blocked_by": [],
  "last_updated": "2025-11-07T10:40:00Z",
  "token_budget": {
    "used": 45000,
    "limit": 200000,
    "percentage": 22.5
  },
  "quality_metrics": {
    "spec_validation": "passed",
    "plan_validation": "not_run",
    "checklists_complete": false
  }
}
```

**Operations:**
- Auto-save state after each command
- `/speckit.status` reads state
- `/speckit.resume` continues from state
- State validation on load

---

### Task 3.2: Configurable Quality Gates
**Priority:** P1
**Effort:** 10 hours
**Impact:** Medium - Enforce quality standards

#### Implementation Details

**Files to Create/Modify:**
```
.speckit.config.json (enhanced)
scripts/bash/quality-gates.sh
templates/commands/config.md (NEW)
```

**Configuration:**
```json
{
  "quality_gates": {
    "mode": "strict",
    "rules": {
      "spec_validation": {
        "enabled": true,
        "block_on_failure": true,
        "auto_fix": false
      },
      "plan_validation": {
        "enabled": true,
        "block_on_failure": true,
        "require_research": true
      },
      "token_budget": {
        "enabled": true,
        "warning_threshold": 150000,
        "critical_threshold": 180000,
        "block_on_critical": true
      },
      "checklist_completion": {
        "enabled": true,
        "block_implement_on_incomplete": true,
        "required_checklists": ["requirements", "architecture"]
      }
    }
  }
}
```

**Commands:**
```bash
/speckit.config set quality-gates strict
/speckit.config set quality-gates warnings
/speckit.config set quality-gates off
/speckit.config show
```

---

### Task 3.3: Automated Checklist Management
**Priority:** P1
**Effort:** 8 hours
**Impact:** Medium - Streamline quality tracking

#### Implementation Details

**Files to Create:**
```
templates/commands/quality.md (NEW)
scripts/bash/checklist-manager.sh
templates/checklists/requirements.md (enhanced)
templates/checklists/architecture.md
templates/checklists/implementation.md
templates/checklists/security.md
```

**Commands:**
```bash
/speckit.quality                    # Dashboard of all checklist status
/speckit.quality --enforce          # Block commands if incomplete
/speckit.quality --feature 001      # Show metrics for specific feature
/speckit.quality --generate         # Auto-generate checklists
```

**Quality Dashboard Output:**
```
═══════════════════════════════════════════════════════
  FEATURE QUALITY DASHBOARD
═══════════════════════════════════════════════════════

Feature: 001-task-management
Overall Score: 85/100 (B)

┌─────────────────┬───────┬───────────┬──────────┬────────┐
│ Checklist       │ Total │ Complete  │ Pending  │ Status │
├─────────────────┼───────┼───────────┼──────────┼────────┤
│ Requirements    │  12   │    12     │    0     │ ✓ PASS │
│ Architecture    │   8   │     8     │    0     │ ✓ PASS │
│ Implementation  │  15   │    12     │    3     │ ✗ FAIL │
│ Security        │   6   │     4     │    2     │ ✗ FAIL │
└─────────────────┴───────┴───────────┴──────────┴────────┘

⚠️  BLOCKING ISSUES (2)
  ❌ Implementation: 3 tasks incomplete
  ❌ Security: 2 security checks not verified

📊 QUALITY METRICS
  Code Coverage: 78% (target: 80%)
  Token Budget: 45K / 200K (22%)
  Validation: All passed
  Documentation: Complete

💡 NEXT STEPS
  1. Complete remaining implementation tasks
  2. Run security checklist verification
  3. Increase test coverage by 2%
  4. Ready for deployment after fixes

═══════════════════════════════════════════════════════
```

---

### Task 3.4: Template Versioning System
**Priority:** P2
**Effort:** 8 hours
**Impact:** Low - Future-proofing

#### Implementation Details

**Files to Create:**
```
templates/_version.json
scripts/bash/template-upgrade.sh
templates/commands/upgrade-templates.md (NEW)
```

**Version Tracking:**
```json
{
  "spec-template.md": {
    "version": "2.0.0",
    "updated": "2025-11-07",
    "changelog": [
      {
        "version": "2.0.0",
        "date": "2025-11-07",
        "changes": ["Added priority-based user story structure"]
      },
      {
        "version": "1.5.0",
        "date": "2025-10-01",
        "changes": ["Added independent test criteria"]
      }
    ]
  }
}
```

**Migration:**
```bash
/speckit.upgrade-templates               # Check for updates
/speckit.upgrade-templates --apply       # Upgrade all features
/speckit.upgrade-templates --feature 001 # Upgrade specific feature
```

---

### Task 3.5: Testing & Documentation for Phase 3
**Priority:** P1
**Effort:** 8 hours
**Impact:** Ensures quality

**(Testing and documentation details...)**

---

## Phase 4: Advanced (Weeks 7-8)

**Goal**: Enable advanced workflows and optimization.

### Task 4.1: Multi-Feature Support
**Priority:** P1
**Effort:** 12 hours
**Impact:** Medium - Team collaboration

#### Implementation Details

**Files to Create:**
```
templates/commands/features.md (NEW)
scripts/bash/feature-manager.sh
.speckit-features.json (project registry)
```

**Commands:**
```bash
/speckit.features list              # Show all features with status
/speckit.features prioritize        # Interactive prioritization
/speckit.features switch 002-auth   # Switch to different feature
/speckit.features status            # Multi-feature dashboard
/speckit.features dependencies      # Manage feature dependencies
```

**Multi-Feature Dashboard:**
```
═══════════════════════════════════════════════════════════
  PROJECT FEATURES
═══════════════════════════════════════════════════════════

Current Feature: 001-task-management

┌─────┬──────────────────────┬──────────┬──────────┬────────┐
│ #   │ Feature              │ Priority │ Progress │ Status │
├─────┼──────────────────────┼──────────┼──────────┼────────┤
│ 001 │ Task Management      │   P1     │   65%    │ ⚙ IMPL │
│ 002 │ User Authentication  │   P1     │   100%   │ ✓ DONE │
│ 003 │ Real-time Sync       │   P2     │    0%    │ ⏳ PLAN│
│ 004 │ Mobile Responsive    │   P2     │   30%    │ ⚙ SPEC │
│ 005 │ Analytics Dashboard  │   P3     │    0%    │ ⏳ TODO│
└─────┴──────────────────────┴──────────┴──────────┴────────┘

📊 PROJECT STATUS
  Features Total: 5
  Completed: 1 (20%)
  In Progress: 2 (40%)
  Planned: 2 (40%)

💡 SUGGESTIONS
  • Feature 001 ready for review (65% → 100%)
  • Feature 003 blocked by 001 completion
  • Feature 004 can proceed in parallel

═══════════════════════════════════════════════════════════
```

---

### Task 4.2: Architecture Pattern Library
**Priority:** P1
**Effort:** 14 hours
**Impact:** Medium - Better design guidance

#### Implementation Details

**Files to Create:**
```
templates/patterns/
├── layered-architecture.md
├── hexagonal-architecture.md
├── event-driven.md
├── cqrs.md
├── serverless.md
├── microservices.md
└── modular-monolith.md

templates/plan-template.md (enhanced with pattern selection)
```

**Each pattern file includes:**
- Pattern description
- When to use / when not to use
- Benefits and tradeoffs
- Implementation guide
- File structure example
- Code organization
- Testing strategy
- Common pitfalls

**Pattern Selection in Plan:**
```markdown
## Architecture Pattern Selection

**Chosen Pattern**: Layered Architecture (3-tier)

**Rationale**:
  - Standard CRUD operations fit well with layers
  - Team familiar with this pattern
  - Simplifies testing (Repository pattern)
  - Good separation of concerns

**Pattern Structure**:
```
src/
├── presentation/     # API controllers, routes
│   ├── routes/
│   └── middleware/
├── application/      # Business logic, services
│   ├── services/
│   └── use-cases/
├── domain/          # Core entities, domain logic
│   ├── models/
│   └── interfaces/
└── infrastructure/  # External concerns
    ├── database/
    ├── logging/
    └── external-apis/
```

**Layer Responsibilities**:
- Presentation: HTTP handling, input validation, response formatting
- Application: Business workflows, service orchestration
- Domain: Core business rules, entity behavior
- Infrastructure: Database access, external integrations

**Dependency Rules**:
- Outer layers depend on inner layers
- Inner layers never depend on outer layers
- Domain layer has no external dependencies
```

---

### Task 4.3: AI-Optimized Templates
**Priority:** P2
**Effort:** 10 hours
**Impact:** Low - Performance optimization

#### Implementation Details

**Files to Create:**
```
templates/commands-ai-optimized/
├── specify.ai.md
├── plan.ai.md
├── tasks.ai.md
└── implement.ai.md
```

**Optimization Strategy:**
- Reduce verbosity by 60%
- Use structured formats (JSON, YAML)
- Remove examples (link to separate files)
- Use schemas for validation
- Prioritize instructions over explanations

**Example - specify.ai.md:**
```markdown
---
description: Create feature specification (AI-optimized)
version: 2.0.0-ai
token_budget: low
---

## EXECUTION SEQUENCE (strict order)

1. Generate branch name: Extract 2-4 keywords from $ARGUMENTS
2. Check existing: git ls-remote + git branch + ls specs/
3. Run script: {SCRIPT} --number N --short-name "name" "$ARGUMENTS"
4. Parse JSON: BRANCH_NAME, SPEC_FILE
5. Load template: templates/spec-template.md
6. Fill sections: Use schema below
7. Validate: Run quality checks
8. Report: Completion status + next command

## SPEC SCHEMA (JSON-like)

```json
{
  "feature_name": "string",
  "user_stories": [
    {
      "priority": "P1|P2|P3",
      "title": "string",
      "description": "string",
      "why_this_priority": "string",
      "independent_test": "string",
      "acceptance_scenarios": ["Given...When...Then..."]
    }
  ],
  "functional_requirements": [
    {"id": "FR-001", "requirement": "string"}
  ],
  "success_criteria": [
    {"metric": "string", "target": "measurable"}
  ]
}
```

## QUALITY GATES (must pass)

- [ ] No tech details (frameworks, APIs, databases)
- [ ] All mandatory sections filled
- [ ] Success criteria measurable
- [ ] Max 3 [NEEDS CLARIFICATION] markers
- [ ] User stories prioritized

## ERROR HANDLING

| Condition | Action |
|-----------|--------|
| Empty $ARGUMENTS | ERROR "No feature description" |
| Script fails | ERROR with script output |
| Validation fails | Show issues + suggest fixes |

## NEXT COMMAND

After success: `/speckit.clarify` or `/speckit.plan`
```

---

### Task 4.4: Workflow Mode Selection
**Priority:** P2
**Effort:** 8 hours
**Impact:** Low - Flexibility for different use cases

#### Implementation Details

**Files to Create:**
```
templates/commands/mode.md (NEW)
.speckit-mode.json (project mode config)
templates/modes/
├── greenfield.json
├── feature-add.json
├── spike.json
├── bugfix.json
└── modernize.json
```

**Mode Configurations:**
```json
{
  "greenfield": {
    "name": "Greenfield Project",
    "description": "New project from scratch",
    "required_steps": [
      "constitution",
      "specify",
      "clarify",
      "plan",
      "tasks",
      "implement"
    ],
    "optional_steps": ["validate", "analyze", "checklist"],
    "quality_gates": "strict",
    "token_optimization": "standard"
  },
  "spike": {
    "name": "Quick Prototype",
    "description": "Fast experimentation, minimal planning",
    "required_steps": [
      "plan",
      "implement"
    ],
    "optional_steps": [],
    "quality_gates": "off",
    "token_optimization": "aggressive",
    "skip_documentation": true
  },
  "bugfix": {
    "name": "Bug Fix",
    "description": "Minimal workflow for bug fixes",
    "required_steps": [
      "analyze",
      "implement"
    ],
    "optional_steps": ["document"],
    "quality_gates": "warnings",
    "token_optimization": "aggressive",
    "spec_required": false
  }
}
```

**Usage:**
```bash
/speckit.mode greenfield    # Full workflow
/speckit.mode spike          # Quick prototype
/speckit.mode bugfix         # Minimal for bugs
/speckit.mode show           # Show current mode
```

---

### Task 4.5: Testing & Documentation for Phase 4
**Priority:** P1
**Effort:** 10 hours
**Impact:** Ensures quality

**(Testing and documentation details...)**

---

## Testing Strategy

### Unit Tests
- All bash scripts have corresponding test files
- Test error conditions and edge cases
- Mock external dependencies (git, APIs)

### Integration Tests
- Test complete workflows end-to-end
- Validate file creation and content
- Test command chaining

### User Acceptance Testing
- Beta test with 5-10 users per phase
- Collect feedback on usability
- Measure time-to-first-feature
- Track confusion points

### Performance Testing
- Measure token usage reduction
- Track command execution time
- Validate state persistence performance

---

## Documentation Updates

### User-Facing
- Update README.md with new commands
- Create tutorial videos for wizard
- Update quickstart guide
- Add troubleshooting section

### Developer-Facing
- Document new script libraries
- Update CONTRIBUTING.md
- Create architecture decision records (ADRs)
- Update API documentation

---

## Rollout Plan

### Phase 1: Internal Testing (1 week)
- Deploy to internal test projects
- Gather feedback from team
- Fix critical bugs
- Refine error messages

### Phase 2: Beta Release (2 weeks)
- Announce beta to community
- Gather usage metrics
- Monitor GitHub issues
- Iterate based on feedback

### Phase 3: Stable Release (1 week)
- Tag v2.0.0 release
- Update all documentation
- Announce on social media
- Create migration guide

### Phase 4: Long-term Support
- Monthly updates based on feedback
- Quarterly feature additions
- Continuous improvement

---

## Success Metrics & KPIs

### Quantitative
- Time to first feature: 30min → 10min (67% reduction)
- Workflow completion rate: 40% → 80% (100% increase)
- Token budget overruns: 25% → 5% (80% reduction)
- Support requests: Baseline → -60%

### Qualitative
- User satisfaction score: 4.5/5 target
- Net Promoter Score (NPS): 40+ target
- Feature adoption rate: 70%+ for new commands
- Documentation clarity: 4/5 target

---

## Risk Mitigation

### Technical Risks
- **Backward compatibility**: All existing workflows must continue working
  - Mitigation: Extensive integration testing
- **Performance degradation**: New features may slow down commands
  - Mitigation: Performance benchmarking, optimization
- **State corruption**: Workflow state may become inconsistent
  - Mitigation: State validation, recovery mechanisms

### User Adoption Risks
- **Learning curve**: Users resist new commands
  - Mitigation: Gradual rollout, comprehensive docs
- **Feature overload**: Too many commands confuse users
  - Mitigation: Clear categorization, wizard guidance
- **Migration friction**: Users don't upgrade
  - Mitigation: Auto-upgrade suggestions, clear benefits

---

## Maintenance Plan

### Weekly
- Monitor GitHub issues
- Respond to user questions
- Fix critical bugs

### Monthly
- Review usage analytics
- Update documentation
- Release patch versions

### Quarterly
- Major feature additions
- Performance optimization
- User feedback surveys
- Roadmap updates

---

## Appendix A: File Structure Changes

```
spec-kit/
├── src/specify_cli/
│   └── __init__.py (enhanced)
├── templates/
│   ├── commands/
│   │   ├── status.md (NEW)
│   │   ├── wizard.md (NEW)
│   │   ├── help.md (NEW)
│   │   ├── quickstart.md (NEW)
│   │   ├── full-cycle.md (NEW)
│   │   ├── quality.md (NEW)
│   │   ├── features.md (NEW)
│   │   ├── mode.md (NEW)
│   │   └── _aliases.json (NEW)
│   ├── commands-ai-optimized/ (NEW)
│   ├── constitutions/ (NEW)
│   ├── patterns/ (NEW)
│   ├── modes/ (NEW)
│   ├── wizard/ (NEW)
│   └── help/ (NEW)
├── scripts/bash/
│   ├── lib/
│   │   ├── error-messages.sh (NEW)
│   │   ├── token-estimation.sh (NEW)
│   │   └── common.sh (enhanced)
│   ├── workflow-status.sh (NEW)
│   ├── interactive-wizard.sh (NEW)
│   ├── help-system.sh (NEW)
│   ├── workflow-automation.sh (NEW)
│   ├── state-manager.sh (NEW)
│   ├── quality-gates.sh (NEW)
│   ├── checklist-manager.sh (NEW)
│   ├── template-upgrade.sh (NEW)
│   └── feature-manager.sh (NEW)
├── scripts/powershell/ (parallel implementations)
├── tests/
│   ├── phase1-core-ux/
│   ├── phase2-onboarding/
│   ├── phase3-workflow/
│   └── phase4-advanced/
└── docs/
    ├── troubleshooting.md (NEW)
    ├── command-reference.md (enhanced)
    └── workflow-modes.md (NEW)
```

---

## Appendix B: Command Reference

### New Commands Summary

| Command | Phase | Description |
|---------|-------|-------------|
| `/speckit.status` | 1 | Show workflow status and next steps |
| `/speckit.wizard` | 2 | Interactive feature creation wizard |
| `/speckit.help` | 2 | Command documentation and search |
| `/speckit.quickstart` | 2 | Automated: specify → plan → tasks |
| `/speckit.full-cycle` | 2 | Automated: full workflow |
| `/speckit.resume` | 3 | Resume from last state |
| `/speckit.quality` | 3 | Quality dashboard and metrics |
| `/speckit.config` | 3 | Configure quality gates |
| `/speckit.features` | 4 | Multi-feature management |
| `/speckit.mode` | 4 | Set workflow mode |
| `/speckit.upgrade-templates` | 3 | Upgrade to latest templates |

### Command Aliases

| Alias | Target | Description |
|-------|--------|-------------|
| `/speckit.ask-questions` | `clarify` | Ask clarifying questions |
| `/speckit.token-usage` | `budget` | View token budget |
| `/speckit.compress-context` | `prune` | Compress session |
| `/speckit.search-code` | `find` | Search code semantically |
| `/speckit.debug-error` | `error-context` | Debug with spec context |
| `/speckit.check-quality` | `validate` | Validate artifacts |
| `/speckit.what-next` | `status` | Show next step |

---

## End of Implementation Plan

**Next Steps:**
1. Review and approve this plan
2. Set up project board with tasks
3. Assign developers to phases
4. Begin Phase 1 implementation
5. Weekly progress reviews

**Questions or Feedback:**
- Open GitHub issue for discussion
- Tag @maintainers for review
- Join community Discord for real-time discussion
