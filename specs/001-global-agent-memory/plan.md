# Implementation Plan: Global Agent Memory Integration

> **Feature**: Global Agent Memory Integration
> **Spec**: [spec.md](spec.md)
> **Version**: 3.7
> **Status**: COMPLETE (Updated: Round 7 - Detailed Prompt Templates)
> **Created**: 2025-03-10
> **Updated**: 2025-03-10 (Memory-Aware Templates, AI Classification)

---

## Executive Summary

Интеграция четырёх компонентов (SpecKit, AgentForge patterns, AgentMemory-MCP, SkillsMP) для создания глобальной системы памяти агентов с автоматическим накоплением знаний, векторным поиском и умным определением scope.

**Ключевые зависимости**:
- SpecKit (github.com/github/spec-kit)
- agent-memory-mcp (ipiton/agent-memory-mcp) - MCP сервер для векторной памяти
- Ollama с моделью mxbai-embed-large
- SkillsMP (skillsmp.com) - web scraping для поиска скиллов

**Graceful Degradation**: Система продолжает работу при недоступности любой зависимости.

---

## Technical Context

### Core Components

1. **Global Installation Manager**
   - Location: `C:\Users\{username}\.claude`
   - Symlink-based SpecKit integration
   - Config backup + merge strategy
   - AI-executable INSTALL.md

2. **Multi-Level Memory System**
   - **Level 1**: Contextual (session-only)
   - **Level 2**: File-based (lessons.md, patterns.md, etc.)
   - **Level 3**: Vector-based (agent-memory-mcp + Ollama)
   - **Level 4**: Identity (AGENTS.md, SOUL.md, USER.md, MEMORY.md)

3. **Smart Search System**
   - Explicit markers: "вообще", "везде" → global
   - Intent classification: "как исправить" → global, "где находится" → local
   - Self-learning: effectiveness feedback → rule refinement
   - Fallback: local < 3 results → auto global

4. **SpecKit Integration**
   - All speckit commands auto-use memory
   - /speckit.features for quick fixes (< 4 hours)
   - Built-in memory access

### Dependencies

| Component | Type | Required | Fallback |
|-----------|------|----------|----------|
| SpecKit | Local repo | Yes | N/A |
| agent-memory-mcp | MCP server | No | File-based search |
| Ollama | Local service | No | File-based search |
| mxbai-embed-large | Ollama model | No | N/A |
| SkillsMP | Web service | No | Work without skill search |

### Unknowns Requiring Research

- [ ] agent-memory-mcp: exact MCP protocol integration patterns
- [ ] Ollama embeddings API: rate limits, batch size
- [ ] SkillsMP HTML structure: selectors, anti-scraping measures
- [ ] File watching: inotify vs ReadDirectoryChangesW patterns
- [ ] MCP server discovery: how to detect if agent-memory-mcp is installed

---

## Constitution Check

> **Note**: No constitution file found at `.specify/memory/constitution.md`  
> Skipping constitution evaluation.

---

## Phase 0: Research & Library Decisions ✅

### Research Results

See [research.md](research.md) for complete findings.

**Key Decisions**:
- agent-memory-mcp: Use CLI mode (not MCP protocol)
- SkillsMP: GitHub API + hybrid approach
- Ollama: Direct HTTP API with graceful degradation
- File watching: watchdog library (Python)

### Research Tasks

1. **agent-memory-mcp Integration Patterns**
   - Research MCP protocol for Python
   - Find examples of MCP server integration
   - Understand resource cleanup and lifecycle

2. **Ollama Embeddings API**
   - Research batch embedding limits
   - Find rate limiting information
   - Understand error handling patterns

3. **SkillsMP Web Scraping**
   - Analyze HTML structure
   - Identify anti-scraping measures
   - Determine optimal request patterns

4. **File Watching Cross-Platform**
   - Research inotify (Linux)
   - Research ReadDirectoryChangesW (Windows)
   - Research FSEvents (macOS)
   - Find unified library or implement abstraction

### Library-First Search Results

✅ COMPLETE

---

## Phase 1: Design Decisions

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Claude Code / Cursor                  │
│                    (AI Assistant)                       │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │   Memory Orchestrator  │
         │   (NEW - core module)  │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐   ┌──────▼──────┐   ┌───▼────────┐
│ File   │   │   Vector    │   │  SkillsMP  │
│ Memory │   │   Memory    │   │  Scraper   │
│        │   │ (optional)  │   │ (optional) │
└───┬────┘   └──────┬──────┘   └───┬────────┘
    │               │               │
    │         ┌─────▼─────┐         │
    │         │ Ollama    │         │
    │         │ (local)   │         │
    │         └───────────┘         │
    │                                │
┌───▼────────────────────────────────▼────────┐
│         Project Memory Structure            │
│  C:\Users\{user}\.claude\memory\projects\  │
│    {project-id}\                           │
│      ├── lessons.md                         │
│      ├── patterns.md                        │
│      ├── projects-log.md                    │
│      ├── architecture.md                    │
│      └── handoff.md                         │
└─────────────────────────────────────────────┘
```

### Core Modules

1. **Memory Orchestrator** (NEW)
   - Coordinates all memory operations
   - Implements smart search scope determination
   - Handles graceful degradation
   - Manages fallback logic

2. **File Memory Manager** (NEW)
   - Reads/writes markdown files
   - Manages project-specific memory isolation
   - Handles backup + merge on install

3. **Vector Memory Client** (NEW - optional)
   - Integrates with agent-memory-mcp
   - Manages embeddings via Ollama
   - Graceful degradation when unavailable

4. **SkillsMP Scraper** (NEW - optional)
   - Web scraping with rate limiting
   - Local cache management
   - Skill comparison logic

5. **SpecKit Integrations** (MODIFY existing)
   - Modify /speckit.specify to read memory
   - Modify /speckit.plan to read architecture
   - Modify /speckit.tasks to read patterns
   - Add /speckit.features command

---

## Data Model

✅ COMPLETE

---

## API Contracts

Skipped - API contracts not needed (CLI integration)

---

## Quickstart

✅ COMPLETE

---

## Implementation Phases (Updated: Round 7)

### Phase 1: Foundation (Week 1-2)
- [ ] Global installation infrastructure
- [ ] File memory manager with one-line summary headers
- [ ] Memory orchestrator base
- [ ] Config backup + merge
- [ ] **Memory-Aware Agent base (NEW ✨)**
  - [ ] Headers-First extraction (grep "^## ")
  - [ ] Context optimization (~80-120 tokens)
  - [ ] Before/When/After workflow skeleton
- [ ] Basic testing

### Phase 2: Vector Memory (Week 3-4)
- [ ] agent-memory-mcp integration (CLI mode)
- [ ] Ollama embeddings client
- [ ] Graceful degradation logic
- [ ] Memory content templates (Problem → Solution → Lessons)
- [ ] **Structured prompt templates (NEW ✨)**
  - [ ] Before Task: headers extraction
  - [ ] When Stuck: vector search + deep dive
  - [ ] After Task: auto-documentation
- [ ] Testing with/without Ollama

### Phase 3: AI Classification & Smart Search (Week 5)
- [ ] **AI Importance Classifier (NEW ✨)**
  - [ ] Multi-factor scoring (semantic, complexity, impact, repeatability)
  - [ ] Routing logic (>0.7 → architecture, 0.4-0.7 → patterns, <0.4 → log)
  - [ ] Explicit user marker override
- [ ] Intent classification
- [ ] Scope determination logic
- [ ] Self-learning feedback loop
- [ ] Fallback mechanisms
- [ ] Testing classification accuracy

### Phase 4: SkillsMP Integration (Week 6)
- [ ] Web scraper implementation
- [ ] Local cache
- [ ] Skill comparison
- [ ] Conflict resolution UI
- [ ] Rate limiting

### Phase 5: SpecKit Integration (Week 7-8)
- [ ] Modify existing speckit commands (memory-aware)
- [ ] Add /speckit.features
- [ ] **Integrate Memory-Aware workflow (NEW ✨)**
  - [ ] All speckit commands use headers-first reading
  - [ ] Auto-documentation after each command
  - [ ] Cross-project learning when relevant
- [ ] End-to-end testing
- [ ] Documentation

### Phase 6: Optimization & Polish (Week 9) ✨ NEW
- [ ] Measure actual context usage
- [ ] Optimize one-line summary format
- [ ] Fine-tune AI classification thresholds
- [ ] User feedback collection
- [ ] Performance tuning

---

## Risks & Mitigation (Updated: Round 7)

| Risk | Mitigation |
|------|------------|
| Ollama unavailable | Graceful degradation - file memory works |
| SkillsMP blocks scraping | Local cache, fallback to GitHub search |
| MCP protocol changes | Version pinning, abstraction layer |
| File watching issues | Unified library with platform detection |
| **AI classification false positives (NEW)** | User explicit markers override, self-learning |
| **Context bloat from one-line summaries (NEW)** | Monitor token usage, enforce 100-char limit |
| **Wrong routing decisions (NEW)** | Feedback loop, user can manually correct |

---

*Plan updated: 2025-03-10 (Round 7: Memory-Aware Templates, AI Classification)*
