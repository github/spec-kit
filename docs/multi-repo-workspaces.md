# Multi-Repo Workspace Support

Spec-kit now supports **multi-repository workspaces**, allowing you to manage specifications that span multiple git repositories from a centralized location.

## Overview

In a multi-repo workspace:

- **Specs live in a parent folder** (`~/git/my-workspace/specs/`)
- **Code changes happen in target repositories** (`~/git/my-workspace/backend/`, `~/git/my-workspace/frontend/`)
- **Convention-based routing** automatically determines which repo(s) a spec targets
- **Capabilities are single-repo** while parent specs can span multiple repos

## Initialization Methods

There are **two ways** to initialize a workspace:

### Method 1: Python CLI (Recommended)

```bash
# Install the CLI globally (one time)
uvx --from git+https://github.com/github/spec-kit.git@main specify-cli

# Then use it anywhere
specify init --workspace
specify init --workspace --auto-init
```

**Advantages:**
- ✅ Works from anywhere
- ✅ User-friendly `--workspace` flag
- ✅ Auto-finds scripts
- ✅ Pretty formatted output

### Method 2: Bash Script (Direct)

```bash
# Call the script directly (no installation needed)
/path/to/spec-kit/scripts/bash/init-workspace.sh .
/path/to/spec-kit/scripts/bash/init-workspace.sh . --auto-init
```

**Advantages:**
- ✅ No Python CLI installation required
- ✅ Direct, no wrapper
- ✅ Works immediately after cloning spec-kit

**Note:** Both methods are functionally identical - the Python CLI simply wraps the bash script with a nicer interface.

## Two Multi-Repo Modes

Spec-kit provides **two different multi-repo features** that serve complementary purposes:

### Mode 1: Batch Updates (`init.sh --all-repos`)

**Purpose**: Update multiple independent spec-kit repositories in bulk

**What it does**:
- Finds repos that **already have** `.specify/` folders
- Applies the same initialization/update to each one
- Updates templates, scripts, and AI commands in parallel
- Each repo remains independent with its own `specs/` folder

**When to use**:
- You have multiple separate projects using spec-kit
- You want to update templates/scripts across all projects
- Each repo manages its own specifications independently
- Projects are not tightly coupled

**Example**:
```bash
# Update all my spec-kit projects at once
cd ~/git
./spec-kit/init.sh --all-repos --ai claude --search-path . --max-depth 3

# Preview shows:
# Found 5 repos with .specify:
#   ~/git/project-a (.specify exists)
#   ~/git/project-b (.specify exists)
#   ~/git/api-service (.specify exists)
# ...
```

**Result**: Each repo gets updated independently, maintains its own specs.

---

### Mode 2: Centralized Workspace (`specify init --workspace`)

**Purpose**: Create a unified workspace for related repositories that work together

**What it does**:
- Finds **all git repos** in a directory (whether they have `.specify/` or not)
- Creates workspace configuration (`.specify/workspace.yml`)
- Sets up centralized `specs/` folder at workspace level
- Enables cross-repo features and convention-based routing
- Optionally initializes `.specify/` in each repo

**When to use**:
- You have related repos that form a single system (e.g., backend + frontend)
- You want centralized spec management for the entire system
- You need features that span multiple repos
- You want convention-based routing of specs to repos

**Example**:
```bash
# Initialize workspace for multi-repo project
cd ~/git/attun-project
specify init --workspace --auto-init

# Creates:
# ~/git/attun-project/
#   .specify/workspace.yml   ← Workspace config
#   specs/                     ← Centralized specs
#   attun-backend/.specify/    ← Repo-specific config
#   attun-frontend/.specify/
```

**Result**: Unified workspace with centralized specs, specs can target multiple repos.

---

### Comparison Table

| Feature | `--all-repos` (Batch) | `--workspace` (Centralized) |
|---------|----------------------|----------------------------|
| **Discovery** | Repos with `.specify/` | All git repos |
| **Specs Location** | Each repo's `specs/` | Workspace `specs/` |
| **Use Case** | Independent projects | Related system |
| **Updates** | Templates/scripts | Workspace structure |
| **Cross-repo Features** | ❌ No | ✅ Yes |
| **Convention Routing** | ❌ No | ✅ Yes |
| **Repo Independence** | ✅ Full | 🔗 Coordinated |

### Can They Work Together?

**Yes!** You can use both features in combination:

```bash
# 1. Initialize workspace for your multi-repo system
cd ~/git/attun-project
specify init --workspace --auto-init

# 2. Later, bulk update templates in all repos
cd ~/git
./spec-kit/init.sh --all-repos --search-path attun-project --max-depth 2
```

This gives you:
- ✅ Centralized workspace for related repos (backend + frontend)
- ✅ Ability to bulk update `.specify/` folders when templates change

### Decision Guide

**Choose `--all-repos` if**:
- ✅ You maintain multiple independent projects
- ✅ Each project has its own specification lifecycle
- ✅ You want to update spec-kit tooling across all projects
- ✅ Projects don't share features or capabilities

**Choose `--workspace` if**:
- ✅ You have a backend + frontend (or similar multi-repo system)
- ✅ Features span multiple repositories
- ✅ You want centralized spec management
- ✅ You need convention-based routing (e.g., `backend-*` → backend repo)

**Use both if**:
- ✅ You have a workspace AND want to bulk update templates
- ✅ You manage multiple workspaces and want to update them all

---

## Quick Start (Workspace Mode)

### 1. Initialize a Workspace

```bash
cd ~/git/my-project
specify init --workspace --auto-init
```

This will:
- ✅ Discover all git repositories in the directory
- ✅ Create `.specify/workspace.yml` with auto-detected configuration
- ✅ Create `specs/` directory for centralized specifications
- ✅ Initialize `.specify/` in each repo (with `--auto-init`)

### 2. Customize Conventions

Edit `.specify/workspace.yml` to define how spec names map to repositories:

```yaml
conventions:
  prefix_rules:
    backend-: [my-backend]      # backend-* → my-backend repo
    frontend-: [my-frontend]    # frontend-* → my-frontend repo
    fullstack-: [my-backend, my-frontend]  # fullstack-* → both repos

  suffix_rules:
    -api: [my-backend]          # *-api → my-backend repo
    -ui: [my-frontend]          # *-ui → my-frontend repo
```

### 3. Create Features

**Convention-based (automatic repo targeting):**

```bash
cd ~/git/my-project
/specify backend-user-auth      # Auto-routes to backend repo
/specify frontend-login-ui      # Auto-routes to frontend repo
/specify fullstack-dashboard    # Parent spec for both repos
```

**Explicit targeting:**

```bash
/specify --repo=my-backend custom-feature
```

### 4. Create Implementation Plans

Navigate to the target repository and create a plan:

```bash
cd my-backend
/plan
```

The plan will be created in the workspace specs directory, but git operations happen in the current repo.

### 5. Create Capabilities (Single-Repo)

For multi-repo parent specs, capabilities target a specific repository:

```bash
# From parent spec fullstack-dashboard
cd my-backend
/plan --capability cap-001 --repo=my-backend

cd ../my-frontend
/plan --capability cap-002 --repo=my-frontend
```

You'll be prompted to select the target repo if not specified.

## Workspace Structure

```
my-workspace/                    # Parent directory
  .specify/
    workspace.yml                # Workspace configuration
  specs/                         # Centralized specifications
    backend-user-auth/
      spec.md
      plan.md
      cap-001-auth-api/
        spec.md
        plan.md
    fullstack-dashboard/
      spec.md                    # Multi-repo parent spec
      plan.md
      cap-001-backend-api/       # Backend capability
        spec.md
        plan.md
      cap-002-frontend-ui/       # Frontend capability
        spec.md
        plan.md
  my-backend/                    # Git repository
    .specify/                    # Repo-specific config
    src/
    ...
  my-frontend/                   # Git repository
    .specify/
    src/
    ...
```

## Convention-Based Targeting

Specs are automatically routed to repositories based on their names:

| Spec Name | Matches | Target Repo(s) |
|-----------|---------|----------------|
| `backend-api-auth` | Prefix: `backend-` | Backend repo |
| `user-service-api` | Suffix: `-api` | Backend repo |
| `frontend-login-ui` | Prefix: `frontend-` | Frontend repo |
| `dashboard-ui` | Suffix: `-ui` | Frontend repo |
| `fullstack-admin` | Prefix: `fullstack-` | All repos |
| `random-feature` | No match | Prompts user to select |

Configure custom rules in `.specify/workspace.yml`.

## Workflow Examples

### Example 1: Backend-Only Feature

```bash
cd ~/git/my-workspace

# Create backend spec (auto-routed)
/specify backend-payment-api

# Verify spec location and branch
ls specs/backend-payment-api/spec.md    # ✓ Spec in workspace
cd my-backend && git branch             # ✓ Branch in backend repo

# Create implementation plan
/plan

# Implement in backend repo
# (all git operations happen in my-backend/)
```

### Example 2: Full-Stack Feature with Capabilities

```bash
cd ~/git/my-workspace

# Create parent spec (multi-repo)
/specify fullstack-user-management

# Decompose into capabilities
/decompose

# Capability 1: Backend API (targets my-backend)
cd my-backend
/plan --capability cap-001 --repo=my-backend

# Capability 2: Frontend UI (targets my-frontend)
cd ../my-frontend
/plan --capability cap-002 --repo=my-frontend

# Each capability:
# - Has its own branch in its target repo
# - Has spec/plan in workspace specs directory
# - Can be implemented and PR'd independently
```

### Example 3: Explicit Repo Targeting

```bash
cd ~/git/my-workspace

# Force a spec to target specific repo
/specify --repo=my-backend custom-feature

# Overrides convention-based routing
```

## Advanced Features

### Auto-Discovery

The `init-workspace.sh` script automatically discovers:

- All git repositories (searches up to depth 2)
- Repository names and paths
- Inferred aliases (e.g., `backend-service` → aliases: `backend`, `service`)

### Interactive Disambiguation

When multiple repos match a spec name, you'll be prompted:

```
Multiple target repositories matched for 'api-service':
  1) backend-api
  2) shared-api
Select target repository (1-2):
```

### Template Fallback

Templates are loaded in this order:

1. Workspace templates: `workspace-root/.specify/templates/`
2. Repo templates: `target-repo/.specify/templates/`

This allows workspace-wide template customization with repo-specific overrides.

### Git Operations

All git operations execute in the **target repository**, not the workspace root:

```bash
# When you run:
/specify backend-feature

# Behind the scenes:
# - Spec created in: workspace-root/specs/backend-feature/spec.md
# - Branch created in: workspace-root/backend-repo/ (via git -C)
```

## Migration from Single-Repo

To migrate an existing single-repo project to workspace mode:

1. **Create workspace structure:**

```bash
mkdir ~/git/my-workspace
mv ~/git/my-repo ~/git/my-workspace/
cd ~/git/my-workspace
```

2. **Initialize workspace:**

```bash
specify init --workspace
```

3. **Migrate existing specs (optional):**

```bash
mkdir -p specs
cp -r my-repo/specs/* specs/
# Update specs to remove them from repo if desired
```

4. **Update conventions:**

Edit `.specify/workspace.yml` to configure routing rules.

## Troubleshooting

### "No workspace found" Error

**Problem**: Scripts can't detect workspace mode.

**Solution**: Ensure `.specify/workspace.yml` exists in parent directory.

```bash
cd ~/git/my-workspace
ls .specify/workspace.yml  # Should exist
```

### "No target repository found" Error

**Problem**: Convention-based targeting didn't match any repo.

**Solutions**:
1. Use explicit targeting: `/specify --repo=backend my-feature`
2. Update conventions in `.specify/workspace.yml`
3. Choose from prompt when multiple matches

### Branch Created in Wrong Repo

**Problem**: Feature branch created in incorrect repository.

**Solution**:
1. Check spec name matches conventions
2. Verify workspace config conventions
3. Use `--repo` flag for explicit targeting

### Template Not Found

**Problem**: Template files missing during spec/plan creation.

**Solution**:
1. Check workspace templates: `workspace-root/.specify/templates/`
2. Check repo templates: `target-repo/.specify/templates/`
3. Re-run `specify init --workspace --auto-init` to initialize templates

## Configuration Reference

### Workspace Config (`.specify/workspace.yml`)

```yaml
workspace:
  name: my-workspace           # Workspace identifier
  root: /path/to/workspace     # Absolute path
  version: 1.0.0               # Config schema version

repos:
  - name: backend-service      # Repository name (directory name)
    path: ./backend-service    # Relative to workspace root
    aliases: [backend, api]    # Alternative names for matching

  - name: frontend-app
    path: ./frontend-app
    aliases: [frontend, ui]

conventions:
  prefix_rules:
    backend-: [backend-service]
    frontend-: [frontend-app]
    fullstack-: [backend-service, frontend-app]

  suffix_rules:
    -api: [backend-service]
    -ui: [frontend-app]

  defaults:
    ambiguous_prompt: true     # Prompt on multiple matches
    default_repo: null         # Default when no match (null = prompt)
```

### Convention Rule Matching

**Order of precedence:**

1. Explicit `--repo` flag
2. Prefix rules (left-to-right in config)
3. Suffix rules (left-to-right in config)
4. Default repo (if configured)
5. Interactive prompt (if `ambiguous_prompt: true`)
6. All repos (if no match and `ambiguous_prompt: false`)

## CLI Reference

### Workspace Initialization

```bash
specify init --workspace [workspace-dir]
specify init --workspace --auto-init         # Initialize .specify/ in all repos
specify init --workspace --force             # Overwrite existing config
```

### Feature Creation

```bash
/specify <feature-name>                      # Convention-based targeting
/specify --repo=<repo-name> <feature-name>   # Explicit targeting
```

### Plan Creation

```bash
/plan                                        # Parent feature plan
/plan --capability cap-001 --repo=<repo>     # Capability plan with target repo
```

## Best Practices

1. **Use descriptive spec names** that clearly indicate target repo(s)
   - ✅ `backend-payment-api`
   - ✅ `frontend-user-profile-ui`
   - ❌ `feature-123`

2. **Configure conventions early** based on your repo naming patterns

3. **Document workspace structure** in workspace `specs/README.md`

4. **Keep capabilities single-repo** even if parent spans multiple repos

5. **Use workspace templates** for organization-wide standards

6. **Test convention rules** with `/specify --help` and dry-runs

## Example Workspace Configurations

### Microservices

```yaml
repos:
  - name: auth-service
  - name: user-service
  - name: payment-service
  - name: notification-service

conventions:
  prefix_rules:
    auth-: [auth-service]
    user-: [user-service]
    payment-: [payment-service]
    notification-: [notification-service]
    platform-: [auth-service, user-service, payment-service, notification-service]
```

### Frontend + Backend + Mobile

```yaml
repos:
  - name: backend-api
  - name: web-app
  - name: mobile-app

conventions:
  prefix_rules:
    backend-: [backend-api]
    web-: [web-app]
    mobile-: [mobile-app]
    fullstack-: [backend-api, web-app, mobile-app]
```

### Monorepo + Libraries

```yaml
repos:
  - name: main-app
  - name: ui-library
  - name: utils-library

conventions:
  suffix_rules:
    -app: [main-app]
    -ui: [ui-library]
    -lib: [utils-library]
```

## Getting Help

- Documentation: `docs/multi-repo-workspaces.md` (this file)
- Testing Guide: `docs/multi-repo-testing.md`
- Example Config: `docs/example-workspace.yml`
- Issues: https://github.com/your-org/spec-kit/issues

---

**Next Steps:**
1. Initialize your first workspace: `specify init --workspace`
2. Customize conventions in `.specify/workspace.yml`
3. Create a test spec to validate routing
4. Review the testing guide for comprehensive examples
