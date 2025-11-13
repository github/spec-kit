# New Slash Commands for Spec-Kit

## Overview

This document describes two new productivity commands added to the Spec-Kit toolkit, designed to optimize AI agent context management and conversation efficiency.

## Commands Added

### 1. `/rec_remove_agents_mcp`

**Purpose**: Analyze current project and recommend which agents/MCP servers to keep or remove for optimal context management

**Location**: `templates/commands/rec_remove_agents_mcp.md`

**Key Features**:
- Analyzes active agents and installed MCP servers
- Reviews usage patterns from conversation history
- Provides actionable recommendations (KEEP/REMOVE/CONSIDER)
- Estimates context window savings
- Project-type specific heuristics

**When to Use**:
- Context window is becoming constrained
- Starting a new project phase
- After installing multiple MCP servers
- When experiencing performance issues

**Example Output**:
```markdown
## Recommendations

### ✅ KEEP (Essential)
- **filesystem**: File operations essential for all development
- **git**: Version control integration

### ❌ REMOVE (Unused/Redundant)
- **sqlite**: Database operations not needed for frontend-only project
  - Savings: ~15% context window reduction

### 🤔 CONSIDER (Project-Specific)
- **playwright**: Add if doing E2E testing
```

---

### 2. `/compact_with_topic`

**Purpose**: Automatically analyze recent conversation topics and run `/compact` with intelligent focus

**Location**: `templates/commands/compact_with_topic.md`

**Key Features**:
- Analyzes last 30-50 messages for key topics
- Identifies what must be preserved vs. noise
- Generates optimized compact focus
- Automatically invokes `/compact`
- Handles multiple conversation patterns (debugging, feature dev, exploration)

**When to Use**:
- Conversation exceeds 100+ messages
- Context window pressure
- After completing a major topic
- Before switching to new feature

**Example Scenarios**:

**Feature Development**:
```bash
/compact_with_topic
# Preserves: JWT implementation, active work on auth.py, CORS issues
# Drops: OAuth exploration (decision made), resolved errors
```

**Debugging Session**:
```bash
/compact_with_topic
# Preserves: Active CORS errors, file paths, error messages
# Drops: Fixed issues, off-topic discussions
```

**User-Specified Focus**:
```bash
/compact_with_topic Keep only the API design discussion
# Focuses specifically on API design while adding critical context
```

---

## Design Decisions

### Following Spec-Kit Conventions

Both commands follow the established patterns in spec-kit:

1. **YAML Frontmatter**:
   ```yaml
   ---
   description: Clear one-line description
   ---
   ```

2. **User Input Section**: Always consider `$ARGUMENTS`

3. **Structured Outline**:
   - Phase-based execution flow
   - Clear prerequisites and outputs
   - Error handling specified

4. **Detailed Guidelines**:
   - Examples (✅ CORRECT / ❌ WRONG)
   - Special cases documented
   - Best practices included

5. **Non-Destructive by Default**:
   - `/rec_remove_agents_mcp`: Only recommends, doesn't execute
   - `/compact_with_topic`: Warns about destructive nature

### Design Philosophy Alignment

These commands align with Spec-Kit's core principles:

- **Spec-Driven**: Commands follow template-driven structure
- **Constitutional**: Respect project constraints and conventions
- **Executable**: Immediately usable with clear outcomes
- **Validated**: Built-in checks and error handling

---

## Testing Locally

To test these commands locally:

1. **Create release packages**:
   ```bash
   ./.github/workflows/scripts/create-release-packages.sh v1.0.0
   ```

2. **Copy to test project**:
   ```bash
   cp -r .genreleases/sdd-[agent]-package-sh/. <test-project-path>/
   ```

3. **Open agent and test**:
   ```bash
   cd <test-project-path>
   claude  # or your AI agent

   # Test commands
   /rec_remove_agents_mcp
   /compact_with_topic
   ```

---

## Documentation Updates

Updated `README.md` to include new section:

```markdown
#### Productivity & Optimization Commands

Commands for managing development environment and conversation efficiency:

| Command                     | Description                                                           |
|-----------------------------|-----------------------------------------------------------------------|
| `/rec_remove_agents_mcp`    | Analyze current project and recommend which agents/MCP servers to keep or remove for optimal context management |
| `/compact_with_topic`       | Automatically analyze recent conversation topics and run `/compact` with intelligent focus |
```

---

## Use Cases

### Scenario 1: Starting a New Project

```bash
# Initialize project
specify init my-app

# Too many MCP servers installed?
/rec_remove_agents_mcp

# Follow recommendations to optimize context
```

### Scenario 2: Long Debugging Session

```bash
# After 100+ messages debugging CORS issues...
/compact_with_topic

# Preserves: error context, file paths, attempted solutions
# Drops: resolved issues, tangents, greetings
```

### Scenario 3: Project Phase Shift

```bash
# Finished authentication, starting on payment system

# Clean up unused context
/rec_remove_agents_mcp
# Remove: auth-specific MCP servers
# Add: payment-related servers

/compact_with_topic
# Preserve: key auth decisions, API structure
# Drop: detailed auth debugging history
```

---

## Future Enhancements

Potential improvements for future iterations:

1. **Automatic Invocation**:
   - Auto-suggest `/rec_remove_agents_mcp` when multiple servers detected
   - Auto-suggest `/compact_with_topic` at message count thresholds

2. **Usage Analytics**:
   - Track actual MCP server usage over time
   - Provide trend analysis

3. **Smart Compaction Strategies**:
   - Learn from user's compact preferences
   - Adaptive topic detection

4. **Integration with Spec-Kit Workflow**:
   - Trigger `/rec_remove_agents_mcp` after `/speckit.plan`
   - Suggest `/compact_with_topic` between features

---

## Contributing

These commands were created following the guidelines in `CONTRIBUTING.md`:

- ✅ AI-assisted (disclosed)
- ✅ Tested locally
- ✅ Documentation updated
- ✅ Follows project conventions
- ✅ Includes examples and error handling

---

## Files Changed

```
templates/commands/rec_remove_agents_mcp.md      (new)
templates/commands/compact_with_topic.md         (new)
README.md                                        (modified - added command table)
NEW_COMMANDS_SUMMARY.md                          (new - this file)
```

---

## Next Steps

1. **Local Testing**: Test commands with various project types
2. **Community Review**: Get feedback on command structure and usefulness
3. **Documentation**: Add to spec-kit documentation site if accepted
4. **Integration**: Consider adding to `specify init` workflow

---

## Contact

For questions or feedback about these commands, please open an issue in the spec-kit repository.
