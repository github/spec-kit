# Changelog

All notable changes to SpecKit Memory System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-10

### Added

#### Core Memory System
- 4-level memory architecture (File, Vector, Context, Identity)
- Memory Orchestrator for unified memory access
- File Memory Manager for structured storage
- Headers-First Reader for efficient context loading
- Memory-Aware Agent base class

#### Memory Files
- lessons.md - Learnings from mistakes
- patterns.md - Reusable solutions
- architecture.md - Technical decisions
- projects-log.md - Project milestones

#### Vector Memory
- Agent Memory MCP client integration
- Ollama embeddings client
- RAG indexer for semantic search
- 4 memory types support

#### Smart Search
- Automatic scope detection (local/global)
- Cross-project learning
- AI-powered semantic search
- GitHub fallback for skills

#### SkillsMP Integration
- API client with rate limiting
- Local cache for results
- Skill comparison and conflict resolution
- GitHub fallback for community skills

#### Agent Creation
- Template generator for agents
- Auto-improvement from patterns
- Auto-handoff between specialists
- Skill creation workflow (search-before-create)

#### Auto-Save & Backup
- Auto-save trigger for events
- Memory backup system
- Project auto-detection
- Configuration management

#### Installation
- Global installation scripts
- Cross-platform support (Windows/Linux/macOS)
- Verification scripts
- Migration tools

#### Documentation
- Complete README
- Quickstart guide
- Migration guide
- Performance tuning guide
- Context usage analysis
- AI threshold tuning guide
- Feedback collection guide

#### Tests
- Unit tests for all modules
- Integration tests
- End-to-end tests
- Extension tests

#### SpecKit Integration
- `/speckit.specify` - Memory context before spec
- `/speckit.plan` - Architecture context for planning
- `/speckit.tasks` - Pattern suggestions for tasks
- `/speckit.clarify` - Cross-project context
- `/speckit.features` - Quick feature generation

### Performance

- Headers-first reading uses only ~1-2% of context window
- Supports 1000+ entries per project
- Search time <200ms for local, <1s for vector
- Scalable to large memory bases

### Security

- Local-only storage (no cloud upload)
- API keys stored securely
- Graceful degradation without Ollama
- Optional feedback collection

## [Unreleased]

### Planned for v0.2.0
- Fix extension import issues on Windows
- Add feedback collection system
- Implement performance monitoring
- Add automatic threshold tuning

### Planned for v0.3.0
- Database migration for 10K+ entries
- Web UI for memory browsing
- Team collaboration features
- Export/import functionality

---

[0.1.0]: https://github.com/spec-kit/spec-kit/releases/tag/v0.1.0
