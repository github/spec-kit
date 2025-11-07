# Mode Conversion Guide

Complete guide for converting between standard and shadow modes.

---

## Table of Contents

- [Overview](#overview)
- [Before You Convert](#before-you-convert)
- [Standard to Shadow](#standard-to-shadow)
- [Shadow to Standard](#shadow-to-standard)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

---

## Overview

Speckit supports two modes:
- **Standard Mode:** Full Speckit presence with branding
- **Shadow Mode:** Hidden Speckit with generic branding

You can convert between modes at any time using the `specify convert` command.

---

## Before You Convert

### Prerequisites

1. **Check Current Mode**
   ```bash
   specify info
   ```

2. **Commit Changes**
   ```bash
   git status
   git add .
   git commit -m "Checkpoint before mode conversion"
   ```

3. **Backup Important Files**
   - Specifications in `.specs/`
   - Plans in `.plans/`
   - Custom scripts or configurations

4. **Review Open Work**
   - Complete or checkpoint in-progress tasks
   - Note any active branches
   - Document current state

### What Gets Changed

#### Standard → Shadow
- ✅ Scripts moved to `.devtools/speckit/`
- ✅ Templates replaced with generic versions
- ✅ Commands renamed (remove `/speckit.` prefix)
- ✅ Configuration moved to `.devtools/.config.json`
- ✅ `.devtools/` added to `.gitignore`

#### Shadow → Standard
- ✅ Scripts moved to `scripts/`
- ✅ Templates replaced with Speckit versions
- ✅ Commands renamed (add `/speckit.` prefix)
- ✅ Configuration moved to `.speckit.config.json`
- ✅ `.devtools/` removed

### What Stays the Same

- ✅ Your specifications
- ✅ Your plans and tasks
- ✅ Your code
- ✅ Git history
- ✅ Script functionality

---

## Standard to Shadow

### Basic Conversion

```bash
specify convert --to shadow
```

### With Custom Branding

```bash
specify convert --to shadow --brand "Your Company DevTools"
```

### With Custom Shadow Path

```bash
specify convert --to shadow --shadow-path .internal/tools
```

### Step-by-Step Process

1. **Run Conversion Command**
   ```bash
   specify convert --to shadow --brand "Acme DevTools"
   ```

2. **Verify Conversion**
   ```bash
   # Check mode
   specify info

   # Verify scripts
   ls .devtools/speckit/scripts/bash/

   # Check configuration
   cat .devtools/.config.json

   # Verify gitignore
   cat .gitignore | grep devtools
   ```

3. **Test Commands**
   ```bash
   # Try a command
   /budget

   # Or directly
   .devtools/speckit/scripts/bash/token-budget.sh
   ```

4. **Update Team**
   - Notify team of mode change
   - Update any documentation
   - Share new command names

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Convert to shadow mode"
   ```

### What to Expect

**Console Output:**
```
Speckit Project Setup

Converting from standard to shadow mode...
Creating backup before conversion...

Convert standard → shadow
  ● Detect current configuration (standard mode)
  ● Create backup (standard-mode-20250107-143022)
  ● Setup shadow structure
  ● Move scripts to shadow
  ● Replace templates
  ● Replace commands
  ● Create shadow config
  ● Update .gitignore
  ● Remove standard mode files

Successfully converted to shadow mode
Backup saved to: .devtools/backups
```

**File Changes:**
```
Modified:
  .gitignore              # Added .devtools/
  .claude/commands/       # Updated command files

Moved:
  scripts/               → .devtools/speckit/scripts/
  .speckit.config.json   → .devtools/.config.json

Replaced:
  templates/             # Generic versions
  .claude/commands/      # Unbranded commands

Created:
  .devtools/backups/standard-mode-*/  # Backup
```

---

## Shadow to Standard

### Basic Conversion

```bash
specify convert --to standard
```

### Step-by-Step Process

1. **Run Conversion Command**
   ```bash
   specify convert --to standard
   ```

2. **Verify Conversion**
   ```bash
   # Check mode
   specify info

   # Verify scripts
   ls scripts/bash/

   # Check configuration
   cat .speckit.config.json
   ```

3. **Test Commands**
   ```bash
   # Try a command (note the prefix)
   /speckit.budget

   # Or directly
   scripts/bash/token-budget.sh
   ```

4. **Update Team**
   - Notify team of mode change
   - Update any documentation
   - Share new command names (with `/speckit.` prefix)

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Convert to standard mode"
   ```

### What to Expect

**Console Output:**
```
Speckit Project Setup

Converting from shadow to standard mode...
Creating backup before conversion...

Convert shadow → standard
  ● Detect current configuration (shadow mode)
  ● Create backup (shadow-mode-20250107-150315)
  ● Move scripts to standard location
  ● Remove shadow directory
  ● Create standard config
  ● Update .gitignore

Successfully converted to standard mode
Backup saved to: .devtools/backups
```

**File Changes:**
```
Modified:
  .gitignore              # Removed .devtools/

Moved:
  .devtools/speckit/scripts/  → scripts/
  .devtools/.config.json      → .speckit.config.json

Replaced:
  templates/             # Speckit versions
  .claude/commands/      # Speckit commands

Removed:
  .devtools/             # Entire directory (except backups)

Created:
  .devtools/backups/shadow-mode-*/  # Backup
```

---

## Backup and Recovery

### Automatic Backups

Backups are created automatically during conversion at:
```
.devtools/backups/<mode>-<timestamp>/
```

Example:
```
.devtools/backups/
├── standard-mode-20250107-143022/
│   ├── scripts/
│   ├── templates/
│   ├── hooks/
│   └── .speckit.config.json
└── shadow-mode-20250107-150315/
    ├── speckit/
    └── .config.json
```

### Manual Backup

Before converting:
```bash
# Create manual backup
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  scripts/ templates/ .claude/ .speckit.config.json

# Or for shadow mode
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  .devtools/ templates/ .claude/
```

### Restore from Backup

#### Restore Scripts
```bash
# Standard mode
cp -r .devtools/backups/standard-mode-*/scripts ./

# Shadow mode
cp -r .devtools/backups/shadow-mode-*/speckit .devtools/
```

#### Restore Configuration
```bash
# Standard mode
cp .devtools/backups/standard-mode-*/.speckit.config.json ./

# Shadow mode
cp .devtools/backups/shadow-mode-*/.config.json .devtools/
```

#### Full Restore
```bash
# Use git to revert
git checkout HEAD -- scripts/ templates/ .claude/
git checkout HEAD -- .speckit.config.json  # or .devtools/.config.json
```

### Disable Backups

**Not recommended**, but possible:
```bash
specify convert --to shadow --no-backup
```

---

## Troubleshooting

### Conversion Failed

**Problem:** Conversion command failed mid-process

**Solution:**
1. Check error message
2. Restore from backup if needed
3. Fix the issue
4. Try conversion again

### Commands Not Working After Conversion

**Problem:** Slash commands don't work

**Solutions:**

**For Standard Mode:**
```bash
# Commands now have /speckit. prefix
/speckit.budget      # Not /budget
/speckit.specify     # Not /specify
```

**For Shadow Mode:**
```bash
# Commands have no prefix
/budget      # Not /speckit.budget
/specify     # Not /speckit.specify
```

### Scripts Not Found

**Problem:** Scripts cannot be found

**Solutions:**

**Check script location:**
```bash
# Standard mode
ls scripts/bash/

# Shadow mode
ls .devtools/speckit/scripts/bash/
```

**Verify configuration:**
```bash
specify info
```

**Fix permissions:**
```bash
# Standard mode
chmod +x scripts/bash/*.sh

# Shadow mode
chmod +x .devtools/speckit/scripts/bash/*.sh
```

### Configuration Issues

**Problem:** Configuration file missing or invalid

**Solutions:**

**Recreate configuration:**
```bash
# Standard mode
specify init --here --mode standard --force

# Shadow mode
specify init --here --mode shadow --force
```

### Gitignore Issues

**Problem:** .devtools/ visible in git

**Solutions:**

**Verify .gitignore:**
```bash
cat .gitignore | grep devtools
```

**Add manually if missing:**
```bash
echo "" >> .gitignore
echo "# Shadow mode - hidden development tools" >> .gitignore
echo ".devtools/" >> .gitignore
```

**Remove from git if tracked:**
```bash
git rm -r --cached .devtools/
git commit -m "Remove .devtools from tracking"
```

---

## Migration Checklist

### Before Conversion

- [ ] Run `specify info` to confirm current mode
- [ ] Commit all changes
- [ ] Note any custom configurations
- [ ] Document current command names
- [ ] Inform team of upcoming change

### After Conversion

- [ ] Run `specify info` to verify new mode
- [ ] Test key commands
- [ ] Verify scripts are accessible
- [ ] Check .gitignore is correct
- [ ] Update team documentation
- [ ] Commit conversion changes
- [ ] Test with team members

---

## Best Practices

### Timing

- Convert during low-activity periods
- Avoid converting mid-sprint
- Choose time when team is available
- Schedule time for testing

### Communication

- Announce conversion in advance
- Share new command names
- Update documentation
- Provide support during transition

### Testing

- Test all critical commands
- Verify scripts work
- Check CI/CD pipelines
- Validate with multiple team members

### Documentation

- Update README
- Revise team wikis
- Update onboarding docs
- Share conversion guide

---

## Getting Help

If you encounter issues:

1. **Check this guide** - Review troubleshooting section
2. **Check backups** - Restore if needed
3. **Verify setup** - Run `specify info`
4. **Review logs** - Check command output
5. **Ask for help** - Consult team or documentation

---

**Remember:** Backups are created automatically. You can always revert if needed.
