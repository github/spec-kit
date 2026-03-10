# SpecKit Memory System

Complete documentation for the Global Agent Memory Integration.

## Quick Start

```bash
# Install globally
python scripts/memory/install_all.py

# Initialize memory for current project
python scripts/memory/init_memory.py

# Verify installation
python scripts/memory/verify_install.py
```

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Usage](#usage)
5. [API Reference](#api-reference)
6. [Configuration](#configuration)
7. [Performance](#performance)
8. [Troubleshooting](#troubleshooting)

## Overview

SpecKit Memory provides a 4-level memory system for AI agents:

| Level | Name | Purpose | Example |
|-------|------|---------|---------|
| 1 | File Memory | Structured storage | lessons.md, patterns.md |
| 2 | Vector Memory | Semantic search | Find similar past issues |
| 3 | Context Memory | Working memory | Current task context |
| 4 | Identity Memory | Long-term learning | User preferences, skills |

### Key Features

- **Automatic accumulation**: Learns from every task
- **Cross-project**: Share knowledge across projects
- **Semantic search**: Find relevant past solutions
- **Skills integration**: Search 425K+ agent skills
- **Agent creation**: Build agents with proven patterns

## Architecture

```
.claude/
├── memory/
│   ├── projects/
│   │   ├── .global/          # Cross-project knowledge
│   │   ├── project-a/        # Project-specific memory
│   │   └── project-b/
│   ├── backups/              # Automatic backups
│   └── cache/                # Search results cache
├── spec-kit/                 # SpecKit installation
│   └── → ~/IdeaProjects/spec-kit
└── CLAUDE.md                 # User preferences
```

### File Memory Types

| File | Purpose | When Updated |
|------|---------|--------------|
| lessons.md | Learnings from mistakes | After error fix |
| patterns.md | Reusable solutions | When pattern discovered |
| architecture.md | Technical decisions | After major decision |
| projects-log.md | Project history | After milestone |

## Installation

### Prerequisites

- Python 3.10+
- Optional: Ollama for vector search
- Optional: SkillsMP API key for skill search

### Global Install

```bash
# Automatic (recommended)
python scripts/memory/install_all.py

# Manual
bash scripts/memory/install_global.sh
python scripts/memory/init_memory.py
python scripts/memory/verify_install.py
```

### Verify Installation

```bash
python scripts/memory/verify_install.py
```

Expected output:
```
[OK] Global home exists
[OK] SpecKit link created
[OK] Memory directories ready
[OK] Templates installed
[OK] Configuration valid
```

## Usage

### Basic Commands

```bash
# Search memory
spec-kit memory search "authentication error"

# Add entry
spec-kit memory add --type lesson --title "JWT fix" --content "..."

# List entries
spec-kit memory list --type patterns

# Show stats
spec-kit memory stats
```

### Python API

```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

# Initialize
orchestrator = MemoryOrchestrator(project_id="my-project")

# Search memory
results = orchestrator.search("authentication pattern")

# Add learning
orchestrator.add_lesson(
    title="JWT token expiration",
    problem="Tokens expired after 1 hour",
    solution="Use refresh tokens, increase access token to 24h"
)

# Get patterns
patterns = orchestrator.get_patterns()
```

### SpecKit Integration

The memory system integrates with SpecKit commands:

```bash
# /speckit.specify - Reads memory before creating spec
# /speckit.plan - Gets architecture context for planning
# /speckit.tasks - Suggests patterns for task breakdown
# /speckit.clarify - Cross-project context for questions
# /speckit.features - Quick feature generation
```

## API Reference

### MemoryOrchestrator

Main entry point for memory operations.

```python
orchestrator = MemoryOrchestrator(
    project_id="my-project",
    global_home="~/.claude"
)

# Search
results = orchestrator.search(
    query="error message",
    scope="auto",  # "local", "global", "auto"
    limit=10
)

# Add entries
orchestrator.add_lesson(title, problem, solution)
orchestrator.add_pattern(title, description, code)
orchestrator.add_architecture(title, context, decision, rationale)

# Read memory
lessons = orchestrator.get_lessons(limit=10)
patterns = orchestrator.get_patterns(limit=10)
```

### HeadersFirstReader

Efficient reading without loading full content.

```python
reader = HeadersFirstReader(project_id="my-project")

# Read just headers (titles + summaries)
headers = reader.read_headers_first(
    file_types=["lessons", "patterns"]
)

# Read specific section
content = reader.read_section(
    file_type="lessons",
    header_match="JWT token expiration"
)
```

### Vector Search

Semantic search with Ollama.

```python
from specify_cli.memory.vector.agent_memory_client import AgentMemoryClient

client = AgentMemoryClient(
    ollama_base_url="http://localhost:11434",
    embedding_model="nomic-embed-text"
)

# Search by meaning
results = client.search(
    query="how to fix authentication timeout",
    limit=5
)
```

### SkillsMP Integration

Search 425K+ agent skills.

```python
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration

skills = SkillsMPIntegration()

# Search for existing agents
results = skills.search_skills(
    query="frontend development with React",
    limit=10
)

# Create new agent with patterns
workflow = SkillCreationWorkflow()
workflow.create_agent_from_requirements(
    agent_name="frontend-dev",
    requirements={
        "role": "Frontend Developer",
        "skills": ["React", "TypeScript", "CSS"],
        "personality": "Creative and detail-oriented"
    }
)
```

## Configuration

### Memory Configuration

File: `~/.claude/spec-kit/config/memory.json`

```json
{
  "enabled": true,
  "auto_save": true,
  "project_detection": "auto",
  "vector_search": {
    "enabled": true,
    "ollama_url": "http://localhost:11434",
    "model": "nomic-embed-text"
  },
  "skillsmp": {
    "api_key": "sk_live_*",
    "fallback_to_github": true
  },
  "thresholds": {
    "high_importance": 0.7,
    "medium_importance": 0.4
  }
}
```

### Project Configuration

File: `.spec-kit/project.json`

```json
{
  "project_id": "spec-kit",
  "project_name": "SpecKit",
  "memory_enabled": true,
  "auto_save_errors": true,
  "auto_discover_patterns": true
}
```

## Performance

### Context Usage

Headers-first reading uses only ~1-2% of context window:
- lessons.md: ~50-100 tokens
- patterns.md: ~50-100 tokens
- architecture.md: ~30-80 tokens

### Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Headers read | <100ms | 3 files, 500 entries |
| Local search | <200ms | String matching |
| Vector search | <1s | With Ollama |
| Write entry | <100ms | Append to file |

### Optimization

See [Performance Tuning Guide](performance_tuning.md) for:
- Caching strategies
- Parallel I/O
- Compression for large files
- Database migration for 10K+ entries

## Troubleshooting

### Common Issues

**Memory not accumulating**
```bash
# Check auto-save is enabled
python -c "from specify_cli.memory.orchestrator import MemoryOrchestrator; print(MemoryOrchestrator().config.auto_save)"
```

**Vector search not working**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Test embedding
curl http://localhost:11434/api/embeddings -d '{"model":"nomic-embed-text","prompt":"test"}'
```

**Import errors**
```bash
# Verify installation
python scripts/memory/verify_install.py

# Check paths
python -c "import sys; print(sys.path)"
```

### Debug Mode

```bash
# Enable debug logging
export SPEC_KIT_DEBUG=1

# Run with verbose output
python -m specify_cli.memory.orchestrator --verbose
```

### Get Help

- GitHub Issues: https://github.com/spec-kit/spec-kit/issues
- Documentation: https://docs.spec-kit.dev/memory
- Community: https://discord.gg/spec-kit

## See Also

- [Context Usage Analysis](context_usage.md)
- [Summary Format Guide](summary_format.md)
- [AI Threshold Tuning](ai_thresholds.md)
- [Performance Tuning](performance_tuning.md)
- [Feedback Collection](feedback.md)
