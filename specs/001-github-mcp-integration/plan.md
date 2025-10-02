# Implementation Plan: GitHub MCP Integration for Spec-Driven Development

**Branch**: `001-github-mcp-integration` | **Date**: 2025-10-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-github-mcp-integration/spec.md`

## Execution Flow (/plan command scope)

1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+API)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:

- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

This feature integrates GitHub MCP (Model Context Protocol) throughout the Spec-Driven Development workflow, enabling specifications to become tracked GitHub issues with semantic labels, planning to create draft PRs with plan content, tasks to update PR descriptions with checkboxes, and implementation to mark PRs ready for review while updating the project constitution. The integration provides complete traceability from idea to delivery while keeping documentation synchronized through automated GitHub operations.

Primary requirements:
- Update all command templates (specify, plan, tasks, implement) with GitHub MCP operations
- Implement AI-powered branch name generation in specify command
- Create/update GitHub issues and PRs with proper formatting, labels, and linking
- Synchronize both GitHub Copilot-specific prompts and generic agent templates
- Update spec template structure to prioritize user scenarios over requirements
- Provide error handling for GitHub API failures

## Technical Context

**Language/Version**: Python 3.11+ (for Specify CLI), Markdown (for templates)
**Primary Dependencies**: GitHub MCP tools (built into AI agents), Git, GitHub API
**Storage**: Git repository, GitHub issues/PRs for tracking
**Testing**: Manual validation of workflow phases, GitHub API integration tests
**Target Platform**: Cross-platform (Windows/macOS/Linux) - supports bash and PowerShell
**Project Type**: CLI tool with template system (single project structure)
**Performance Goals**: Fast template generation (<1s), reliable GitHub API operations
**Constraints**: Must work across 11+ AI agents, maintain backward compatibility with existing projects
**Scale/Scope**: Update 7 command templates, sync 2 template locations, document integration patterns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification as Source of Truth (NON-NEGOTIABLE)

- [x] Feature preserves specifications as primary artifacts
- [x] Templates remain tech-agnostic (no implementation details in spec templates)
- [x] User-centric language maintained in specifications
- [x] Living documentation approach supported (specs evolve with implementation)
- [x] Constitution principles guide all template updates

### II. Multi-Agent Compatibility (NON-NEGOTIABLE)

- [x] Changes work across all 11+ supported AI agents
- [x] Format adaptation maintained (Markdown vs TOML where appropriate)
- [x] Directory conventions preserved (`.github/prompts/`, `.claude/commands/`, etc.)
- [x] Placeholder patterns supported (`$ARGUMENTS`, `{{args}}`, etc.)
- [x] No vendor lock-in introduced
- [x] Both `.github/prompts/*.prompt.md` and `templates/commands/*.md` synchronized

### III. Template-Driven Consistency (REQUIRED)

- [x] Standard template structure maintained
- [x] Execution flows clearly defined in updated templates
- [x] Validation gates included (GitHub API error handling)
- [x] Explicit sections for GitHub operations added
- [x] Context preservation maintained across workflow phases
- [x] Template structure updated to prioritize user scenarios (spec template)

### IV. Test-Driven Development Integration (NON-NEGOTIABLE)

- [x] TDD workflow preserved in tasks template
- [x] Tests-first approach maintained
- [x] No impact on existing TDD gates
- [x] GitHub MCP operations don't bypass TDD requirements

### V. Cross-Platform Support (REQUIRED)

- [x] Works on Windows, macOS, and Linux
- [x] Both bash and PowerShell scripts maintained
- [x] No platform-specific dependencies introduced
- [x] Git operations remain cross-platform compatible

### VI. Workflow Phase Tracking (NEW REQUIREMENT)

- [x] GitHub issue labels track workflow phases (`Specification`, `Plan`, `Implementation`)
- [x] PR descriptions progressively updated through phases
- [x] Issue-PR linking maintained with "Fixes #" keyword
- [x] Draft PR status properly managed
- [x] Constitution updates automated during implementation phase

## Project Structure

### Documentation (this feature)

```plaintext
specs/001-github-mcp-integration/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
└── contracts/           # Phase 1 output (/plan command)
    └── github-mcp-integration.md
```

### Source Code (repository root)

```plaintext
# Spec Kit CLI and Templates Structure
src/
└── specify_cli/
    └── __init__.py                # Main CLI entry point

templates/
├── spec-template.md               # Generic spec template (to be updated)
├── plan-template.md               # Generic plan template
├── tasks-template.md              # Generic tasks template
└── commands/                      # Generic command templates (to be updated)
    ├── constitution.md
    ├── specify.md                 # Needs GitHub MCP integration
    ├── plan.md                    # Needs GitHub MCP integration
    ├── tasks.md                   # Needs GitHub MCP integration
    ├── implement.md               # Needs GitHub MCP integration
    ├── analyze.md
    └── clarify.md

.github/
└── prompts/                       # GitHub Copilot-specific prompts (reference implementation)
    ├── specify.prompt.md          # Already has GitHub MCP integration
    ├── plan.prompt.md             # Already has GitHub MCP integration
    ├── tasks.prompt.md            # Already has GitHub MCP integration
    └── implement.prompt.md        # Already has GitHub MCP integration

.specify/
├── memory/
│   └── constitution.md            # Project constitution
├── templates/                     # Project-specific templates
│   ├── spec-template.md          # Already updated with user scenarios first
│   ├── plan-template.md
│   ├── tasks-template.md
│   └── commands/
│       └── [various .md files]
└── scripts/
    ├── bash/
    │   ├── create-new-feature.sh
    │   ├── setup-plan.sh
    │   └── update-agent-context.sh
    └── powershell/
        ├── create-new-feature.ps1
        ├── setup-plan.ps1
        └── update-agent-context.ps1

docs/
└── [documentation files]         # May need updates for GitHub MCP integration
```

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: Single project structure (CLI tool with template system). This feature modifies existing template files in `templates/commands/` and `.github/prompts/` directories, synchronizing GitHub MCP operations across both locations. No new source code structure needed - only template content updates.

## Phase 0: Outline & Research ✓ COMPLETE

**Research completed** in `research.md` covering:

1. **GitHub MCP Capabilities**: Use GitHub MCP tools through AI agents for issue/PR management
2. **Template Synchronization**: Maintain two locations (`.github/prompts/` and `templates/`) with identical GitHub MCP logic
3. **Label Schema**: Semantic labels with backticks for phase (`Specification`, `Plan`, `Implementation`) and type tracking
4. **PR Formatting**: Structured format with icons, progressive content updates, and issue linking
5. **Branch Name Generation**: AI-powered kebab-case generation from feature descriptions
6. **Constitution Updates**: Automated updates during `/implement` phase
7. **Error Handling**: Graceful degradation with clear recovery instructions
8. **Cross-Platform**: Maintains existing bash/PowerShell support

**Key Decisions**:
- Use GitHub MCP through AI agents (no additional auth needed)
- Synchronize `.github/prompts/` and `templates/commands/` locations
- Apply semantic labels for workflow tracking
- Implement AI-powered branch naming
- Auto-update constitution during implementation

**Output**: ✓ research.md completed with all technical decisions documented

## Phase 1: Design & Contracts ✓ COMPLETE

**Entities defined** in `data-model.md`:

1. **GitHub Issue** - Feature specification tracking with labels
2. **Pull Request** - Draft and ready states with progressive content
3. **Label** - Phase and type labels for workflow tracking
4. **Command Template** - Template files with GitHub MCP operations
5. **Feature Branch** - AI-generated branch names with feature numbers
6. **Constitution Document** - Project principles and feature history

**Contracts created** in `contracts/github-mcp-integration.md`:

- `/specify` command: Issue creation, label application, branch naming
- `/plan` command: Draft PR creation, issue linking, label updates
- `/tasks` command: PR description updates with checkboxes
- `/implement` command: Progressive updates, ready status, constitution updates
- Template synchronization contract
- Error handling contract

**Validation scenarios** in `quickstart.md`:

- Scenario 1: Specify phase issue creation
- Scenario 2: Plan phase draft PR creation
- Scenario 3: Tasks phase PR description update
- Scenario 4: Implement phase progressive updates
- Scenario 5: Error handling validation
- Scenario 6: End-to-end workflow
- Scenario 7: Multi-agent compatibility

**Agent context updated**: ✓ GitHub Copilot context file updated with new technologies

**Output**: ✓ data-model.md, contracts/github-mcp-integration.md, quickstart.md, agent context file

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

The `/tasks` command will generate implementation tasks based on the functional requirements from spec.md and design artifacts from Phase 1. Tasks will be organized into logical phases following TDD principles.

**Expected Task Categories**:

1. **Template Synchronization Tasks** [P]
   - Compare `.github/prompts/specify.prompt.md` with `templates/commands/specify.md`
   - Identify GitHub MCP operations to add
   - Repeat for plan, tasks, implement commands
   - Each template update can be done in parallel

2. **Template Update Tasks** (sequential per file)
   - Update `templates/commands/specify.md` with:
     * Branch name generation logic
     * Issue creation operations
     * Label application logic
     * Error handling
   - Update `templates/commands/plan.md` with:
     * Git commit/push operations
     * Draft PR creation
     * Issue linking
     * Label updates
   - Update `templates/commands/tasks.md` with:
     * PR description fetch
     * Content append operations
     * Checkbox formatting
   - Update `templates/commands/implement.md` with:
     * Progressive checkbox updates
     * Ready status change
     * Constitution update logic
     * Label updates

3. **Spec Template Update Tasks**
   - Update `templates/spec-template.md` to match `.specify/templates/spec-template.md`
   - Ensure "User Scenarios & Testing" section comes first
   - Preserve all other template structure

4. **Documentation Tasks** [P]
   - Update CONTRIBUTING.md with template synchronization requirements
   - Update AGENTS.md if needed for GitHub MCP integration notes
   - Update README.md with workflow phase tracking explanation
   - Create or update docs/github-mcp-integration.md with integration guide

5. **Validation Tasks**
   - Manual validation using quickstart.md scenarios
   - Test each command template across multiple agents
   - Verify error handling paths
   - Confirm cross-platform compatibility

**Ordering Strategy**:

1. **Phase 0**: Documentation and planning (establish baseline)
2. **Phase 1**: Template analysis and comparison [P]
3. **Phase 2**: Template updates (specify → plan → tasks → implement in sequence)
4. **Phase 3**: Spec template update
5. **Phase 4**: Documentation updates [P]
6. **Phase 5**: Validation and testing

**Parallel Execution Markers**:
- Template analysis can be done in parallel [P]
- Documentation updates can be done in parallel [P]
- Template implementation must be sequential (tests for each before next)

**TDD Approach**:
- No code tests needed (template changes only)
- Validation scenarios in quickstart.md serve as acceptance tests
- Manual testing required for GitHub MCP operations
- Each template update validated before proceeding to next

**Estimated Output**: 20-25 numbered tasks covering:
- 4-6 template synchronization analysis tasks
- 8-10 template update tasks (2-3 per command file)
- 2-3 spec template update tasks
- 4-5 documentation tasks
- 3-4 validation tasks

**Dependencies**:
- Template updates depend on analysis tasks
- Documentation depends on template updates
- Validation depends on all updates complete

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md with detailed breakdown)
**Phase 4**: Implementation (execute tasks.md, updating templates and documentation)
**Phase 5**: Validation (execute quickstart.md scenarios, verify across agents)

## Complexity Tracking

*No constitutional violations - all checks passed*

This feature maintains all constitutional principles:
- Specification as source of truth ✓
- Multi-agent compatibility ✓
- Template-driven consistency ✓
- TDD integration ✓
- Cross-platform support ✓
- New: Workflow phase tracking ✓

No complexity deviations to document.

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:

- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

**Artifacts Generated**:
- [x] research.md - Technical decisions and research findings
- [x] data-model.md - Entity definitions and relationships
- [x] contracts/github-mcp-integration.md - Operation contracts and requirements
- [x] quickstart.md - Validation scenarios and testing guide
- [x] .github/copilot-instructions.md - Updated agent context

**Next Steps**:
1. Commit and push all planning artifacts
2. Create draft Pull Request linking to issue #709
3. Update issue labels: Remove `Specification`, add `Plan`
4. Run `/tasks` command to generate implementation tasks

---
*Based on Constitution - See `.specify/memory/constitution.md`*

*This checklist is updated during execution flow*

**Phase Status**:

- [ ] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [ ] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution - See `.specify/memory/constitution.md`*
