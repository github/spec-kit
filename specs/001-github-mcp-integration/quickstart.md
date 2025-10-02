# Quickstart Validation: GitHub MCP Integration

**Feature**: 001-github-mcp-integration
**Date**: 2025-10-02
**Purpose**: Manual validation scenarios for GitHub MCP workflow integration

## Overview

This document provides step-by-step validation scenarios to verify the GitHub MCP integration works correctly throughout the Spec-Driven Development workflow. Each scenario should be tested in a real repository environment with GitHub access.

## Prerequisites

- [ ] AI agent with GitHub MCP support (GitHub Copilot, Claude Code, etc.)
- [ ] GitHub repository with write access
- [ ] Specify CLI installed and initialized
- [ ] Git configured with remote repository
- [ ] Network connectivity to GitHub

## Validation Scenarios

### Scenario 1: Specify Phase - Issue Creation

**Objective**: Verify `/specify` command creates GitHub issue correctly

**Steps**:
1. Start on `main` branch with clean working directory
2. Run command: `/specify Build a simple calculator app`
3. Observe AI generates branch name (e.g., `calculator-app`)
4. Check feature branch created: `001-calculator-app`
5. Verify `specs/001-calculator-app/spec.md` exists
6. Check GitHub issue created

**Expected Results**:
- [x] Branch name is AI-generated, kebab-case, 2-4 words
- [x] Feature number auto-incremented correctly
- [x] Spec file exists at correct path
- [x] GitHub issue created with:
  - Title format: `🚀 [Feature]: Build a simple calculator app`
  - Body starts with "## User Scenarios & Testing"
  - Body includes "**Feature Branch**: \`001-calculator-app\`"
  - Labels: `Specification`, `Minor` (or appropriate type)
  - Issue is open

**Acceptance Criteria**:
- Issue number reported in command output
- Issue viewable in GitHub UI
- All required content present in issue body
- Labels correctly applied

**Rollback on Failure**:
```bash
git checkout main
git branch -D 001-calculator-app
# Manually close created issue if any
```

---

### Scenario 2: Plan Phase - Draft PR Creation

**Objective**: Verify `/plan` command creates draft PR and updates labels

**Prerequisites**: Complete Scenario 1

**Steps**:
1. On feature branch `001-calculator-app`
2. Run command: `/plan Use Python with simple CLI interface`
3. Wait for plan artifacts generation
4. Observe git commit and push
5. Check draft PR created
6. Verify issue labels updated

**Expected Results**:
- [x] Planning artifacts generated:
  - `research.md` exists and complete
  - `data-model.md` exists with entities
  - `contracts/` directory with API contracts
  - `quickstart.md` with test scenarios
- [x] Changes committed with descriptive message
- [x] Branch pushed to remote
- [x] Draft PR created with:
  - Same title as issue
  - Body has summary paragraph (no title heading)
  - Body includes plan.md content
  - Body ends with "- Fixes #<issue-number>"
  - Draft status: true
  - Base branch: main
- [x] Issue labels updated:
  - Removed: `Specification`
  - Added: `Plan`
  - Kept: Type label (e.g., `Minor`)

**Acceptance Criteria**:
- PR number reported in command output
- PR viewable in GitHub UI as draft
- PR properly linked to issue
- Issue shows label changes
- All plan artifacts committed and pushed

**Rollback on Failure**:
```bash
git reset --hard HEAD~1
git push --force
# Manually close PR and revert issue labels if needed
```

---

### Scenario 3: Tasks Phase - PR Description Update

**Objective**: Verify `/tasks` command updates PR description with checkboxes

**Prerequisites**: Complete Scenario 2

**Steps**:
1. On feature branch with draft PR existing
2. Run command: `/tasks`
3. Wait for tasks.md generation
4. Check PR description updated
5. Verify existing content preserved

**Expected Results**:
- [x] `tasks.md` file generated with:
  - Numbered tasks (T001, T002, etc.)
  - TDD phases (tests before implementation)
  - Parallel markers [P] where applicable
  - Dependency ordering maintained
- [x] PR description updated with:
  - All previous content preserved (summary + plan.md)
  - tasks.md content appended
  - Tasks formatted as checkboxes: `- [ ] T001: Task description`
  - "- Fixes #<issue-number>" line still present
- [x] PR still in draft status

**Acceptance Criteria**:
- PR description shows tasks with unchecked checkboxes
- Existing PR content intact
- Tasks logically ordered and complete
- All functional requirements covered by tasks

**Rollback on Failure**:
```bash
rm specs/001-calculator-app/tasks.md
git checkout specs/001-calculator-app/tasks.md
# Manually revert PR description if updated
```

---

### Scenario 4: Implement Phase - Progressive Updates

**Objective**: Verify `/implement` command updates checkboxes and marks PR ready

**Prerequisites**: Complete Scenario 3

**Steps**:
1. On feature branch with tasks in PR
2. Run command: `/implement`
3. Observe progressive task execution
4. Watch PR description checkboxes update
5. Verify PR marked ready when complete
6. Check constitution updated
7. Verify issue labels updated

**Expected Results**:
- [x] Implementation progresses through tasks
- [x] PR description checkboxes update progressively:
  - After Phase 0 complete: `- [x] T001: ...`, `- [x] T002: ...`
  - After Phase 1 complete: More checkboxes marked
  - After Phase 2 complete: More checkboxes marked
  - After Phase 3 complete: All tasks checked
- [x] PR status changes:
  - Draft: false (ready for review)
- [x] Constitution updated:
  - `.specify/memory/constitution.md` has new entry
  - New feature capabilities documented
  - Changes committed
- [x] Issue labels updated:
  - Added: `Implementation`
  - Kept: `Plan`, Type label

**Acceptance Criteria**:
- All task checkboxes marked complete
- PR ready for review (not draft)
- Constitution contains feature documentation
- Issue shows `Implementation` label
- Implementation code committed and pushed
- All tests passing

**Manual Validation Points**:
- Check PR in GitHub UI shows green "Ready for review"
- Verify issue timeline shows label changes
- Read constitution entry for accuracy
- Run tests to confirm passing status

**Rollback on Failure**:
```bash
git reset --hard origin/main
git push --force
# Manually revert PR to draft
# Manually remove Implementation label
# Manually revert constitution changes
```

---

### Scenario 5: Error Handling - GitHub API Failure

**Objective**: Verify graceful degradation when GitHub API unavailable

**Prerequisites**: None (simulate failure)

**Steps**:
1. Disconnect from network or simulate rate limiting
2. Run command: `/specify Build a todo app`
3. Observe error handling

**Expected Results**:
- [x] Clear error message displayed:
  ```
  Error: Cannot connect to GitHub API
  ```
- [x] Recovery instructions provided:
  ```
  Please create issue manually:
  - Title: 🚀 [Feature]: Build a todo app
  - Body: [spec content shown]
  - Labels: Specification, Minor
  - Link to branch: 002-todo-app
  ```
- [x] Spec file still created locally
- [x] Branch still created
- [x] Command does not crash
- [x] Partial state documented

**Acceptance Criteria**:
- Error message is clear and actionable
- Manual fallback instructions complete
- Local artifacts created successfully
- User can resume workflow manually

**Recovery Steps**:
1. Restore network connectivity
2. Create issue manually per instructions
3. Continue with `/plan` command
4. Or re-run `/specify` to auto-create issue

---

### Scenario 6: End-to-End Workflow

**Objective**: Verify complete workflow from specify to merge

**Prerequisites**: Clean repository state

**Steps**:
1. Run `/specify Build REST API for blog posts`
2. Verify issue created (Issue #N)
3. Run `/plan Use FastAPI, PostgreSQL, TDD approach`
4. Verify draft PR created (PR #M linking to Issue #N)
5. Run `/tasks`
6. Verify PR updated with tasks
7. Run `/implement`
8. Verify PR ready, constitution updated
9. Review PR in GitHub UI
10. Merge PR via GitHub
11. Verify issue auto-closed

**Expected Results**:
- [x] Issue #N created with `Specification` label
- [x] PR #M created as draft, linked to Issue #N
- [x] Issue labels: `Specification` → `Plan` → `Plan, Implementation`
- [x] PR status: Draft → Ready for review
- [x] PR description shows: summary + plan + tasks (all checked)
- [x] Constitution updated with blog API feature
- [x] All artifacts committed and pushed
- [x] After merge:
  - PR status: Closed
  - Issue status: Closed (auto-closed by "Fixes #N")
  - Branch can be deleted
  - Main branch has all changes

**Acceptance Criteria**:
- Complete traceability from idea to delivery
- All workflow phases represented in GitHub
- Documentation synchronized throughout
- Issue auto-closes on PR merge
- Constitution reflects implemented feature

**Duration**: 10-30 minutes depending on feature complexity

---

### Scenario 7: Multi-Agent Compatibility

**Objective**: Verify workflow works across different AI agents

**Prerequisites**: Access to multiple AI agents

**Steps for Each Agent**:
1. Initialize new project with agent: `specify init --ai <agent>`
2. Verify agent-specific directory created (e.g., `.claude/commands/`)
3. Run `/specify Build user authentication`
4. Verify issue created successfully
5. Run `/plan Use agent-appropriate stack`
6. Verify draft PR created
7. Check command templates have GitHub MCP operations

**Test Agents**:
- [ ] GitHub Copilot (`.github/prompts/`)
- [ ] Claude Code (`.claude/commands/`)
- [ ] Gemini CLI (`.gemini/commands/`)
- [ ] Cursor (`.cursor/commands/`)
- [ ] Qwen Code (`.qwen/commands/`)
- [ ] opencode (`.opencode/command/`)
- [ ] Windsurf (`.windsurf/workflows/`)

**Expected Results**:
- [x] All agents can create issues via GitHub MCP
- [x] All agents can create/update PRs
- [x] Command format differs (Markdown vs TOML) but operations identical
- [x] Argument patterns differ (`$ARGUMENTS` vs `{{args}}`) but work correctly
- [x] No vendor lock-in - workflow portable across agents

**Acceptance Criteria**:
- At least 3 different agents tested successfully
- GitHub operations work identically
- Template synchronization maintained
- Documentation covers agent differences

---

## Validation Checklist

### Functional Requirements Coverage

Based on spec.md requirements:

- [ ] **FR-001**: `specify.md` template updated with GitHub MCP operations
- [ ] **FR-002**: `plan.md` template updated with GitHub MCP operations
- [ ] **FR-003**: `tasks.md` template updated with PR description updates
- [ ] **FR-004**: `implement.md` template updated with progressive updates
- [ ] **FR-005**: Branch name generation uses AI analysis
- [ ] **FR-006**: PR title formatting consistent with icons
- [ ] **FR-007**: PR description format followed correctly
- [ ] **FR-008**: Labels formatted and applied correctly
- [ ] **FR-009**: Constitution updated during implement phase
- [ ] **FR-010**: `.github/prompts/` and `templates/` synchronized
- [ ] **FR-011**: Spec template structure updated (user scenarios first)
- [ ] **FR-012**: Error handling implemented for GitHub API failures
- [ ] **FR-013**: Documentation updated with GitHub MCP integration

### Success Criteria Coverage

From spec.md success criteria:

- [ ] Generic templates match GitHub Copilot prompts for GitHub MCP
- [ ] `/specify` creates spec file AND GitHub issue
- [ ] `/plan` creates design artifacts, draft PR, updates labels
- [ ] `/tasks` updates PR description with checkboxes
- [ ] `/implement` updates checkboxes, marks ready, updates constitution
- [ ] Error messages clear and helpful
- [ ] Documentation explains GitHub MCP integration
- [ ] Spec template prioritizes user scenarios
- [ ] Labels consistently formatted with backticks

### Non-Functional Validation

- [ ] Performance: Issue/PR creation < 5 seconds
- [ ] Reliability: Error handling prevents data loss
- [ ] Usability: Clear instructions for manual fallback
- [ ] Compatibility: Works across all supported agents
- [ ] Maintainability: Template synchronization documented

## Troubleshooting Guide

### Common Issues

**Issue**: Branch name not AI-generated, uses placeholder
- **Cause**: AI failed to analyze feature description
- **Fix**: Provide clearer feature description with action verbs

**Issue**: GitHub issue creation fails silently
- **Cause**: GitHub MCP tool not available in agent
- **Fix**: Verify agent supports GitHub MCP, update agent version

**Issue**: PR description formatting broken
- **Cause**: Manual edits to PR conflicted with updates
- **Fix**: Avoid manual PR edits during workflow, or re-run commands

**Issue**: Labels not updating on issue
- **Cause**: Label update operation failed
- **Fix**: Manually update labels in GitHub UI per instructions

**Issue**: Constitution not updated
- **Cause**: File permissions or merge conflicts
- **Fix**: Check write permissions, resolve conflicts manually

### Debugging Steps

1. **Enable verbose logging** (if supported by agent)
2. **Check command output** for error messages
3. **Verify GitHub connectivity**: `curl https://api.github.com`
4. **Check repository permissions**: Ensure write access
5. **Review Git status**: `git status`, `git log`
6. **Inspect generated files**: Verify content completeness
7. **Check GitHub UI**: Confirm issue/PR state
8. **Review agent logs**: Agent-specific log locations

## Next Steps After Validation

Once all scenarios pass:
1. Document any edge cases discovered
2. Update templates with improvements
3. Add validation scenarios to documentation
4. Create automated tests if possible
5. Update CONTRIBUTING.md with testing guidelines
6. Mark PR ready for review
7. Update constitution with implemented feature
