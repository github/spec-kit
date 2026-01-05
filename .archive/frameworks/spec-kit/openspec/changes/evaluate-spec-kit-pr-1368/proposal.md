# Proposal: Evaluate Spec-Kit PR #1368 - Antigravity Agent Support

**Change ID:** `evaluate-spec-kit-pr-1368`  
**Date:** 2026-01-04  
**Author:** LeonAI Development Team  
**Status:** Proposal

---

## Why

This proposal addresses the need to thoroughly evaluate GitHub Pull Request #1368 for the spec-kit framework before implementing it in our local copy. The PR adds support for Google's Antigravity IDE as an AI assistant option in the Specify CLI.

### Background

- **Original Framework:** `/frameworks/spec-kit`
- **Pull Request:** https://github.com/github/spec-kit/pull/1368
- **PR Author:** serhiishtokal
- **PR Date:** December 21, 2025
- **PR Status:** Open (pending review)

### Motivation

1. **Risk Mitigation:** Ensure no bugs or breaking changes are introduced to our local spec-kit installation
2. **Compatibility Assessment:** Verify that the changes align with our workflow and environment
3. **Integration Planning:** Determine if we can safely merge this PR before the upstream project does
4. **Quality Assurance:** Conduct deep evaluation of code quality, naming conventions, and architectural consistency

### Related Issues

The PR relates to the following GitHub issues:

- #1213 - Initial request for Antigravity support
- #1217 - Discussion on Antigravity integration
- #1220 - Alternative implementation (superseded by #1368)

---

## What Changes

### PR Overview

Pull Request #1368 adds support for **Antigravity IDE** (Google's Antigravity IDE) as a new AI assistant option in Specify CLI. The implementation consists of **two commits**:

#### Commit 1: `f3ba03e` - feat: antigravity agent

Adds basic Antigravity support across all spec-kit components

#### Commit 2: `a8c6570` - fix: rename Antigravity to Antigravity IDE and mark as IDE-based

Corrects naming and classification issues identified during review

### Files Modified (10 files)

1. **`.github/workflows/scripts/create-github-release.sh`** (2 lines added)
   - Adds Antigravity template packages to release artifacts

2. **`.github/workflows/scripts/create-release-packages.ps1`** (8 additions, 2 deletions)
   - Adds Antigravity to agent list
   - Adds case handling for `.agent/workflows/` directory structure
   - Updates help text and documentation

3. **`.github/workflows/scripts/create-release-packages.sh`** (5 additions, 1 deletion)
   - Mirrors PowerShell changes for bash variant
   - Adds Antigravity to `ALL_AGENTS` array
   - Adds case statement for directory generation

4. **`AGENTS.md`** (8 additions, 3 deletions)
   - Adds Antigravity IDE to supported agents table
   - Updates agent type documentation
   - Adds directory structure (`.agent/workflows/`)
   - Marks as IDE-based (not CLI-based)
   - Updates multi-agent support lists

5. **`CHANGELOG.md`** (6 additions)
   - Adds version 0.0.23 entry
   - Documents Antigravity support addition

6. **`README.md`** (5 additions, 2 deletions)
   - Adds Antigravity to supported agents table
   - Updates`--ai` option documentation
   - Updates `check` command agent list

7. **`pyproject.toml`** (1 addition, 1 deletion)
   - Bumps version from 0.0.22 to 0.0.23

8. **`scripts/bash/update-agent-context.sh`** (17 additions, 4 deletions)
   - Defines `ANTIGRAVITY_FILE` variable (`.agent/rules/specify-rules.md`)
   - Adds `antigravity` case in `update_specific_agent()` function
   - Adds existence check in `update_all_existing_agents()` function
   - Updates help text and usage documentation

9. **`scripts/powershell/update-agent-context.ps1`** (11 additions, 4 deletions)
   - Mirrors bash script changes for PowerShell
   - Adds validation set entry for 'antigravity'
   - Defines `$ANTIGRAVITY_FILE` variable
   - Updates agent update logic

10. **`src/specify_cli/__init__.py`** (8 additions, 1 deletion)
    - Adds Antigravity to `AGENT_CONFIG` dictionary
    - Configures as IDE-based (`requires_cli: False`)
    - Sets folder to `.agent/`
    - Updates `--ai` help text

### Key Implementation Details

#### Agent Configuration

```python
"antigravity": {
    "name": "Antigravity IDE",
    "folder": ".agent/",
    "install_url": None,
    "requires_cli": False,
}
```

#### Directory Structure

- **Commands/Workflows:** `.agent/workflows/`
- **Rules:** `.agent/rules/specify-rules.md`
- **Format:** Markdown
- **Arg Format:** `$ARGUMENTS`

### Copilot Review Findings

GitHub Copilot AI reviewed all 10 files and generated **4 comments** identifying potential issues:

#### Issue 1: CLI Tool Column Inconsistency (ADDRESSED in Commit 2)

**Location:** `AGENTS.md` table  
**Problem:** Listed "antigravity" CLI tool despite `requires_cli: False`  
**Resolution:** Changed to "N/A (IDE-based)" to match pattern of Windsurf, GitHub Copilot, and IBM Bob  
**Status:** ✅ FIXED

#### Issue 2: Directory Path Inconsistency (REMAINS UNRESOLVED)

**Location:** Multiple files  
**Problem:** Directory path mismatch between documentation and scripts:

- **Documentation (AGENTS.md, release scripts):** `.agent/workflows/`
- **Implementation (update-agent-context scripts):** `.agent/rules/specify-rules.md`
  **Comparison:** Windsurf uses `.windsurf/workflows/` in similar pattern  
  **Status:** ⚠️ UNRESOLVED INCONSISTENCY

---

## Critical Issues Identified

### 1. Directory Path Inconsistency (HIGH SEVERITY)

**Problem Details:**

| File                          | Path Referenced                 |
| ----------------------------- | ------------------------------- |
| `AGENTS.md`                   | `.agent/workflows/`             |
| `create-release-packages.sh`  | `.agent/workflows/`             |
| `create-release-packages.ps1` | `.agent/workflows/`             |
| `update-agent-context.sh`     | `.agent/rules/specify-rules.md` |
| `update-agent-context.ps1`    | `.agent/rules/specify-rules.md` |

**Impact:**

- Template generation scripts create `.agent/workflows/` directory
- Context update scripts look for `.agent/rules/specify-rules.md`
- Mismatch may cause runtime errors or missing files
- Users installing Antigravity support may experience broken functionality

**Risk Level:** HIGH - Core functionality discrepancy

### 2. Naming Consistency (LOW SEVERITY, ADDRESSED)

**Original Issue:** First commit used "Antigravity" while agent should be "Antigravity IDE"  
**Resolution:** Commit 2 corrected naming across all files  
**Status:** ✅ RESOLVED

### 3. Missing Tests

**Problem:** No test coverage added for Antigravity agent configuration  
**Impact:** Changes cannot be validated programmatically  
**Risk Level:** MEDIUM - Testing gap

---

## Test Strategy

### Phase 1: Static Analysis (Automated)

1. **Directory Structure Validation**
   - [ ] Verify all file paths referenced in PR exist or will be created correctly
   - [ ] Confirm `.agent/workflows/` vs `.agent/rules/` discrepancy
   - [ ] Validate directory structure against existing agent patterns (Windsurf, Cursor, Bob)

2. **Configuration Validation**
   - [ ] Verify `AGENT_CONFIG` dictionary syntax in `__init__.py`
   - [ ] Confirm Python dictionary structure is valid
   - [ ] Check for typos in agent key ("antigravity")

3. **Script Syntax Validation**
   - [ ] Validate bash script syntax (`shellcheck` on `.sh` files)
   - [ ] Validate PowerShell script syntax (`.ps1` files)
   - [ ] Confirm case statement completeness in both script variants

4. **Documentation Review**
   - [ ] Verify all agent lists are updated consistently
   - [ ] Check CHANGELOG format and version number
   - [ ] Validate markdown formatting in all `.md` files

### Phase 2: Integration Testing (Manual)

1. **Fresh Installation Test**

   ```bash
   # Test initialization with Antigravity agent
   specify init test-antigravity-project --ai antigravity --script sh
   ```

   - [ ] Verify `.agent/workflows/` directory is created
   - [ ] Confirm workflow files are generated correctly
   - [ ] Validate file permissions and structure

2. **Context Update Test**

   ```bash
   # Test agent context update script
   ./scripts/bash/update-agent-context.sh antigravity
   ```

   - [ ] Verify script finds or creates correct files
   - [ ] Confirm `.agent/rules/specify-rules.md` path resolution
   - [ ] Check for script errors or warnings

3. **Release Package Generation Test**

```bash
# Test release package creation (requires release environment)
./.github/workflows/scripts/create-release-packages.sh --agents antigravity --scripts sh
```

- [ ] Verify Antigravity template package is created
- [ ] Confirm directory structure within package
- [ ] Validate package naming convention

4. **Cross-Platform Test**
   - [ ] Test on Linux (bash scripts)
   - [ ] Test on Windows (PowerShell scripts)
   - [ ] Verify consistent behavior across platforms

### Phase 3: Comparison Testing

1. **Pattern Consistency**
   - [ ] Compare Antigravity implementation with Windsurf (IDE-based, `.windsurf/workflows/`)
   - [ ] Compare with Cursor (IDE-based, `.cursor/commands/`)
   - [ ] Compare with IBM Bob (IDE-based)
   - [ ] Identify any deviations from established patterns

2. **Regression Testing**
   - [ ] Verify existing agents still work (claude, gemini, copilot)
   - [ ] Confirm no breaking changes to existing functionality
   - [ ] Test `specify check` command includes Antigravity

### Phase 4: Issue Resolution Validation

1. **Directory Path Fix**
   - Create corrected implementation that resolves inconsistency
   - Test both documentation and script paths align
   - Verify against Windsurf pattern

2. **Test Coverage Addition**
   - Write unit tests for Antigravity agent configuration
   - Add integration tests for directory creation
   - Validate test coverage for new code paths

### Test Exemptions

**None** - This is a code change requiring comprehensive testing to ensure system integrity.

---

## Dependencies

### Upstream Dependencies

- **spec-kit upstream repository:** github/spec-kit
- **PR merge status:** Currently open (not yet merged)

### Internal Dependencies

- Current spec-kit version in `/frameworks/spec-kit`
- Git branch: `main` (creating `feat/evaluate-spec-kit-pr-1368`)

### Tool Dependencies

- `shellcheck` (for bash script validation)
- Python 3.11+ (for CLI testing)
- `uv` package manager (for specify-cli installation)
- Git (for PR download and apply)

---

## Success Criteria

### Must Have (Blocking)

1. ✅ All static analysis tests pass
2. ✅ Directory path inconsistency is resolved
3. ✅ Fresh installation test succeeds on Linux
4. ✅ Context update scripts work correctly
5. ✅ No regressions in existing agent functionality

### Should Have (Important)

1. Cross-platform testing completed (Windows PowerShell)
2. Release package generation validates successfully
3. Pattern consistency with other IDE-based agents confirmed
4. Unit test coverage added for new configuration

### Nice to Have (Optional)

1. Performance benchmarks for initialization time
2. Documentation examples for Antigravity-specific workflows
3. Contributor guide updated with Antigravity patterns

---

## Implementation Approach

### Option 1: Apply PR as-is and Fix Issues (RECOMMENDED)

**Steps:**

1. Download and apply PR patches to local spec-kit
2. Identify and document all issues (already done above)
3. Create corrective commits to resolve inconsistencies
4. Test thoroughly before merging to main
5. Optionally contribute fixes back to upstream PR

**Pros:**

- Gets us Antigravity support quickly
- Allows us to test and use while waiting for upstream merge
- We can contribute improvements back to community

**Cons:**

- Requires additional work to fix issues
- May diverge from upstream if PR is modified

### Option 2: Wait for Upstream Merge

**Steps:**

1. Monitor PR #1368 for merge status
2. Provide feedback to PR author about directory path issue
3. Pull changes once merged to upstream main branch

**Pros:**

- No maintenance burden for fixes
- Guaranteed alignment with upstream

**Cons:**

- Unknown timeline for merge
- No access to Antigravity support in interim

### Option 3: Hybrid Approach (RECOMMENDED FOR THIS PROJECT)

**Steps:**

1. Apply PR locally with corrective patches
2. Create detailed bug report for upstream PR
3. Maintain fork with patches until upstream incorporates fixes
4. Sync with upstream once PR is merged and issues resolved

**Pros:**

- Immediate access to functionality
- Contributes to upstream quality
- Maintains sync capability

**Cons:**

- Requires tracking upstream changes
- Some merge work when syncing later

---

## Risks and Mitigation

### Risk 1: Directory Path Mismatch

**Probability:** HIGH  
**Impact:** HIGH  
**Mitigation:** Fix directory paths to use `.agent/workflows/` consistently in all scripts before deployment

### Risk 2: Upstream PR Changes

**Probability:** MEDIUM  
**Impact:** MEDIUM  
**Mitigation:** Monitor PR for updates; maintain patch compatibility; document our changes clearly

### Risk 3: Regression in Existing Agents

**Probability:** LOW  
**Impact:** HIGH  
**Mitigation:** Comprehensive regression testing; rollback plan; version control

### Risk 4: Platform-Specific Issues

**Probability:** MEDIUM  
**Impact:** MEDIUM  
**Mitigation:** Test on both Linux (bash) and Windows (PowerShell); maintain platform parity

---

## Rollback Plan

If issues are discovered after implementation:

1. **Immediate:** Revert to previous commit on `main` branch
2. **Backup:** Restore from `guardian-state` branch if needed
3. **Data:** No data loss risk (configuration only)
4. **Timeline:** Rollback can be completed in < 5 minutes

---

## Next Steps

1. **Approval:** Review and approve this proposal
2. **Task Breakdown:** Create detailed `tasks.md` from this proposal
3. **Implementation:** Follow `/opt-openspec-global-apply` workflow
4. **Testing:** Execute comprehensive test strategy
5. **Documentation:** Update local docs with findings
6. **Reporting:** Create completion report in `docs/docs-local/2026-01-04/`

---

## References

- **Pull Request:** https://github.com/github/spec-kit/pull/1368
- **Spec-Kit Repository:** https://github.com/github/spec-kit
- **Related Issues:** #1213, #1217, #1220
- **Local Framework:** `/home/leonai-do/Host-D-Drive/LeonAI_DO/dev/Framework Comparison/frameworks/spec-kit`

---

**Proposal Version:** 1.0  
**Last Updated:** 2026-01-04T20:45:59-04:00
