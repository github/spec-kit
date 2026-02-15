# MiniSpec Constitution

## Core Principles

### I. Template Quality

**Priority: MUST**

Prompts are the product. All slash command templates must:

- Guide engineers toward good decisions without being prescriptive
- Support collaborative workflows that increase velocity and productivity
- Use clear, unambiguous language that works across different AI agents
- Feel like a skilled pair partner, not a checklist

### II. Extensibility

**Priority: MUST**

MiniSpec is a platform, not just a tool. The architecture must support:

- Community-contributed slash commands, skills, and hooks
- A registry model for distributing extensions (public curated + private enterprise)
- Engineers adjusting MiniSpec to suit their specific workflows and needs
- Clean extension points that don't require forking the core

### III. Enterprise Safety

**Priority: MUST**

Enterprise adoption requires trust. All extensibility must be matched with safety:

- Public registries are heavily controlled and reviewed before publishing
- Private registries allow enterprises to maintain internal-only extensions
- Both process (vetting, review) and technical (sandboxing, signing, permissions) guardrails
- Skills and hooks from external sources must be safe for enterprise environments
- Registry installation from internal repos (e.g., private Git, Artifactory)

### IV. Documentation

**Priority: MUST**

Enterprise context demands transparency:

- User-facing documentation for all features and workflows
- Architecture decisions recorded as ADRs for transparency
- Documentation maintained as a byproduct of development, not an afterthought

### V. Test Coverage

**Priority: SHOULD**

- CLI behavior and commands must be tested
- Template validation is out of scope (would require an evals suite)
- Tests should catch regressions in core functionality

## Technology Stack

- **Language**: Python 3.11+
- **CLI Framework**: Typer
- **Package Manager**: uv
- **Target Users**: Enterprise software engineers
- **AI Agents**: Claude Code (primary), with support for Cursor, Copilot, Gemini CLI, and others

## Development Workflow

- Feature branches off main
- PR reviews required
- CI must pass (markdownlint, tests)
- Conventional commit messages

---

## MiniSpec Preferences

### Review Chunk Size

adaptive

### Documentation Review Policy

trust-ai

### Autonomy Level

familiar-areas

### Design Evolution Handling

always-discuss

### Walkthrough Depth

standard

---

## Governance

This constitution supersedes default practices for the MiniSpec project. Principles are non-negotiable unless amended through explicit discussion. MiniSpec preferences can be adjusted per-feature if needed.

**Version**: 1.0.0 | **Ratified**: 2026-02-15 | **Last Amended**: 2026-02-15
