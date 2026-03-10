# Global Agent Memory Integration - Installation Guide

> **AI-Executable Installation Instructions**
> This document is written for execution by AI assistants (Claude, ChatGPT, etc.)
> Last updated: 2025-03-11 (Added Docker Compose + Command Sync Instructions)

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

**Option A: Native Installation**

```bash
# Check if Ollama is installed
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

**Option B: Docker Compose (Recommended for Windows)**

> **Advantages**: Isolated environment, easy updates, consistent behavior across platforms

```bash
# 1. Create docker projects directory
mkdir -p "$HOME/.claude/projects/docker"
cd "$HOME/.claude/projects/docker"

# 2. Copy docker-compose file (already created in: ~/.claude/projects/docker/ollama-docker-compose.yml)
# The file includes:
# - ollama/ollama:latest image
# - Persistent volume for models
# - Health checks
# - Auto-restart on failure

# 3. Start Ollama container
docker-compose -f ollama-docker-compose.yml up -d

# 4. Wait for container to be ready (check health)
docker-compose -f ollama-docker-compose.yml ps

# 5. Pull embedding model
docker exec -it ollama ollama pull mxbai-embed-large

# 6. Verify model
docker exec ollama ollama list | grep mxbai-embed-large

# 7. Test embedding
docker exec ollama ollama embed mxbai-embed-large "test" | head -c 50
```

**Using the setup script (simpler):**

```bash
# All-in-one script for Docker Ollama management
cd "$HOME/.claude/projects/docker"
bash ollama-setup.sh start   # Start container
bash ollama-setup.sh pull    # Pull model
bash ollama-setup.sh status  # Check status
bash ollama-setup.sh stop    # Stop container
```

**Pull embedding model (after Ollama is running):**

```bash
# Native installation
if command -v ollama &> /dev/null; then
    echo "Pulling mxbai-embed-large model..."
    ollama pull mxbai-embed-large

    # Verify model
    echo "Testing embedding generation..."
    ollama embed mxbai-embed-large "test" | head -c 50

    echo "mxbai-embed-large ready"
fi

# Docker installation
if docker ps --format '{{.Names}}' | grep -q "^ollama$"; then
    echo "Pulling mxbai-embed-large model..."
    docker exec -it ollama ollama pull mxbai-embed-large

    # Verify model
    echo "Testing embedding generation..."
    docker exec ollama ollama embed mxbai-embed-large "test" | head -c 50

    echo "mxbai-embed-large ready"
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
OLLAMA_FOUND=false

# Check native installation
if command -v ollama &> /dev/null; then
    echo "✓ Ollama installed: $(ollama --version)"
    OLLAMA_FOUND=true
    if ollama list 2>/dev/null | grep -q "mxbai-embed-large"; then
        echo "✓ mxbai-embed-large model available (native)"
    else
        echo "⚠ mxbai-embed-large not found. Run: ollama pull mxbai-embed-large"
    fi
fi

# Check Docker installation
if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^ollama$"; then
        echo "✓ Ollama running in Docker container"
        OLLAMA_FOUND=true
        if docker exec ollama ollama list 2>/dev/null | grep -q "mxbai-embed-large"; then
            echo "✓ mxbai-embed-large model available (Docker)"
        else
            echo "⚠ mxbai-embed-large not found in Docker. Run: docker exec -it ollama ollama pull mxbai-embed-large"
        fi
    fi
fi

if [ "$OLLAMA_FOUND" = false ]; then
    echo "⚠ Ollama not installed (optional)"
    echo "  Install natively: https://ollama.com/download"
    echo "  Install via Docker: See Step 6B in INSTALL.md"
fi

echo "=== Verification Complete ==="
```

### Step 8: Update SpecKit Commands (CRITICAL)

> **IMPORTANT**: Always keep SpecKit commands synchronized with the latest version!
>
> SpecKit is under active development. Commands in `~/.claude/commands/` can become outdated,
> causing issues with workflows. Always update them after installing or updating SpecKit.

```bash
# Navigate to .claude directory
cd "$HOME/.claude"

# Backup existing commands before updating
mkdir -p commands/.backup.$(date +%Y%m%d_%H%M%S)
cp commands/speckit.*.md commands/.backup.$(date +%Y%m%d_%H%M%S)/

# Update commands from latest SpecKit templates
# Commands are sourced from spec-kit/templates/commands/ in the symlinked repository
for cmd in specify plan tasks clarify analyze implement checklist constitution taskstoissues; do
  # Skip custom commands not in templates (e.g., features)
  [ -f "spec-kit/templates/commands/$cmd.md" ] || continue
  cp "spec-kit/templates/commands/$cmd.md" "commands/speckit.$cmd.md"
  echo "✓ Updated speckit.$cmd.md"
done

# Preserve custom commands not in templates (e.g., tobeads.md)
echo "Custom commands preserved"

echo "=== Commands updated ==="
ls -la commands/speckit.*.md
```

**Why this is necessary:**

- SpecKit commands receive regular updates and bug fixes
- Outdated commands may use deprecated APIs or incorrect workflows
- The symlink ensures commands always use the latest templates from the repository
- Updates are safe - they only replace command definitions, not your data

**When to update:**

- After initial installation
- After pulling changes to the SpecKit repository
- If speckit commands behave unexpectedly
- Before starting new features (recommended weekly)

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

**Native installation**:

```bash
# Linux/macOS
ollama serve

# Windows: Ollama runs as background service
# Check Task Manager for "ollama-app"
```

**Docker installation**:

```bash
# Check container status
docker ps | grep ollama

# Check logs
docker logs ollama

# Restart container
docker-compose -f ~/.claude/projects/docker/ollama-docker-compose.yml restart

# Access shell
docker exec -it ollama sh
```

### Issue: Docker Ollama fails to start

**Solution**: Check Docker Desktop is running:

```bash
# Verify Docker is available
docker info

# Check port conflicts (11434)
netstat -an | grep 11434  # Linux/macOS
netstat -an | findstr 11434  # Windows

# If port is in use, stop conflicting service or change port in docker-compose.yml
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

*Installation Guide v3.2 - AI-Executable*
*Compatible with: SpecKit, AgentMemory-MCP, Ollama (Native & Docker)*
