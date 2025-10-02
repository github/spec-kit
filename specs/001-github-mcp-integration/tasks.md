# Tasks: GitHub MCP Integration for Spec-Driven Development

**Input**: Design documents from `specs/001-github-mcp-integration/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow

This document provides the complete task breakdown for implementing GitHub MCP integration into the Spec-Driven Development workflow. Tasks are organized by phase and marked [P] when they can be executed in parallel.

## Path Conventions

- **Project type**: CLI tool + template system (single project structure)
- **Templates**: `templates/commands/*.md` (generic agent templates)
- **Prompts**: `.github/prompts/*.prompt.md` (GitHub Copilot-specific)
- **Documentation**: Root-level docs and specs/

## Phase 3.1: Setup & Validation

- [x] T001: Verify current state of templates and prompts
  - Read all files in `templates/commands/` directory
  - Read all files in `.github/prompts/` directory
  - Compare GitHub MCP operations between locations
  - Document differences for synchronization
  - **Files**: `templates/commands/*.md`, `.github/prompts/*.prompt.md`

- [x] T002: Analyze contracts for implementation requirements
  - Read `specs/001-github-mcp-integration/contracts/github-mcp-integration.md`
  - Extract required GitHub MCP operations per command
  - List template modifications needed
  - Identify error handling patterns
  - **Files**: `specs/001-github-mcp-integration/contracts/github-mcp-integration.md`

## Phase 3.2: Template Updates (Core Implementation)

### Specify Command

- [x] T003: Update generic specify template with GitHub integration
  - Add AI-powered branch name generation step
  - Add GitHub issue creation with MCP/CLI fallback
  - Add icon and type determination logic
  - Add label application instructions
  - Add error handling for GitHub API failures
  - **Files**: `templates/commands/specify.md`

- [x] T004: Synchronize specify prompt with MCP guidance
  - Ensure `.github/prompts/specify.prompt.md` has explicit MCP mention
  - Add CLI fallback command examples
  - Verify consistency with generic template
  - **Files**: `.github/prompts/specify.prompt.md`

### Plan Command

- [x] T005: Update generic plan template with GitHub integration
  - Add git commit and push operations
  - Add draft PR creation with MCP/CLI fallback
  - Add PR description formatting logic
  - Add issue linking with "Fixes #" pattern
  - Add label management (remove Specification, add Plan)
  - Add error handling instructions
  - **Files**: `templates/commands/plan.md`

- [x] T006: Synchronize plan prompt with MCP guidance
  - Ensure `.github/prompts/plan.prompt.md` has explicit MCP mention
  - Add CLI fallback command examples
  - Verify consistency with generic template
  - **Files**: `.github/prompts/plan.prompt.md`

### Tasks Command

- [x] T007: Update generic tasks template with PR description updates
  - Add PR description update step
  - Add checkbox formatting for task phases
  - Add section header logic ("## Implementation Tasks")
  - Add MCP/CLI fallback for PR updates
  - Preserve existing PR content
  - **Files**: `templates/commands/tasks.md`

- [x] T008: Synchronize tasks prompt with MCP guidance
  - Ensure `.github/prompts/tasks.prompt.md` has explicit MCP mention
  - Add CLI fallback command examples
  - Verify consistency with generic template
  - **Files**: `.github/prompts/tasks.prompt.md`

### Implement Command

- [x] T009: Update generic implement template with PR finalization
  - Add PR ready status update (remove draft)
  - Add progressive checkbox updates
  - Add label management (remove Plan, add Implementation)
  - Add constitution update step
  - Add merge conflict handling guidance
  - Add MCP/CLI fallback for all GitHub operations
  - **Files**: `templates/commands/implement.md`

- [x] T010: Synchronize implement prompt with MCP guidance
  - Ensure `.github/prompts/implement.prompt.md` has explicit MCP mention
  - Add CLI fallback command examples
  - Verify consistency with generic template
  - **Files**: `.github/prompts/implement.prompt.md`

## Phase 3.3: Integration & Validation

- [ ] T011: Test specify command with MCP-enabled agent
  - Run `/specify` with test feature description
  - Verify branch name generation
  - Verify GitHub issue creation
  - Verify labels applied correctly
  - Verify branch mentioned in issue body
  - **Validation**: Manual test following quickstart.md Scenario 1

- [ ] T012: Test plan command with MCP-enabled agent
  - Run `/plan` on test feature
  - Verify draft PR creation
  - Verify PR description format
  - Verify issue label updates
  - Verify git commit and push
  - **Validation**: Manual test following quickstart.md Scenario 2

- [ ] T013: Test tasks command with MCP-enabled agent
  - Run `/tasks` on test feature
  - Verify tasks.md generation
  - Verify PR description update with checkboxes
  - Verify existing PR content preserved
  - **Validation**: Manual test following quickstart.md Scenario 3

- [ ] T014: Test implement command with MCP-enabled agent
  - Run `/implement` on test feature
  - Verify PR marked ready for review
  - Verify checkbox updates as tasks complete
  - Verify issue label updates
  - Verify constitution update
  - **Validation**: Manual test following quickstart.md Scenario 4

- [ ] T015 [P]: Test CLI fallback scenario
  - Test workflow with non-MCP agent
  - Verify error messages provide clear instructions
  - Verify `gh` CLI commands work correctly
  - Document any issues with fallback pattern
  - **Validation**: Manual test following quickstart.md Scenario 6

## Phase 3.4: Documentation & Polish

- [ ] T016 [P]: Update README.md with GitHub MCP information
  - Add GitHub MCP integration section
  - Explain MCP-first approach with CLI fallback
  - Document error handling pattern
  - Add troubleshooting section for GitHub API issues
  - **Files**: `README.md`

- [ ] T017 [P]: Update AGENTS.md with integration notes
  - Document which agents have native MCP support
  - Explain CLI fallback for non-MCP agents
  - Add testing notes for GitHub integration
  - **Files**: `AGENTS.md`

- [ ] T018 [P]: Update constitution with new capabilities
  - Document GitHub MCP integration in Product Overview
  - Add GitHub workflow tracking to Core Workflow section
  - Document label management conventions
  - Add PR progressive update pattern
  - **Files**: `.specify/memory/constitution.md`

- [ ] T019 [P]: Validate cross-artifact consistency
  - Run `/analyze` command
  - Review all findings
  - Address any CRITICAL or HIGH severity issues
  - Document any intentional deviations
  - **Validation**: Use analyze.prompt.md

- [ ] T020: Final end-to-end workflow test
  - Create new test feature from scratch
  - Execute full workflow: specify → plan → tasks → implement
  - Verify all GitHub operations work correctly
  - Verify constitution updated correctly
  - Close and clean up test feature
  - **Validation**: Complete workflow test

## Parallel Execution Strategy

### Parallel Group 1 (T015-T018): Documentation
All documentation updates can run in parallel as they touch different files:
```bash
# Can execute simultaneously
/task T015  # CLI fallback testing
/task T016  # README update
/task T017  # AGENTS.md update
/task T018  # Constitution update
```

### Sequential Requirements
- T001-T002 must complete before T003-T010 (need to understand current state)
- T003-T010 must complete before T011-T015 (templates must exist to test)
- T011-T015 should complete before T016-T018 (test results inform docs)
- T019 must run after all other tasks (analyzes completed work)
- T020 must be last (final validation)

## Task Summary

- **Total Tasks**: 20
- **Completed**: 10 (Setup + Core Implementation)
- **Remaining**: 10 (Integration + Documentation)
- **Parallel Tasks**: 5 (T015-T018, plus T019 if needed)
- **Estimated Effort**: 2-3 hours for remaining tasks

## Dependencies

- **T011-T015** depend on **T003-T010** (need updated templates)
- **T019** depends on **T011-T018** (analyzes completed implementation)
- **T020** depends on **T019** (final validation after fixes)

## Success Criteria

- ✅ All templates synchronized between `templates/commands/` and `.github/prompts/`
- ✅ All GitHub MCP operations include natural language suggestions
- ✅ All GitHub operations include CLI fallback commands
- ✅ Error handling documented and tested
- ✅ Constitution updated with new capabilities
- ✅ All quickstart scenarios pass validation
- ✅ Cross-artifact analysis shows no CRITICAL issues

---

**Status**: Phase 3.2 Complete (Core Implementation) - Ready for Phase 3.3 (Integration & Validation)
**Next**: Run T011 to begin integration testing
