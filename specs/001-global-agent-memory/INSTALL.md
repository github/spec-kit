# Global Agent Memory Integration - Installation Guide

> **AI-Executable Installation Instructions**
> This document is written for execution by AI assistants (Claude, ChatGPT, etc.)
> Last updated: 2025-03-10

---

## Prerequisites Check

Before installation, verify:

1. **Operating System**: Windows 11, Linux, or macOS
2. **Git installed**: Run `git --version`
3. **Python 3.11+**: Run `python --version`
4. **SpecKit repository**: Located at `F:\IdeaProjects\spec-kit`
5. **Write permissions**: Access to `C:\Users\{username}\.claude`

**If any prerequisite is missing, install it first before proceeding.**

---

## Installation Steps

### Step 1: Prepare Target Directory

```bash
# Create global .claude directory if it doesn't exist
mkdir -p "$HOME/.claude"
cd "$HOME/.claude"
```

### Step 2: Backup Existing Configurations

```bash
# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".backup.$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

# Backup existing configs if they exist
if [ -f "config.json" ]; then cp config.json "$BACKUP_DIR/"; fi
if [ -d "memory" ]; then cp -r memory "$BACKUP_DIR/"; fi
if [ -d "skills" ]; then cp -r skills "$BACKUP_DIR/"; fi
if [ -d "spec-kit" ]; then cp -r spec-kit "$BACKUP_DIR/"; fi

echo "Backup created: $BACKUP_DIR"
```

### Step 3: Create Directory Structure

```bash
# Create memory directories
mkdir -p memory/projects
mkdir -p memory/backups

# Create skills directory
mkdir -p skills

echo "Directory structure created"
```

### Step 4: Create SpecKit Symlink

```bash
# Remove existing symlink if present
if [ -L "spec-kit" ]; then rm spec-kit; fi

# Create symlink to SpecKit repository
ln -s "F:/IdeaProjects/spec-kit" spec-kit

echo "SpecKit symlink created"
```

### Step 5: Create Project Config Template

```bash
# Create .spec-kit directory
mkdir -p .spec-kit

# Create project config template
cat > .spec-kit/project.json << 'EOF'
{
  "project_id": "",
  "project_name": "",
  "memory_enabled": true,
  "created_at": ""
}
EOF

echo "Project config template created"
```

### Step 6: Optional - Install Ollama

**Check if Ollama is installed:**

```bash
if command -v ollama &> /dev/null; then
    echo "Ollama already installed: $(ollama --version)"
else
    echo "Ollama not found. Install?"
    read -p "Install Ollama now? (y/n): " install_ollama
    
    if [ "$install_ollama" = "y" ]; then
        # Install Ollama (Linux/macOS)
        curl -fsSL https://ollama.com/install.sh | sh
        
        # For Windows: download from https://ollama.com/download
        echo "Ollama installed. Please restart terminal and verify with: ollama --version"
    fi
fi
```

**Pull embedding model (if Ollama installed):**

```bash
if command -v ollama &> /dev/null; then
    echo "Pulling mxbai-embed-large model..."
    ollama pull mxbai-embed-large
    
    # Verify model
    echo "Testing embedding generation..."
    ollama embed mxbai-embed-large "test" | head -c 50
    
    echo "mxbai-embed-large ready"
else
    echo "Skipping model pull (Ollama not installed)"
fi
```

### Step 7: Verify Installation

```bash
echo "=== Installation Verification ==="

# Check symlink
if [ -L "spec-kit" ]; then
    echo "✓ SpecKit symlink exists"
else
    echo "✗ SpecKit symlink missing"
fi

# Check directories
if [ -d "memory/projects" ]; then
    echo "✓ Memory directory exists"
else
    echo "✗ Memory directory missing"
fi

if [ -d "skills" ]; then
    echo "✓ Skills directory exists"
else
    echo "✗ Skills directory missing"
fi

# Check config template
if [ -f ".spec-kit/project.json" ]; then
    echo "✓ Project config template exists"
else
    echo "✗ Project config template missing"
fi

# Check Ollama (optional)
if command -v ollama &> /dev/null; then
    echo "✓ Ollama installed: $(ollama --version)"
    if ollama list | grep -q "mxbai-embed-large"; then
        echo "✓ mxbai-embed-large model available"
    else
        echo "⚠ mxbai-embed-large not found. Run: ollama pull mxbai-embed-large"
    fi
else
    echo "⚠ Ollama not installed (optional)"
fi

echo "=== Verification Complete ==="
```

---

## Update Existing Installation

When updating an existing installation:

1. **Check current version**: Read `.spec-kit/version.json`
2. **Create backup**: Automatic backup before update
3. **Apply delta changes**: Only new/modified files
4. **Preserve user data**: memory, configs remain intact
5. **Verify**: Run verification steps

```bash
# Update command
cd "$HOME/.claude"
bash spec-kit/.specify/scripts/install/update.sh
```

---

## Troubleshooting

### Issue: Symlink creation fails on Windows

**Solution**: Run as Administrator or use Git Bash:

```bash
# In Git Bash
ln -s "F:/IdeaProjects/spec-kit" spec-kit
```

### Issue: Ollama not accessible

**Solution**: Check Ollama service status:

```bash
# Linux/macOS
ollama serve

# Windows: Ollama runs as background service
# Check Task Manager for "ollama-app"
```

### Issue: Permission denied

**Solution**: Ensure write permissions to home directory:

```bash
# Fix permissions
chmod +w "$HOME/.claude"
```

### Issue: Conflicts during merge

**Solution**: Review backup and manually resolve:

```bash
# List backups
ls -la .backup.*

# Restore from backup if needed
cp -r .backup.TIMESTAMP/memory/* memory/
```

---

## Rollback

If installation fails:

```bash
cd "$HOME/.claude"

# Find latest backup
LATEST_BACKUP=$(ls -td .backup.* | head -1)

# Restore from backup
cp -r $LATEST_BACKUP/* .

echo "Rolled back to $LATEST_BACKUP"
```

---

## Next Steps

After successful installation:

1. **Initialize project memory**: Run `.spec-kit/scripts/init-memory.sh` in your project
2. **Test memory search**: `memory_search("test query")`
3. **Try /speckit.features**: Quick fix workflow
4. **Read project README**: For unique features

---

## Support

- **Original SpecKit**: https://github.com/github/spec-kit
- **Issue Tracker**: Report issues in project repository
- **Documentation**: See README.md for feature overview

---

*Installation Guide v3.0 - AI-Executable*
*Compatible with: SpecKit, AgentMemory-MCP, Ollama*
