# Migration Guide: Moving to Global Specify CLI

This guide helps you migrate from local `init.sh` usage to the global `specify` CLI while ensuring your existing projects use the latest templates.

## Understanding the Architecture

### How Slash Commands Work

```
┌────────────────────────────────────────────────────────┐
│ /specify command in your project                       │
└────────────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────────────┐
│ Executes: .specify/scripts/bash/create-new-feature.sh │
│ Loads: .specify/templates/spec-template.md            │
│ NOT: Latest templates from GitHub/global CLI          │
└────────────────────────────────────────────────────────┘
```

**Key Point**: Global install of `specify` CLI does NOT automatically update your existing projects. Each project has its own `.specify/` directory with local templates and scripts.

### Why Templates Don't Auto-Update

When you run `/specify`, `/plan`, or other slash commands in your project:

1. Your AI agent reads the command from `.claude/commands/spec-kit/specify.md` (or `.gemini/`, etc.)
2. The command executes a script: `.specify/scripts/bash/create-new-feature.sh`
3. The script loads templates: `.specify/templates/spec-template.md`
4. All paths are **relative to your project directory**
5. The global `specify` CLI is **not involved** in this workflow

**Result**: Your projects use whatever template version was installed when you first initialized them.

## Migration Scenarios

### Scenario 1: Single Project Migration

**Situation**: You have one project initialized with `init.sh`, want to use global CLI going forward.

**Steps:**

```bash
# 1. Install globally (one-time)
uv tool install git+https://github.com/hcnimi/spec-kit.git

# 2. Update your existing project
cd ~/git/my-project
specify init --here --ai claude

# 3. When prompted about constitution.md:
#    - Choose "y" to preserve your existing constitution
#    - Choose "n" to use the latest template version

# 4. Verify update
ls .specify/templates/  # Should show latest templates
git diff .specify/      # Review what changed
```

**What gets updated:**
- ✅ `.specify/templates/` → Latest spec/plan templates
- ✅ `.specify/scripts/` → Latest automation scripts
- ✅ `.specify/memory/` → Latest memory files (except constitution if preserved)
- ✅ `.claude/commands/spec-kit/` → Latest slash commands (or `.gemini/`, `.cursor/`, etc.)
- ✅ `.specify/docs/` → Latest documentation

**What gets preserved:**
- ✅ `specs/` → All your specifications
- ✅ `constitution.md` → If you chose to preserve it
- ✅ Your project code → Never touched
- ✅ `.gitignore` → Updated, not replaced

### Scenario 2: Multiple Independent Projects

**Situation**: You maintain several unrelated projects, all use spec-kit.

**Recommendation**: Keep using `init.sh --all-repos` for bulk updates!

**Steps:**

```bash
# 1. Install globally (for creating new projects)
uv tool install git+https://github.com/hcnimi/spec-kit.git

# 2. Clone spec-kit locally (for bulk updates)
git clone https://github.com/hcnimi/spec-kit.git ~/git/spec-kit

# 3. Bulk update all existing projects
cd ~/git
./spec-kit/init.sh --all-repos \
  --ai claude \
  --search-path . \
  --max-depth 3

# What happens:
# - Finds all repos with .specify/ directories
# - Shows preview of what will be updated
# - Asks for confirmation
# - Updates each repo's templates
# - Asks about preserving constitution.md for each repo
```

**Why not `specify init --here` for each project?**
- ❌ Tedious: Need to cd into each project manually
- ❌ Error-prone: Easy to forget projects
- ❌ Time-consuming: No batch processing
- ✅ `init.sh --all-repos` is designed specifically for this use case

**Example output:**

```
Found 5 repositories with .specify:
  1. /Users/you/git/project-a
  2. /Users/you/git/project-b
  3. /Users/you/git/project-c
  4. /Users/you/git/project-d
  5. /Users/you/git/project-e

Settings:
  AI: claude
  Script: sh
  Destroy: no

=== PREVIEW MODE ===

[1/5] Would update: project-a
Would create .specify directory structure
Would copy memory folder
...

Do you want to proceed with these changes? (y/N):
```

### Scenario 3: Workspace Migration

**Situation**: You have a workspace initialized with `init.sh`, want modern workspace mode.

**Steps:**

```bash
# 1. Install globally
uv tool install git+https://github.com/hcnimi/spec-kit.git

# 2. Navigate to workspace parent
cd ~/git/my-workspace

# 3. Check if workspace is a git repo (REQUIRED)
git status
# If not a git repo, initialize:
# git init
# git add .
# git commit -m "Initialize workspace"

# 4. Initialize as proper workspace
specify init --workspace --auto-init

# 5. Update templates in all sub-repos (optional but recommended)
./spec-kit/init.sh --all-repos --search-path . --max-depth 2

# Result:
# - Workspace config: .specify/workspace.yml
# - Centralized specs: specs/
# - Latest templates in all discovered repos
```

**Important**: The workspace directory MUST be a git repository for version controlling your specifications. This is critical for team collaboration.

### Scenario 4: Force Clean Update

**Situation**: Your project templates are corrupted, heavily modified, or you want a completely fresh start.

**Steps:**

```bash
cd ~/git/my-project

# Option A: Force overwrite via specify CLI
specify init --here --ai claude --force

# Option B: Destroy and rebuild via init.sh
# (if you have local clone)
./spec-kit/init.sh . --destroy --ai claude

# Both options:
# - Overwrite ALL .specify/ contents
# - Ask about preserving constitution.md
# - Preserve specs/ folder
# - Show confirmation prompts for safety
```

**Use `--force` when:**
- Templates are corrupted or won't update properly
- You made custom modifications and want to revert to defaults
- Upgrading from a very old version with breaking changes

**Warning**: `--force` will overwrite any customizations you made to templates or scripts.

## Verification Checklist

After migration, verify your project is using latest templates:

### 1. Check Template Files

```bash
# View template directory
ls -la .specify/templates/

# Check a specific template (should show recent modification date)
head -20 .specify/templates/spec-template.md

# Review what changed
git status .specify/
git diff .specify/
```

### 2. Test Slash Commands

```bash
# Open project in your AI agent (Claude Code, VS Code, etc.)
# 1. Type / to see available commands
# 2. Run /specify with a test description
# 3. Verify it creates a spec file with the latest template structure
```

### 3. Check Script Permissions (Unix/macOS only)

```bash
ls -la .specify/scripts/bash/*.sh
# Should show executable permissions: -rwxr-xr-x

# If not executable, run:
chmod +x .specify/scripts/bash/*.sh
```

### 4. Verify AI Assistant Configuration

```bash
# For Claude
ls .claude/commands/spec-kit/
# Should show: specify.md, plan.md, tasks.md, etc.

# For Gemini
ls .gemini/commands/
# Should show: specify.toml, plan.toml, etc.

# For Copilot
ls .github/prompts/
# Should show: specify.prompt.md, plan.prompt.md, etc.
```

## Common Issues

### Issue 1: "Command not found: specify"

**Cause**: Global CLI not installed or not in PATH

**Fix:**

```bash
# Verify installation
uv tool list | grep specify

# If missing, install
uv tool install git+https://github.com/hcnimi/spec-kit.git

# If installed but not in PATH, add to shell config
# For bash (~/.bashrc) or zsh (~/.zshrc):
export PATH="$HOME/.local/bin:$PATH"

# Reload shell config
source ~/.bashrc  # or source ~/.zshrc
```

### Issue 2: "Templates seem outdated after update"

**Cause**: Ran `/specify` before updating local templates, or update didn't complete successfully

**Fix:**

```bash
# Update templates first
cd your-project
specify init --here --ai claude

# Verify update worked
git diff .specify/templates/

# Then test /specify command in your AI agent
# Should now use latest templates
```

### Issue 3: "init.sh not found"

**Cause**: Don't have local spec-kit clone

**Fix:**

```bash
# Clone spec-kit to access init.sh
git clone https://github.com/hcnimi/spec-kit.git ~/git/spec-kit

# Verify it's accessible
~/git/spec-kit/init.sh --help

# Now you can use init.sh for bulk operations
cd ~/git
~/git/spec-kit/init.sh --all-repos --ai claude
```

### Issue 4: "Workspace mode not working"

**Cause**: Workspace directory not a git repository

**Fix:**

```bash
cd ~/git/my-workspace

# Check if git repo
git status

# If error: "not a git repository"
git init
git add .specify/ specs/
git commit -m "Initialize spec-kit workspace"

# Now workspace mode should work
specify init --workspace --auto-init
```

### Issue 5: "Permission denied when running scripts"

**Cause**: Script files not marked as executable (Unix/macOS only)

**Fix:**

```bash
# Make all bash scripts executable
find .specify/scripts/bash -name "*.sh" -type f -exec chmod +x {} \;

# Verify permissions
ls -la .specify/scripts/bash/*.sh
# Should show: -rwxr-xr-x
```

### Issue 6: "Existing constitution.md was overwritten"

**Cause**: Didn't choose to preserve during update, or used `--force` without reading prompt

**Fix:**

```bash
# Restore from git history
git checkout HEAD~1 -- .specify/memory/constitution.md

# Or restore from git stash if you stashed changes
git stash list
git stash pop
```

**Prevention**: Always read prompts carefully during updates.

## Best Practices

### For Individual Developers

**Initial Setup (one-time):**

```bash
# 1. Install global CLI
uv tool install git+https://github.com/hcnimi/spec-kit.git

# 2. Clone spec-kit for init.sh access
git clone https://github.com/hcnimi/spec-kit.git ~/git/spec-kit
```

**Creating New Projects:**

```bash
# Use global CLI
specify init my-new-project --ai claude
```

**Updating Existing Projects:**

```bash
# Single project
cd my-project
specify init --here --ai claude

# Multiple projects (bulk update)
cd ~/git
~/git/spec-kit/init.sh --all-repos --ai claude
```

### For Teams

**Standardize Installation:**

Every team member should install globally:

```bash
uv tool install git+https://github.com/hcnimi/spec-kit.git
```

**Template Update Cadence:**

Establish a regular update schedule:

```bash
# Quarterly update process (example)
# 1. Check for spec-kit updates
cd ~/git/spec-kit
git pull origin main

# 2. Test on a non-critical project first
cd ~/git/test-project
specify init --here --ai claude

# 3. If successful, bulk update all projects
cd ~/git/team-projects
~/git/spec-kit/init.sh --all-repos --ai claude

# 4. Commit updated templates
cd each-project
git add .specify/
git commit -m "Update spec-kit templates to vX.X.X"
```

**When Spec-Kit Releases New Version:**

1. Review [release notes](https://github.com/hcnimi/spec-kit/releases)
2. Test on non-critical project
3. Bulk update if changes are valuable
4. Communicate changes to team

### Update Frequency Recommendations

| Scenario | Frequency | Rationale |
|----------|-----------|-----------|
| **Major releases** | Immediately | New features, important fixes |
| **Minor releases** | Within 1-2 weeks | Improvements, non-critical fixes |
| **Patch releases** | Optional | Bug fixes for edge cases |
| **Regular maintenance** | Quarterly | Keep projects in sync |
| **Before major features** | Always | Ensure latest best practices |

## FAQ

### Do I need to keep init.sh after global install?

**Yes!** `init.sh` is still valuable for:
- ✅ Bulk updates (`--all-repos` flag)
- ✅ Local development and testing
- ✅ Offline scenarios (no network needed)
- ✅ Multi-repo batch operations
- ✅ Custom template testing

Both tools are **complementary**, not replacements.

### Will global install break my existing projects?

**No.** Existing projects continue using their local `.specify/` templates until you explicitly update them with:
- `specify init --here` (single project), or
- `init.sh --all-repos` (multiple projects)

Nothing changes automatically.

### How often should I update templates?

**Recommendation:**
- **After spec-kit major releases**: Review release notes, update if valuable features
- **Quarterly routine maintenance**: Keep projects in sync with latest patterns
- **Before starting major features**: Ensure you have latest best practices and bug fixes

### Can I customize templates after update?

**Yes**, but consider the implications:

**If you customize:**
- ⚠️ Customizations will be **overwritten** on next update
- 📝 Document customizations in project README
- 🔄 Be prepared to reapply customizations after updates

**Better alternatives:**
- 🎯 Contribute improvements upstream to spec-kit
- 📋 Use project-specific `.specify/memory/` files for custom guidance
- 🏗️ Keep business logic in `constitution.md` (which can be preserved)

### What if I want different AI assistants per project?

**Fully supported:**

```bash
# Project A with Claude
cd ~/git/project-a
specify init --here --ai claude

# Project B with Gemini
cd ~/git/project-b
specify init --here --ai gemini

# Project C with Copilot
cd ~/git/project-c
specify init --here --ai copilot
```

**Bulk updates preserve AI choice:**

```bash
# Only updates projects already using Claude
~/git/spec-kit/init.sh --all-repos --ai claude

# This won't change Gemini or Copilot projects
```

### Can I mix global CLI and init.sh?

**Absolutely!** Use each tool for its strengths:

```bash
# Use global CLI for new projects
specify init new-microservice --ai claude

# Use init.sh for bulk updates
cd ~/git
~/git/spec-kit/init.sh --all-repos --ai claude

# Use whichever is convenient for single updates
cd existing-project
specify init --here --ai claude
# OR
~/git/spec-kit/init.sh . --ai claude
```

### What about workspaces initialized with old init.sh?

You can convert to modern workspace mode:

```bash
cd ~/git/my-workspace

# Ensure it's a git repo
git init  # if not already

# Convert to modern workspace
specify init --workspace --auto-init

# Optionally update all repo templates
~/git/spec-kit/init.sh --all-repos --search-path . --max-depth 2
```

Both old and new workspaces are compatible.

### How do I know which version of templates I'm using?

Check template file headers or modification dates:

```bash
# Check when templates were last updated
ls -la .specify/templates/

# View template content
head -50 .specify/templates/spec-template.md

# Compare with latest from repo
git diff origin/main:.specify/templates/spec-template.md \
         .specify/templates/spec-template.md
```

Consider adding template version to your project documentation.

## Summary

### Quick Reference: Actions & Commands

| Action | Tool | Command |
|--------|------|---------|
| **Install globally** | uv | `uv tool install git+https://github.com/hcnimi/spec-kit.git` |
| **Create new project** | specify CLI | `specify init my-project --ai claude` |
| **Update single project** | specify CLI | `cd project && specify init --here` |
| **Update multiple projects** | init.sh | `init.sh --all-repos --ai claude` |
| **Setup workspace** | specify CLI | `specify init --workspace` |
| **Force clean update** | Either | `specify init --here --force` or `init.sh . --destroy` |
| **Clone for init.sh** | git | `git clone https://github.com/hcnimi/spec-kit.git ~/git/spec-kit` |

### Key Takeaways

1. **🚨 Templates don't auto-update**: Existing projects use local `.specify/` templates until explicitly updated
2. **🔧 Both tools are valuable**: Use `specify` for new projects, `init.sh` for bulk operations
3. **📦 Preserves your work**: Updates never touch `specs/`, and `constitution.md` is optional to preserve
4. **✅ Verify after update**: Check templates, test slash commands, review git diff
5. **🔄 Update regularly**: Keep templates current for latest best practices

### Need Help?

- **Documentation**: [Getting Started](../getting-started/README.md)
- **Issues**: [GitHub Issues](https://github.com/hcnimi/spec-kit/issues)
- **Workspace Guide**: [Multi-Repo Workspaces](./multi-repo-workspaces.md)
- **CLI Reference**: [CLI Commands](../reference/cli-commands.md)

**Remember**: After global install, existing projects need explicit updates to use latest templates. Don't skip this step!
