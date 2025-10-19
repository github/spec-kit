# Multi-Repo Workspace Support

Spec-kit now supports **multi-repository workspaces**, allowing you to manage specifications that span multiple git repositories from a centralized location.

## Overview

In a multi-repo workspace:

- **Specs live in a parent folder** (`~/git/my-workspace/specs/`)
- **Code changes happen in target repositories** (`~/git/my-workspace/backend/`, `~/git/my-workspace/frontend/`)
- **Convention-based routing** automatically determines which repo(s) a spec targets
- **Capabilities are single-repo** while parent specs can span multiple repos

## Quick Start

### 1. Initialize a Workspace

```bash
cd ~/git/my-project
specify init --workspace --auto-init
```

This will:
- ✅ Discover all git repositories in the directory
- ✅ Create `.spec-kit/workspace.yml` with auto-detected configuration
- ✅ Create `specs/` directory for centralized specifications
- ✅ Initialize `.specify/` in each repo (with `--auto-init`)

### 2. Customize Conventions

Edit `.spec-kit/workspace.yml` to define how spec names map to repositories:

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
  .spec-kit/
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

Configure custom rules in `.spec-kit/workspace.yml`.

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

Edit `.spec-kit/workspace.yml` to configure routing rules.

## Troubleshooting

### "No workspace found" Error

**Problem**: Scripts can't detect workspace mode.

**Solution**: Ensure `.spec-kit/workspace.yml` exists in parent directory.

```bash
cd ~/git/my-workspace
ls .spec-kit/workspace.yml  # Should exist
```

### "No target repository found" Error

**Problem**: Convention-based targeting didn't match any repo.

**Solutions**:
1. Use explicit targeting: `/specify --repo=backend my-feature`
2. Update conventions in `.spec-kit/workspace.yml`
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

### Workspace Config (`.spec-kit/workspace.yml`)

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
2. Customize conventions in `.spec-kit/workspace.yml`
3. Create a test spec to validate routing
4. Review the testing guide for comprehensive examples
