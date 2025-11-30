# AGENTS.md

## About Spectrena

**Spectrena** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) with lineage tracking - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, CLI commands, MCP servers, and workflows that guide development teams through a structured approach to building software.

Spectrena extends [GitHub Spec Kit](https://github.com/github/spec-kit) with configurable spec IDs, discovery phases, parallel development via git worktrees, and full traceability from specs → tasks → code.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## General Practices

- All CLI code is in `src/spectrena/` (pure Python, no bash/PowerShell)
- Version changes require updates to `pyproject.toml` and `CHANGELOG.md`
- Agent support is configured in `src/spectrena/agents.py`

## Adding New Agent Support

This section explains how to add support for new AI agents/assistants to Spectrena. Use this guide as a reference when integrating new AI tools into the Spec-Driven Development workflow.

### Overview

Spectrena supports multiple AI agents by generating agent-specific command files and directory structures when initializing projects. Each agent has its own conventions for:

- **Command file formats** (Markdown, TOML, etc.)
- **Directory structures** (`.claude/commands/`, `.windsurf/workflows/`, etc.)
- **Command invocation patterns** (slash commands, CLI tools, etc.)
- **Argument passing conventions** (`$ARGUMENTS`, `{{args}}`, etc.)

### Current Supported Agents

| Agent | Directory | Format | CLI Tool | Description |
|-------|-----------|--------|----------|-------------|
| **Claude Code** | `.claude/commands/` | Markdown | `claude` | Anthropic's Claude Code CLI |
| **Gemini CLI** | `.gemini/commands/` | TOML | `gemini` | Google's Gemini CLI |
| **GitHub Copilot** | `.github/agents/` | Markdown | N/A (IDE-based) | GitHub Copilot in VS Code |
| **Cursor** | `.cursor/commands/` | Markdown | `cursor-agent` | Cursor CLI |
| **Qwen Code** | `.qwen/commands/` | TOML | `qwen` | Alibaba's Qwen Code CLI |
| **opencode** | `.opencode/command/` | Markdown | `opencode` | opencode CLI |
| **Codex CLI** | `.codex/commands/` | Markdown | `codex` | Codex CLI |
| **Windsurf** | `.windsurf/workflows/` | Markdown | N/A (IDE-based) | Windsurf IDE workflows |
| **Kilo Code** | `.kilocode/rules/` | Markdown | N/A (IDE-based) | Kilo Code IDE |
| **Auggie CLI** | `.augment/rules/` | Markdown | `auggie` | Auggie CLI |
| **Roo Code** | `.roo/rules/` | Markdown | N/A (IDE-based) | Roo Code IDE |
| **CodeBuddy CLI** | `.codebuddy/commands/` | Markdown | `codebuddy` | CodeBuddy CLI |
| **Amazon Q Developer CLI** | `.amazonq/prompts/` | Markdown | `q` | Amazon Q Developer CLI |
| **Amp** | `.agents/commands/` | Markdown | `amp` | Amp CLI |
| **SHAI** | `.shai/commands/` | Markdown | `shai` | SHAI CLI |
| **IBM Bob** | `.bob/commands/` | Markdown | N/A (IDE-based) | IBM Bob IDE |

### Step-by-Step Integration Guide

Follow these steps to add a new agent:

#### 1. Add to AGENT_CONFIG

**IMPORTANT**: Use the actual CLI tool name as the key, not a shortened version.

Add the new agent to `src/spectrena/agents.py`:

```python
AGENT_CONFIG: dict[str, AgentConfig] = {
    # ... existing agents ...
    "new-agent-cli": AgentConfig(
        name="New Agent Display Name",
        folder=".newagent/",           # Directory for agent files
        commands_subdir="commands/",    # Subdirectory for command files
        format="markdown",              # "markdown" or "toml"
        arg_placeholder="$ARGUMENTS",   # How arguments are passed
        install_url="https://example.com/install",  # URL for installation (None if IDE-based)
        requires_cli=True,              # True if CLI tool required
    ),
}
```

**Key Design Principle**: The dictionary key should match the actual executable name that users install. For example:

- ✅ Use `"cursor-agent"` because the CLI tool is literally called `cursor-agent`
- ❌ Don't use `"cursor"` as a shortcut if the tool is `cursor-agent`

#### 2. Add Command Generation Logic

In `src/spectrena/agents.py`, ensure the agent's format is handled:

```python
def generate_command_file(
    agent: str,
    command_name: str,
    content: str,
    output_dir: Path,
) -> Path:
    """Generate a command file for the specified agent."""
    config = AGENT_CONFIG[agent]
    
    if config.format == "markdown":
        return _generate_markdown_command(config, command_name, content, output_dir)
    elif config.format == "toml":
        return _generate_toml_command(config, command_name, content, output_dir)
    else:
        raise ValueError(f"Unknown format: {config.format}")
```

#### 3. Update CLI Help Text

Update the `--ai` parameter in `src/spectrena/__init__.py`:

```python
@app.command()
def init(
    ai_assistant: Optional[str] = typer.Option(
        None, 
        "--ai", 
        help="AI assistant: claude, gemini, copilot, cursor-agent, qwen, opencode, windsurf, q, ..."
    ),
):
```

#### 4. Update Documentation

Update `README.md`:
- Add to the Supported AI Agents table
- Include installation link
- Note any special requirements

Update this `AGENTS.md`:
- Add to the Current Supported Agents table
- Add to the appropriate category (CLI-based or IDE-based)

#### 5. Add Context Update Support

In `src/spectrena/context.py`, add the agent's context file path:

```python
AGENT_CONTEXT_FILES: dict[str, str] = {
    # ... existing agents ...
    "new-agent-cli": ".newagent/context.md",
}

def get_agent_context_file(agent: str, project_root: Path) -> Path:
    """Get the path to an agent's context file."""
    if agent in AGENT_CONTEXT_FILES:
        return project_root / AGENT_CONTEXT_FILES[agent]
    # Fallback to AGENTS.md
    return project_root / "AGENTS.md"
```

#### 6. Update Doctor Command

In `src/spectrena/doctor.py`, agent CLI checks are automatic based on `AGENT_CONFIG`:

```python
def check_agents() -> list[CheckResult]:
    """Check all agents that require CLI tools."""
    results = []
    for agent_key, config in AGENT_CONFIG.items():
        if config.requires_cli:
            results.append(check_tool(
                agent_key, 
                config.name,
                config.install_url,
                required=False  # Agents are optional
            ))
    return results
```

No additional code needed - just set `requires_cli=True` in the config.

---

## Important Design Decisions

### Using Actual CLI Tool Names as Keys

**CRITICAL**: When adding a new agent to AGENT_CONFIG, always use the **actual executable name** as the dictionary key.

**Why this matters:**

- The `check_tool()` function uses `shutil.which(tool)` to find executables
- If the key doesn't match the actual CLI tool name, you'll need special-case mappings
- This creates unnecessary complexity and maintenance burden

**Example - The Cursor Lesson:**

❌ **Wrong approach** (requires special-case mapping):
```python
AGENT_CONFIG = {
    "cursor": AgentConfig(  # Shorthand that doesn't match the actual tool
        name="Cursor",
        ...
    )
}
# Then you need special cases everywhere
```

✅ **Correct approach** (no mapping needed):
```python
AGENT_CONFIG = {
    "cursor-agent": AgentConfig(  # Matches the actual executable name
        name="Cursor",
        ...
    )
}
# No special cases needed!
```

### Pure Python Implementation

Spectrena uses pure Python instead of bash/PowerShell scripts:

- **Cross-platform**: Works on Windows, macOS, Linux without shell dependencies
- **Testable**: Use pytest instead of bats/pester
- **Maintainable**: Single codebase, no duplicate scripts
- **Type-safe**: Full type hints with pyright checking

---

## Agent Categories

### CLI-Based Agents

Require a command-line tool to be installed:

- **Claude Code**: `claude` CLI
- **Gemini CLI**: `gemini` CLI  
- **Cursor**: `cursor-agent` CLI
- **Qwen Code**: `qwen` CLI
- **opencode**: `opencode` CLI
- **Amazon Q Developer CLI**: `q` CLI
- **CodeBuddy CLI**: `codebuddy` CLI
- **Amp**: `amp` CLI
- **SHAI**: `shai` CLI

### IDE-Based Agents

Work within integrated development environments:

- **GitHub Copilot**: Built into VS Code/compatible editors
- **Windsurf**: Built into Windsurf IDE
- **Kilo Code**: Built into Kilo Code IDE
- **Roo Code**: Built into Roo Code IDE
- **IBM Bob**: Built into IBM Bob IDE

---

## Command File Formats

### Markdown Format

Used by: Claude, Cursor, opencode, Windsurf, Amazon Q Developer, Amp, SHAI, IBM Bob, Copilot

**Standard format:**
```markdown
---
description: "Command description"
---

Command content with $ARGUMENTS placeholder.
```

**GitHub Copilot Chat Mode format:**
```markdown
---
description: "Command description"
mode: spectrena.command-name
---

Command content with $ARGUMENTS placeholder.
```

### TOML Format

Used by: Gemini, Qwen

```toml
description = "Command description"

prompt = """
Command content with {{args}} placeholder.
"""
```

---

## Directory Conventions

| Agent Type | Pattern | Example |
|------------|---------|---------|
| CLI agents | `.<agent>/commands/` | `.claude/commands/` |
| IDE agents | Varies by IDE | `.windsurf/workflows/` |
| Copilot | `.github/agents/` | `.github/agents/` |

---

## Argument Patterns

| Format | Placeholder | Used By |
|--------|-------------|---------|
| Markdown | `$ARGUMENTS` | Claude, Cursor, Windsurf, etc. |
| TOML | `{{args}}` | Gemini, Qwen |

---

## Testing New Agent Integration

1. **Unit test**: Add tests in `tests/test_agents.py`
2. **CLI test**: Run `spectrena init --ai <agent>` 
3. **File generation**: Verify correct directory structure
4. **Command validation**: Ensure generated commands work
5. **Context update**: Test `spectrena update-context --agent <agent>`

```bash
# Run agent tests
pytest tests/test_agents.py -v

# Test specific agent initialization
spectrena init --ai new-agent-cli
ls -la .newagent/commands/
```

---

## Common Pitfalls

1. **Using shorthand keys**: Always use the actual CLI executable name as the AGENT_CONFIG key
2. **Wrong `requires_cli` value**: Set `True` only for agents with CLI tools; `False` for IDE-based
3. **Wrong argument format**: Use `$ARGUMENTS` for Markdown, `{{args}}` for TOML
4. **Directory naming**: Follow agent-specific conventions exactly
5. **Missing documentation**: Update README.md and AGENTS.md together

---

## Spectrena-Specific Commands

Spectrena adds these slash commands beyond spec-kit:

| Command | Description |
|---------|-------------|
| `/spectrena.specify` | Create new spec |
| `/spectrena.clarify` | Refine current spec |
| `/spectrena.plan` | Generate implementation plan |
| `/spectrena.tasks` | Extract tasks from plan |
| `/spectrena.deps` | Analyze dependency graph |

These are generated for all supported agents in their respective formats.

---

## MCP Integration

For agents that support MCP (Model Context Protocol), Spectrena provides:

- `spectrena-mcp`: Spec/task management server
- `serena-mcp`: Semantic code editing with lineage tracking

Configure in `.mcp.json`:
```json
{
  "mcpServers": {
    "spectrena": {
      "command": "spectrena-mcp"
    },
    "serena": {
      "command": "serena",
      "args": ["start-mcp-server", "--transport", "stdio"]
    }
  }
}
```

Currently, MCP is primarily used with Claude Code, but other agents may add support.

---

*This documentation should be updated whenever new agents are added to maintain accuracy and completeness.*
