# Data Model: GitHub MCP Integration

**Feature**: 001-github-mcp-integration  
**Date**: 2025-10-02  
**Phase**: 1 - Design & Contracts

## Overview

This data model defines the key entities involved in GitHub MCP integration for the Spec-Driven Development workflow. These entities represent GitHub resources (Issues, PRs, Labels) and workflow artifacts (Templates, Commands) that are manipulated during the SDD process.

## Core Entities

### 1. GitHub Issue

Represents a feature specification tracked in GitHub's issue tracking system.

**Attributes**:
- `number`: Integer - GitHub issue number (auto-assigned)
- `title`: String - Formatted as `<Icon> [Type]: <Feature name>`
- `body`: String - Spec content starting from "Primary User Story" section
- `labels`: Array<Label> - Semantic labels for phase and type tracking
- `state`: Enum - `open` | `closed`
- `branch_name`: String - Feature branch mentioned in description
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- Title MUST match pattern: `<Icon> [Type]: <Description>`
- Body MUST start with "## User Scenarios & Testing" (first two headers removed from spec)
- Body MUST include "**Feature Branch**: `branch-name`" line
- Labels MUST include one phase label and one type label
- Labels MUST be formatted with backticks in documentation

**State Transitions**:
- `open` → `closed` (when PR is merged)

**Relationships**:
- Created by: `/specify` command
- Links to: Feature specification file (spec.md)
- Links to: Feature branch
- Links to: Pull Request (via "Fixes #" keyword)

### 2. Pull Request

Represents a draft or ready-for-review PR containing feature implementation.

**Attributes**:
- `number`: Integer - GitHub PR number (auto-assigned)
- `title`: String - Same format as issue title
- `body`: String - Structured description with progressive updates
- `labels`: Array<Label> - Semantic labels matching issue
- `state`: Enum - `open` | `closed`
- `draft`: Boolean - True until `/implement` marks ready
- `base`: String - Target branch (typically `main`)
- `head`: String - Feature branch name
- `issue_number`: Integer - Linked issue number
- `created_at`: DateTime
- `updated_at`: DateTime

**Validation Rules**:
- Title MUST match issue title format
- Body MUST contain: summary paragraph, plan content, tasks content (when added), "- Fixes #<issue-number>"
- Body MUST NOT have title heading before first paragraph
- Draft status MUST be true until `/implement` completes
- Base branch MUST be repository default branch

**State Transitions**:
- Draft → Ready (when `/implement` completes)
- `open` → `closed` (when merged)

**Progressive Content Updates**:
1. `/plan`: Initial creation with summary + plan.md content
2. `/tasks`: Append tasks.md content with checkboxes
3. `/implement`: Update checkboxes, mark ready for review

**Relationships**:
- Created by: `/plan` command
- Updated by: `/tasks`, `/implement` commands
- Links to: GitHub Issue (via "Fixes #" keyword)
- Links to: Feature branch
- Contains: plan.md, tasks.md content

### 3. Label

Represents semantic labels for tracking workflow phase and change type.

**Attributes**:
- `name`: String - Label name (with backticks in documentation)
- `description`: String - Label purpose
- `color`: String - Hex color code
- `type`: Enum - `phase` | `semantic`

**Phase Labels** (mutually exclusive):
- `Specification` - Issue created, spec written
- `Plan` - Plan created, design artifacts generated
- `Implementation` - Implementation in progress or complete

**Type Labels** (change type for semantic versioning):
- `Docs` - Documentation changes only
- `Fix` - Bug fix (patch or minor)
- `Patch` - Small fix, no new features
- `Minor` - New feature, backward compatible
- `Major` - Breaking change

**Validation Rules**:
- Phase labels MUST be mutually exclusive (only one active)
- Type labels SHOULD have one primary label
- Labels MUST be formatted with backticks when referenced in documentation

**State Transitions**:
- `/specify`: Add `Specification` + type label to issue
- `/plan`: Remove `Specification`, add `Plan` on issue
- `/implement`: Add `Implementation` to issue

**Relationships**:
- Applied to: GitHub Issues and Pull Requests
- Managed by: Command templates

### 4. Command Template

Represents a command file that executes a workflow phase.

**Attributes**:
- `name`: String - Command name (e.g., "specify", "plan", "tasks", "implement")
- `path`: String - File path in templates or agent directory
- `format`: Enum - `markdown` | `toml`
- `agent_type`: Enum - `copilot` | `claude` | `gemini` | `cursor` | `qwen` | `opencode` | `generic`
- `has_github_mcp`: Boolean - Whether GitHub MCP operations are included
- `description`: String - Command purpose
- `arguments`: String - Argument pattern (`$ARGUMENTS` or `{{args}}`)

**Generic Template Locations**:
- `templates/commands/constitution.md`
- `templates/commands/specify.md` → Needs GitHub MCP
- `templates/commands/plan.md` → Needs GitHub MCP
- `templates/commands/tasks.md` → Needs GitHub MCP
- `templates/commands/implement.md` → Needs GitHub MCP
- `templates/commands/analyze.md`
- `templates/commands/clarify.md`

**GitHub Copilot Template Locations** (reference implementation):
- `.github/prompts/specify.prompt.md` → Has GitHub MCP
- `.github/prompts/plan.prompt.md` → Has GitHub MCP
- `.github/prompts/tasks.prompt.md` → Has GitHub MCP
- `.github/prompts/implement.prompt.md` → Has GitHub MCP

**Validation Rules**:
- Generic templates and Copilot templates MUST have synchronized GitHub MCP operations
- GitHub MCP operations MUST include error handling
- Commands MUST support argument patterns for user input

**Relationships**:
- Copied to: Agent-specific directories during project initialization
- Executed by: AI agents during SDD workflow
- References: Other artifacts (spec.md, plan.md, tasks.md)

### 5. Feature Branch

Represents a Git branch for feature development.

**Attributes**:
- `name`: String - Format: `###-kebab-case-description`
- `feature_number`: Integer - Auto-incremented number (###)
- `description`: String - Kebab-case feature description (AI-generated)
- `base_branch`: String - Parent branch (typically `main`)
- `created_at`: DateTime

**Validation Rules**:
- Name MUST match pattern: `\d{3}-[a-z0-9-]+`
- Feature number MUST be auto-incremented from existing branches
- Description MUST be 2-4 words in kebab-case
- Description MUST be AI-generated from feature description

**Relationships**:
- Created by: `create-new-feature.ps1` script
- Referenced in: GitHub Issue description
- Contains: Feature specification and implementation
- Linked to: Pull Request

### 6. Constitution Document

Represents the project's constitutional principles and implemented features.

**Attributes**:
- `path`: String - `.specify/memory/constitution.md`
- `version`: String - Constitution version
- `principles`: Array<Principle> - Core principles
- `implemented_features`: Array<Feature> - Historical feature record
- `last_updated`: DateTime

**Validation Rules**:
- MUST be updated during `/implement` phase
- Updates MUST describe newly implemented functionality
- Updates MUST maintain historical record
- MUST remain single source of truth for project capabilities

**Relationships**:
- Updated by: `/implement` command
- Referenced by: All command templates for constitution checks
- Contains: Project principles, capabilities, feature history

## Entity Relationships Diagram

```
┌─────────────────┐
│ GitHub Issue    │
│ #709            │◄────────┐
│ Specification   │         │
└────────┬────────┘         │
         │                  │
         │ Fixes #          │
         │                  │
         ▼                  │
┌─────────────────┐         │
│ Pull Request    │─────────┘
│ #711 (Draft)    │
│ Plan            │
└────────┬────────┘
         │
         │ Contains
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│ Feature Branch  │◄─────│ Spec Files      │
│ 001-github-mcp  │      │ - spec.md       │
└────────┬────────┘      │ - plan.md       │
         │               │ - tasks.md      │
         │               └─────────────────┘
         │
         │ Tracks with
         │
         ▼
┌─────────────────┐
│ Labels          │
│ Specification   │
│ Minor           │
└─────────────────┘
```

## Workflow State Machine

```
[/specify] → Issue created with Specification label
            ↓
[/plan]    → PR created (draft), Issue label: Specification → Plan
            ↓
[/tasks]   → PR updated with tasks.md content
            ↓
[/implement] → PR updated with checkmarks, marked ready, Issue label: + Implementation
            ↓
[Merge]    → PR closed, Issue closed
```

## Data Flow

### Specify Phase
```
User Input → AI Analysis → Branch Name Generation
                         → Spec File Creation (spec.md)
                         → Issue Creation (GitHub MCP)
                         → Labels Applied
```

### Plan Phase
```
Spec File → Planning → Design Artifacts (research.md, data-model.md, contracts/, quickstart.md)
                    → Git Commit & Push
                    → Draft PR Creation (GitHub MCP)
                    → Issue Labels Update (GitHub MCP)
```

### Tasks Phase
```
Plan Artifacts → Task Generation (tasks.md)
              → PR Description Update (GitHub MCP)
```

### Implement Phase
```
Tasks Execution → Progressive Checkmarks → PR Description Update (GitHub MCP)
                                        → PR Ready for Review (GitHub MCP)
                                        → Constitution Update
                                        → Issue Labels Update (GitHub MCP)
```

## Constraints and Invariants

1. **Phase Label Uniqueness**: Only one phase label active on issue at a time
2. **PR-Issue Linking**: Every PR MUST link to exactly one issue via "Fixes #"
3. **Branch Naming**: Feature branches MUST be unique and follow `###-kebab-case` pattern
4. **Template Synchronization**: Generic and Copilot templates MUST have identical GitHub MCP logic
5. **Draft Status**: PRs MUST remain draft until `/implement` completes
6. **Constitution Updates**: MUST occur during `/implement` phase, not earlier
7. **Error Handling**: All GitHub MCP operations MUST handle API failures gracefully

## Implementation Notes

- GitHub MCP operations are executed through AI agent tooling
- No direct GitHub API calls or authentication management needed
- Template updates propagate to agent-specific directories during project initialization
- Label formatting with backticks is for documentation only, not in actual GitHub labels
- Constitution updates are append-only to maintain historical record
