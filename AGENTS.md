# Agent Integration Guide

## About Spec Kit and Specify

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework. It sets up the necessary directory structures, templates, and AI agent integrations to support the Spec-Driven Development workflow.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## General practices

- Any changes to `__init__.py` for the Specify CLI require a version rev in `pyproject.toml` and addition of entries to `CHANGELOG.md`.

## Adding New Agent Support

This section explains how to add support for new AI agents/assistants to the Specify CLI. Use this guide as a reference when integrating new AI tools into the Spec-Driven Development workflow.

### Overview

Specify supports multiple AI agents by generating agent-specific command files and directory structures when initializing projects. Each agent has its own conventions for:

- **Command file formats** (Markdown, TOML, etc.)
- **Directory structures** (`.claude/commands/`, `.windsurf/workflows/`, etc.)
- **Command invocation patterns** (slash commands, CLI tools, etc.)
- **Argument passing conventions** (`$ARGUMENTS`, `{{args}}`, etc.)

### Current Supported Agents

| Agent | Directory | Format | CLI Tool | Description |
|-------|-----------|---------|----------|-------------|
| **Claude Code** | `.claude/commands/` | Markdown | `claude` | Anthropic's Claude Code CLI |
| **Gemini CLI** | `.gemini/commands/` | TOML | `gemini` | Google's Gemini CLI |
| **GitHub Copilot** | `.github/prompts/` | Markdown | N/A (IDE-based) | GitHub Copilot in VS Code |
| **Cursor** | `.cursor/commands/` | Markdown | `cursor-agent` | Cursor CLI |
| **Qwen Code** | `.qwen/commands/` | TOML | `qwen` | Alibaba's Qwen Code CLI |
| **opencode** | `.opencode/command/` | Markdown | `opencode` | opencode CLI |
| **Windsurf** | `.windsurf/workflows/` | Markdown | N/A (IDE-based) | Windsurf IDE workflows |

### Step-by-Step Integration Guide

Follow these steps to add a new agent (using Windsurf as an example):

#### 1. Update AI_CHOICES Constant

Add the new agent to the `AI_CHOICES` dictionary in `src/specify_cli/__init__.py`:

```python
AI_CHOICES = {
    "copilot": "GitHub Copilot",
    "claude": "Claude Code",
    "gemini": "Gemini CLI",
    "cursor": "Cursor",
    "qwen": "Qwen Code",
    "opencode": "opencode",
    "windsurf": "Windsurf"  # Add new agent here
}
```

Also update the `agent_folder_map` in the same file to include the new agent's folder for the security notice:

```python
agent_folder_map = {
    "claude": ".claude/",
    "gemini": ".gemini/",
    "cursor": ".cursor/",
    "qwen": ".qwen/",
    "opencode": ".opencode/",
    "codex": ".codex/",
    "windsurf": ".windsurf/",  # Add new agent folder here
    "kilocode": ".kilocode/",
    "auggie": ".auggie/",
    "copilot": ".github/"
}
```

#### 2. Update CLI Help Text

Update all help text and examples to include the new agent:

- Command option help: `--ai` parameter description
- Function docstrings and examples
- Error messages with agent lists

#### 3. Update README Documentation

Update the **Supported AI Agents** section in `README.md` to include the new agent:

- Add the new agent to the table with appropriate support level (Full/Partial)
- Include the agent's official website link
- Add any relevant notes about the agent's implementation
- Ensure the table formatting remains aligned and consistent

#### 4. Update Release Package Script

Modify `.github/workflows/scripts/create-release-packages.sh`:

##### Add to ALL_AGENTS array:
```bash
ALL_AGENTS=(claude gemini copilot cursor qwen opencode windsurf)
```

##### Add case statement for directory structure:
```bash
case $agent in
  # ... existing cases ...
  windsurf)
    mkdir -p "$base_dir/.windsurf/workflows"
    generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script" ;;
esac
```

#### 4. Update GitHub Release Script

Modify `.github/workflows/scripts/create-github-release.sh` to include the new agent's packages:

```bash
gh release create "$VERSION" \
  # ... existing packages ...
  .genreleases/spec-kit-template-windsurf-sh-"$VERSION".zip \
  .genreleases/spec-kit-template-windsurf-ps-"$VERSION".zip \
  # Add new agent packages here
```

#### 5. Update Agent Context Scripts

##### Bash script (`scripts/bash/update-agent-context.sh`):

Add file variable:
```bash
WINDSURF_FILE="$REPO_ROOT/.windsurf/rules/specify-rules.md"
```

Add to case statement:
```bash
case "$AGENT_TYPE" in
  # ... existing cases ...
  windsurf) update_agent_file "$WINDSURF_FILE" "Windsurf" ;;
  "")
    # ... existing checks ...
    [ -f "$WINDSURF_FILE" ] && update_agent_file "$WINDSURF_FILE" "Windsurf";
    # Update default creation condition
    ;;
esac
```

##### PowerShell script (`scripts/powershell/update-agent-context.ps1`):

Add file variable:
```powershell
$windsurfFile = Join-Path $repoRoot '.windsurf/rules/specify-rules.md'
```

Add to switch statement:
```powershell
switch ($AgentType) {
    # ... existing cases ...
    'windsurf' { Update-AgentFile $windsurfFile 'Windsurf' }
    '' {
        foreach ($pair in @(
            # ... existing pairs ...
            @{file=$windsurfFile; name='Windsurf'}
        )) {
            if (Test-Path $pair.file) { Update-AgentFile $pair.file $pair.name }
        }
        # Update default creation condition
    }
}
```

#### 6. Update CLI Tool Checks (Optional)

For agents that require CLI tools, add checks in the `check()` command and agent validation:

```python
# In check() command
tracker.add("windsurf", "Windsurf IDE (optional)")
windsurf_ok = check_tool_for_tracker("windsurf", "https://windsurf.com/", tracker)

# In init validation (only if CLI tool required)
elif selected_ai == "windsurf":
    if not check_tool("windsurf", "Install from: https://windsurf.com/"):
        console.print("[red]Error:[/red] Windsurf CLI is required for Windsurf projects")
        agent_tool_missing = True
```

**Note**: Skip CLI checks for IDE-based agents (Copilot, Windsurf).

## Agent Categories

### CLI-Based Agents

Require a command-line tool to be installed:

| Agent | CLI Tool |
|-------|----------|
| Claude Code | `claude` |
| Gemini CLI | `gemini` |
| Cursor | `cursor-agent` |
| Qwen Code | `qwen` |
| opencode | `opencode` |

### IDE-Based Agents

Work within integrated development environments:

| Agent | Description |
|-------|-------------|
| GitHub Copilot | Built into VS Code/compatible editors |
| Windsurf | Built into Windsurf IDE |

## Command File Formats

### Markdown Format
Used by: Claude, Cursor, opencode, Windsurf

```markdown
---
description: "Command description"
---

Command content with {SCRIPT} and $ARGUMENTS placeholders.
```

### TOML Format
Used by: Gemini, Qwen

```toml
description = "Command description"

prompt = """
Command content with {SCRIPT} and {{args}} placeholders.
"""
```

## Directory Conventions

- **CLI agents**: Usually `.<agent-name>/commands/`
- **IDE agents**: Follow IDE-specific patterns:
  - Copilot: `.github/prompts/`
  - Cursor: `.cursor/commands/`
  - Windsurf: `.windsurf/workflows/`

## Argument Patterns

Different agents use different argument placeholders:

| Type | Placeholder | Description |
|------|-------------|-------------|
| Markdown/prompt-based | `$ARGUMENTS` | Used in markdown-based commands |
| TOML-based | `{{args}}` | Used in TOML configurations |
| Script placeholders | `{SCRIPT}` | Replaced with actual script path |
| Agent placeholders | `__AGENT__` | Replaced with agent name |

## Testing New Agent Integration

1. **Build test**: Run package creation script locally
2. **CLI test**: Test `specify init --ai <agent>` command
3. **File generation**: Verify correct directory structure and files
4. **Command validation**: Ensure generated commands work with the agent
5. **Context update**: Test agent context update scripts

## GitHub Integration Support

Spec Kit integrates with GitHub to track development workflow through issues and pull requests. Understanding how agents interact with GitHub is important for successful integration.

### Agents with Native GitHub MCP Support

The following agents have native support for GitHub MCP (Model Context Protocol):

| Agent | GitHub MCP Support | Notes |
|-------|-------------------|-------|
| **GitHub Copilot** | ✅ Native | Full MCP integration in VS Code |
| **Claude Code** | ✅ Likely | Anthropic supports MCP servers |
| **Cursor** | ⚠️ Partial | May require additional setup |
| **Gemini CLI** | ⚠️ Unknown | Requires testing |
| **Qwen Code** | ⚠️ Unknown | Requires testing |
| **opencode** | ⚠️ Unknown | Requires testing |
| **Windsurf** | ⚠️ Unknown | Requires testing |

**Legend:**
- ✅ Native: Works out-of-the-box with GitHub MCP tools
- ⚠️ Partial/Unknown: May work but requires testing or additional configuration
- ❌ None: Requires GitHub CLI (`gh`) fallback

### CLI Fallback for Non-MCP Agents

For agents without native GitHub MCP support, Spec Kit commands provide manual fallback instructions using the GitHub CLI:

**Example fallback commands:**
```bash
# Create issue
gh issue create --title "🚀 [Minor]: Feature name" --body "..." --label "Specification,Minor"

# Create draft PR
gh pr create --title "🚀 [Minor]: Feature name" --body "..." --draft --head branch-name

# Update PR status
gh pr ready <PR-number>

# Update labels
gh issue edit <issue-number> --remove-label "Plan" --add-label "Implementation"
```

### Testing GitHub Integration

When testing a new agent with GitHub integration:

1. **Test with MCP first**: Try using GitHub MCP operations in commands
2. **Verify error handling**: Ensure graceful fallback if MCP unavailable
3. **Test CLI fallback**: Run provided `gh` commands manually
4. **Document results**: Update agent table above with findings
5. **Report issues**: Open GitHub issues for integration problems

### GitHub Workflow Labels

Spec Kit uses semantic labels to track workflow state:

**Phase Labels** (mutually exclusive):
- `Specification` - Issue created, spec written
- `Plan` - Design complete, draft PR created
- `Implementation` - Implementation in progress/complete

**Type Labels** (semantic versioning hints):
- `Docs` - Documentation changes
- `Fix` - Bug fixes
- `Patch` - Small fixes
- `Minor` - New features (backward compatible)
- `Major` - Breaking changes

These labels are automatically managed by `/specify`, `/plan`, and `/implement` commands.

### Troubleshooting GitHub Integration

**Problem**: GitHub operations fail with "tools not available"

**Solutions:**
1. Check if agent supports GitHub MCP
2. Verify GitHub CLI (`gh`) is installed and authenticated
3. Use manual fallback commands provided in error messages
4. Report issue with agent details for investigation

**Problem**: Rate limiting errors

**Solutions:**
1. Wait for rate limit reset
2. Use GitHub token with higher limits
3. Continue with local workflow (specs/plans/tasks work offline)

## Common Pitfalls

1. **Forgetting update scripts**: Both bash and PowerShell scripts must be updated
2. **Missing CLI checks**: Only add for agents that actually have CLI tools
3. **Wrong argument format**: Use correct placeholder format for each agent type
4. **Directory naming**: Follow agent-specific conventions exactly
5. **Help text inconsistency**: Update all user-facing text consistently

## Future Considerations

When adding new agents:
- Consider the agent's native command/workflow patterns
- Ensure compatibility with the Spec-Driven Development process
- Document any special requirements or limitations
- Update this guide with lessons learned

---

*This documentation should be updated whenever new agents are added to maintain accuracy and completeness.*
