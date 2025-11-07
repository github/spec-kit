# Migration Guide: Upgrading to Improved Spec-Kit

This guide helps you upgrade your existing spec-kit project to include all Phases 1-5 improvements.

## What's New?

The improved spec-kit includes:

### Phase 1: Quick Wins
- ✅ Token Budget Tracker (`/speckit.budget`)
- ✅ Specification Validation (`/speckit.validate`)
- ✅ Quick Reference Cards (ultra-compact docs)

### Phase 2: Core Enhancements
- ✅ Semantic Code Search (`/speckit.find`)
- ✅ Session Context Compression (`/speckit.prune`)
- ✅ Configuration Management (`.speckit.config.json`)
- ✅ Resume System (checkpoint recovery)

### Phase 3: Advanced Features
- ✅ Error Context Enhancer (`/speckit.error-context`)
- ✅ Differential Analysis (`--diff-only` mode)
- ✅ Clarification History Tracker (`/speckit.clarify-history`)

### Phase 4: Platform Parity & Automation
- ✅ PowerShell scripts for Windows (Core features)
- ✅ Git Pre-Commit Hook (automatic validation)

### Phase 5: Complete Platform Parity
- ✅ 100% PowerShell feature parity (all features on Windows)
- ✅ Cross-platform documentation

**Total Token Savings Potential: 85-98%**

## Prerequisites

Before migrating, ensure you have:

1. ✅ Git installed
2. ✅ Access to improved spec-kit repository (your fork or upstream)
3. ✅ Backup of any custom modifications

## Migration Methods

### Method 1: Automated Migration Script (Recommended)

The migration scripts automatically:
- Back up your existing project
- Copy all new scripts and templates
- Update configuration files
- Install Git hooks (optional)
- Preserve your specs, memory, and custom commands

#### For Linux/macOS/WSL:

```bash
# Download the migration script from improved spec-kit
curl -O https://raw.githubusercontent.com/guisantossi/spec-kit/main/migrate-to-improved-speckit.sh

# Make it executable
chmod +x migrate-to-improved-speckit.sh

# Run migration
./migrate-to-improved-speckit.sh

# Or provide source directory directly
./migrate-to-improved-speckit.sh /path/to/improved-speckit
```

#### For Windows (PowerShell):

```powershell
# Download the migration script
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/guisantossi/spec-kit/main/migrate-to-improved-speckit.ps1" -OutFile "migrate-to-improved-speckit.ps1"

# Run migration
.\migrate-to-improved-speckit.ps1

# Or provide source directory directly
.\migrate-to-improved-speckit.ps1 -SourceDir "C:\path\to\improved-speckit"
```

The script will:
1. ✅ Verify you're in a spec-kit project
2. ✅ Create a timestamped backup
3. ✅ Copy all new bash scripts (7 new + 2 updated)
4. ✅ Copy all PowerShell scripts (7 scripts)
5. ✅ Copy new command templates (7 new + 1 updated)
6. ✅ Copy Git hooks
7. ✅ Update `.gitignore`
8. ✅ Optionally install pre-commit hook
9. ✅ Provide verification steps

### Method 2: Manual Migration

If you prefer manual control:

#### Step 1: Clone Improved Spec-Kit

```bash
git clone https://github.com/guisantossi/spec-kit.git /tmp/spec-kit-improved
cd /tmp/spec-kit-improved
```

#### Step 2: Backup Your Project

```bash
cd /path/to/your/project

# Create backup
mkdir -p .speckit-backup-$(date +%Y%m%d)
cp memory/constitution.md .speckit-backup-*/
cp -r templates/commands .speckit-backup-*/
cp .gitignore .speckit-backup-*/
```

#### Step 3: Copy New Files

```bash
# Bash scripts (Linux/macOS/WSL)
cp /tmp/spec-kit-improved/scripts/bash/*.sh scripts/bash/
chmod +x scripts/bash/*.sh

# PowerShell scripts (Windows)
cp /tmp/spec-kit-improved/scripts/powershell/*.ps1 scripts/powershell/

# Command templates
cp /tmp/spec-kit-improved/templates/commands/budget.md templates/commands/
cp /tmp/spec-kit-improved/templates/commands/validate.md templates/commands/
cp /tmp/spec-kit-improved/templates/commands/find.md templates/commands/
cp /tmp/spec-kit-improved/templates/commands/prune.md templates/commands/
cp /tmp/spec-kit-improved/templates/commands/error-context.md templates/commands/
cp /tmp/spec-kit-improved/templates/commands/clarify-history.md templates/commands/
cp /tmp/spec-kit-improved/templates/commands/resume.md templates/commands/
cp /tmp/spec-kit-improved/templates/quick-ref-template.md templates/

# Git hooks
cp -r /tmp/spec-kit-improved/hooks hooks/
chmod +x hooks/pre-commit

# Documentation
cp /tmp/spec-kit-improved/PLATFORM-COMPATIBILITY.md .
cp /tmp/spec-kit-improved/IMPROVED-WORKFLOW.md .
```

#### Step 4: Update .gitignore

```bash
cat >> .gitignore << 'EOF'

# Spec-kit Phase 1-5 additions
.speckit-cache/
.speckit-analysis-cache.json
.speckit-progress.json
.speckit/memory/session-summary-*.md
.speckit.config.json
EOF
```

#### Step 5: Install Git Hook (Optional)

```bash
# Symlink (recommended)
ln -s ../../hooks/pre-commit .git/hooks/pre-commit

# Or copy
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Method 3: Git Merge

Merge the improved spec-kit directly:

```bash
cd /path/to/your/project

# Add upstream remote if not already added
git remote add upstream https://github.com/guisantossi/spec-kit.git

# Fetch latest
git fetch upstream main

# Merge improvements
git merge upstream/main

# Resolve any conflicts
git add -A
git commit -m "Merge improved spec-kit from upstream"
```

## Post-Migration Steps

### 1. Verify Installation

```bash
# Linux/macOS/WSL
./scripts/bash/token-budget.sh --help
./scripts/bash/validate-spec.sh --help
./scripts/bash/semantic-search.sh --help

# Windows
.\scripts\powershell\token-budget.ps1 -Help
.\scripts\powershell\validate-spec.ps1 -Help
.\scripts\powershell\semantic-search.ps1 -Help
```

### 2. Test New Features

```bash
# Check token budget
./scripts/bash/token-budget.sh

# Validate all specs
./scripts/bash/validate-spec.sh --all

# Try semantic search
./scripts/bash/semantic-search.sh "authentication"

# Windows
.\scripts\powershell\token-budget.ps1
.\scripts\powershell\validate-spec.ps1 -All
.\scripts\powershell\semantic-search.ps1 "authentication"
```

### 3. Review Documentation

```bash
# Platform compatibility guide
cat PLATFORM-COMPATIBILITY.md

# Improved workflow examples
cat IMPROVED-WORKFLOW.md
```

### 4. Configure (Optional)

Create `.speckit.config.json`:

```json
{
  "cache": {
    "enabled": true,
    "retention_days": 30
  },
  "analysis": {
    "default_mode": "incremental",
    "sample_size": 20
  },
  "budget": {
    "warn_threshold": 120000,
    "critical_threshold": 160000
  }
}
```

### 5. Commit Changes

```bash
git add -A
git commit -m "feat: upgrade to improved spec-kit with Phases 1-5

- Add token optimization features
- Add advanced debugging tools
- Add PowerShell support for Windows
- Add Git pre-commit hook
- Update documentation
"
```

## What's Preserved?

The migration **preserves**:
- ✅ All your existing specs (`specs/`)
- ✅ Your constitution (`memory/constitution.md`)
- ✅ Your custom slash commands (templates get updated, not replaced)
- ✅ Your git history
- ✅ Your project structure

The migration **updates**:
- ✅ Scripts (all new scripts added, some updated)
- ✅ Command templates (new added, document.md updated)
- ✅ .gitignore (additions only)

The migration **backs up**:
- ✅ constitution.md → `.speckit-backup-*/`
- ✅ templates/commands → `.speckit-backup-*/`
- ✅ .gitignore → `.speckit-backup-*/`
- ✅ Existing pre-commit hook → `.speckit-backup-*/`

## Troubleshooting

### "Script not found" errors

**Problem:** Can't find new scripts after migration

**Solution:**
```bash
# Verify scripts exist
ls -la scripts/bash/token-budget.sh
ls -la scripts/powershell/token-budget.ps1

# Make bash scripts executable
chmod +x scripts/bash/*.sh
```

### Git hook not running

**Problem:** Pre-commit hook doesn't execute

**Solution:**
```bash
# Check if hook exists and is executable
ls -la .git/hooks/pre-commit

# Make executable
chmod +x .git/hooks/pre-commit

# Test manually
.git/hooks/pre-commit
```

### PowerShell "execution policy" error

**Problem:** Can't run PowerShell scripts

**Solution:**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### "Command not found" in AI agent

**Problem:** New commands like `/speckit.budget` not working

**Solution:**
1. Verify template exists: `ls templates/commands/budget.md`
2. Restart your AI agent session
3. Try the command again

## Rollback

If you need to rollback:

```bash
# Find your backup
ls -la .speckit-backup-*

# Restore from backup
BACKUP_DIR=".speckit-backup-20250107-123456"  # Use your actual backup dir

cp "$BACKUP_DIR/constitution.md" memory/
cp -r "$BACKUP_DIR/commands" templates/
cp "$BACKUP_DIR/.gitignore" .

# Remove new scripts (optional)
rm scripts/bash/token-budget.sh
rm scripts/bash/validate-spec.sh
# ... etc
```

## Getting Help

If you encounter issues:

1. Check the backup: `.speckit-backup-*/`
2. Review logs from migration script
3. Verify file permissions: `chmod +x scripts/bash/*.sh`
4. Check documentation: `cat PLATFORM-COMPATIBILITY.md`
5. Open an issue on GitHub with:
   - Your platform (Linux/macOS/Windows/WSL)
   - Migration method used
   - Error messages
   - Backup directory location

## Next Steps After Migration

1. **Learn new features**: Read `IMPROVED-WORKFLOW.md`
2. **Optimize your workflow**: Use `/speckit.budget` to track usage
3. **Validate your specs**: Run `/speckit.validate --all`
4. **Try semantic search**: `/speckit.find "your query"`
5. **Use compression**: `/speckit.prune` when context gets large
6. **Track decisions**: `/speckit.clarify-history`

## Benefits Summary

After migration, you'll have:

- ✅ **85-98% token savings** potential
- ✅ **100% cross-platform** support (Linux/macOS/Windows/WSL)
- ✅ **Automated quality gates** via Git hooks
- ✅ **Advanced debugging** with spec cross-referencing
- ✅ **Better code discovery** via semantic search
- ✅ **Session management** for long conversations
- ✅ **Complete documentation** for all features

Welcome to improved spec-kit! 🚀
