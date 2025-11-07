# AI Agent Configuration

**Purpose:** Configure AI coding assistant behavior for this project
**Last Updated:** [Date]

---

## Context Files

The AI agent has access to these context files:

- **Constitution:** `memory/constitution.md` - Core principles and guidelines
- **Quick Reference:** `.ai/quick-ref.md` - Ultra-compact project reference
- **AI Documentation:** `.ai/ai-doc.md` - Detailed project context

---

## Agent Behavior

### Communication Style
- Be concise and direct
- Ask clarifying questions when requirements are ambiguous
- Explain reasoning for significant decisions
- Acknowledge limitations and uncertainties

### Code Generation
- Follow project coding standards
- Include appropriate error handling
- Add comments for complex logic
- Generate tests alongside implementation

### Problem Solving
- Break down complex problems into manageable steps
- Consider edge cases and error conditions
- Suggest multiple approaches when appropriate
- Explain trade-offs between solutions

---

## Workflow Integration

### Before Coding
1. Read relevant specifications
2. Understand acceptance criteria
3. Review related code
4. Plan approach

### During Coding
1. Follow established patterns
2. Write tests first (TDD)
3. Commit frequently with clear messages
4. Update documentation as needed

### After Coding
1. Run all tests
2. Check code quality (linting, formatting)
3. Review changes carefully
4. Update relevant specifications

---

## Commands Reference

### Development
- `/specify` - Create feature specification
- `/plan` - Generate implementation plan
- `/tasks` - Break down into actionable tasks
- `/implement` - Execute implementation

### Quality
- `/validate` - Validate specification quality
- `/analyze` - Analyze cross-artifact consistency
- `/checklist` - Generate quality checklist

### Utilities
- `/budget` - Check token usage
- `/prune` - Compress session context
- `/find <query>` - Semantic code search

---

## Project-Specific Guidelines

### File Organization
[Describe project-specific file organization]

### Testing Approach
[Describe testing requirements and patterns]

### Documentation Standards
[Describe documentation expectations]

### Code Review Process
[Describe how code reviews work]

---

## Common Tasks

### Adding a New Feature
1. Create specification with `/specify`
2. Generate plan with `/plan`
3. Break into tasks with `/tasks`
4. Implement with `/implement`
5. Validate with tests

### Fixing a Bug
1. Reproduce the issue
2. Write failing test
3. Fix the bug
4. Verify test passes
5. Add regression test

### Refactoring Code
1. Ensure existing tests pass
2. Make incremental changes
3. Run tests after each change
4. Update documentation
5. Review for side effects

---

## Resources

- **Main Documentation:** `docs/`
- **Architecture Diagrams:** `docs/architecture/`
- **API Documentation:** `docs/api/`
- **Team Wiki:** [Link]
