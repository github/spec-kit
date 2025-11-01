# Multi-Repo Modes: Visual Comparison

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│  Which Multi-Repo Mode Do I Need?                          │
└─────────────────────────────────────────────────────────────┘

Start here:
  ↓
┌─────────────────────────────────────────────────┐
│ Do my repos work together as a single system?  │
│ (e.g., backend + frontend)                     │
└─────────────────────────────────────────────────┘
  ↓ YES                                  ↓ NO
  ↓                                      ↓
┌──────────────────────────┐  ┌────────────────────────────┐
│ Use WORKSPACE Mode       │  │ Use BATCH Mode             │
│ specify init --workspace │  │ init.sh --all-repos        │
└──────────────────────────┘  └────────────────────────────┘
  ↓                                      ↓
Centralized specs/              Independent repos
Cross-repo features             Bulk template updates
Convention routing              Each repo isolated
```

---

## Architecture Comparison

### Batch Mode (`--all-repos`)

```
~/git/
├── project-a/
│   ├── .specify/          ← Updated
│   ├── specs/             ← Project A's specs (independent)
│   └── ...
├── project-b/
│   ├── .specify/          ← Updated
│   ├── specs/             ← Project B's specs (independent)
│   └── ...
└── project-c/
    ├── .specify/          ← Updated
    ├── specs/             ← Project C's specs (independent)
    └── ...

Result: 3 independent projects, all with updated tooling
```

**Flow**:
1. Scan for repos with `.specify/`
2. Preview changes
3. Apply same updates to each repo
4. Each repo continues independently

---

### Workspace Mode (`--workspace`)

```
~/git/attun-project/
├── .specify/
│   └── workspace.yml      ← Workspace config (routing rules)
├── specs/                 ← Centralized specs for ALL repos
│   ├── backend-api/
│   ├── frontend-ui/
│   └── fullstack-feature/
├── attun-backend/         ← Target repo 1
│   ├── .specify/
│   └── src/
└── attun-frontend/        ← Target repo 2
    ├── .specify/
    └── src/

Result: Unified system with centralized spec management
```

**Flow**:
1. Discover all git repos
2. Create workspace config
3. Setup centralized specs/
4. Route specs to repos via conventions

---

## Command Comparison

### Batch Updates

```bash
# Update all my spec-kit projects
cd ~/git
./spec-kit/init.sh --all-repos \
  --ai claude \
  --search-path . \
  --max-depth 3

# What happens:
# 1. Finds: project-a/.specify, project-b/.specify, ...
# 2. Updates each repo's:
#    - .specify/templates/
#    - .specify/scripts/
#    - .claude/commands/ (or .gemini/, etc.)
# 3. Each repo stays independent

# Use when:
# - Different products/services
# - No shared features
# - Want same tooling everywhere
```

### Workspace Initialization

```bash
# Create workspace for related repos
cd ~/git/my-system
specify init --workspace --auto-init

# What happens:
# 1. Finds all git repos: backend/, frontend/, ...
# 2. Creates .specify/workspace.yml
# 3. Creates specs/ directory
# 4. Initializes .specify/ in each repo
# 5. Sets up convention rules

# Use when:
# - Single product with multiple repos
# - Features span repos
# - Want centralized specs
```

---

## Real-World Scenarios

### Scenario 1: Freelancer with Multiple Clients

**Situation**: You maintain 5 different client projects, each using spec-kit

**Solution**: Batch Mode (`--all-repos`)

```bash
~/projects/
├── client-a-website/     (independent)
├── client-b-api/         (independent)
├── client-c-app/         (independent)
├── client-d-service/     (independent)
└── client-e-platform/    (independent)

Command: init.sh --all-repos
Reason: Projects are unrelated, just need same tooling
```

---

### Scenario 2: Full-Stack Application

**Situation**: You build a SaaS product with separate backend and frontend repos

**Solution**: Workspace Mode (`--workspace`)

```bash
~/git/my-saas/
├── api-server/          (coordinated)
├── web-client/          (coordinated)
└── mobile-app/          (coordinated)

Command: specify init --workspace
Reason: Repos work together, features span multiple repos
```

---

### Scenario 3: Enterprise Microservices

**Situation**: 10 microservices that need coordinated features

**Solution**: Workspace Mode (`--workspace`)

```bash
~/git/platform/
├── auth-service/
├── user-service/
├── payment-service/
├── notification-service/
├── analytics-service/
└── ... (10 total)

Command: specify init --workspace
Reason: Cross-service features, centralized management
```

---

### Scenario 4: Open Source Maintainer

**Situation**: You maintain 3 different open-source projects

**Solution**: Batch Mode (`--all-repos`)

```bash
~/oss/
├── project-alpha/       (OSS project 1)
├── project-beta/        (OSS project 2)
└── project-gamma/       (OSS project 3)

Command: init.sh --all-repos
Reason: Different projects, just want to update spec-kit tooling
```

---

## Feature Matrix

| Feature | Batch Mode | Workspace Mode |
|---------|-----------|----------------|
| **Discovery Method** | Finds `.specify/` | Finds `.git/` |
| **Minimum Setup** | Repos already initialized | Any git repos |
| **Specs Storage** | `repo/specs/` | `workspace/specs/` |
| **Cross-Repo Specs** | ❌ No | ✅ Yes |
| **Convention Routing** | ❌ No | ✅ Yes |
| **Multi-Repo Features** | ❌ No | ✅ Yes |
| **Capabilities Targeting** | N/A | ✅ Single-repo |
| **Template Updates** | ✅ Yes | Via batch mode |
| **Independent Repos** | ✅ Yes | 🔗 Coordinated |
| **Bulk Operations** | ✅ Yes | ❌ No |
| **Preview Before Execute** | ✅ Yes | N/A |

---

## Common Questions

### Can I convert from batch to workspace mode?

**Yes!** If you have independent repos and want to coordinate them:

```bash
# 1. Start with batch mode (each repo has .specify/)
init.sh --all-repos

# 2. Later, create workspace structure
cd parent-directory
specify init --workspace
# Repos keep their .specify/, now coordinated via workspace
```

### Can I use batch mode within a workspace?

**Yes!** Update templates across workspace repos:

```bash
# 1. Have workspace
cd ~/git/my-workspace
ls .specify/workspace.yml  # ✓ Exists

# 2. Bulk update all repos in workspace
init.sh --all-repos --search-path . --max-depth 2
```

### Which mode should I use for a monorepo?

**Neither!** A monorepo is a single git repository, so use standard single-repo mode:

```bash
cd my-monorepo
specify init --here
```

### Can I have multiple workspaces?

**Yes!** Each workspace is independent:

```bash
~/git/
├── workspace-1/
│   ├── .specify/workspace.yml
│   └── specs/
└── workspace-2/
    ├── .specify/workspace.yml
    └── specs/

# Update all workspaces:
cd ~/git
init.sh --all-repos --search-path workspace-1 --max-depth 2
init.sh --all-repos --search-path workspace-2 --max-depth 2
```

### Can I use specify CLI to update projects initialized with init.sh?

**Yes!** This is the recommended migration path for existing projects.

**Single project update:**

```bash
cd my-project
specify init --here --ai claude

# This updates:
# - .specify/templates/ (latest spec/plan templates)
# - .specify/scripts/ (latest automation scripts)
# - .claude/commands/ (or .gemini/, etc.)
#
# This preserves:
# - specs/ (all your specifications)
# - constitution.md (optional, you'll be prompted)
# - Your project code (never touched)
```

**Multiple projects - keep using init.sh!**

```bash
cd ~/git
./spec-kit/init.sh --all-repos --ai claude --search-path . --max-depth 3
```

**Important**: Both tools are complementary, not replacements:
- ✅ `specify init` → Better for new projects, single updates, cross-platform
- ✅ `init.sh --all-repos` → Better for bulk updates, batch operations, development

**Why update is needed:**

Slash commands (`/specify`, `/plan`) use **local templates** from `.specify/templates/`, not the globally installed CLI. Installing `specify` globally does NOT automatically update existing projects.

**See**: [Migration Guide](../../docs/guides/migration-init-to-cli.md) for comprehensive instructions.

---

## Decision Flowchart

```
Are your repos part of the same product/system?
│
├─ YES → Do features span multiple repos?
│   │
│   ├─ YES → WORKSPACE MODE
│   │         specify init --workspace
│   │
│   └─ NO  → Could still use workspace for centralization
│             or batch mode if truly independent
│
└─ NO  → Are they just different projects needing same tooling?
    │
    ├─ YES → BATCH MODE
    │         init.sh --all-repos
    │
    └─ NO  → Single repo mode
              specify init my-project
```

---

## Summary

| Your Situation | Use This | Command |
|----------------|----------|---------|
| Multiple independent projects | Batch Mode | `init.sh --all-repos` |
| Backend + Frontend system | Workspace Mode | `specify init --workspace` |
| Microservices platform | Workspace Mode | `specify init --workspace` |
| OSS projects (unrelated) | Batch Mode | `init.sh --all-repos` |
| Want to update all projects | Batch Mode | `init.sh --all-repos` |
| Need cross-repo features | Workspace Mode | `specify init --workspace` |
| Single monorepo | Single-Repo Mode | `specify init --here` |

**Still unsure?** Start with workspace mode - you can always use batch mode within it for template updates!
