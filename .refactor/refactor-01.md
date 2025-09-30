# Refactoring Plan 01: Fish Shell Integration Completion

**Status**: Draft  
**Priority**: High  
**Estimated Effort**: 4-6 hours  
**Target Version**: 0.0.18  
**Created**: 2025-09-30  
**Branch**: feature-add-fish-shell-support

---

## Executive Summary

The fish shell support refactoring is incomplete and non-functional. While fish scripts have been written and documentation updated, critical integration with the CLI has been omitted, and the fish scripts contain syntax errors that prevent execution. This plan addresses all blockers, consistency issues, and code quality concerns to deliver a fully functional fish shell option for users.

### Current State
- ✅ Fish scripts exist in `scripts/fish/`
- ✅ Documentation advertises fish support
- ❌ CLI doesn't recognize `--script fish` flag
- ❌ Fish scripts contain blocking syntax errors
- ❌ No release packages will be generated for fish
- ❌ Version/changelog not updated per project rules

### Target State
- Users can run `specify init <project> --script fish`
- Fish scripts execute without errors
- Release packages include fish templates
- Documentation matches implementation
- Version bumped and changelog updated

---

## Issues By Severity

### 🔴 Critical (Blocking - Must Fix)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| C1 | Fish missing from SCRIPT_TYPE_CHOICES | `src/specify_cli/__init__.py:82` | Complete feature broken |
| C2 | Invalid `set -e argv` usage | 3 fish scripts | Scripts fail immediately |
| C3 | Broken cleanup function syntax | `update-agent-context.fish:100` | Runtime error on exit |
| C4 | Missing from release packages | `.github/workflows/scripts/` | Users can't download fish templates |

### 🟡 High Priority (Must Fix)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| H1 | Missing CHANGELOG entry | `CHANGELOG.md` | Violates project standards |
| H2 | Missing version bump | `pyproject.toml:3` | Violates project standards |
| H3 | Documentation promises broken feature | Multiple docs | User confusion, bug reports |

### 🔵 Medium Priority (Should Fix)

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| M1 | Inconsistent string quoting | Multiple fish scripts | Code quality, potential edge cases |
| M2 | Redundant regex extraction | `common.fish:41-46` | Performance, code clarity |

---

## Detailed Task Breakdown

### Phase 1: Fix Critical Blockers

#### Task 1.1: Add Fish to CLI Script Type Choices
**File**: `src/specify_cli/__init__.py`  
**Line**: 82

**Current Code**:
```python
SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}
```

**Required Change**:
```python
SCRIPT_TYPE_CHOICES = {
    "sh": "POSIX Shell (bash/zsh)", 
    "ps": "PowerShell",
    "fish": "Fish Shell"
}
```

**Validation**:
- CLI accepts `--script fish` without error
- Interactive mode shows fish as an option
- Selection completes successfully

---

#### Task 1.2: Remove Invalid `set -e argv` from Fish Scripts
**Files**: 
- `scripts/fish/create-new-feature.fish:4`
- `scripts/fish/setup-plan.fish:4`
- `scripts/fish/update-agent-context.fish:41`

**Problem**: `set -e` in fish erases variables, not exit-on-error

**Required Changes**:

**File 1**: `scripts/fish/create-new-feature.fish`
```fish
# DELETE LINE 4:
set -e argv

# Fish has implicit error handling; no replacement needed
# Alternatively, add explicit error handling where critical:
# some_command; or exit 1
```

**File 2**: `scripts/fish/setup-plan.fish`
```fish
# DELETE LINE 4:
set -e argv
```

**File 3**: `scripts/fish/update-agent-context.fish`
```fish
# DELETE LINE 41:
set -e argv

# Line 40 comment "Enable strict error handling" is misleading
# UPDATE COMMENT to reflect fish's actual behavior:
# Fish functions return non-zero on command failure by default
```

**Validation**:
- Scripts accept arguments correctly
- `$argv` variable accessible throughout script
- Test: `./create-new-feature.fish "test feature"` succeeds

---

#### Task 1.3: Fix Cleanup Function Syntax
**File**: `scripts/fish/update-agent-context.fish`  
**Lines**: 99-102

**Current Code**:
```fish
function cleanup --on-process-exit
    rm -f /tmp/agent_update_*_(echo %self)
    rm -f /tmp/manual_additions_(echo %self)
end
```

**Problem**: `(echo %self)` is invalid syntax; `%self` is not a fish variable

**Required Change**:
```fish
function cleanup --on-process-exit
    rm -f /tmp/agent_update_*_$fish_pid
    rm -f /tmp/manual_additions_$fish_pid
end
```

**Alternative** (more robust):
```fish
function cleanup --on-event fish_exit
    set -l pid $fish_pid
    rm -f /tmp/agent_update_*_$pid
    rm -f /tmp/manual_additions_$pid
end
```

**Validation**:
- No syntax errors on script load
- Temporary files cleaned up after execution
- Test with: `fish -c 'source update-agent-context.fish'`

---

#### Task 1.4: Add Fish to Release Package Scripts
**File**: `.github/workflows/scripts/create-release-packages.sh`

**Required Changes**:

1. **Add to ALL_AGENTS array** (locate existing array):
```bash
ALL_AGENTS=(claude gemini copilot cursor qwen opencode windsurf)
```
No change needed here - this is agents, not script types.

2. **Verify fish is generated for each agent**:
Look for the script type loop that generates packages. Should already exist if bash/ps work.
Check that the loop covers all three types: `sh`, `ps`, `fish`.

3. **If missing, add fish generation**:
```bash
# Should generate for each agent + script type combination
for agent in "${ALL_AGENTS[@]}"; do
    for script_type in sh ps fish; do
        # Generate package logic
    done
done
```

**Validation**:
- Build packages locally: `bash .github/workflows/scripts/create-release-packages.sh`
- Verify fish zip files created: `spec-kit-template-claude-fish-*.zip`
- Count packages: should be 3x agents (sh, ps, fish for each)

---

**File**: `.github/workflows/scripts/create-github-release.sh`

**Required Changes**:

Add fish packages to release upload command. Locate the `gh release create` command and ensure fish packages are included:

```bash
gh release create "$VERSION" \
  .genreleases/spec-kit-template-claude-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-claude-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-claude-fish-"$VERSION".zip \
  .genreleases/spec-kit-template-gemini-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-gemini-ps-"$VERSION".zip \
  .genreleases/spec-kit-template-gemini-fish-"$VERSION".zip \
  # ... (repeat for all agents)
```

**Validation**:
- Check generated release notes include all fish packages
- Verify download URLs work for fish templates

---

### Phase 2: Project Standards Compliance

#### Task 2.1: Update CHANGELOG.md
**File**: `CHANGELOG.md`  
**Location**: After line 10 (in LATEST_VERSION section)

**Required Addition**:
```markdown
## [LATEST_VERSION] - RELEASE_DATE

### Added

- Support for Fish Shell as a script type option via `--script fish` flag
- Fish shell variants for all automation scripts: `check-prerequisites.fish`, `create-new-feature.fish`, `setup-plan.fish`, `update-agent-context.fish`, and `common.fish`
- Interactive script type selection includes Fish Shell option
- Fish shell templates available for all supported AI agents

### Changed

- Script type selection now offers three options: POSIX Shell (bash/zsh), PowerShell, and Fish Shell
- Default script type detection remains OS-based (Windows: PowerShell, other: POSIX Shell)

### Fixed

- Corrected fish script syntax errors that would prevent execution
- Fish scripts now properly handle arguments and error conditions
```

**Validation**:
- Entry follows Keep a Changelog format
- Links to Semantic Versioning maintained
- Clear description of changes

---

#### Task 2.2: Bump Version in pyproject.toml
**File**: `pyproject.toml`  
**Line**: 3

**Current**:
```toml
version = "0.0.17"
```

**Required Change**:
```toml
version = "0.0.18"
```

**Note**: This follows semantic versioning for a minor feature addition.

**Validation**:
- Version matches CHANGELOG entry
- No other version references need updating

---

#### Task 2.3: Update CHANGELOG Version Header
**File**: `CHANGELOG.md`  
**Line**: 10

**Current**:
```markdown
## [LATEST_VERSION] - RELEASE_DATE
```

**Required Change**:
```markdown
## [0.0.18] - 2025-09-30
```

**Validation**:
- Date is actual release date
- Version matches pyproject.toml

---

### Phase 3: Code Quality Improvements

#### Task 3.1: Improve String Quoting Consistency in Fish Scripts
**Files**: All fish scripts in `scripts/fish/`

**Pattern to Fix**:
```fish
# Inconsistent:
if test -d "$argv[1]"; and test -n "(ls -A $argv[1] 2>/dev/null)"

# Consistent:
if test -d "$argv[1]"; and test -n "(ls -A "$argv[1]" 2>/dev/null)"
```

**Files to Review**:
- `common.fish:126` - Directory checking
- `check-prerequisites.fish:119` - Command substitution contexts
- `update-agent-context.fish` - Variable expansions in loops

**Validation**:
- Run shellcheck equivalent for fish (if available)
- Test with filenames containing spaces
- No regressions in existing functionality

---

#### Task 3.2: Optimize Number Extraction in common.fish
**File**: `scripts/fish/common.fish`  
**Lines**: 40-50

**Current Code**:
```fish
set -l matches (string match -r '^([0-9]{3})-' $dirname)
if test (count $matches) -gt 0
    set -l number (string sub -s 1 -l 3 $dirname)
    # Convert to decimal (remove leading zeros)
    set -l number (math $number)
```

**Problem**: Extracts number with regex, then extracts again with substring

**Improved Code**:
```fish
set -l matches (string match -r '^([0-9]{3})-' $dirname)
if test (count $matches) -gt 0
    # Use captured group directly
    set -l number (string replace -r '^0+' '' $matches[2])
    # Convert to number
    set -l number (math $number + 0)
```

**Or simpler**:
```fish
if string match -qr '^([0-9]{3})-' $dirname
    set -l number (string sub -s 1 -l 3 $dirname)
    set -l number (math $number + 0)  # Forces numeric conversion
```

**Validation**:
- Feature directories correctly identified
- Highest number calculation works
- Leading zeros handled properly

---

### Phase 4: Testing & Validation

#### Task 4.1: Manual Testing Checklist

**Pre-Release Testing**:

1. **CLI Integration**
   ```bash
   # Test fish flag acceptance
   specify init test-project --script fish --ai claude
   
   # Test interactive selection
   specify init test-project --ai claude
   # Verify fish appears in menu
   
   # Test all agents with fish
   for agent in claude gemini copilot cursor qwen opencode windsurf kilocode auggie roo; do
       specify init "test-$agent" --script fish --ai "$agent" --ignore-agent-tools
   done
   ```

2. **Fish Script Execution**
   ```bash
   cd test-project
   
   # Test each fish script
   fish .specify/scripts/fish/check-prerequisites.fish --help
   fish .specify/scripts/fish/create-new-feature.fish --json "Test Feature"
   fish .specify/scripts/fish/setup-plan.fish --json
   fish .specify/scripts/fish/update-agent-context.fish claude
   ```

3. **Command Template Integration**
   ```bash
   # Verify fish scripts referenced in templates
   grep -r "fish:" .specify/templates/commands/
   
   # Test command execution (if AI agent available)
   # /specify "Test feature"
   # /plan "Use Python"
   # /tasks
   ```

4. **Edge Cases**
   - Project names with spaces
   - Non-git repositories (--no-git)
   - Current directory initialization (--here)
   - Feature directories with leading zeros (001, 010, 099)

---

#### Task 4.2: Package Generation Validation

**Build Packages**:
```bash
cd .github/workflows/scripts
./create-release-packages.sh
```

**Verify**:
```bash
# Count packages (should be agents × 3 script types)
ls -1 ../../.genreleases/*.zip | wc -l

# Check fish packages exist
ls -1 ../../.genreleases/*-fish-*.zip

# Inspect a fish package
unzip -l ../../.genreleases/spec-kit-template-claude-fish-*.zip | grep -E '\.fish$'
```

**Expected**:
- At least 10 agents × 3 types = 30+ zip files
- Each fish package contains all fish scripts
- Scripts have correct permissions (if applicable)
- Templates reference fish paths correctly

---

#### Task 4.3: Cross-Shell Compatibility

**Verify Parity Across Script Types**:

For each automation script, ensure consistent behavior:

| Script | Bash | PowerShell | Fish |
|--------|------|------------|------|
| check-prerequisites.sh/ps1/fish | ✓ | ✓ | Test |
| create-new-feature.sh/ps1/fish | ✓ | ✓ | Test |
| setup-plan.sh/ps1/fish | ✓ | ✓ | Test |
| update-agent-context.sh/ps1/fish | ✓ | ✓ | Test |

**Test Matrix**:
```bash
# Same inputs should produce same outputs
FEATURE="Test Feature Name"

# Bash
./scripts/bash/create-new-feature.sh "$FEATURE"
# PowerShell
pwsh ./scripts/powershell/create-new-feature.ps1 "$FEATURE"
# Fish
fish ./scripts/fish/create-new-feature.fish "$FEATURE"

# Compare outputs
```

---

### Phase 5: Documentation Sync

#### Task 5.1: Verify Documentation Accuracy

**Files to Review**:
- `README.md` - Example commands with fish
- `docs/installation.md` - Fish installation instructions
- `docs/quickstart.md` - Fish usage examples
- `AGENTS.md` - Process documentation (no changes needed)

**Verification**:
- All example commands are valid
- Screenshots/GIFs don't contradict fish support
- Installation steps complete and accurate
- No references to "coming soon" or "experimental"

---

#### Task 5.2: Add Fish Shell to Supported Environments

**File**: `README.md` (if prerequisites section exists)

**Addition**:
Under shell/environment requirements:
```markdown
- **Shell**: Bash, Zsh, Fish, or PowerShell
```

**Validation**:
- Clear which shells are supported
- Users understand fish is fully supported

---

## Success Criteria

### Must Have (MVP)
- [ ] `specify init --script fish` executes without errors
- [ ] All fish scripts execute without syntax errors
- [ ] Fish packages generated in release builds
- [ ] Version bumped to 0.0.18
- [ ] CHANGELOG updated with fish support
- [ ] Manual testing passes for core workflows

### Should Have
- [ ] String quoting consistent across fish scripts
- [ ] All agents tested with fish scripts
- [ ] Cross-shell parity validated
- [ ] Documentation reviewed and accurate

### Nice to Have
- [ ] Optimized regex extraction in common.fish
- [ ] Automated tests for fish scripts
- [ ] CI pipeline includes fish script validation

---

## Risk Assessment

### High Risk
- **Release package generation might fail**: Mitigate by testing build locally before release
- **Fish syntax differences from bash**: Mitigate with thorough manual testing
- **User environment issues**: Document fish installation requirements clearly

### Medium Risk
- **Breaking existing bash/PowerShell users**: No changes to existing scripts, isolated impact
- **Template command parsing**: Fish script paths already in templates, should work

### Low Risk
- **Version conflicts**: Clean version bump with no conflicts expected
- **Documentation drift**: All docs already reference fish, just making it work

---

## Rollback Plan

If critical issues discovered after release:

1. **Immediate**: Update documentation to mark fish as "experimental" or "beta"
2. **Short-term**: Release hotfix 0.0.19 removing fish from SCRIPT_TYPE_CHOICES
3. **Long-term**: Fix issues, test thoroughly, re-release in 0.0.20

**Rollback is safe because**:
- Fish is new feature, no existing users depend on it
- Bash and PowerShell users unaffected
- CLI flag is opt-in only

---

## Implementation Order

### Day 1: Critical Fixes (2-3 hours)
1. Task 1.1: Add fish to SCRIPT_TYPE_CHOICES ✓
2. Task 1.2: Remove `set -e argv` ✓
3. Task 1.3: Fix cleanup function ✓
4. Task 4.1: Basic manual testing

### Day 2: Integration (2-3 hours)
5. Task 1.4: Release package scripts ✓
6. Task 2.1: Update CHANGELOG ✓
7. Task 2.2-2.3: Version bump ✓
8. Task 4.2: Package validation

### Day 3: Polish (1-2 hours)
9. Task 3.1: String quoting review
10. Task 3.2: Optimize regex (optional)
11. Task 4.3: Cross-shell testing
12. Task 5.1: Documentation review

### Day 4: Final Validation
13. Complete testing checklist
14. Review all changes
15. Prepare for merge/release

---

## Notes

### Fish Shell Specific Considerations

**Error Handling**:
- Fish doesn't have `set -e` equivalent
- Use explicit `command; or return 1` pattern
- Functions return last command's exit status by default

**Variable Scoping**:
- `set -l` for local variables
- `set -g` for global variables
- `set -x` for exported (environment) variables
- Use `set -gx` for exported globals

**String Operations**:
- `string` command is powerful but different from bash
- Command substitution uses `(command)` not `$(command)`
- No parameter expansion like `${var:-default}`

**Arrays**:
- Fish uses 1-based indexing for arrays (unlike bash's 0-based)
- `$argv[1]` is first argument, not `$argv[0]`
- `(count $array)` for length, not `${#array[@]}`

---

## Related Issues

- Feature branch: `feature-add-fish-shell-support`
- Related PRs: (none yet)
- Discussion: (link if applicable)

---

## Approvals Required

- [ ] Technical lead review
- [ ] QA testing passed
- [ ] Documentation reviewed
- [ ] Release notes approved

---

**Document Version**: 1.0  
**Last Updated**: 2025-09-30  
**Owner**: Development Team
