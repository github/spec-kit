# AI-Executable Installation Instructions

> **SpecKit Global Agent Memory Integration**
> **Version**: 0.1.0
> **Installation Type**: Global extension for SpecKit
> **Platform**: Windows, Linux, macOS

---

## Quick Start (5 Minutes)

### Prerequisites

- Python 3.11+ installed
- Git installed
- (Optional) Ollama for vector memory features

### Installation

```bash
# 1. Navigate to SpecKit repository
cd F:/IdeaProjects/spec-kit

# 2. Run installation script
bash scripts/memory/install_global.sh
```

This will:
- Create global directories at `~/.claude/memory/`
- Create symlink to SpecKit at `~/.claude/spec-kit`
- Setup configuration system

---

## Verify Installation

```bash
# Run verification script
bash scripts/memory/verify_install.sh
```

Expected output:
```
✓ Global home: C:\Users\[user]\.claude
✓ SpecKit link: C:\Users\[user]\.claude\spec-kit
✓ Memory directories: Created
✓ Templates: Installed
```

---

## Optional: Ollama Setup (Vector Memory)

### Check Ollama Status

```bash
python -c "from specify_cli.memory.install.ollama_checker import OllamaChecker; checker = OllamaChecker(); print(checker.check_availability())"
```

### Install Ollama (if needed)

**Windows**:
1. Download from https://ollama.ai
2. Run installer
3. Start Ollama from Start Menu

**Linux**:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS**:
```bash
brew install ollama
```

### Pull Required Model

```bash
ollama pull mxbai-embed-large
```

### Verify

```bash
ollama list
```

Expected: `mxbai-embed-large` in the list.

---

## Graceful Degradation

**If Ollama is unavailable**, the system:
- ✓ Works with file-based memory only
- ✓ No errors or crashes
- ✓ Warning shown once per session
- ✓ Vector memory features disabled

**The system continues to work** - core functionality is file-based.

---

## Configuration

### Config Location

- **Global Config**: `~/.claude/spec-kit/config/`
- **Project Memory**: `~/.claude/memory/projects/{project-id}/`

### Project Setup

Each project needs `.spec-kit/project.json`:

```json
{
  "project_id": "my-project",
  "project_name": "My Project",
  "memory_enabled": true,
  "created_at": "2025-03-10"
}
```

The system auto-creates this on first run.

---

## Troubleshooting

### Symlink Fails (Windows)

**Problem**: Cannot create symlink

**Solution**: Run as Administrator, or use junction instead:
```cmd
mklink /J "C:\Users\[user]\.claude\spec-kit" "F:\IdeaProjects\spec-kit"
```

### Ollama Connection Refused

**Problem**: Cannot connect to localhost:11434

**Solution**: Start Ollama application first

### Import Errors

**Problem**: Module not found errors

**Solution**: Install dependencies:
```bash
pip install -e .
```

---

## Verification Checklist

- [ ] Global installation script executed
- [ ] SpecKit symlink created/verified
- [ ] Memory directories exist
- [ ] Templates installed
- [ ] (Optional) Ollama installed and running
- [ ] (Optional) mxbai-embed-large model pulled
- [ ] Project configuration template available

---

## Next Steps

After installation:

1. Create your first project memory:
   ```bash
   # Project memory auto-initialized on first use
   ```

2. Start using memory-aware workflow in your AI agents

3. See README.md for usage examples

---

**Installation documentation**: `docs/INSTALL.md`
**Feature spec**: `specs/001-global-agent-memory/spec.md`
