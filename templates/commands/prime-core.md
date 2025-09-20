---
description: Prime AI agent with comprehensive project context for effective development assistance.
---

# Prime Core - Project Context Loading

**Context Request**: $ARGUMENTS

## Context Priming Process

### 1. Project Overview Discovery

**Essential Project Information**:

```bash
# Get basic project structure
ls -la
tree -L 2 -I 'node_modules|.git|__pycache__'

# Check project type and configuration
find . -name "package.json" -o -name "pyproject.toml" -o -name "Cargo.toml" -o -name "go.mod" -o -name "pom.xml" | head -5

# Identify main programming languages
find . -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" -o -name "*.java" | head -10
```

**Project Type Classification**:
- [ ] **Single Library**: Focused library with CLI interface
- [ ] **Web Application**: Frontend + Backend architecture
- [ ] **Mobile App**: Native mobile with API backend
- [ ] **Microservices**: Multiple interconnected services
- [ ] **CLI Tool**: Command-line application
- [ ] **Mixed/Complex**: Hybrid architecture

### 2. Spec Kit Framework Understanding

**Constitutional Principles** (from memory/constitution.md):

Load and summarize the project's constitutional principles:
- Library-first development approach
- CLI interface requirements
- Test-first methodology (NON-NEGOTIABLE)
- Integration testing strategy
- Observability requirements
- Versioning and change management

**Current Development Phase**:
```bash
# Check for active specifications
find specs/ -name "spec.md" -exec head -5 {} \; 2>/dev/null

# Look for current plans and tasks
find specs/ -name "plan.md" -o -name "tasks.md" 2>/dev/null

# Identify current branch and feature
git branch --show-current
git log --oneline -5
```

### 3. Codebase Architecture Analysis

**Core Structure Discovery**:

```bash
# Identify libraries and their purposes
ls -la src/*/cli/ 2>/dev/null || echo "No CLI interfaces found"
ls -la src/ | grep -E "^d" | head -10

# Check testing structure
ls -la tests/ 2>/dev/null
find . -name "*test*" -type d | head -5

# Look for documentation
ls -la docs/ ai_docs/ 2>/dev/null
find . -name "README*" -o -name "*.md" | head -10
```

**Library Interface Analysis**:
- Document each library's purpose and CLI interface
- Note inter-library dependencies
- Identify shared utilities and common patterns
- Map external service integrations

### 4. Context Engineering Resources

**AI Documentation Loading**:

```bash
# Load project-specific AI documentation
ls -la ai_docs/
cat ai_docs/README.md 2>/dev/null
```

**Essential Context Files**:
1. **Library Gotchas** (`ai_docs/library_gotchas.md`):
   - Version-specific quirks and limitations
   - Common pitfalls and workarounds
   - Performance considerations

2. **Implementation Patterns** (`ai_docs/framework_patterns.md`):
   - Established codebase conventions
   - Reusable design patterns
   - Integration approaches

3. **Custom Utilities** (`ai_docs/custom_utils.md`):
   - Project-specific helper functions
   - Internal APIs and interfaces
   - Development tools and scripts

### 5. Recent Context & Development State

**Git History Analysis**:
```bash
# Recent development activity
git log --oneline --since="2 weeks ago"
git log --stat --since="1 week ago" | head -20

# Current changes and work in progress
git status
git diff --stat

# Active branches and their purposes
git branch -a | head -10
```

**Current Work Context**:
- What feature is currently being developed?
- What tests are failing or need attention?
- Are there merge conflicts or blockers?
- What specifications are in draft state?

### 6. Technology Stack & Dependencies

**Primary Dependencies**:
```bash
# Python projects
cat pyproject.toml requirements.txt 2>/dev/null | head -20

# Node.js projects
cat package.json | head -20

# Go projects
cat go.mod go.sum 2>/dev/null | head -20

# Rust projects
cat Cargo.toml 2>/dev/null | head -20
```

**Development Environment**:
- Required tools and versions
- Local development setup
- Testing framework configuration
- Build and deployment processes

### 7. Quality & Compliance Status

**Current Validation State**:
```bash
# Run basic health checks
git status --porcelain | wc -l  # Uncommitted changes
find . -name "*.py" -exec python -m py_compile {} \; 2>&1 | head -5  # Syntax check
find . -name "package.json" -exec npm list --depth=0 2>/dev/null \; | head -10  # Dependency check
```

**Constitutional Compliance**:
- Are all libraries exposing CLI interfaces?
- Is test-first development being followed?
- Are integration tests comprehensive?
- Is structured logging implemented?

### 8. Context Integration Summary

**Comprehensive Context Report**:

```markdown
# Project Context Summary

## Project Classification
**Type**: [Single Library/Web App/Mobile/Microservices/CLI/Mixed]
**Primary Language**: [Python/JavaScript/Go/Rust/Java]
**Architecture**: [Brief description of overall architecture]

## Constitutional Status
- **Library-First**: [Compliant/Needs Attention/Non-Compliant]
- **CLI Interfaces**: [Count of libraries with CLI/Total libraries]
- **Test-First**: [Evidence in git history/Needs improvement]
- **Integration Tests**: [Comprehensive/Basic/Missing]

## Active Development
**Current Feature**: [Description of current work]
**Active Branch**: [Branch name and purpose]
**Recent Focus**: [What's been worked on recently]
**Blockers**: [Any current impediments]

## Technology Stack
**Core Dependencies**: [List 3-5 most important dependencies]
**Testing Framework**: [Primary testing approach]
**Build System**: [How project is built and deployed]
**Database**: [If applicable, database technology]

## Context Engineering Resources
**AI Docs Available**: [List available ai_docs/ files]
**Library Gotchas**: [Count of documented gotchas]
**Pattern Documentation**: [Available pattern guides]
**Similar Features**: [Examples for reference]

## Code Quality Status
**Test Coverage**: [Estimated coverage level]
**Linting Status**: [Clean/Has issues/Unknown]
**Documentation**: [Comprehensive/Basic/Needs work]
**Performance**: [Known issues or concerns]

## Immediate Context
**Ready for Development**: [Yes/Needs setup/Has blockers]
**Recommended Next Actions**: [What should be worked on next]
**Key Files to Review**: [Most important files for understanding]
**Common Patterns**: [Established patterns to follow]
```

### 9. Specialized Context Loading

**For Specification Work**:
- Load current specifications and their completeness
- Review context engineering sections
- Identify research gaps or clarification needs
- Check user story coverage and acceptance criteria

**For Implementation Work**:
- Analyze test coverage and testing strategy
- Review architectural decisions and constraints
- Load relevant implementation patterns
- Check for integration requirements

**For Debugging Work**:
- Review recent error logs and issues
- Load troubleshooting documentation
- Check for known issues in ai_docs/library_gotchas.md
- Analyze recent changes that might have introduced problems

### 10. Context Validation & Readiness

**Context Completeness Check**:
- [ ] Project structure understood
- [ ] Constitutional principles loaded
- [ ] Current development state clear
- [ ] Technology stack documented
- [ ] Key dependencies identified
- [ ] Testing approach understood
- [ ] Quality status assessed
- [ ] Development environment ready

**Readiness Assessment**:
```markdown
## Context Loading Complete

**Readiness Level**: [Fully Ready/Mostly Ready/Needs Attention/Blocked]

**Confidence Areas**:
- [List areas where context is comprehensive]

**Knowledge Gaps**:
- [List areas needing more information]

**Recommended Actions**:
- [Specific steps to improve context or begin work]

**Key Reminders**:
- [Critical project-specific considerations]
```

## Context Refresh Protocol

**When to Re-prime**:
- After major architectural changes
- When switching between different features
- After long periods of inactivity
- When onboarding new team members
- Before major refactoring efforts

**Quick Context Updates**:
```bash
# Fast context refresh for ongoing work
git log --oneline -10
git status
ls specs/*/plan.md 2>/dev/null | xargs ls -la
```

Remember: Good context priming prevents implementation errors and accelerates development. Invest time in comprehensive context loading for better outcomes.