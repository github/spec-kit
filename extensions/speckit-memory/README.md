# SpecKit Memory Integration Extension

> **Extension**: `speckit-memory`
> **Version**: 0.1.0
> **Status**: Alpha (Phase 8 - In Progress)

---

## Overview

Integrates Global Agent Memory system with SpecKit commands for automatic knowledge accumulation and retrieval.

---

## Registered Commands

| Command | Description | Status |
|---------|-------------|--------|
| `speckit.memory.specify` | Enhanced spec creation with memory context | ✅ Created |
| `speckit.memory.plan` | Enhanced planning with architecture memory | ⏳ TODO |
| `speckit.memory.tasks` | Task generation with pattern memory | ⏳ TODO |
| `speckit.memory.clarify` | Clarification with cross-project context | ⏳ TODO |
| `speckit.memory.features` | Quick feature mode for small fixes | ✅ Created |

---

## Features

### Memory-Enhanced Workflow

**Before Task** (Headers-First):
```python
# Reads only headers (~80-120 tokens)
lessons.md: 5 entries → titles only
patterns.md: 5 entries → titles only
architecture.md: 3 sections → headers only
```

**When Stuck**:
```python
# Vector search + deep dive
results = orchestrator.search("database connection error")
```

**After Task**:
```python
# Auto-document with AI classification
agent.after_task(
    problem="JWT token expired",
    solution="Implement refresh token flow",
    lessons="Tokens expire after 15 minutes",
    importance=0.8  # → architecture.md
)
```

### Quick Feature Mode

`speckit.memory.features` - Simplified workflow for tasks < 4 hours:

- No deep research
- Short spec (1-2 pages vs 5-10)
- Basic plan (no detailed architecture)
- Quick tasks (minimal dependency analysis)

**Ideal for**:
- Bug fixes
- Small features
- Hotfixes
- UI tweaks

---

## Installation

```bash
# Link extension to SpecKit
cd F:/IdeaProjects/spec-kit
bash scripts/memory/link_speckit_extension.sh
```

---

## Usage

### Enhanced Spec Creation

```bash
# Create spec with memory context
python -m extensions.speckit_memory.speckit_memory_specify \
    --project-id my-feature \
    --spec-file specs/001-my-feature/spec.md
```

### Quick Feature Mode

```bash
# Interactive quick feature
python -m extensions.speckit_memory.speckit_memory_features

# Non-interactive (with defaults)
python -m extensions.speckit_memory.speckit_memory_features \
    --non-interactive \
    --specs-dir /path/to/specs
```

---

## Architecture

```
extensions/speckit-memory/
├── manifest.json              # Extension metadata
├── README.md                   # This file
├── speckit_memory_specify.py  # Enhanced spec command
└── speckit_memory_features.py # Quick feature command
```

---

## Integration Points

### With Memory System

- **HeadersFirstReader**: Reads memory file headers efficiently
- **SmartSearchScope**: Auto-determines search scope (local vs global)
- **MemoryOrchestrator**: Unified memory access API
- **MemoryAwareAgent**: Before/When/After workflow

### With SpecKit

- **Extension API**: Follows `speckit.{ext}.{cmd}` naming
- **Command registration**: Via manifest.json
- **Spec file enhancement**: Inserts memory context automatically

---

## TODO (Phase 8 Completion)

- [ ] speckit.memory.plan - Enhanced planning
- [ ] speckit.memory.tasks - Pattern-aware task generation
- [ ] speckit.memory.clarify - Cross-project clarifications
- [ ] Headers-first integration test
- [ ] Cross-project learning verification
- [ ] Full integration tests

---

## See Also

- [Global Memory README](../README.md)
- [Phase 7: Agent Creation](../../specs/001-global-agent-memory/tasks.md#phase-7---us5---agent-creation)
- [INSTALL_MEMORY.md](../../docs/INSTALL_MEMORY.md)

---

**Created**: 2025-03-10
**Phase**: 8 - SpecKit Integration (In Progress)
