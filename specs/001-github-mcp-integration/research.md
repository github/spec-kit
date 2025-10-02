# Research: GitHub MCP Integration for Spec-Driven Development

**Feature**: 001-github-mcp-integration
**Date**: 2025-10-02
**Status**: Complete

## Research Overview

This document captures technical research and decisions for integrating GitHub MCP (Model Context Protocol) operations throughout the Spec-Driven Development workflow. The research focuses on understanding existing implementations in `.github/prompts/` files and determining the best approach to synchronize them with generic `templates/commands/` files.

## Key Research Areas

### 1. GitHub MCP Capabilities

**Decision**: Use GitHub MCP tools available through AI agents for issue/PR management

**Rationale**:
- GitHub MCP provides native integration with GitHub API through AI agents
- Enables automated issue creation, PR management, and label updates
- No additional authentication setup required (uses agent's GitHub context)
- Consistent API across different AI agents

**Alternatives considered**:
- GitHub CLI (`gh`) - Would require installation and authentication setup
- Direct GitHub API calls - Would require token management and more complex error handling
- Manual workflow - Defeats the purpose of automation

**Implementation approach**:
- Use MCP commands like `mcp_github_create_issue`, `mcp_github_create_pull_request`, etc.
- Leverage existing GitHub context from AI agents
- Implement error handling for API failures

### 2. Template Synchronization Strategy

**Decision**: Maintain two synchronized locations with consistent GitHub MCP operations

**Rationale**:
- `.github/prompts/*.prompt.md` - GitHub Copilot-specific (already has GitHub MCP)
- `templates/commands/*.md` - Generic agent templates (needs GitHub MCP added)
- Both must have identical GitHub integration logic
- Project initialization copies from `templates/` to agent-specific directories

**Alternatives considered**:
- Single source of truth with generation - Would complicate existing project structure
- Agent-specific only - Would break non-Copilot agent support
- Manual synchronization - Error-prone and maintenance burden

**Implementation approach**:
- Use `.github/prompts/` as reference implementation
- Compare and identify GitHub MCP operations in each command
- Add equivalent operations to `templates/commands/` files
- Document synchronization requirement in constitution

### 3. Issue and PR Label Schema

**Decision**: Use semantic labels with backtick formatting for phase and type tracking

**Rationale**:
- Phase labels: `Specification`, `Plan`, `Implementation` - Track workflow state
- Type labels: `Docs`, `Fix`, `Patch`, `Minor`, `Major` - Semantic versioning hints
- Backtick formatting emphasizes these are system-managed labels
- Supports filtering and automation based on label state

**Alternatives considered**:
- Plain text labels - Less visually distinctive
- Status field instead of labels - Not standard GitHub approach
- Single combined label - Loses granularity for filtering

**Implementation approach**:
- `/specify` creates issue with `Specification` + type label
- `/plan` removes `Specification`, adds `Plan`
- `/implement` adds `Implementation`
- Labels formatted with backticks in documentation and code

### 4. PR Title and Description Formatting

**Decision**: Use structured format with icons, types, and progressive content updates

**PR Title Format**: `<Icon> [Type]: <Short description>`

**Icons mapping**:
- 📖 Docs
- 🪲 Fix
- ⚠️ Security fix
- 🩹 Patch
- 🚀 Feature (Minor)
- 🌟 Breaking change (Major)

**PR Description Format**:
1. Leading summary paragraph (no title)
2. Plan content (from plan.md)
3. Tasks content with checkboxes (from tasks.md)
4. "- Fixes #<issue-number>" line
5. Additional context (Why, How, What)

**Rationale**:
- Visual icons provide quick PR type identification
- Structured description maintains all phase artifacts
- Progressive updates show workflow state
- Issue linking enables automatic closure on merge
- Avoids superfluous headers that add noise

**Alternatives considered**:
- Plain text titles - Less visually distinctive in PR lists
- Separate PRs per phase - Would fragment the workflow
- Static description - Wouldn't show progress through phases

**Implementation approach**:
- `/plan` creates draft PR with initial structure
- `/tasks` appends tasks.md content with checkboxes
- `/implement` updates checkboxes and marks ready for review

### 5. Branch Name Generation Strategy

**Decision**: AI-powered branch name generation from feature descriptions

**Rationale**:
- AI analyzes feature description to extract core concepts (2-4 words)
- Generates kebab-case names focused on primary change
- Auto-incremented feature number prepended by script
- Results in meaningful branch names like `001-github-mcp-integration`

**Alternatives considered**:
- User-provided names - Inconsistent formatting and quality
- Hash-based names - Not human-readable
- Full sentence slugification - Too long and noisy

**Implementation approach**:
- `/specify` prompt includes branch name generation logic
- Extracts core action/concept from feature description
- Converts to kebab-case format
- Passes to `create-new-feature.ps1` script for feature number prepending

### 6. Constitution Update Strategy

**Decision**: Automated constitution updates during `/implement` phase

**Rationale**:
- Constitution is the single source of truth for project capabilities
- Must be updated when new functionality is implemented
- Automation ensures documentation stays synchronized
- Updates captured in implementation commit

**Alternatives considered**:
- Manual updates - Often forgotten, leads to documentation drift
- Post-merge updates - Too late, loses context
- No updates - Constitution becomes stale

**Implementation approach**:
- `/implement` command includes constitution update step
- AI summarizes newly implemented functionality
- Appends to appropriate constitution section
- Commits with implementation changes

### 7. Error Handling and Rollback Strategy

**Decision**: Graceful degradation with clear error messages

**Rationale**:
- GitHub API may be unavailable or rate-limited
- Network issues can interrupt operations
- Users need clear guidance on recovery

**Alternatives considered**:
- Fail fast with no recovery - Poor user experience
- Automatic retry loops - May hit rate limits
- Silent failures - Worse than crashes

**Implementation approach**:
- Check for GitHub API availability before operations
- Provide clear error messages with recovery steps
- Document manual fallback procedures
- Log operation state for debugging

### 8. Cross-Platform Compatibility

**Decision**: Maintain both bash and PowerShell script implementations

**Rationale**:
- Spec Kit supports Windows, macOS, and Linux
- Bash scripts for Unix-like systems
- PowerShell scripts for Windows (and cross-platform)
- Git operations are inherently cross-platform

**Alternatives considered**:
- PowerShell only - Would limit macOS/Linux users
- Bash only - Would limit Windows users
- Python scripts - Adds dependency, not always available

**Implementation approach**:
- No script changes needed for this feature (GitHub MCP in templates only)
- Verify existing scripts remain cross-platform compatible
- Document any platform-specific GitHub MCP behaviors

## Technical Decisions Summary

| Area | Decision | Impact |
|------|----------|--------|
| GitHub Integration | Use GitHub MCP through AI agents | Enables automation without auth complexity |
| Template Sync | Maintain `.github/prompts/` and `templates/` | Consistent experience across agents |
| Labels | Semantic labels with backticks | Clear workflow state tracking |
| PR Format | Icons + structured progressive description | Visual clarity + workflow visibility |
| Branch Names | AI-generated kebab-case | Meaningful, consistent naming |
| Constitution | Auto-update during implement | Documentation stays current |
| Error Handling | Graceful degradation | Better user experience |
| Platform Support | No changes needed | Maintains existing cross-platform support |

## Implementation Risks

| Risk | Mitigation |
|------|-----------|
| GitHub API rate limits | Implement error handling, document manual fallback |
| Template synchronization drift | Add to constitution, document in CONTRIBUTING.md |
| Agent compatibility issues | Test across multiple agents before release |
| Label conflicts with existing projects | Use backtick formatting to distinguish system labels |
| PR description format changes breaking automation | Version template format, document breaking changes |

## Dependencies

- **External**: GitHub MCP tools in AI agents (GitHub Copilot, Claude Code, etc.)
- **Internal**: Existing Specify CLI, template system, script infrastructure
- **Documentation**: AGENTS.md, CONTRIBUTING.md, constitution.md

## Next Steps (Phase 1)

1. Create data model for GitHub entities (Issue, PR, Labels)
2. Generate contracts for GitHub MCP operations
3. Create quickstart validation scenarios
4. Update agent context with GitHub integration details
