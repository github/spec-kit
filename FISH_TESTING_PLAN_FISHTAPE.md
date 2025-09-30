# Fish Shell Testing Plan - Fishtape Implementation

**Framework**: Fishtape (TAP-producing test runner for fish shell)  
**Created**: 2025-09-30  
**Status**: Planning Phase

## Executive Summary

This document outlines a comprehensive testing strategy for all fish shell scripts in spec-kit using **Fishtape**, a test runner specifically designed for fish shell. Unlike generic shell testing frameworks, Fishtape runs natively in fish, allowing us to test fish functions directly without cross-shell compatibility issues.

## Why Fishtape?

### Advantages
- ✅ **Native fish support** - Runs in fish shell, no syntax translation needed
- ✅ **TAP output** - Test Anything Protocol for CI/CD integration
- ✅ **Simple syntax** - Clean `@test` decorator pattern
- ✅ **Active maintenance** - Well-maintained by Jorge Bucaran
- ✅ **CI/CD ready** - Official GitHub Actions support
- ✅ **Fisher integration** - Easy installation via fisher plugin manager

### Comparison to Previous Attempt
| Aspect | ShellSpec (Failed) | Fishtape (Recommended) |
|--------|-------------------|------------------------|
| Shell compatibility | POSIX (sh/bash) only | Native fish |
| Function testing | ❌ Can't import fish | ✅ Direct function access |
| Syntax | Complex BDD DSL | Simple @test pattern |
| Setup | Manual configuration | Fisher one-liner |
| CI integration | Generic | fish-shop GitHub Actions |

## Project Context

**Repository**: spec-kit (Spec-Driven Development toolkit)  
**Fish Scripts Location**: `/scripts/fish/`  
**Test Location**: `/test/` (Fishtape convention)  
**Scripts to Test**: 5 files, ~1,000 lines total

## Fish Shell Components Inventory

### 1. common.fish (132 lines)
**Complexity**: Medium  
**Type**: Shared library  
**Priority**: CRITICAL - All other scripts depend on this

**Functions to Test**:
- `get_repo_root()` - Repository root detection
- `get_current_branch()` - Branch/feature name resolution  
- `has_git()` - Git availability check
- `check_feature_branch()` - Branch naming validation
- `get_feature_dir()` - Feature directory path builder
- `get_feature_paths()` - Comprehensive path resolution
- `check_file()` - File status display
- `check_dir()` - Directory status display

**Estimated Tests**: ~25-30

### 2. check-prerequisites.fish (163 lines)
**Complexity**: Medium-High  
**Type**: CLI script with argument parsing  
**Priority**: HIGH

**Test Areas**:
- Command-line argument parsing
- JSON/text output modes
- Feature directory validation
- Document availability detection
- Error handling and messages

**Estimated Tests**: ~20-25

### 3. create-new-feature.fish (119 lines)
**Complexity**: Medium  
**Type**: Feature initialization script  
**Priority**: HIGH

**Test Areas**:
- Feature numbering system
- Branch name generation
- Git operations (conditional)
- Directory/file creation
- Template handling
- Environment variable setting

**Estimated Tests**: ~25-30

### 4. setup-plan.fish (55 lines)
**Complexity**: Low  
**Type**: Plan setup script  
**Priority**: MEDIUM

**Test Areas**:
- Template copying
- JSON/text output
- Feature path resolution
- Error handling

**Estimated Tests**: ~10-15

### 5. update-agent-context.fish (674 lines)
**Complexity**: High  
**Type**: Agent file management system  
**Priority**: HIGH

**Test Areas**:
- Plan.md parsing
- Multi-agent file handling
- Template generation
- File updates (atomic)
- Technology stack management

**Estimated Tests**: ~40-50

---

## Implementation Plan

### Phase 1: Setup & Infrastructure (Week 1)

#### 1.1 Install Fishtape
**Tasks**:
- [ ] Install Fisher if not present: `curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher`
- [ ] Install Fishtape: `fisher install jorgebucaran/fishtape`
- [ ] Verify installation: `fishtape --version`
- [ ] Document installation in README

**Deliverables**:
- Fishtape installed and working
- Installation documentation

#### 1.2 Directory Structure
**Tasks**:
- [ ] Create `test/` directory in project root
- [ ] Create `test/fixtures/` for test data
- [ ] Create `test/helpers.fish` for shared test utilities
- [ ] Create subdirectory structure matching scripts

**Directory Layout**:
```
test/
├── common.test.fish           # Tests for common.fish
├── check-prerequisites.test.fish
├── create-new-feature.test.fish
├── setup-plan.test.fish
├── update-agent-context.test.fish
├── helpers.fish               # Shared test utilities
└── fixtures/
    ├── templates/             # Sample template files
    ├── plans/                 # Sample plan.md files
    └── repos/                 # Mock repository structures
```

#### 1.3 Test Helpers
**Create**: `test/helpers.fish`

**Helper Functions**:
```fish
function setup_test_repo -d "Create isolated test repository"
    # Creates temp directory with optional git init
end

function cleanup_test_repo -d "Remove test repository"
    # Cleans up temp directories
end

function create_mock_feature -d "Create mock feature directory structure"
    # Sets up feature directories for testing
end

function create_mock_templates -d "Create test template files"
    # Generates template files for testing
end

function assert_output_contains -d "Check if output contains string"
    # Helper assertion for string matching
end
```

#### 1.4 CI/CD Setup
**Tasks**:
- [ ] Create `.github/workflows/fish-tests.yml`
- [ ] Use `fish-shop/install-fish-shell` action
- [ ] Use `fish-shop/run-fishtape-tests` action
- [ ] Configure for Ubuntu and macOS
- [ ] Add test status badge to README

**GitHub Actions Workflow**:
```yaml
name: Fish Tests

on:
  push:
    paths:
      - 'scripts/fish/**'
      - 'test/**'
  pull_request:
    paths:
      - 'scripts/fish/**'
      - 'test/**'

jobs:
  test:
    name: Test on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Fish Shell
        uses: fish-shop/install-fish-shell@v2
      
      - name: Install Fisher
        run: |
          fish -c "curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher"
      
      - name: Install Fishtape
        run: fish -c "fisher install jorgebucaran/fishtape"
      
      - name: Run Tests
        uses: fish-shop/run-fishtape-tests@v2
        with:
          patterns: test/*.test.fish
```

---

### Phase 2: Core Library Testing (Week 2)

#### Test File: `test/common.test.fish`

**Test Structure**:
```fish
# Source the script under test
source scripts/fish/common.fish

@test "get_repo_root: returns git root in git repository"
    # Setup
    set -l temp_repo (mktemp -d)
    git -C $temp_repo init -q
    
    # Test
    cd $temp_repo
    set -l result (get_repo_root)
    
    # Assert
    test "$result" = "$temp_repo"
    
    # Cleanup
    rm -rf $temp_repo
end

@test "get_repo_root: returns calculated path outside git"
    set -l temp_dir (mktemp -d)
    cd $temp_dir
    set -l result (get_repo_root)
    test -n "$result"
    rm -rf $temp_dir
end

@test "get_current_branch: returns SPECIFY_FEATURE when set"
    set -gx SPECIFY_FEATURE "001-test-feature"
    set -l result (get_current_branch)
    test "$result" = "001-test-feature"
    set -e SPECIFY_FEATURE
end

@test "has_git: returns success in git repository"
    set -l temp_repo (mktemp -d)
    git -C $temp_repo init -q
    cd $temp_repo
    has_git
    set -l status $status
    rm -rf $temp_repo
    test $status -eq 0
end

@test "check_feature_branch: accepts valid pattern 001-feature"
    check_feature_branch "001-test-feature" "true"
end

@test "check_feature_branch: rejects invalid pattern"
    not check_feature_branch "invalid-branch" "true"
end

@test "get_feature_dir: constructs correct path"
    set -l result (get_feature_dir "/test/repo" "001-feature")
    test "$result" = "/test/repo/specs/001-feature"
end

@test "check_file: shows checkmark for existing file"
    set -l temp_file (mktemp)
    set -l output (check_file "$temp_file" "test file")
    echo $output | grep -q "✓"
    set -l status $status
    rm $temp_file
    test $status -eq 0
end

@test "check_file: shows X for missing file"
    set -l output (check_file "/nonexistent/file" "missing file")
    echo $output | grep -q "✗"
end

@test "check_dir: shows checkmark for non-empty directory"
    set -l temp_dir (mktemp -d)
    touch $temp_dir/file.txt
    set -l output (check_dir "$temp_dir" "test dir")
    echo $output | grep -q "✓"
    set -l status $status
    rm -rf $temp_dir
    test $status -eq 0
end
```

**Estimated Tests**: ~25-30 tests covering all functions

---

### Phase 3: Script Testing (Weeks 3-4)

#### 3.1 Test File: `test/check-prerequisites.test.fish`

**Test Categories**:
- Argument parsing (--json, --require-tasks, --include-tasks, --paths-only)
- Feature directory validation
- Plan.md existence checks
- Available documents detection
- JSON output validation
- Error messages

**Sample Tests**:
```fish
@test "check-prerequisites: --help shows usage"
    set -l output (fish scripts/fish/check-prerequisites.fish --help 2>&1)
    echo $output | grep -q "Usage"
end

@test "check-prerequisites: --paths-only outputs without validation"
    # Setup mock feature
    set -l temp_repo (mktemp -d)
    # ... setup code ...
    
    cd $temp_repo
    set -l output (fish scripts/fish/check-prerequisites.fish --paths-only)
    echo $output | grep -q "REPO_ROOT"
    
    # Cleanup
    rm -rf $temp_repo
end

@test "check-prerequisites: --json outputs valid JSON"
    # Setup
    # ... create valid feature structure ...
    
    set -l output (fish scripts/fish/check-prerequisites.fish --json)
    echo $output | string match -q '{"*'
end
```

**Estimated Tests**: ~20-25 tests

#### 3.2 Test File: `test/create-new-feature.test.fish`

**Test Categories**:
- Feature number calculation
- Branch name generation
- Git operations (mocked)
- Directory creation
- Template copying
- SPECIFY_FEATURE environment variable

**Sample Tests**:
```fish
@test "create-new-feature: starts at 001 for empty specs"
    set -l temp_repo (mktemp -d)
    git -C $temp_repo init -q
    cd $temp_repo
    mkdir -p .specify/templates
    
    set -l output (fish scripts/fish/create-new-feature.fish "test feature")
    echo $output | grep -q "001"
    
    rm -rf $temp_repo
end

@test "create-new-feature: increments from highest existing"
    # Setup with existing features 001, 002, 005
    # Test that new feature is 006
end

@test "create-new-feature: converts name to lowercase"
    # Test branch name generation
end

@test "create-new-feature: replaces special characters with hyphens"
    # Test name sanitization
end
```

**Estimated Tests**: ~25-30 tests

#### 3.3 Test File: `test/setup-plan.test.fish`

**Test Categories**:
- Template copying
- JSON output
- Feature path resolution
- Error handling

**Estimated Tests**: ~10-15 tests

#### 3.4 Test File: `test/update-agent-context.test.fish`

**Test Categories**:
- Plan parsing (Language/Version, Dependencies, Storage, Project Type)
- Technology stack formatting
- Template generation
- File updates (atomic operations)
- Multi-agent support (10+ agents)
- Timestamp updates
- Recent changes tracking

**Estimated Tests**: ~40-50 tests

---

### Phase 4: Integration & Edge Cases (Week 5)

#### Test File: `test/integration.test.fish`

**Test Scenarios**:
- Full workflow: create-new-feature → setup-plan → check-prerequisites → update-agent-context
- Multiple features in sequence
- Git vs non-git workflows
- Template availability handling

**Estimated Tests**: ~10-15 tests

#### Test File: `test/edge-cases.test.fish`

**Test Scenarios**:
- Empty repositories
- Missing templates
- Permission errors
- Invalid UTF-8 characters
- Extremely long inputs
- Concurrent execution
- Out-of-sequence feature numbers

**Estimated Tests**: ~15-20 tests

---

### Phase 5: Documentation & Polish (Week 6)

**Tasks**:
- [ ] Create `TESTING.md` - Comprehensive testing guide
- [ ] Update `README.md` with testing section and badge
- [ ] Add comments to all test files
- [ ] Create `test/README.md` with test organization
- [ ] Document test helper functions
- [ ] Create troubleshooting guide
- [ ] Add contributing guidelines for tests

---

## Fishtape Test Syntax Reference

### Basic Test Structure
```fish
@test "description" (command) = "expected"
@test "description" (command) -eq 5
@test "description" (command)  # Tests exit code 0
```

### Operators
- `=` - String equality
- `-eq` - Numeric equality
- `-ne` - Numeric inequality
- `-gt` - Greater than
- `-lt` - Less than
- `-ge` - Greater than or equal
- `-le` - Less than or equal

### Setup and Teardown Pattern
```fish
function setup
    set -g TEST_DIR (mktemp -d)
end

function teardown
    rm -rf $TEST_DIR
end

@test "my test"
    setup
    # Test code here
    teardown
end
```

### Testing Exit Codes
```fish
@test "command succeeds"
    my_function
end

@test "command fails"
    not my_failing_function
end
```

### Testing Output
```fish
@test "function outputs correct text"
    set -l output (my_function)
    echo $output | grep -q "expected text"
end
```

---

## Test Fixtures

### Fixture Organization
```
test/fixtures/
├── templates/
│   ├── spec-template.md
│   ├── plan-template.md
│   └── agent-file-template.md
├── plans/
│   ├── complete-plan.md      # Full plan with all fields
│   ├── minimal-plan.md        # Sparse plan
│   └── invalid-plan.md        # Malformed plan
└── repos/
    ├── empty-repo/            # No features
    ├── single-feature/        # One feature (001)
    └── multi-feature/         # Multiple features (001-005)
```

### Loading Fixtures
```fish
function load_fixture
    set -l fixture_path "test/fixtures/$argv[1]"
    cat $fixture_path
end

# Usage in tests
@test "parses complete plan"
    set -l plan_content (load_fixture "plans/complete-plan.md")
    # Test parsing logic
end
```

---

## Success Metrics

### Coverage Targets
- **Overall Coverage**: ≥ 80% of functions
- **Critical Functions** (common.fish): ≥ 90%
- **Error Paths**: ≥ 75%
- **Edge Cases**: ≥ 70%

### Quality Gates
- [ ] All tests pass on macOS and Linux
- [ ] Test execution time < 30 seconds for full suite
- [ ] No test flakiness (3 consecutive runs pass)
- [ ] All public functions have tests
- [ ] Documentation complete

---

## Test Count Summary

| Phase | Component | Tests | Effort |
|-------|-----------|-------|--------|
| Phase 1 | Infrastructure | - | 1 week |
| Phase 2 | common.fish | ~25-30 | 1 week |
| Phase 3.1 | check-prerequisites.fish | ~20-25 | 2 days |
| Phase 3.2 | create-new-feature.fish | ~25-30 | 3 days |
| Phase 3.3 | setup-plan.fish | ~10-15 | 1 day |
| Phase 3.4 | update-agent-context.fish | ~40-50 | 4 days |
| Phase 4 | Integration & Edge Cases | ~25-35 | 1 week |
| Phase 5 | Documentation | - | 1 week |
| **Total** | **All Components** | **~145-185** | **6 weeks** |

---

## Running Tests

### Local Development
```bash
# Run all tests
fishtape test/*.test.fish

# Run specific test file
fishtape test/common.test.fish

# Run with verbose output
fishtape test/*.test.fish -v

# Run specific test by pattern
fishtape test/common.test.fish | grep "get_repo_root"
```

### CI/CD
Tests run automatically via GitHub Actions on:
- Push to any branch
- Pull requests
- Manual workflow dispatch

---

## Advantages Over Previous Approach

| Aspect | ShellSpec (Failed) | Fishtape (This Plan) |
|--------|-------------------|----------------------|
| **Complexity** | High (BDD DSL, contexts, describes) | Low (simple @test pattern) |
| **Setup Time** | Hours of configuration | Minutes (`fisher install`) |
| **Test Writing** | Complex mocking, can't import fish | Direct function calls |
| **Maintenance** | Difficult to debug | Clear, straightforward |
| **CI Integration** | Generic, manual setup | Purpose-built GitHub Actions |
| **Documentation** | Extensive reading required | Simple, clear syntax |
| **Learning Curve** | Steep | Gentle |

---

## Risk Mitigation

### Risks Identified
1. **Fishtape Compatibility** - Verify works with fish 3.3+
2. **CI Environment** - Ensure GitHub Actions runners support fish
3. **Test Isolation** - Prevent tests from interfering with each other
4. **Git Operations** - Handle git commands in CI environments

### Mitigation Strategies
1. Test locally with fish 3.3+ before CI integration
2. Use official `fish-shop` GitHub Actions (proven reliable)
3. Use temporary directories with unique names for each test
4. Mock git operations or use temporary git repos

---

## Next Steps

1. **Review and approve this plan**
2. **Install Fishtape** locally for validation
3. **Create Phase 1 infrastructure** (directories, helpers, CI)
4. **Write Phase 2 tests** for common.fish (most critical)
5. **Iterate** through remaining phases
6. **Document** as we go

---

**Document Version**: 1.0  
**Created**: 2025-09-30  
**Framework**: Fishtape  
**Status**: Planning - Awaiting Approval
