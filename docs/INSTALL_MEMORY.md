# AI-Executable Installation Instructions

> **For**: Claude Code / Cursor AI Assistant
> **Feature**: SpecKit Global Agent Memory Integration
> **Version**: 0.1.0
> **Execution Mode**: Interactive Step-by-Step

---

## Overview for AI Assistant

You are installing the SpecKit Global Memory System. This is an **interactive installation** - execute each step, validate, and ask user for choices when needed.

**Key Principles**:
1. Execute one step at a time
2. Validate after each step
3. Ask user before destructive operations
4. Offer choices when multiple options exist
5. Handle errors gracefully with fallback options

---

## STEP 1: Detect Environment

**Actions**:
1. Detect platform: Windows, Linux, or macOS
2. Detect Python version (require 3.11+)
3. Detect current git repository
4. Detect if global home already exists

**Execute**:
```bash
# Platform detection
python -c "import platform; print(f'Platform: {platform.system()}')"

# Python version
python --version

# Git repository check
git rev-parse --git-dir

# Global home check
ls ~/.claude 2>/dev/null || echo "Global home does not exist"
```

**Validation**:
- Python 3.11+ installed? → If NO, ask: "Install Python 3.11+ or use existing version?"
- Git repository detected? → If NO, error: "Must be in git repository"
- Global home exists? → If YES, ask: "Existing installation detected. Backup and merge, or fresh install?"

**Wait for user confirmation before proceeding to STEP 2.**

---

## STEP 2: Confirm Installation Parameters

**Ask User**:

```
Installation Parameters:
- Platform: <detected>
- Global Home: ~/.claude (default) or custom path?
- SpecKit Repo: <current path>
- Vector Memory: Enable (requires Ollama) or Disable?

Choices:
1. Use default parameters (recommended)
2. Customize global home path
3. Skip vector memory setup
4. See advanced options
```

**Read user choice and adjust parameters accordingly.**

---

## STEP 3: Backup Existing Configuration (if exists)

**Condition**: Only if `~/.claude/spec-kit/config` exists

**Actions**:
1. Create backup directory: `~/.claude/memory/backups/<timestamp>`
2. Copy existing config to backup
3. List what was backed up

**Execute**:
```bash
# Create backup
BACKUP_DIR="~/.claude/memory/backups/install_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup config
cp -r ~/.claude/spec-kit/config "$BACKUP_DIR/" 2>/dev/null || true

# Show backup
echo "Backup created at: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
```

**Validation**:
- Backup directory created?
- Config files copied?

**Ask user**: "Backup created. Continue with installation?"

---

## STEP 4: Create Directory Structure

**Actions**:
1. Create global home directory structure
2. Set proper permissions
3. Verify creation

**Execute**:
```bash
# Create directories
mkdir -p ~/.claude/spec-kit/config
mkdir -p ~/.claude/spec-kit/templates
mkdir -p ~/.claude/memory/projects
mkdir -p ~/.claude/memory/backups

# Verify
echo "Directories created:"
ls -la ~/.claude/spec-kit/
ls -la ~/.claude/memory/
```

**Windows Alternative**:
```cmd
mkdir %USERPROFILE%\.claude\spec-kit\config
mkdir %USERPROFILE%\.claude\spec-kit\templates
mkdir %USERPROFILE%\.claude\memory\projects
mkdir %USERPROFILE%\.claude\memory\backups
```

**Validation**:
- All directories exist?
- Writable permissions?

**If fails**: Ask user "Directory creation failed. Run as administrator/sudo or choose different location?"

---

## STEP 5: Copy Memory Templates

**Actions**:
1. Copy templates from `templates/memory/` to global home
2. Verify template files
3. List installed templates

**Execute**:
```bash
# Copy templates (assuming in spec-kit root)
cp -r templates/memory/* ~/.claude/spec-kit/templates/memory/

# Verify
echo "Templates installed:"
ls -la ~/.claude/spec-kit/templates/memory/
```

**Validation**:
- lessons.md template exists?
- patterns.md template exists?
- architecture.md template exists?

**If templates not found**: Ask user "Templates not found in repository. Download from GitHub or create defaults?"

---

## STEP 6: Initialize Global Memory

**Actions**:
1. Run memory initialization script
2. Create global memory files
3. Verify creation

**Execute**:
```bash
# Initialize global memory
python scripts/memory/init_memory.py --project-id ".global" --project-name "Global Memory"

# Verify
echo "Global memory files:"
ls -la ~/.claude/memory/projects/.global/
```

**Validation**:
- lessons.md created?
- patterns.md created?
- architecture.md created?
- projects-log.md created?
- handoff.md created?

**If fails**: Show error and ask "Retry initialization or create files manually?"

---

## STEP 7: Setup Ollama (Optional)

**Condition**: Only if user chose to enable vector memory

**Actions**:
1. Check if Ollama is installed
2. Check if Ollama is running
3. Check if mxbai-embed-large model is available
4. Offer installation instructions if missing

**Execute**:
```bash
# Check Ollama
python -c "
import requests
try:
    r = requests.get('http://localhost:11434/api/tags', timeout=2)
    print('Ollama: RUNNING')
except:
    print('Ollama: NOT RUNNING')
"

# Check model
ollama list 2>/dev/null || echo "Ollama CLI not found"
```

**If Ollama not installed**:

**Ask user**:

```
Ollama is required for vector memory but not installed.

Options:
1. Install Ollama now (I'll provide instructions for your platform)
2. Skip vector memory (system will work without it)
3. Install later (run setup again)

Choose:
```

**If user chooses install**:

**Windows**:
```
1. Download: https://ollama.ai/download
2. Run installer
3. Start Ollama from Start Menu
4. Run: ollama pull mxbai-embed-large

Press Enter when done, I'll verify.
```

**Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &  # Start in background
ollama pull mxbai-embed-large
```

**macOS**:
```bash
brew install ollama
ollama serve &
ollama pull mxbai-embed-large
```

**After installation**: Re-check and validate.

**If user chooses skip**: Set vector_memory=false in config, continue.


## STEP 7.5: Setup agent-memory-mcp (Optional)

**Condition**: Only if user chose to enable advanced vector memory

**Actions**:
1. Check if agent-memory-mcp is installed
2. Offer installation instructions if missing
3. Verify CLI commands work

**Execute**:
```bash
# Check agent-memory-mcp
agent-memory-mcp --help 2>/dev/null || echo "agent-memory-mcp not found"
```

**If agent-memory-mcp not installed**:

**Ask user**:

```
agent-memory-mcp provides advanced vector memory with built-in
fallback to Jina AI/OpenAI embeddings. It's optional but recommended.

Options:
1. Install agent-memory-mcp now (I'll provide instructions)
2. Skip (use Ollama embeddings only)
3. Install later

Choose:
```

**If user chooses install**:

**Instructions**:
```bash
# Download from GitHub releases
# https://github.com/ipiton/agent-memory-mcp/releases

# Windows (PowerShell):
# 1. Download agent-memory-mcp-windows-amd64.exe
# 2. Rename to agent-memory-mcp.exe
# 3. Add to PATH or place in: C:\Users\<user>\.local\bin

# Linux/macOS:
curl -L https://github.com/ipiton/agent-memory-mcp/releases/latest/download/agent-memory-mcp-$(uname -s)-amd64 -o ~/.local/bin/agent-memory-mcp
chmod +x ~/.local/bin/agent-memory-mcp

# Verify
agent-memory-mcp --help
```

**After installation**: Re-check and validate.

**If user chooses skip**: Continue without agent-memory-mcp (Ollama-only mode).
## STEP 7.6: Setup SkillsMP Search (Optional)

**Condition**: Ask user if they want SkillsMP skill search

**Actions**:
1. Ask if user wants SkillsMP integration
2. If yes, request API key
3. Store API key securely
4. Verify API access

**Ask user**:

```
SkillsMP provides access to 425K+ agent skills and MCP servers.
This helps find existing solutions before creating new agents.

Options:
1. Enable SkillsMP search (requires API key)
2. Skip (use GitHub fallback only)
3. Decide later

Choose:
```

**If user chooses Enable**:

**Request API key**:

```
SkillsMP API Key Required

To get your API key:
1. Visit: https://skillsmp.com/docs/api
2. Sign up / Login
3. Navigate to API Keys section
4. Generate new API key

Enter your SkillsMP API key (or press Enter to skip):
```

**Store and validate API key**:
```bash
# Store and validate API key
python -c "
import sys
sys.path.insert(0, 'src')

from specify_cli.memory.skillsmp.api_key_storage import APIKeyStorage
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration

print('Enter SkillsMP API key (or press Enter to skip):')
api_key = input().strip()

if api_key and len(api_key) > 10:
    storage = APIKeyStorage()
    if storage.store_api_key(api_key):
        print('[OK] API key stored securely')

        # Validate
        integration = SkillsMPIntegration(api_key=api_key)
        results = integration.search_skills('agent', limit=1)

        if results:
            print('[OK] SkillsMP API working')
        else:
            print('[WARNING] API key stored but search failed (may be rate limited)')
    else:
        print('[ERROR] Failed to store API key')
        sys.exit(1)
else:
    print('[SKIP] No API key provided - SkillsMP disabled')
"
```

**If user chooses Skip**:
- Continue without SkillsMP API
- GitHub fallback will be used for skill search
- Note: Limited search capabilities without API

---


---

---

## STEP 8: Setup Configuration Files

**Actions**:
1. Create degradation config
2. Create version file
3. Setup project config template

**Execute**:
```bash
# Create degradation config
cat > ~/.claude/spec-kit/config/degradation.json << 'EOF'
{
  "ollama": {
    "required": false,
    "fallback": "file_based",
    "warning_once": true,
    "warning_message": "Vector memory unavailable (Ollama not found). Using file-based memory only."
  },
  "agent_memory_mcp": {
    "required": false,
    "fallback": "ollama_only",
    "warning_once": true,
    "warning_message": "agent-memory-mcp unavailable. Using Ollama embeddings only."
  },
  "vector_memory": {
    "required": false,
    "fallback": "file_based",
    "warning_once": true,
    "warning_message": "Vector memory unavailable. Using file-based search only."
  },
  "skillsmp": {
    "required": false,
    "fallback": "skip",
    "warning_once": true
  }
}
EOF

# Create version file
echo "0.1.0" > ~/.claude/spec-kit/config/.version

# Verify
echo "Config files:"
ls -la ~/.claude/spec-kit/config/
```

**Validation**:
- degradation.json created?
- .version file created?

---

## STEP 9: Create Cross-Platform Link (Optional)

**Purpose**: Link global home to SpecKit repository for easy updates

**Ask user**:

```
Create symlink from ~/.claude/spec-kit to repository?
This allows easy updates to templates and config.

Options:
1. Create symlink (recommended)
2. Skip (manual updates required)

Choose:
```

**If symlink chosen**:

**Linux/macOS**:
```bash
ln -s <repo-path> ~/.claude/spec-kit
```

**Windows** (requires Admin):
```cmd
mklink /D "C:\Users\<user>\.claude\spec-kit" "F:\IdeaProjects\spec-kit"
```

**If fails**: "Symlink creation failed. Continuing without link."

---

## STEP 10: Verify Installation

**Actions**:
1. Run verification script
2. Check all components
3. Show summary

**Execute**:
```bash
# Run verification
python scripts/memory/verify_install.py

# Manual verification checks
echo "=== Installation Verification ==="

# Check directories
[ -d ~/.claude/spec-kit/config ] && echo "[OK] Config directory"
[ -d ~/.claude/memory/projects ] && echo "[OK] Projects directory"

# Check global memory
[ -f ~/.claude/memory/projects/.global/lessons.md ] && echo "[OK] Global lessons"

# Check version
VERSION=$(cat ~/.claude/spec-kit/config/.version)
echo "[OK] Version: $VERSION"
```

**Expected Output**:
```
=== Installation Verification ===
[OK] Config directory
[OK] Projects directory
[OK] Global lessons
[OK] Version: 0.1.0
```

**Validation**:
- All checks pass?

**If any fail**: Show what failed and ask "Retry or continue with partial installation?"

---

## STEP 11: Test Basic Functionality

**Actions**:
1. Test importing memory modules (including vector memory)
2. Test project detection
3. Test writing to memory
4. Test vector memory components (if enabled)

**Execute**:
```bash
# Test core imports
python -c "
from specify_cli.memory.config import MemoryConfigManager
from specify_cli.memory.file_manager import FileMemoryManager
from specify_cli.memory.project_detector import ProjectDetector
print('[OK] Core modules imported successfully')
"

# Test vector memory imports (optional, may fail if dependencies missing)
python -c "
from specify_cli.memory.vector import OllamaClient, AgentMemoryClient
from specify_cli.memory.vector import FourLevelMemory, VectorSearchAPI
print('[OK] Vector memory modules imported')
" 2>/dev/null || echo "[NOTE] Vector memory modules require optional dependencies"

# Test project detection
python -c "
from specify_cli.memory.project_detector import ProjectDetector
detector = ProjectDetector()
info = detector.detect_current_project()
print(f'[OK] Project detected: {info[\"project_id\"]}')
"

# Test memory write
python -c "
from specify_cli.memory.file_manager import FileMemoryManager
manager = FileMemoryManager()
manager.write_entry('lessons', 'Test Entry', 'Test content', 'Test summary')
print('[OK] Memory write successful')
"
```

**Validation**:
- Core imports pass?
- Project detection works?
- Memory write works?

**If any fail**: Show error and suggest solution.

---

## STEP 12: Installation Summary

**Display**:

```
=== Installation Complete ===

Installed Components:
  [OK] Directory structure
  [OK] Memory templates
  [OK] Global memory files
  [OK] Configuration system
  [OK] Verification tests

Memory Location: ~/.claude/memory/projects/.global
Config Location: ~/.claude/spec-kit/config

Next Steps:
1. Initialize memory for your project:
   python scripts/memory/init_memory.py

2. Start using memory-aware workflow

3. (Optional) Install agent-memory-mcp for advanced features

4. See extensions/global-memory/README.md for usage

Installation successful! The system is ready to use.
```

---

## Error Handling Reference

**If any step fails**:

1. **Directory permissions**: Ask to run as admin/sudo
2. **Python not found**: Ask to install Python 3.11+
3. **Git not found**: Error - must be in git repository
4. **Ollama timeout**: Offer to skip vector memory
5. **Module import errors**: Ask to run `pip install -e .`
6. **File write errors**: Check disk space and permissions

**Always offer**:
- Retry the step
- Skip and continue
- Abort installation

---

**End of AI-Executable Instructions**

The AI assistant should execute these steps sequentially, validating each step and asking for user choices when needed.
