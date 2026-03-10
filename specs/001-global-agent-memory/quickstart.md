# Quickstart: Global Agent Memory Integration

> **Get started in 5 minutes**

---

## Prerequisites

- Windows 11, Linux, or macOS
- Git installed
- Python 3.11+ (for optional extensions)
- Write access to home directory

---

## Installation

### Quick Install (Recommended)

```bash
# 1. Navigate to spec-kit
cd F:/IdeaProjects/spec-kit

# 2. Run installation script
bash .specify/scripts/install.sh

# 3. Verify installation
ls -la ~/.claude/memory/projects
```

### Manual Install

See [INSTALL.md](INSTALL.md) for detailed steps.

---

## First Time Setup

### 1. Create Project Config

```bash
cd /path/to/your/project
mkdir -p .spec-kit

cat > .spec-kit/project.json << EOF
{
  "project_id": "my-awesome-project",
  "project_name": "My Awesome Project",
  "memory_enabled": true
}
EOF
```

### 2. Initialize Memory Structure

```bash
# Memory directories will be created automatically
# First task completion triggers initial memory save
```

---

## Usage

### Basic Memory Operations

```bash
# Save memory (automatic at task completion)
# Just complete a task - memory saves automatically

# Search memory
memory_search("how did we fix the authentication bug?")

# Local search (current project only)
memory_search("где у нас конфиг базы данных?")

# Global search (all projects, best practices)
memory_search("как исправить ошибку с encoding")
```

### Speckit Integration

All speckit commands auto-use memory:

```bash
# Specify - reads lessons.md to avoid past mistakes
/speckit.specify "Add user authentication"

# Plan - reads architecture.md for context
/speckit.plan

# Tasks - reads patterns.md for accumulated patterns
/speckit.tasks

# Quick fixes (< 4 hours)
/speckit.features "Fix login button color"
```

---

## Optional: Ollama Setup

### Install Ollama

```bash
# Windows: Download from https://ollama.com/download
# Linux/macOS:
curl -fsSL https://ollama.com/install.sh | sh
```

### Pull Embedding Model

```bash
ollama pull mxbai-embed-large
```

### Verify

```bash
ollama list | grep mxbai-embed-large
```

---

## Verification

### Check Installation

```bash
# Check global installation
ls -la ~/.claude/spec-kit

# Check memory structure
ls -la ~/.claude/memory/projects

# Check project config
cat .spec-kit/project.json
```

### Test Memory

```bash
# In Claude Code or Cursor, try:
"Save this to memory: We use chi router for this project"

# Then recall:
"What router do we use for this project?"
```

---

## Troubleshooting

### Ollama Not Available

**Warning shown**: "Ollama недоступен, векторная память отключена"

**Impact**: File-based memory still works, only vector search disabled

**Solution**: Install Ollama (see above) or continue without it

### Project Not Detected

**Problem**: Memory not saving for current project

**Solution**: Create `.spec-kit/project.json` in project root

### Memory Not Found

**Problem**: Search returns nothing

**Solution**: 
- Check if memory enabled: `memory_enabled: true`
- Try global search: "вообще, как мы делали X?"
- Check file-based memory: `~/.claude/memory/projects/{project_id}/`

---

## Next Steps

1. **Customize**: Edit `.spec-kit/project.json` per project
2. **Learn**: Read [AGENT_TEMPLATES.md](AGENT_TEMPLATES.md) for agent patterns
3. **Extend**: Add custom skills to `~/.claude/skills/`
4. **Contribute**: Share your improvements!

---

## Documentation

- [Full Spec](spec.md) - Complete specification
- [INSTALL.md](INSTALL.md) - Detailed installation guide
- [Data Model](data-model.md) - Entity relationships
- [Research](research.md) - Library decisions

---

*Quickstart updated: 2025-03-10*
