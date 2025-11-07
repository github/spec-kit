#!/usr/bin/env pwsh
#requires -version 5.1

<#
.SYNOPSIS
    Enhanced error message library for PowerShell
.DESCRIPTION
    Provides context-aware, actionable error messages with fix suggestions
#>

function Write-ErrorMissingSpecSection {
    param(
        [string]$Section,
        [string]$FilePath
    )

    Write-Host @"
❌ Error: Specification validation failed

Issue: Missing mandatory section "$Section"
  Location: $FilePath

Why this matters:
  The "$Section" section is required for planning and implementation.
  Without it, the AI agent cannot generate a complete implementation plan.

How to fix:
  1. Open the file: $FilePath
  2. Add the missing section: ## $Section
  3. Fill in the required content (see template for guidance)
  4. Run validation again: /speckit.validate --spec

Need help?
  • See template: templates/spec-template.md
  • Run: /speckit.help specify
  • Example: examples/specify.md

💡 Pro tip: Run /speckit.validate --fix to auto-add missing sections
"@ -ForegroundColor Red
}

function Write-ErrorImplementationDetailsInSpec {
    param(
        [string]$FilePath,
        [int]$LineNumber,
        [string]$OffendingText
    )

    Write-Host @"
❌ Error: Implementation details found in specification

Issue: Specification contains technical implementation details
  Location: ${FilePath}:${LineNumber}
  Found: "$OffendingText"

Why this matters:
  Specifications should describe WHAT and WHY, not HOW.
  Including implementation details makes the spec fragile and
  ties it to specific technologies.

How to fix:
  1. Open: $FilePath
  2. Go to line: $LineNumber
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
"@ -ForegroundColor Red
}

function Write-ErrorTokenBudgetExceeded {
    param(
        [int]$UsedTokens,
        [int]$BudgetLimit,
        [string]$SuggestedAction
    )

    $overage = $UsedTokens - $BudgetLimit
    $overagePct = [math]::Floor(($overage / $BudgetLimit) * 100)

    Write-Host @"
⚠️  Warning: Token budget limit exceeded

Current usage: ${UsedTokens}K tokens
Budget limit: ${BudgetLimit}K tokens
Overage: ${overage}K tokens (${overagePct}% over)

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
  $SuggestedAction

💡 Pro tip: Run /speckit.budget before starting implementation
  to catch token issues early.
"@ -ForegroundColor Yellow
}

function Write-ErrorFeatureNotFound {
    param(
        [string]$FeatureRef,
        [string]$AvailableFeatures
    )

    Write-Host @"
❌ Error: Feature not found

Requested feature: $FeatureRef

Available features:
$AvailableFeatures

Possible causes:
  1. Feature doesn't exist yet
  2. Not on feature branch
  3. Wrong feature number or name

How to fix:
  • List all features: /speckit.features list
  • Switch to feature: git checkout $FeatureRef
  • Create new feature: /speckit.specify "Your feature description"
  • Check current status: /speckit.status

💡 Pro tip: Use tab completion for feature names (if supported by your shell)
"@ -ForegroundColor Red
}

function Write-ErrorGitNotInitialized {
    Write-Host @"
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
    `$env:SPECIFY_FEATURE = "001-my-feature"

    Then proceed with /speckit.specify

Need help?
  • See: docs/installation.md#git-setup
  • Run: /speckit.help setup
"@ -ForegroundColor Red
}

function Write-ErrorSpecValidationFailed {
    param(
        [int]$Issues,
        [string]$FilePath
    )

    Write-Host @"
❌ Error: Specification validation failed

Found $Issues validation issues in: $FilePath

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
  • Manual edit: $FilePath

Next steps:
  1. Run /speckit.validate --spec --fix (attempts auto-repair)
  2. Review and adjust auto-fixes
  3. Run /speckit.validate --spec again
  4. Proceed to /speckit.plan when validation passes

💡 Pro tip: Validate early and often to catch issues quickly
"@ -ForegroundColor Red
}

function Write-ErrorPlanValidationFailed {
    param(
        [int]$Issues,
        [string]$FilePath
    )

    Write-Host @"
❌ Error: Implementation plan validation failed

Found $Issues validation issues in: $FilePath

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
  • Manual edit: $FilePath

Next steps:
  1. Add missing sections to plan
  2. Run /speckit.validate --plan again
  3. Proceed to /speckit.tasks when validation passes

💡 Pro tip: Use /speckit.plan [tech stack] to regenerate with fixes
"@ -ForegroundColor Red
}

function Write-ErrorTasksValidationFailed {
    param(
        [int]$Issues,
        [string]$FilePath
    )

    Write-Host @"
❌ Error: Task breakdown validation failed

Found $Issues validation issues in: $FilePath

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
  • Manual edit: $FilePath

Next steps:
  1. Fix validation issues
  2. Run /speckit.validate --tasks again
  3. Proceed to /speckit.implement when validation passes

💡 Pro tip: Good tasks are specific, small, and have clear file paths
"@ -ForegroundColor Red
}

function Write-ErrorCommandNotFound {
    param(
        [string]$Command,
        [string]$AvailableCommands
    )

    Write-Host @"
❌ Error: Command not found

Unknown command: $Command

Available commands:
$AvailableCommands

Did you mean:
  • /speckit.status - Show workflow status
  • /speckit.specify - Create specification
  • /speckit.help - Get help with commands

How to fix:
  • List all commands: /speckit.help
  • Search commands: /speckit.help search [keyword]
  • Get command help: /speckit.help [command-name]

💡 Pro tip: Most commands follow the pattern /speckit.[action]
"@ -ForegroundColor Red
}

function Write-ErrorPrerequisitesMissing {
    param(
        [string]$Command,
        [string]$MissingPrereqs
    )

    Write-Host @"
❌ Error: Prerequisites missing for $Command

Cannot run $Command because:
$MissingPrereqs

Why this matters:
  Each command depends on previous steps being complete.
  Running commands out of order causes errors.

How to fix:
  1. Check current status: /speckit.status
  2. Complete missing prerequisites
  3. Try $Command again

Typical workflow order:
  1. /speckit.constitution
  2. /speckit.specify
  3. /speckit.plan
  4. /speckit.tasks
  5. /speckit.implement

💡 Pro tip: Run /speckit.status to see what's needed next
"@ -ForegroundColor Red
}

function Write-ErrorFileNotFound {
    param(
        [string]$FilePath,
        [string]$Context
    )

    Write-Host @"
❌ Error: File not found

Cannot find: $FilePath
Context: $Context

Possible causes:
  1. File was never created
  2. Wrong file path
  3. Working in wrong directory
  4. File was deleted

How to fix:
  • Check current directory: Get-Location
  • List files: Get-ChildItem
  • Verify feature directory: Get-ChildItem specs/
  • Check if on correct branch: git branch

💡 Pro tip: Run /speckit.status to verify your current location
"@ -ForegroundColor Red
}

# Export functions (PowerShell module style)
Export-ModuleMember -Function @(
    'Write-ErrorMissingSpecSection',
    'Write-ErrorImplementationDetailsInSpec',
    'Write-ErrorTokenBudgetExceeded',
    'Write-ErrorFeatureNotFound',
    'Write-ErrorGitNotInitialized',
    'Write-ErrorSpecValidationFailed',
    'Write-ErrorPlanValidationFailed',
    'Write-ErrorTasksValidationFailed',
    'Write-ErrorCommandNotFound',
    'Write-ErrorPrerequisitesMissing',
    'Write-ErrorFileNotFound'
)
