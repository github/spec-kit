# Multi-Repo Workspace Support

Spec-kit now supports **multi-repository workspaces**, allowing you to manage specifications that span multiple git repositories from a centralized location.

## Overview

In a multi-repo workspace:

- **Specs live in a parent folder** (`~/git/my-workspace/specs/`)
- **Code changes happen in target repositories** (`~/git/my-workspace/backend/`, `~/git/my-workspace/frontend/`)
- **Convention-based routing** automatically determines which repo(s) a spec targets
- **Capabilities are single-repo** while parent specs can span multiple repos

## Version Controlling Your Workspace

> **⚠️ CRITICAL REQUIREMENT**: The workspace directory must be a git repository to version control your specifications. Without this, specs will not be tracked, and you'll lose the benefits of version control, code review, and team collaboration.

### Why This Matters

Specifications are living documents that evolve with your product. They need:
- **Version history** - Track why decisions were made and how requirements changed
- **Code review** - Specs should be reviewed just like code
- **Team collaboration** - Multiple developers need to work on specs
- **CI/CD integration** - Automated tooling needs to access specs
- **Traceability** - Link specs to commits, PRs, and deployments

### Initial Workspace Setup

When creating a multi-repo workspace, initialize it as a git repository:

```bash
# Navigate to your workspace directory
cd ~/git/my-workspace

# Initialize workspace-level configuration
specify init --workspace --auto-init

# Initialize git repository for the workspace
git init
git add .specify/ specs/
git commit -m "Initialize spec-kit workspace"

# Add remote and push (optional but recommended)
git remote add origin git@github.com:company/my-workspace.git
git push -u origin main
```

### Team Onboarding

Team members clone the workspace repository:

```bash
# Clone the workspace repository
git clone git@github.com:company/my-workspace.git
cd my-workspace

# Sub-repositories can be cloned as siblings (manual approach)
# They are NOT tracked in the workspace git repo
cd my-workspace
# (Sub-repos like backend/ and frontend/ already exist from workspace init)
```

### Alternative: Git Submodules

For tighter integration, use git submodules to track sub-repositories:

```bash
cd ~/git/my-workspace
git init

# Add sub-repositories as submodules
git submodule add git@github.com:company/backend.git backend
git submodule add git@github.com:company/frontend.git frontend

# Initialize workspace
specify init --workspace --auto-init

# Commit everything
git add .
git commit -m "Initialize workspace with submodules"
git push -u origin main
```

**Team setup with submodules:**
```bash
git clone --recursive git@github.com:company/my-workspace.git
cd my-workspace
# All sub-repos are automatically cloned
```

### Alternative Patterns

Different teams may prefer different approaches to managing specs:

#### Pattern A: Workspace as Git Repo (Recommended, Current Default)

**Structure:**
```
~/git/my-workspace/          ← Git repository for workspace
  .git/                      ← Version control for specs
  .specify/workspace.yml
  specs/                     ← Tracked by workspace repo
  backend/                   ← Separate git repo
  frontend/                  ← Separate git repo
```

**Pros:**
- ✅ Centralized spec management
- ✅ Cross-repo features easily documented
- ✅ Single source of truth for all specs

**Cons:**
- ❌ Requires team standardization
- ❌ Extra repo to manage

**Best for:** Teams with tightly coupled frontend/backend, microservices architectures

#### Pattern B: Separate Specs Repository

**Structure:**
```
~/git/
  company-specs/             ← Git repo for all specs
    specs/
  backend/                   ← Git repo
  frontend/                  ← Git repo
```

**Pros:**
- ✅ Clear separation of concerns
- ✅ Independent lifecycle
- ✅ Easier access control

**Cons:**
- ❌ Need to manage references between repos
- ❌ Extra coordination required

**Best for:** Large organizations, RFC/KEP-style processes (like Kubernetes, Rust)

#### Pattern C: Specs in Dominant Repository

**Structure:**
```
~/git/backend/              ← Git repo (primary)
  specs/                    ← All specs here, including cross-repo
  src/
```

**Pros:**
- ✅ No extra repository
- ✅ Simpler mental model
- ✅ Works with existing workflows

**Cons:**
- ❌ Feels unbalanced (backend "owns" frontend specs)
- ❌ Frontend team might miss updates

**Best for:** Small teams, backend-heavy systems, early-stage products

### Industry Precedent

This workspace-as-repository pattern is well-established:

- **Kubernetes** - Uses `kubernetes/enhancements` repo for KEPs spanning multiple component repos
- **Rust Language** - Uses `rust-lang/rfcs` repo for RFCs affecting compiler, stdlib, and tools
- **Android (AOSP)** - Uses repo manifest system with central coordination
- **Many enterprises** - Separate "platform-docs" or "architecture" repos for cross-cutting concerns

### Best Practices

1. **Commit specs frequently** - Treat specs like code
2. **Use PR reviews for specs** - Specs should be reviewed before implementation
3. **Write meaningful commit messages** - Explain why requirements changed
4. **Tag major versions** - Use git tags for major spec milestones
5. **Document workspace structure** - Add README to workspace repo
6. **Set up `.gitignore`** - Exclude temporary files, build artifacts
7. **Automate checks** - Use pre-commit hooks or CI to validate spec format

### Example `.gitignore` for Workspace

```gitignore
# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.bak
*~

# Don't ignore the sub-repos themselves
# (They're managed separately)
```

## Initialization Methods

There are **two ways** to initialize a workspace:

### Method 1: Python CLI (Recommended)

```bash
# Install the CLI globally (one time)
uvx --from git+https://github.com/hcnimi/spec-kit.git@main specify-cli

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

### 2. Version Control the Workspace

> **⚠️ IMPORTANT**: Don't skip this step!

```bash
cd ~/git/my-project
git init
git add .specify/ specs/
git commit -m "Initialize spec-kit workspace"

# Optional: Add remote repository
git remote add origin git@github.com:company/my-project.git
git push -u origin main
```

### 3. Customize Conventions

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
my-workspace/                    # Workspace git repository
  .git/                          # ← Version control for workspace
  .specify/
    workspace.yml                # Workspace configuration
  specs/                         # Centralized specifications (tracked by workspace)
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
  my-backend/                    # Git repository (separate from workspace)
    .git/                        # ← Independent git repo
    .specify/                    # Repo-specific config
    src/
    ...
  my-frontend/                   # Git repository (separate from workspace)
    .git/                        # ← Independent git repo
    .specify/
    src/
    ...
```

**Note:** The workspace directory (`my-workspace/`) is its own git repository that tracks specs and configuration. Sub-repositories (`my-backend/`, `my-frontend/`) are separate git repositories that track code. They are NOT tracked by the workspace git repo (unless using git submodules).

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

## GitHub Host Conventions and Jira Keys

### Overview

Spec-kit automatically detects each repository's GitHub host during workspace initialization and configures Jira key requirements accordingly. This enables workspaces with mixed requirements:
- Repos hosted on `github.marqeta.com` → **Jira keys required**
- Repos hosted on `github.com` → **Jira keys optional**
- Mixed workspaces → **Per-repo Jira requirements**

### How It Works

1. **Workspace Initialization:**
   ```bash
   specify init --workspace --auto-init
   ```
   - Detects GitHub remote URL for each repo
   - Extracts GitHub host (e.g., `github.marqeta.com`, `github.com`)
   - Sets `require_jira: true` for enterprise GitHub hosts
   - Sets `require_jira: false` for standard `github.com`

2. **Workspace Configuration:**
   ```yaml
   repos:
     - name: attun-backend
       path: ./attun-backend
       aliases: [backend, api]
       github_host: github.marqeta.com
       require_jira: true               # ← Auto-detected

     - name: attun-frontend
       path: ./attun-frontend
       aliases: [frontend, ui]
       github_host: github.com
       require_jira: false              # ← Auto-detected
   ```

3. **Smart Spec Routing:**
   - Convention matching **strips Jira keys** for routing
   - Example: `proj-123.backend-api` → matches `backend-` rule (using `backend-api`)
   - Full spec ID (with Jira key) preserved for directories and branches

### Spec Naming Patterns

**With Jira Key (required for github.marqeta.com):**
```bash
/specify proj-123.backend-api
# → Spec: specs/proj-123.backend-api/
# → Branch: hnimitanakit/proj-123.backend-api
# → Routes to: backend repo (matches "backend-" convention)
```

**Without Jira Key (allowed for github.com):**
```bash
/specify backend-api
# → Spec: specs/backend-api/
# → Branch: hnimitanakit/backend-api
# → Routes to: backend repo (matches "backend-" convention)
```

### Automatic Jira Key Prompts

When targeting a repo that requires Jira keys, you'll be prompted automatically:

```bash
/specify backend-api   # Forgot Jira key

# Output:
# Target repo 'attun-backend' requires JIRA key.
# Enter JIRA issue key (e.g., proj-123): _
```

### Mixed Workspace Example

**Workspace Structure:**
```
my-workspace/
  .specify/workspace.yml
  internal-service/        # github.marqeta.com (Jira required)
  public-docs/             # github.com (Jira optional)
```

**Workspace Config:**
```yaml
repos:
  - name: internal-service
    github_host: github.marqeta.com
    require_jira: true

  - name: public-docs
    github_host: github.com
    require_jira: false

conventions:
  prefix_rules:
    internal-: [internal-service]
    docs-: [public-docs]
```

**Usage:**
```bash
# Internal service (Jira required)
/specify proj-123.internal-auth
# ✓ Creates specs/proj-123.internal-auth/
# ✓ Routes to internal-service (stripped "proj-123." for matching)

# Public docs (Jira optional)
/specify docs-quickstart
# ✓ Creates specs/docs-quickstart/
# ✓ Routes to public-docs (no Jira key needed)
```

### Troubleshooting

#### "Jira key required" Error

**Problem**: Targeting a repo that requires Jira keys without providing one.

**Solution**:
```bash
# Option 1: Provide Jira key upfront
/specify proj-123.backend-feature

# Option 2: Respond to interactive prompt
/specify backend-feature
# Enter JIRA issue key (e.g., proj-123): proj-456
```

#### Convention Routing with Jira Keys

**Problem**: Spec with Jira key doesn't match conventions.

**Explanation**: Jira keys are automatically stripped for matching.

```bash
/specify proj-123.backend-api
# ↓ Convention matching uses: "backend-api"
# ✓ Matches "backend-" prefix rule
# ✓ Routes to backend repo
# ✓ Creates specs/proj-123.backend-api/ (keeps full name)
```

#### Checking Repo Requirements

**Check workspace config manually:**
```bash
cat .specify/workspace.yml | grep -A5 "name: backend-repo"
```

**Look for:**
```yaml
  - name: backend-repo
    github_host: github.marqeta.com   # ← GitHub host
    require_jira: true                # ← Jira requirement
```

### Best Practices

1. **Let workspace init detect requirements automatically**
   - Don't manually set `require_jira` unless overriding
   - Workspace initialization reads GitHub remotes accurately

2. **Use descriptive spec names** even with Jira keys
   ```bash
   # ✅ Good (clear feature name)
   /specify proj-123.user-auth-flow

   # ❌ Bad (unclear purpose)
   /specify proj-123.feature
   ```

3. **Document Jira key conventions** in team guidelines
   - Specify Jira project keys to use
   - Document branch naming conventions
   - Include examples for your organization

4. **Test convention routing** with sample specs
   ```bash
   # Test without creating branches (dry-run)
   /specify proj-123.test-backend-api --help
   # Check which repo would be targeted
   ```

### Enterprise GitHub Support

Spec-kit automatically detects and supports:
- **github.marqeta.com** (Marqeta enterprise)
- **github.{company}.com** (any enterprise GitHub)
- **Custom GitHub hosts** (set via git remote URL)

**Detection Logic:**
```bash
# github.marqeta.com → require_jira: true
# github.company.com → require_jira: true
# github.com → require_jira: false
```

### Configuration Override

**Manual override** (advanced use cases only):
```yaml
repos:
  - name: special-repo
    github_host: github.com
    require_jira: true    # ← Override: force Jira even for github.com
```

**Use cases for override:**
- Team policy requires Jira for all repos
- Repo switched from enterprise to github.com
- Testing Jira workflows

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

3. **Initialize git repository for workspace:**

```bash
cd ~/git/my-workspace
git init
git add .specify/ specs/
git commit -m "Initialize spec-kit workspace"

# Optional: Add remote
git remote add origin git@github.com:company/my-workspace.git
git push -u origin main
```

4. **Migrate existing specs (optional):**

```bash
mkdir -p specs
cp -r my-repo/specs/* specs/

# Commit migrated specs
git add specs/
git commit -m "Migrate specs from single-repo"

# Optionally remove specs from original repo
cd my-repo
git rm -r specs/
git commit -m "Move specs to workspace"
```

5. **Update conventions:**

Edit `.specify/workspace.yml` to configure routing rules.

```bash
cd ~/git/my-workspace
# Edit .specify/workspace.yml
git add .specify/workspace.yml
git commit -m "Configure workspace routing conventions"
```

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

## Working with Git Worktrees

Spec-kit fully supports git worktrees, allowing you to work on multiple features in parallel without switching branches.

### What are Git Worktrees?

Git worktrees let you have multiple working directories from the same repository, each checked out to a different branch. This enables:
- Working on multiple features simultaneously
- Running tests on one branch while coding on another
- Quick context switching without stashing changes

### Creating Worktrees in Workspaces

**Recommended Structure: Worktrees as Siblings**

```bash
workspace/
  .specify/workspace.yml
  specs/                  # Centralized specs
  backend/                # Main working tree
  frontend/               # Main working tree
  backend-auth-feature/   # Worktree for backend
  frontend-dashboard/     # Worktree for frontend
```

**Create a worktree:**
```bash
cd ~/workspace/backend
git worktree add ../backend-auth-feature

cd ../backend-auth-feature
# Now you're in the worktree
```

### Using `/specify` from Worktrees

You can run `/specify` from anywhere, including inside worktrees:

```bash
# From within a worktree
cd ~/workspace/backend-auth-feature

# Create new spec - operations execute HERE
/specify backend-new-api

# Result:
# - Spec created: workspace/specs/backend-new-api/spec.md
# - Branch created in THIS worktree (not the parent repo)
# - Ready to code immediately
```

### How Worktree Routing Works

**Key Principle: Local context wins when applicable**

| Your Location | Create Spec For | Git Operations Execute In |
|--------------|----------------|--------------------------|
| Backend worktree | `backend-*` spec | Your worktree ✅ |
| Backend worktree | `frontend-*` spec | Frontend parent repo |
| Backend parent repo | Any spec | Backend parent repo |
| Workspace root | Any spec | Target repo's parent |

**Example - Matching Repo:**
```bash
# In backend worktree
cd ~/workspace/backend-dashboard-worktree
/specify backend-api

# Operations execute in current worktree
# Convention: "backend-api" routes to backend repo
# Match: You're in backend worktree → executes here ✅
```

**Example - Different Repo:**
```bash
# In backend worktree, but creating frontend spec
cd ~/workspace/backend-dashboard-worktree
/specify frontend-ui

# Operations execute in frontend parent repo
# Convention: "frontend-ui" routes to frontend repo
# No match: You're in backend worktree → executes in frontend parent
```

### Working with Existing Specs

**For NEW specs:**
```bash
# 1. Create worktree
cd ~/workspace/frontend
git worktree add ../frontend-dashboard

# 2. cd into worktree
cd ../frontend-dashboard

# 3. Create spec FROM the worktree
/specify frontend-dashboard
# ✓ Creates spec and branch in worktree
```

**For EXISTING specs:**
```bash
# Spec already exists at: workspace/specs/frontend-dashboard/spec.md
# Branch already exists: username/frontend-dashboard

# 1. Create worktree from existing branch
cd ~/workspace/frontend
git worktree add ../frontend-dashboard-wt username/frontend-dashboard

# 2. cd into worktree
cd ../frontend-dashboard-wt

# 3. DON'T run /specify - it will prompt about overwriting!
# Instead, just work with the existing spec
vim ~/workspace/specs/frontend-dashboard/spec.md

# 4. Use other commands
/plan frontend-dashboard
/tasks cap-001
```

### Directory Structure Options

**Option 1: Worktrees as Siblings (Flat)**
```bash
workspace/
  backend/
  frontend/
  backend-feature-1/      # Easy to see
  backend-feature-2/
  frontend-feature-1/
```

**Option 2: Worktrees in Subdirectory (Organized)**
```bash
workspace/
  backend/
  frontend/
  .worktrees/             # All worktrees together
    backend-feature-1/
    backend-feature-2/
    frontend-feature-1/
```

**Create with subdirectory:**
```bash
mkdir -p ~/workspace/.worktrees
cd ~/workspace/backend
git worktree add ../.worktrees/backend-auth
```

### Best Practices

1. **Name worktrees descriptively:**
   ```bash
   git worktree add ../backend-auth-refactor    # Good
   git worktree add ../wt1                       # Bad
   ```

2. **Run `/specify` from the worktree when possible:**
   - More intuitive (operations happen where you are)
   - No need to remember to cd around

3. **Clean up worktrees when done:**
   ```bash
   cd ~/workspace/backend
   git worktree remove ../backend-auth-feature
   ```

4. **List all worktrees:**
   ```bash
   cd ~/workspace/backend
   git worktree list
   ```

### Limitations

**Worktrees OUTSIDE the workspace:**
- Workspace detection works via parent repo
- Specs still go to centralized workspace location
- All commands work normally

**Same branch in multiple worktrees:**
- Git prevents this automatically
- Each worktree must be on a different branch

### Troubleshooting

**"Branch already checked out" error:**
```bash
# The branch is checked out in another worktree
git worktree list  # See where it's checked out
# Either remove that worktree or checkout a different branch
```

**Workspace not detected from worktree:**
```bash
# Verify parent repo is in workspace
cd ~/workspace/backend  # parent repo
ls ../.specify/workspace.yml  # should exist

# Worktree detection walks up from parent repo location
```

**Operations executing in wrong location:**
```bash
# Check which repo you're in
git rev-parse --show-toplevel  # Shows worktree path
git rev-parse --git-common-dir  # Shows parent repo .git

# Convention routing depends on parent repo name, not worktree dir name
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
