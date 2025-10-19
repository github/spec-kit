# Multi-Repo Workspace Testing Guide

This guide provides comprehensive testing scenarios for the multi-repo workspace functionality in spec-kit.

## Prerequisites

- spec-kit repository with latest changes
- Access to a directory with multiple git repositories (e.g., `~/git/attun-project`)
- Bash shell (for testing bash scripts)

## Test Environment Setup

### Option 1: Use Existing Multi-Repo Directory

If you have an existing multi-repo workspace (e.g., `~/git/attun-project`):

```bash
cd ~/git/attun-project
ls -la  # Verify multiple git repos exist
```

### Option 2: Create Test Environment

```bash
# Create test workspace
mkdir -p /tmp/test-workspace
cd /tmp/test-workspace

# Create mock repositories
mkdir backend-repo frontend-repo shared-lib
cd backend-repo && git init && cd ..
cd frontend-repo && git init && cd ..
cd shared-lib && git init && cd ..

# Verify structure
ls -la
```

## Test Cases

### Test 1: Workspace Initialization

**Objective**: Verify workspace discovery and configuration generation

```bash
cd /tmp/test-workspace

# Initialize workspace
bash ~/git/spec-kit/scripts/bash/init-workspace.sh .

# Expected outcomes:
# 1. ✓ .spec-kit/workspace.yml created
# 2. ✓ specs/ directory created
# 3. ✓ Configuration shows all 3 discovered repos
# 4. ✓ Convention rules are auto-generated
```

**Validation**:

```bash
# Check workspace config exists
cat .spec-kit/workspace.yml

# Should show:
# - workspace name and root
# - 3 repositories with paths
# - Default conventions (prefix/suffix rules)

# Check specs directory
ls -la specs/
cat specs/README.md  # Should contain usage guide
```

### Test 2: Workspace Discovery Functions

**Objective**: Test core workspace discovery functions

```bash
# Source the discovery script
source ~/git/spec-kit/scripts/bash/workspace-discovery.sh

# Test 1: Detect workspace root
detect_workspace /tmp/test-workspace
# Expected: /tmp/test-workspace

# Test 2: Check if in workspace mode
cd /tmp/test-workspace
is_workspace_mode
echo $?  # Expected: 0 (true)

cd /tmp
is_workspace_mode
echo $?  # Expected: 1 (false)

# Test 3: Find repositories
find_repos /tmp/test-workspace 2
# Expected: List of 3 repo paths

# Test 4: List workspace repos
cd /tmp/test-workspace
list_workspace_repos .
# Expected: backend-repo, frontend-repo, shared-lib

# Test 5: Get repo path
get_repo_path /tmp/test-workspace backend-repo
# Expected: /tmp/test-workspace/backend-repo
```

### Test 3: Convention-Based Repo Targeting

**Objective**: Test automatic repository targeting based on spec naming

**Setup**: Edit `.spec-kit/workspace.yml` to configure conventions:

```yaml
conventions:
  prefix_rules:
    backend-: [backend-repo]
    frontend-: [frontend-repo]
    fullstack-: [backend-repo, frontend-repo]

  suffix_rules:
    -api: [backend-repo]
    -ui: [frontend-repo]
```

**Test Cases**:

```bash
cd /tmp/test-workspace
source ~/git/spec-kit/scripts/bash/workspace-discovery.sh

# Test 1: Prefix match
get_target_repos_for_spec . "backend-user-auth"
# Expected: backend-repo

# Test 2: Suffix match
get_target_repos_for_spec . "user-management-api"
# Expected: backend-repo

# Test 3: Multi-repo match
get_target_repos_for_spec . "fullstack-dashboard"
# Expected: backend-repo frontend-repo

# Test 4: No match (should return all repos)
get_target_repos_for_spec . "random-feature"
# Expected: backend-repo frontend-repo shared-lib
```

### Test 4: Create Feature in Workspace Mode

**Objective**: Test feature creation with workspace mode

```bash
cd /tmp/test-workspace

# Source common functions
source ~/git/spec-kit/scripts/bash/common.sh

# Test 1: Create backend feature (convention-based)
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh backend-api-auth

# Expected outcomes:
# 1. ✓ Spec created in workspace: specs/backend-api-auth/spec.md
# 2. ✓ Branch created in backend-repo
# 3. ✓ Output includes WORKSPACE_ROOT, TARGET_REPO, REPO_PATH

# Validation
ls specs/backend-api-auth/spec.md
cd backend-repo && git branch | grep backend-api-auth

# Test 2: Create frontend feature
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh frontend-login-ui

# Expected: Branch in frontend-repo, spec in workspace

# Test 3: Explicit repo targeting
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh --repo=backend-repo custom-feature

# Expected: Branch in backend-repo regardless of name
```

### Test 5: Setup Plan in Workspace Mode

**Objective**: Test implementation plan creation in workspace

```bash
cd /tmp/test-workspace

# First, create a feature
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh backend-api-auth

# Navigate to target repo
cd backend-repo

# Create plan
bash ~/git/spec-kit/scripts/bash/setup-plan.sh

# Expected outcomes:
# 1. ✓ plan.md created in workspace: specs/backend-api-auth/plan.md
# 2. ✓ Output includes workspace metadata
# 3. ✓ Template loaded from workspace or repo

# Validation
ls ../specs/backend-api-auth/plan.md
cat ../specs/backend-api-auth/plan.md | grep "Workspace:"
```

### Test 6: Capability Targeting in Workspace

**Objective**: Test single-repo capability creation in multi-repo parent

```bash
cd /tmp/test-workspace

# Create multi-repo parent spec
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh fullstack-user-management

# Create capability directory structure
mkdir -p specs/fullstack-user-management/cap-001-backend-api
mkdir -p specs/fullstack-user-management/cap-002-frontend-ui

# Create capability specs
touch specs/fullstack-user-management/cap-001-backend-api/spec.md
touch specs/fullstack-user-management/cap-002-frontend-ui/spec.md

# Setup plan for backend capability
cd backend-repo
bash ~/git/spec-kit/scripts/bash/setup-plan.sh --capability=cap-001 --repo=backend-repo

# Expected outcomes:
# 1. ✓ Prompted for target repo (or uses --repo flag)
# 2. ✓ Capability branch created in backend-repo
# 3. ✓ plan.md in workspace specs/fullstack-user-management/cap-001-backend-api/

# Validation
git branch | grep cap-001
ls ../specs/fullstack-user-management/cap-001-backend-api/plan.md
```

### Test 7: Python CLI Workspace Init

**Objective**: Test Python CLI workspace initialization

```bash
# Create new test workspace
mkdir -p /tmp/test-workspace-2
cd /tmp/test-workspace-2

# Create mock repos
mkdir repo-a repo-b
cd repo-a && git init && cd ..
cd repo-b && git init && cd ..

# Initialize workspace via Python CLI
specify init --workspace --auto-init

# Expected outcomes:
# 1. ✓ .spec-kit/workspace.yml created
# 2. ✓ specs/ directory created
# 3. ✓ .specify/ initialized in repo-a and repo-b (with --auto-init)

# Validation
cat .spec-kit/workspace.yml
ls -la repo-a/.specify
ls -la repo-b/.specify
```

### Test 8: Git Operations in Target Repos

**Objective**: Verify git commands execute in correct repository

```bash
cd /tmp/test-workspace

# Create feature targeting backend
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh backend-feature-x

# Verify branch in backend-repo only
cd backend-repo && git branch | grep backend-feature-x
# Expected: ✓ Branch exists

cd ../frontend-repo && git branch | grep backend-feature-x
# Expected: ✗ Branch does not exist

# Test git_exec function
source ~/git/spec-kit/scripts/bash/workspace-discovery.sh
git_exec /tmp/test-workspace/backend-repo log --oneline -1
# Expected: Shows last commit from backend-repo
```

### Test 9: Path Resolution

**Objective**: Test workspace-aware path resolution

```bash
cd /tmp/test-workspace
source ~/git/spec-kit/scripts/bash/common.sh

# Test get_specs_dir
get_specs_dir
# Expected: /tmp/test-workspace/specs (workspace mode)

# Test get_feature_paths_smart with target repo
eval $(get_feature_paths_smart backend-repo)
echo $WORKSPACE_ROOT
# Expected: /tmp/test-workspace

echo $TARGET_REPO
# Expected: backend-repo

echo $REPO_PATH
# Expected: /tmp/test-workspace/backend-repo
```

### Test 10: Template Metadata

**Objective**: Verify workspace metadata in generated specs

```bash
cd /tmp/test-workspace

# Create feature
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh backend-test-feature

# Check spec template includes workspace metadata
cat specs/backend-test-feature/spec.md | grep -A 2 "Workspace Metadata"
# Expected: Shows workspace name and target repo placeholders

# Create plan
cd backend-repo
bash ~/git/spec-kit/scripts/bash/setup-plan.sh

# Check plan includes workspace metadata
cat ../specs/backend-test-feature/plan.md | grep -A 3 "Workspace:"
# Expected: Shows workspace metadata section
```

## Integration Test: Full Workflow

**Scenario**: Create a full-stack feature with separate frontend and backend capabilities

```bash
cd /tmp/test-workspace

# 1. Create parent multi-repo spec
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh fullstack-auth-system

# 2. Decompose into capabilities
mkdir -p specs/fullstack-auth-system/cap-001-backend-api
mkdir -p specs/fullstack-auth-system/cap-002-frontend-login

# 3. Create capability specs
cp ~/git/spec-kit/templates/capability-spec-template.md \
   specs/fullstack-auth-system/cap-001-backend-api/spec.md

cp ~/git/spec-kit/templates/capability-spec-template.md \
   specs/fullstack-auth-system/cap-002-frontend-login/spec.md

# 4. Setup plan for backend capability
cd backend-repo
bash ~/git/spec-kit/scripts/bash/setup-plan.sh \
     --capability=cap-001 --repo=backend-repo

# 5. Verify backend capability branch
git branch | grep "cap-001"
# Expected: ✓ Capability branch created

# 6. Setup plan for frontend capability
cd ../frontend-repo
bash ~/git/spec-kit/scripts/bash/setup-plan.sh \
     --capability=cap-002 --repo=frontend-repo

# 7. Verify frontend capability branch
git branch | grep "cap-002"
# Expected: ✓ Capability branch created

# 8. Verify workspace structure
tree ../specs/fullstack-auth-system/
# Expected:
# specs/fullstack-auth-system/
#   spec.md
#   plan.md
#   cap-001-backend-api/
#     spec.md
#     plan.md
#   cap-002-frontend-login/
#     spec.md
#     plan.md
```

## Edge Cases and Error Handling

### Test: No Repositories Found

```bash
mkdir /tmp/empty-workspace
bash ~/git/spec-kit/scripts/bash/init-workspace.sh /tmp/empty-workspace

# Expected: ERROR message about no git repositories found
```

### Test: Ambiguous Repo Targeting (Interactive)

```bash
cd /tmp/test-workspace

# Edit workspace.yml to create ambiguous rule
# Both backend-repo and shared-lib match "-api" suffix

# Create feature with ambiguous name
bash ~/git/spec-kit/scripts/bash/create-new-feature.sh generic-api

# Expected: Prompts user to select target repo
```

### Test: Force Overwrite Workspace Config

```bash
cd /tmp/test-workspace

# Reinitialize with --force
bash ~/git/spec-kit/scripts/bash/init-workspace.sh . --force

# Expected: ✓ Workspace config regenerated
```

## Cleanup

```bash
# Remove test workspaces
rm -rf /tmp/test-workspace /tmp/test-workspace-2 /tmp/empty-workspace
```

## Success Criteria

All tests should pass with expected outcomes:

- ✅ Workspace discovery correctly identifies git repositories
- ✅ Configuration auto-generation produces valid YAML
- ✅ Convention-based targeting routes specs to correct repos
- ✅ Git operations execute in target repositories
- ✅ Specs and plans created in workspace directory
- ✅ Capability branches created in single target repo
- ✅ Templates include workspace metadata
- ✅ Python CLI delegates to bash scripts correctly
- ✅ Error handling provides clear messages

## Reporting Issues

If any test fails, please report:

1. Test case number and description
2. Expected vs. actual outcome
3. Error messages (if any)
4. Environment details (OS, bash version, git version)
5. Workspace structure (output of `tree` or `ls -R`)
