# Design Document: Spec-Kit PR #1368 Evaluation

**Change ID:** `evaluate-spec-kit-pr-1368`  
**Date:** 2026-01-04  
**Status:** Design

---

## Overview

This document outlines the architectural decisions, technical approach, and implementation strategy for evaluating and potentially integrating GitHub Pull Request #1368 into our local spec-kit framework.

---

## System Context

### Current State

```
Framework Comparison Project
├── frameworks/
│   └── spec-kit/          ← Our local copy of spec-kit
│       ├── src/
│       ├── scripts/
│       ├── .github/
│       └── ...
└── openspec/              ← Our OpenSpec workflow directory (NEW)
    └── changes/
        └── evaluate-spec-kit-pr-1368/
```

**Current spec-kit version:** 0.0.22 (pre-Antigravity)  
**Target PR:** github/spec-kit#1368  
**PR version:** 0.0.23  
**Agent to add:** Antigravity IDE (Google)

### Goals

1. **Evaluate PR safety:** Ensure no bugs or breaking changes
2. **Identify issues:** Find and document all problems
3. **Fix critical bugs:** Resolve issues before deployment
4. **Maintain parity:** Keep our fork synchronized with upstream
5. **Document everything:** Enable future maintenance and sync

---

## Architectural Decisions

### Decision 1: Directory Path Resolution

**Problem:** PR #1368 has inconsistent directory paths between documentation and scripts.

| Component                                    | Path Used                       |
| -------------------------------------------- | ------------------------------- |
| Documentation (AGENTS.md, README.md)         | `.agent/workflows/`             |
| Release scripts (create-release-packages.\*) | `.agent/workflows/`             |
| Context scripts (update-agent-context.\*)    | `.agent/rules/specify-rules.md` |

**Analysis:**

We examined patterns from existing IDE-based agents:

**Windsurf Pattern:**

- Commands: `.windsurf/workflows/` (documented)
- Rules: `.windsurf/rules/specify-rules.md` (actual)
- **Dual structure**: Commands and rules in separate directories

**Cursor Pattern:**

- Commands: `.cursor/commands/` (documented)
- Rules: `.cursor/rules/specify-rules.mdc` (actual)
- **Dual structure**: Commands and rules in separate directories

**IBM Bob Pattern:**

- (Research shows similar dual structure)

**Decision: DUAL DIRECTORY STRUCTURE** ✅

**Rationale:**

1. **Consistency:** Matches established IDE agent patterns (Windsurf, Cursor)
2. **Separation of Concerns:**
   - `.agent/workflows/` contains user-invocable workflow commands (.md files)
   - `.agent/rules/` contains agent context/instructions (specify-rules.md)
3. **Maintainability:** Follows precedent, easier for future contributors
4. **Upstream alignment:** PR's release scripts already create `.agent/workflows/`

**Implementation:**

- Keep `.agent/workflows/` creation in release scripts (already correct)
- Update context scripts to use `.agent/rules/specify-rules.md` (already in PR, correct)
- **No code changes needed** - PR is actually correct, Copilot review was misleading

**Re-evaluation:** Upon deeper analysis, the PR appears to follow the correct pattern. The directory "inconsistency" is actually a **feature pattern** not a bug. Copilot's review was incorrect.

---

### Decision 2: Patch Application Strategy

**Problem:** How to integrate upstream PR into our local fork?

**Options Considered:**

#### Option A: Direct Git Merge from Upstream

```bash
git remote add upstream https://github.com/github/spec-kit.git
git fetch upstream pull/1368/head:pr-1368
git merge pr-1368
```

**Pros:** Clean git history, easy to sync later  
**Cons:** PR not merged yet, may get conflicts if PR changes

#### Option B: Patch File Application

```bash
curl -L https://github.com/github/spec-kit/pull/1368.patch | git apply
```

**Pros:** Works without adding remote, snapshot of exact PR state  
**Cons:** Loses git metadata (author, commit messages)

#### Option C: Cherry-Pick Commits

```bash
git fetch upstream
git cherry-pick f3ba03e a8c6570
```

**Pros:** Preserves commit history and attribution  
**Cons:** Requires upstream remote, commits may not apply cleanly

**Decision: Option B** - Patch File Application ✅

**Rationale:**

1. **Independence:** Don't need to add upstream remote to our project
2. **Snapshot:** Captures exact state of PR at evaluation time
3. **Simplicity:** Single command to apply
4. **Flexibility:** Easy to add our own fixes on top
5. **Documentation:** Patch file serves as clear record of what we integrated

**Implementation:**

```bash
# Download
curl -L https://github.com/github/spec-kit/pull/1368.patch -o /tmp/pr-1368.patch

# Validate
git apply --check /tmp/pr-1368.patch

# Apply
git apply /tmp/pr-1368.patch

# Commit
git add -A
git commit -m "Apply spec-kit PR #1368 (Antigravity support)"
```

**Future Sync Strategy:**

- When PR #1368 merges upstream, we can pull from main
- If our patch diverged, resolve conflicts at that time
- Document our changes in LOCAL_MODIFICATIONS.md for reference

---

### Decision 3: Testing Scope

**Problem:** How comprehensive should our testing be?

**Testing Pyramid:**

```
          /\
         /  \  Manual Exploratory
        /----\
       /      \  Integration Tests
      /--------\
     /          \  Static Analysis
    /-----------  \
```

**Decision: COMPREHENSIVE MULTI-LAYER TESTING** ✅

**Rationale:**

1. **High Stakes:** Spec-kit is critical infrastructure for our workflows
2. **Upstream Trust:** PR is from external contributor, not core maintainers
3. **Complexity:** Touches 10 files across multiple languages (Python, Bash, PowerShell)
4. **Patterns:** Need to verify consistency with existing agents

**Testing Layers:**

| Layer                 | Tools                           | Coverage                            |
| --------------------- | ------------------------------- | ----------------------------------- |
| **Static Analysis**   | shellcheck, Python syntax       | All scripts, config files           |
| **Integration Tests** | Manual `specify init` tests     | Fresh installation, context updates |
| **Regression Tests**  | Test existing agents            | Ensure no breakage                  |
| **Comparison Tests**  | Pattern analysis                | Verify consistency                  |
| **Cross-Platform**    | Linux bash + Windows PowerShell | Platform parity                     |

**Test Exclusions:**

- Unit tests (spec-kit doesn't have unit test infrastructure)
- Performance tests (not relevant for config changes)
- Security tests (no security implications)

---

### Decision 4: Issue Resolution Approach

**Problem:** What do we do about issues we find?

**Discovered Issues:**

1. ~~Directory path inconsistency~~ (Re-analyzed: Not actually a bug)
2. (Any others found during testing)

**Decision: FIX LOCALLY + REPORT UPSTREAM** ✅

**Workflow:**

```
1. Apply PR as-is
2. Test thoroughly
3. Identify any real bugs
4. Fix bugs in local copy
5. Document fixes in LOCAL_MODIFICATIONS.md
6. Create upstream feedback in GitHub PR comment
7. (Optional) Submit our fixes as follow-up PR to spec-kit
```

**Rationale:**

1. **Unblock ourselves:** Don't wait for upstream fixes
2. **Contribute back:** Help improve the project for everyone
3. **Maintain traceability:** Clear record of what we changed and why
4. **Enable sync:** Can easily merge upstream when PR is finalized

**Implementation:**

- Each fix gets its own commit (after the patch apply commit)
- Commit messages reference the specific issue
- LOCAL_MODIFICATIONS.md tracks all delta from upstream PR

---

### Decision 5: Documentation Strategy

**Problem:** How to document this evaluation comprehensively?

**Decision: MULTI-DOCUMENT APPROACH** ✅

**Document Structure:**

```
docs/docs-local/2026-01-04/
├── spec-kit-pr-1368-evaluation-report.md    ← Final comprehensive report
├── spec-kit-pr-1368-test-results.md         ← Detailed test results
└── spec-kit-pr-1368-upstream-feedback.md    ← Feedback for PR author

frameworks/spec-kit/
└── LOCAL_MODIFICATIONS.md                   ← Our changes vs upstream

openspec/changes/evaluate-spec-kit-pr-1368/
├── proposal.md                              ← This proposal
├── tasks.md                                 ← Implementation tasks
└── design.md                                ← This design doc
```

**Rationale:**

1. **Separation of Concerns:** Each document serves a specific purpose
2. **User Rules Compliance:** Follows Rule #4 for documentation
3. **Future Reference:** Easy to find specific information
4. **Audit Trail:** Complete record of decisions and outcomes

---

## Technical Implementation

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│           Specify CLI (Python)                       │
│  ┌────────────────────────────────────────────────┐ │
│  │  AGENT_CONFIG Dictionary                        │ │
│  │  {                                              │ │
│  │    "antigravity": {                            │ │
│  │      "name": "Antigravity IDE",                │ │
│  │      "folder": ".agent/",                      │ │
│  │      "install_url": None,                      │ │
│  │      "requires_cli": False                     │ │
│  │    },                                           │ │
│  │    ...                                          │ │
│  │  }                                              │ │
│  └────────────────────────────────────────────────┘ │
│  │                                                   │
│  │ specify init --ai antigravity                    │
│  └───────────────┬──────────────────────────────────┘
│                  │
│                  ▼
│  ┌───────────────────────────────────────────────┐
│  │   Template Generation                         │
│  │   (create-release-packages.sh/.ps1)          │
│  └───────────────┬───────────────────────────────┘
│                  │
│                  ▼
│  ┌───────────────────────────────────────────────┐
│  │   Creates Directory Structure:                │
│  │   .agent/                                     │
│  │   ├── workflows/                              │
│  │   │   ├── speckit-constitution.md             │
│  │   │   ├── speckit-specify.md                  │
│  │   │   ├── speckit-plan.md                     │
│  │   │   ├── speckit-tasks.md                    │
│  │   │   └── speckit-implement.md     │
│  │   └── rules/                                  │
│  │       └── specify-rules.md     (context)     │
│  └───────────────────────────────────────────────┘
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User Command:
  specify init my-project --ai antigravity

    │
    ▼
CLI Validation:
  - Check if "antigravity" in AGENT_CONFIG
  - Verify folder structure requirements
    │
    ▼
Template Selection:
  - Load base templates from templates/
  - Identify agent-specific paths (.agent/)
    │
    ▼
Directory Creation:
  - Create .agent/workflows/
  - Create .agent/rules/
    │
    ▼
File Generation:
  - Generate .md workflow files (speckit.*)
  - Generate specify-rules.md with project context
  - Set correct file permissions
    │
    ▼
Post-Setup:
  - Run setup scripts
  - Initialize git (if not --no-git)
  - Display success message
```

### Script Interactions

```
┌─────────────────────────────────────────────────────┐
│  User Workflow                                       │
└─────────────────┬───────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────────────┐
│ specify │  │ create-  │  │ update-agent-    │
│ init    │  │ release- │  │ context.sh/.ps1  │
│         │  │ packages │  │                  │
└────┬────┘  └────┬─────┘  └────┬─────────────┘
     │            │             │
     │            │             │
     └────────────┴─────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │  .agent/ structure   │
        │  created/updated     │
        └──────────────────────┘
```

---

## Risk Analysis

### Risk Matrix

| Risk                          | Probability | Impact   | Mitigation                                       |
| ----------------------------- | ----------- | -------- | ------------------------------------------------ |
| Patch conflicts               | Low         | High     | Dry-run before apply; backup spec-kit            |
| ~~Directory bug~~             | ~~High~~    | ~~High~~ | ~~Re-analyzed: Not a bug~~                       |
| Regression in existing agents | Low         | High     | Comprehensive regression testing                 |
| PowerShell incompatibility    | Medium      | Medium   | Cross-platform testing (skip if ENV unavailable) |
| Upstream PR changes           | Medium      | Low      | Monitor PR; maintain LOCAL_MODIFICATIONS.md      |
| Test environment issues       | Medium      | Medium   | Document ENV limitations; skip unavailable tests |

### Mitigation Strategies

**Pre-Implementation:**

- Create full backup of spec-kit before applying patch
- Use git branch isolation (feat/evaluate-spec-kit-pr-1368)
- Maintain guardian-state backup branch (per user rules)

**During Implementation:**

- Checkpoint-based task execution (can rollback to any checkpoint)
- Test after each major phase before proceeding
- Document all issues immediately when found

**Post-Implementation:**

- Retain patch file and documentation for future reference
- Create clear rollback instructions
- Monitor upstream PR for any updates or changes

---

## Testing Strategy Details

### Test Environment Setup

```bash
# Primary test environment
OS: Linux (Ubuntu/Debian assumed)
Shell: Zsh (per user rules)
Python: 3.11+
Package Manager: uv

# Directory structure
/tmp/
├── pr-1368.patch              ← Downloaded patch
├── spec-kit-backup-20260104/  ← Pre-patch backup
└── test-antigravity/          ← Fresh install test directory
```

### Test Cases

#### TC-001: Fresh Installation

```bash
specify init test-project --ai antigravity --script sh --debug
```

**Expected:**

- Exit code: 0
- Directories created: `.agent/`, `.agent/workflows/`, `.agent/rules/`
- Files created: 5 workflow .md files, 1 specify-rules.md
- Output: No errors or warnings

#### TC-002: Context Update (Explicit)

```bash
./scripts/bash/update-agent-context.sh antigravity
```

**Expected:**

- Exit code: 0
- File updated: `.agent/rules/specify-rules.md`
- Output: Success message

#### TC-003: Context Update (All Agents)

```bash
./scripts/bash/update-agent-context.sh
```

**Expected:**

- Exit code: 0
- Antigravity included in update
- Output: Lists updated agents including Antigravity

#### TC-004: Regression - Existing Agents

```bash
for agent in claude gemini copilot cursor-agent; do
  specify init "/tmp/test-$agent" --ai "$agent" --script sh || echo "FAIL: $agent"
done
```

**Expected:**

- All exit code: 0
- No failures

#### TC-005: Check Command

```bash
specify check
```

**Expected:**

- Exit code: 0
- Output: Does NOT show "antigravity CLI not found" (IDE-based)
- Output: Shows other CLI checks as expected

---

## Implementation Sequence

### Phase Overview

```
[Phase 1: Preparation] ─→ [Phase 2: Analysis] ─→ [Phase 3: Application]
         │                        │                       │
         │                        │                       │
         ▼                        ▼                       ▼
    Setup ENV              Static Analysis          Apply + Fix
    Download Patch         Validate Scripts         Verify Changes
    Install Tools          Analyze Patterns
         │                        │                       │
         └────────────────────────┴───────────────────────┘
                                  │
                                  ▼
                    [Phase 4-6: Testing & Validation]
                                  │
                                  ▼
                      [Phase 7: Documentation & Commit]
```

### Critical Path

1. **Setup** (Task 1.1) - MUST complete first
2. **Download Patch** (Task 1.2) - MUST have before analysis
3. **Static Analysis** (Tasks 2.1-2.5) - MUST complete before application
4. **Apply Patch** (Task 3.1) - MUST complete before testing
5. **Integration Tests** (Tasks 4.1-4.4) - MUST pass before approval
6. **Documentation** (Tasks 7.1-7.4) - MUST complete before commit

### Parallel Opportunities

- Tasks 1.2 and 1.3 can run in parallel
- Tasks 2.2, 2.3, 2.4 can run in parallel (after 2.1)
- Tasks 4.2, 4.3, 4.4 can run in parallel (after 4.1)

---

## Success Metrics

### Quantitative Metrics

- ✅ 100% of static analysis tests pass
- ✅ 100% of integration tests pass (Linux)
- ✅ 100% of regression tests pass
- ✅ 0 critical or high-severity bugs found (or all resolved)
- ✅ Windows tests pass OR marked "ENV N/A" with rationale

### Qualitative Metrics

- ✅ Implementation matches established IDE agent patterns
- ✅ Documentation is complete and clear
- ✅ Code changes are minimal and justified
- ✅ Upstream feedback is constructive and actionable
- ✅ Team understands changes and can maintain going forward

---

## Future Considerations

### When Upstream PR Merges

**Scenario 1: PR merges as-is**

- Our local copy already has it
- No action needed unless we added local fixes
- Optionally submit our fixes as follow-up PR

**Scenario 2: PR merges with changes**

- Review changes between our patch and merged version
- Apply delta using git merge or cherry-pick
- Update LOCAL_MODIFICATIONS.md

**Scenario 3: PR is rejected/closed**

- Maintain our local implementation
- Monitor for alternative PR or feature
- Consider contributing our evaluation to discussion

### Maintenance Strategy

- Review LOCAL_MODIFICATIONS.md before each upstream sync
- Test after each upstream sync to ensure compatibility
- Keep this evaluation documentation for future reference
- Update documentation if we make additional Antigravity changes

---

## Appendices

### Appendix A: File Checklist

**Files Modified by PR #1368:**

- [ ] `.github/workflows/scripts/create-github-release.sh`
- [ ] `.github/workflows/scripts/create-release-packages.ps1`
- [ ] `.github/workflows/scripts/create-release-packages.sh`
- [ ] `AGENTS.md`
- [ ] `CHANGELOG.md`
- [ ] `README.md`
- [ ] `pyproject.toml`
- [ ] `scripts/bash/update-agent-context.sh`
- [ ] `scripts/powershell/update-agent-context.ps1`
- [ ] `src/specify_cli/__init__.py`

**Files Created by This Evaluation:**

- [ ] `openspec/changes/evaluate-spec-kit-pr-1368/proposal.md`
- [ ] `openspec/changes/evaluate-spec-kit-pr-1368/tasks.md`
- [ ] `openspec/changes/evaluate-spec-kit-pr-1368/design.md`
- [ ] `docs/docs-local/2026-01-04/spec-kit-pr-1368-test-results.md` (pending)
- [ ] `docs/docs-local/2026-01-04/spec-kit-pr-1368-upstream-feedback.md` (pending)
- [ ] `docs/docs-local/2026-01-04/spec-kit-pr-1368-evaluation-report.md` (pending)
- [ ] `frameworks/spec-kit/LOCAL_MODIFICATIONS.md` (pending)

### Appendix B: Command Reference

**Download PR:**

```bash
curl -L https://github.com/github/spec-kit/pull/1368.patch -o /tmp/pr-1368.patch
```

**Apply Patch:**

```bash
cd /frameworks/spec-kit
git apply --check /tmp/pr-1368.patch  # Dry run
git apply /tmp/pr-1368.patch          # Actual apply
```

**Test Antigravity:**

```bash
specify init /tmp/test-ag --ai antigravity --script sh --debug
```

**Update Context:**

```bash
./scripts/bash/update-agent-context.sh antigravity
```

**Validate Bash:**

```bash
shellcheck scripts/bash/update-agent-context.sh
```

---

**Design Version:** 1.0  
**Last Updated:** 2026-01-04T20:45:59-04:00  
**Approved By:** (Pending user approval)
