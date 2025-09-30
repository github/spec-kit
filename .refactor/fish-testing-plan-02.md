# Fish Shell Testing Plan - ShellSpec Implementation

## Executive Summary

This document outlines a comprehensive testing strategy for all fish shell scripts in the spec-kit project using ShellSpec, a BDD-style testing framework. The plan covers 5 fish scripts totaling ~1,000 lines of code with varying complexity levels.

## Project Context

**Repository**: spec-kit (Spec-Driven Development toolkit)  
**Fish Scripts Location**: `/scripts/fish/`  
**Testing Framework**: ShellSpec (cross-shell BDD framework)  
**Test Location**: `/spec/fish/` (following ShellSpec conventions)

## Fish Shell Components Inventory

### 1. common.fish (132 lines)
**Complexity**: Medium  
**Type**: Shared library  
**Dependencies**: Git (optional)

**Functions**:
- `get_repo_root()` - Repository root detection with fallback
- `get_current_branch()` - Branch/feature name resolution
- `has_git()` - Git availability check
- `check_feature_branch()` - Branch naming validation
- `get_feature_dir()` - Feature directory path builder
- `get_feature_paths()` - Comprehensive path resolution
- `check_file()` / `check_dir()` - Status display utilities

### 2. check-prerequisites.fish (163 lines)
**Complexity**: Medium-High  
**Type**: Validation script with CLI interface  
**Dependencies**: common.fish, Git (optional)

**Features**:
- Multi-mode operation (JSON, text, paths-only)
- Argument parsing (--json, --require-tasks, --include-tasks, --paths-only)
- Feature directory validation
- Document availability checking
- Conditional file requirements

### 3. create-new-feature.fish (119 lines)
**Complexity**: Medium  
**Type**: Feature initialization script  
**Dependencies**: Git (optional), spec-template.md

**Features**:
- Feature numbering system (001-, 002-, etc.)
- Branch name generation from descriptions
- Git branch creation (conditional)
- Feature directory setup
- Template copying
- Environment variable management (SPECIFY_FEATURE)

### 4. setup-plan.fish (55 lines)
**Complexity**: Low  
**Type**: Plan setup script  
**Dependencies**: common.fish, plan-template.md

**Features**:
- Template copying
- JSON/text output
- Feature path resolution

### 5. update-agent-context.fish (674 lines)
**Complexity**: High  
**Type**: Agent file management system  
**Dependencies**: common.fish, agent-file-template.md, plan.md

**Features**:
- Plan.md parsing (extract metadata)
- Multi-agent support (10+ agents)
- Template-based file creation
- Content generation (build commands, project structures)
- Atomic file updates
- Technology stack management
- Recent changes tracking

---

## Testing Strategy

### Phase 1: Infrastructure Setup (Week 1)

#### 1.1 ShellSpec Installation & Configuration
**Tasks**:
- [ ] Install ShellSpec in development environment
- [ ] Create `.shellspec` configuration file
- [ ] Configure test directory structure (`spec/fish/`)
- [ ] Set up CI/CD integration (GitHub Actions)
- [ ] Document installation for contributors

**Deliverables**:
- ShellSpec installed and verified
- Configuration file with appropriate settings
- CI workflow file for automated testing
- Contributing documentation updated

#### 1.2 Test Fixture & Mock Setup
**Tasks**:
- [ ] Create test fixture directory (`spec/fixtures/`)
- [ ] Create mock git environment
- [ ] Create sample template files (spec, plan, agent)
- [ ] Create helper functions for test setup/teardown
- [ ] Implement isolated test environment (temp directories)

**Deliverables**:
- Reusable test fixtures
- Mock data for all script scenarios
- Helper library for common test operations

---

### Phase 2: Core Library Testing (Week 2)

#### 2.1 Test common.fish Functions
**Priority**: Critical (all other scripts depend on this)

**Test Suite**: `spec/fish/common_spec.sh`

**Test Coverage**:

##### `get_repo_root()`
- [ ] Returns git root when in git repository
- [ ] Returns calculated path when not in git repository
- [ ] Handles nested directory structures
- [ ] Returns consistent results across invocations

##### `get_current_branch()`
- [ ] Returns SPECIFY_FEATURE when set
- [ ] Returns git branch when in git repository
- [ ] Returns latest feature from specs/ directory
- [ ] Returns "main" as final fallback
- [ ] Handles feature numbering (001-, 002-, etc.)
- [ ] Correctly parses highest feature number

##### `has_git()`
- [ ] Returns success when git available
- [ ] Returns failure when git unavailable
- [ ] Handles git repository vs non-repository

##### `check_feature_branch()`
- [ ] Validates XXX- pattern (001-, 002-, etc.)
- [ ] Returns error for invalid branch names
- [ ] Skips validation for non-git repositories
- [ ] Displays appropriate warnings and errors

##### `get_feature_dir()`
- [ ] Constructs correct path from repo root and branch
- [ ] Handles special characters in branch names

##### `get_feature_paths()`
- [ ] Returns all required path variables
- [ ] Uses proper fish variable output format
- [ ] Correctly resolves HAS_GIT flag
- [ ] Generates all expected file paths (spec, plan, tasks, etc.)

##### `check_file()` / `check_dir()`
- [ ] Displays checkmark for existing files/dirs
- [ ] Displays X for missing files/dirs
- [ ] Handles non-empty directory requirement

**Estimated Tests**: ~35 test cases

---

### Phase 3: Script-Level Testing (Weeks 3-4)

#### 3.1 Test check-prerequisites.fish
**Priority**: High  
**Test Suite**: `spec/fish/check-prerequisites_spec.sh`

**Test Coverage**:

##### Argument Parsing
- [ ] Recognizes --json flag
- [ ] Recognizes --require-tasks flag
- [ ] Recognizes --include-tasks flag
- [ ] Recognizes --paths-only flag
- [ ] Displays help with --help/-h
- [ ] Rejects unknown arguments
- [ ] Handles flag combinations

##### Paths-Only Mode
- [ ] Outputs text format paths without validation
- [ ] Outputs JSON format paths without validation
- [ ] Exits successfully without checking files

##### Validation Mode (Default)
- [ ] Errors when feature directory missing
- [ ] Errors when plan.md missing
- [ ] Errors when tasks.md missing (with --require-tasks)
- [ ] Succeeds when all required files present

##### Available Docs Detection
- [ ] Detects research.md when present
- [ ] Detects data-model.md when present
- [ ] Detects contracts/ directory when present and non-empty
- [ ] Detects quickstart.md when present
- [ ] Includes tasks.md with --include-tasks
- [ ] Excludes empty contracts/ directory

##### Output Formats
- [ ] Text output format correct
- [ ] JSON output format valid and parseable
- [ ] JSON array correctly formatted (empty and populated)
- [ ] File status indicators correct (✓/✗)

##### Integration
- [ ] Sources common.fish successfully
- [ ] Uses get_feature_paths correctly
- [ ] Validates feature branch correctly
- [ ] Exits with correct status codes

**Estimated Tests**: ~30 test cases

---

#### 3.2 Test create-new-feature.fish
**Priority**: High  
**Test Suite**: `spec/fish/create-new-feature_spec.sh`

**Test Coverage**:

##### Argument Parsing
- [ ] Requires feature description
- [ ] Accepts --json flag
- [ ] Displays help with --help
- [ ] Concatenates multi-word descriptions

##### Repository Detection
- [ ] Detects git repository
- [ ] Detects .specify directory
- [ ] Falls back to manual search
- [ ] Errors when no repository found
- [ ] Handles script location correctly

##### Feature Numbering
- [ ] Starts at 001 for empty specs/
- [ ] Increments from highest existing number
- [ ] Handles gaps in numbering (001, 003, 004 → 005)
- [ ] Correctly parses three-digit prefixes
- [ ] Handles leading zeros properly

##### Branch Name Generation
- [ ] Converts to lowercase
- [ ] Replaces special characters with hyphens
- [ ] Removes duplicate hyphens
- [ ] Trims leading/trailing hyphens
- [ ] Truncates to first 3 words
- [ ] Adds feature number prefix

##### Git Operations
- [ ] Creates git branch when git available
- [ ] Skips branch creation when git unavailable
- [ ] Displays warning for non-git repos
- [ ] Checks out new branch successfully

##### Feature Directory Setup
- [ ] Creates specs/ directory if missing
- [ ] Creates feature-specific directory
- [ ] Copies spec template when available
- [ ] Creates empty spec.md when template missing
- [ ] Sets SPECIFY_FEATURE environment variable

##### Output
- [ ] Text mode outputs correct format
- [ ] JSON mode outputs valid JSON
- [ ] Includes branch name, spec file, and feature number

**Estimated Tests**: ~35 test cases

---

#### 3.3 Test setup-plan.fish
**Priority**: Medium  
**Test Suite**: `spec/fish/setup-plan_spec.sh`

**Test Coverage**:

##### Argument Parsing
- [ ] Recognizes --json flag
- [ ] Displays help with --help/-h
- [ ] Ignores unknown arguments

##### Integration
- [ ] Sources common.fish successfully
- [ ] Calls get_feature_paths correctly
- [ ] Validates feature branch
- [ ] Exits on invalid branch

##### Directory Operations
- [ ] Creates feature directory if missing
- [ ] Uses existing feature directory

##### Template Handling
- [ ] Copies template when available
- [ ] Displays success message for template copy
- [ ] Creates empty file when template missing
- [ ] Displays warning when template missing

##### Output
- [ ] Text mode outputs all variables
- [ ] JSON mode outputs valid JSON
- [ ] Includes all required fields
- [ ] Handles HAS_GIT correctly

**Estimated Tests**: ~20 test cases

---

#### 3.4 Test update-agent-context.fish
**Priority**: High  
**Test Suite**: `spec/fish/update-agent-context_spec.sh`

**Test Coverage**:

##### Environment Validation
- [ ] Errors when CURRENT_BRANCH empty
- [ ] Errors when plan.md missing
- [ ] Warns when template missing
- [ ] Displays helpful error messages
- [ ] Validates for git and non-git repos

##### Plan Parsing
- [ ] Extracts Language/Version field
- [ ] Extracts Primary Dependencies field
- [ ] Extracts Storage field
- [ ] Extracts Project Type field
- [ ] Handles missing fields gracefully
- [ ] Ignores "NEEDS CLARIFICATION" values
- [ ] Ignores "N/A" values
- [ ] Logs parsed values

##### Technology Stack Formatting
- [ ] Formats language only
- [ ] Formats framework only
- [ ] Formats language + framework
- [ ] Returns empty for no data
- [ ] Handles "NEEDS CLARIFICATION" in input

##### Template Generation
- [ ] Copies template successfully
- [ ] Replaces [PROJECT NAME] placeholder
- [ ] Replaces [DATE] placeholder
- [ ] Replaces technology stack placeholder
- [ ] Replaces project structure placeholder
- [ ] Replaces commands placeholder
- [ ] Replaces language conventions placeholder
- [ ] Replaces recent changes placeholder
- [ ] Converts \n to newlines
- [ ] Creates target directories as needed

##### File Updates
- [ ] Updates existing file without creating duplicates
- [ ] Adds new technology entries
- [ ] Adds new database entries
- [ ] Skips duplicate technology entries
- [ ] Updates timestamp
- [ ] Adds recent change entry
- [ ] Limits recent changes to 3 entries
- [ ] Preserves existing content

##### Agent-Specific Handling
- [ ] Updates Claude file (CLAUDE.md)
- [ ] Updates Gemini file (GEMINI.md)
- [ ] Updates Copilot file (.github/copilot-instructions.md)
- [ ] Updates Cursor file (.cursor/rules/specify-rules.mdc)
- [ ] Updates Qwen file (QWEN.md)
- [ ] Updates Agents file (AGENTS.md)
- [ ] Updates Windsurf file (.windsurf/rules/specify-rules.md)
- [ ] Updates Kilocode file (.kilocode/rules/specify-rules.md)
- [ ] Updates Auggie file (.augment/rules/specify-rules.md)
- [ ] Updates Roo file (.roo/rules/specify-rules.md)
- [ ] Errors on unknown agent type

##### Multi-Agent Operations
- [ ] Updates all existing agent files when no arg provided
- [ ] Creates default Claude file when no agents exist
- [ ] Skips non-existent agent files
- [ ] Reports success for each agent

##### Helper Functions
- [ ] `get_project_structure()` returns correct structure
- [ ] `get_commands_for_language()` generates correct commands
- [ ] `get_language_conventions()` returns conventions
- [ ] `log_info()` outputs to stdout
- [ ] `log_error()` outputs to stderr
- [ ] `log_success()` displays checkmark
- [ ] `log_warning()` outputs to stderr

##### Error Handling
- [ ] Handles unreadable plan files
- [ ] Handles unwritable target files
- [ ] Handles permission errors
- [ ] Cleans up temporary files on exit
- [ ] Returns correct exit codes

##### Summary Output
- [ ] Displays parsed information
- [ ] Shows usage information
- [ ] Reports completion status

**Estimated Tests**: ~70 test cases

---

### Phase 4: Integration & Edge Case Testing (Week 5)

#### 4.1 Cross-Script Integration Tests
**Test Suite**: `spec/fish/integration_spec.sh`

**Test Coverage**:
- [ ] Full workflow: create-new-feature → setup-plan → check-prerequisites → update-agent-context
- [ ] Feature creation with immediate plan setup
- [ ] Multiple features in sequence
- [ ] Git and non-git repository workflows
- [ ] SPECIFY_FEATURE environment variable propagation
- [ ] Template availability scenarios

**Estimated Tests**: ~15 test cases

#### 4.2 Edge Cases & Error Conditions
**Test Suite**: `spec/fish/edge-cases_spec.sh`

**Test Coverage**:
- [ ] Empty repository (no specs/)
- [ ] Corrupted template files
- [ ] Permission denied scenarios
- [ ] Invalid UTF-8 in descriptions
- [ ] Extremely long feature descriptions
- [ ] Special characters in paths
- [ ] Symbolic links in directory structure
- [ ] Concurrent script execution
- [ ] Out-of-sequence feature numbers (001, 005, 003)
- [ ] Missing git but .git directory exists
- [ ] Read-only file systems

**Estimated Tests**: ~25 test cases

---

### Phase 5: Performance & Compatibility Testing (Week 6)

#### 5.1 Performance Tests
**Test Suite**: `spec/fish/performance_spec.sh`

**Test Coverage**:
- [ ] Large repository (100+ features)
- [ ] Deep directory nesting
- [ ] Large plan.md files (>1MB)
- [ ] Many agent files simultaneously
- [ ] Script execution time benchmarks

**Estimated Tests**: ~10 test cases

#### 5.2 Compatibility Tests
**Test Suite**: `spec/fish/compatibility_spec.sh`

**Test Coverage**:
- [ ] Fish 3.x versions (3.0, 3.1, 3.2, 3.3, 3.4, 3.5+)
- [ ] macOS (Darwin)
- [ ] Linux (Ubuntu, Fedora, Alpine)
- [ ] Windows (WSL)
- [ ] Different git versions
- [ ] Different sed implementations (GNU sed, BSD sed)

**Estimated Tests**: ~15 test cases

---

## Test Infrastructure Components

### Directory Structure
```
spec/
├── fish/
│   ├── common_spec.sh           # Core library tests
│   ├── check-prerequisites_spec.sh
│   ├── create-new-feature_spec.sh
│   ├── setup-plan_spec.sh
│   ├── update-agent-context_spec.sh
│   ├── integration_spec.sh
│   ├── edge-cases_spec.sh
│   ├── performance_spec.sh
│   └── compatibility_spec.sh
├── fixtures/
│   ├── templates/
│   │   ├── spec-template.md
│   │   ├── plan-template.md
│   │   └── agent-file-template.md
│   ├── plans/
│   │   ├── complete-plan.md
│   │   ├── minimal-plan.md
│   │   └── invalid-plan.md
│   └── mock-repos/
│       ├── with-git/
│       ├── without-git/
│       └── with-features/
├── support/
│   ├── helpers.sh               # Common test helpers
│   ├── fixtures.sh              # Fixture management
│   └── assertions.sh            # Custom assertions
└── spec_helper.sh               # Global test configuration
```

### Helper Functions Required

#### Test Environment Helpers
```fish
setup_test_repo()      # Create isolated test repository
cleanup_test_repo()    # Remove test repository
create_mock_git()      # Initialize mock git repo
create_templates()     # Create all template files
create_feature_tree()  # Create existing feature structure
```

#### Assertion Helpers
```fish
assert_file_exists()
assert_file_contains()
assert_json_valid()
assert_json_equals()
assert_exit_code()
assert_output_contains()
assert_branch_exists()
assert_env_var_set()
```

#### Mock/Stub Helpers
```fish
mock_git_command()
stub_template_file()
mock_date_output()
mock_file_permissions()
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/fish-tests.yml`

```yaml
name: Fish Shell Tests

on:
  push:
    paths:
      - 'scripts/fish/**'
      - 'spec/fish/**'
  pull_request:
    paths:
      - 'scripts/fish/**'
      - 'spec/fish/**'

jobs:
  test:
    name: Test Fish Scripts
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        fish-version: ['3.3.1', '3.4.1', '3.5.1']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Fish
        run: |
          # OS-specific installation steps
      
      - name: Install ShellSpec
        run: |
          curl -fsSL https://git.io/shellspec | sh -s -- --yes
      
      - name: Run Tests
        run: |
          shellspec --format documentation
      
      - name: Upload Coverage
        if: success()
        uses: codecov/codecov-action@v3
```

---

## Success Metrics

### Code Coverage Targets
- **Overall Coverage**: ≥ 85%
- **Critical Functions**: ≥ 95% (common.fish, validation logic)
- **Error Paths**: ≥ 90%
- **Edge Cases**: ≥ 80%

### Quality Gates
- [ ] All tests pass on macOS and Linux
- [ ] No test failures on Fish 3.3+
- [ ] Test execution time < 60 seconds for full suite
- [ ] Zero test flakiness (3 consecutive runs pass)
- [ ] All critical paths have explicit tests
- [ ] Documentation complete for all test suites

### Maintenance Requirements
- [ ] Tests added for all new fish functions
- [ ] Tests updated when function signatures change
- [ ] CI pipeline passes before merge
- [ ] Test coverage maintained or improved
- [ ] Breaking changes require test updates

---

## Risk Assessment

### High Risk Areas
1. **update-agent-context.fish** - Most complex, many agents, file I/O heavy
2. **Git operations** - Difficult to mock, state management complexity
3. **File system operations** - Platform differences, permission issues
4. **Template parsing** - Regex complexity, edge case handling

### Mitigation Strategies
1. Extensive mocking of git commands
2. Isolated test environments (temp directories)
3. Platform-specific test variants
4. Comprehensive fixture library
5. Incremental rollout (common.fish first)

---

## Timeline Summary

| Phase | Duration | Deliverables | Tests |
|-------|----------|--------------|-------|
| Phase 1: Infrastructure | Week 1 | ShellSpec setup, fixtures, CI | 0 |
| Phase 2: Core Library | Week 2 | common.fish tests | ~35 |
| Phase 3: Script Testing | Weeks 3-4 | 4 script test suites | ~155 |
| Phase 4: Integration | Week 5 | Integration & edge cases | ~40 |
| Phase 5: Performance | Week 6 | Performance & compatibility | ~25 |
| **Total** | **6 weeks** | **Complete test suite** | **~255 tests** |

---

## Dependencies & Prerequisites

### Required Tools
- Fish shell 3.3+
- ShellSpec 0.28.1+
- Git 2.30+
- GNU/BSD sed
- Standard Unix utilities (basename, dirname, mktemp, etc.)

### Development Environment
- macOS 10.15+ or Linux (Ubuntu 20.04+, Fedora 35+)
- GitHub Actions runner compatibility
- Write access to test directories

### Documentation Updates Required
- CONTRIBUTING.md - Add testing guidelines
- README.md - Add testing badge and section
- AGENTS.md - Add testing requirements for new agents
- New file: TESTING.md - Comprehensive testing guide

---

## Open Questions

1. **Test Data Management**: Should we commit test fixtures or generate them dynamically?
   - **Recommendation**: Commit minimal fixtures, generate complex scenarios

2. **Mock Strategy**: How deeply should we mock git operations?
   - **Recommendation**: Mock git commands but use real git repos in temp directories

3. **Performance Baselines**: What are acceptable test execution times?
   - **Recommendation**: Full suite < 60s, individual test files < 10s

4. **Coverage Tools**: Which coverage tool for fish/shell scripts?
   - **Recommendation**: ShellSpec's built-in coverage + kcov for detailed reports

5. **Cross-shell Testing**: Should we test bash/PowerShell equivalents together?
   - **Recommendation**: Separate test suites, but share test scenarios/fixtures

---

## Next Steps

1. **Review this plan** with the team
2. **Approve budget** (6 weeks development time)
3. **Assign resources** (1-2 developers)
4. **Set up initial infrastructure** (Phase 1)
5. **Begin implementation** with common.fish (highest priority)
6. **Weekly progress reviews** and adjustments

---

## Appendix: Example Test Structure

### Example: common_spec.sh (partial)

```fish
#!/usr/bin/env fish

Describe 'common.fish'
  Include scripts/fish/common.fish
  
  Describe 'get_repo_root()'
    Context 'when in a git repository'
      setup() {
        TEST_DIR=$(mktemp -d)
        cd "$TEST_DIR"
        git init
      }
      
      cleanup() {
        rm -rf "$TEST_DIR"
      }
      
      Before 'setup'
      After 'cleanup'
      
      It 'returns the git root directory'
        When call get_repo_root
        The output should equal "$TEST_DIR"
        The status should be success
      End
    End
    
    Context 'when not in a git repository'
      # Test implementation
    End
  End
  
  Describe 'get_current_branch()'
    Context 'when SPECIFY_FEATURE is set'
      # Test implementation
    End
  End
End
```

---

**Document Version**: 1.0  
**Created**: 2025-09-30  
**Author**: AI Assistant  
**Status**: Draft for Review
