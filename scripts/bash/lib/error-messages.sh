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
  3. Fill in the required content (see template for guidance)
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
  • Review: spec-driven.md for philosophy

💡 Pro tip: Think "product requirements" not "technical design"
EOF
}

error_token_budget_exceeded() {
    local used_tokens="$1"
    local budget_limit="$2"
    local suggested_action="$3"

    local overage=$((used_tokens - budget_limit))
    local overage_pct=$((overage * 100 / budget_limit))

    cat <<EOF
⚠️  Warning: Token budget limit exceeded

Current usage: ${used_tokens}K tokens
Budget limit: ${budget_limit}K tokens
Overage: ${overage}K tokens (${overage_pct}% over)

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
  • Switch to feature: git checkout $feature_ref
  • Create new feature: /speckit.specify "Your feature description"
  • Check current status: /speckit.status

💡 Pro tip: Use tab completion for feature names (if supported by your shell)
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
  1. Run /speckit.validate --spec --fix (attempts auto-repair)
  2. Review and adjust auto-fixes
  3. Run /speckit.validate --spec again
  4. Proceed to /speckit.plan when validation passes

💡 Pro tip: Validate early and often to catch issues quickly
EOF
}

error_plan_validation_failed() {
    local issues="$1"
    local file_path="$2"

    cat <<EOF
❌ Error: Implementation plan validation failed

Found $issues validation issues in: $file_path

Common issues and fixes:

1. Missing technology stack section
   Fix: Add ## Technology Stack with specific choices
   Include: Frontend, Backend, Database, Other tools

2. No architectural pattern specified
   Fix: Choose and document pattern (Layered, Hexagonal, etc.)
   See: templates/patterns/ for options

3. Missing constitutional compliance checks
   Fix: Verify plan follows constitution principles
   Run: /speckit.validate --plan --check-constitution

4. Incomplete research for technology choices
   Fix: Document rationale for each tech choice
   Include alternatives considered

Quick actions:
  • See plan template: templates/plan-template.md
  • Review patterns: templates/patterns/
  • Manual edit: $file_path

Next steps:
  1. Add missing sections to plan
  2. Run /speckit.validate --plan again
  3. Proceed to /speckit.tasks when validation passes

💡 Pro tip: Use /speckit.plan [tech stack] to regenerate with fixes
EOF
}

error_tasks_validation_failed() {
    local issues="$1"
    local file_path="$2"

    cat <<EOF
❌ Error: Task breakdown validation failed

Found $issues validation issues in: $file_path

Common issues and fixes:

1. Too few tasks (minimum 5 recommended)
   Fix: Break down larger tasks into smaller steps
   Each task should be completable in <2 hours

2. Tasks not organized by user story
   Fix: Group tasks under user story headers
   Use format: ## Phase N: User Story [N] - [Title]

3. No parallel markers [P] for independent tasks
   Fix: Mark tasks that can run in parallel
   Example: - [ ] T001 [P] [US1] Create model...

4. Missing file paths in task descriptions
   Fix: Include specific file paths
   Example: - [ ] T002 Create UserService in src/services/user.ts

Quick actions:
  • Regenerate tasks: /speckit.tasks
  • See template: templates/tasks-template.md
  • Manual edit: $file_path

Next steps:
  1. Fix validation issues
  2. Run /speckit.validate --tasks again
  3. Proceed to /speckit.implement when validation passes

💡 Pro tip: Good tasks are specific, small, and have clear file paths
EOF
}

error_command_not_found() {
    local command="$1"
    local available_commands="$2"

    cat <<EOF
❌ Error: Command not found

Unknown command: $command

Available commands:
$available_commands

Did you mean:
  • /speckit.status - Show workflow status
  • /speckit.specify - Create specification
  • /speckit.help - Get help with commands

How to fix:
  • List all commands: /speckit.help
  • Search commands: /speckit.help search [keyword]
  • Get command help: /speckit.help [command-name]

💡 Pro tip: Most commands follow the pattern /speckit.[action]
EOF
}

error_prerequisites_missing() {
    local command="$1"
    local missing_prereqs="$2"

    cat <<EOF
❌ Error: Prerequisites missing for $command

Cannot run $command because:
$missing_prereqs

Why this matters:
  Each command depends on previous steps being complete.
  Running commands out of order causes errors.

How to fix:
  1. Check current status: /speckit.status
  2. Complete missing prerequisites
  3. Try $command again

Typical workflow order:
  1. /speckit.constitution
  2. /speckit.specify
  3. /speckit.plan
  4. /speckit.tasks
  5. /speckit.implement

💡 Pro tip: Run /speckit.status to see what's needed next
EOF
}

error_file_not_found() {
    local file_path="$1"
    local context="$2"

    cat <<EOF
❌ Error: File not found

Cannot find: $file_path
Context: $context

Possible causes:
  1. File was never created
  2. Wrong file path
  3. Working in wrong directory
  4. File was deleted

How to fix:
  • Check current directory: pwd
  • List files: ls -la
  • Verify feature directory: ls specs/
  • Check if on correct branch: git branch

💡 Pro tip: Run /speckit.status to verify your current location
EOF
}

# Export functions
export -f error_missing_spec_section
export -f error_implementation_details_in_spec
export -f error_token_budget_exceeded
export -f error_feature_not_found
export -f error_git_not_initialized
export -f error_spec_validation_failed
export -f error_plan_validation_failed
export -f error_tasks_validation_failed
export -f error_command_not_found
export -f error_prerequisites_missing
export -f error_file_not_found
