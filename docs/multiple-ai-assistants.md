# Multiple AI Assistants Support

Specify CLI now supports initializing projects with multiple AI assistants simultaneously, allowing you to use different AI tools for different scenarios within the same project.

## Why Multiple AI Assistants?

Different AI assistants excel in different areas:

- **GitHub Copilot**: Excellent for VS Code integration and code completion
- **Cursor**: Great for AI-assisted refactoring and code editing
- **Gemini CLI**: Powerful for experimentation and command-line workflows
- **Claude Code**: Strong for complex reasoning and detailed specifications
- **Qwen Code**: Useful for specialized code generation tasks
- **Windsurf**: Integrated development environment with AI workflows
- **opencode**: Open-source AI coding assistant

## Usage

### Command Line Selection (Multiple AIs)

```bash
# Select multiple AI assistants
specify init my-project --ai copilot --ai cursor --ai gemini

# VS Code ecosystem setup
specify init my-project --ai copilot --ai cursor

# CLI-focused setup  
specify init my-project --ai gemini --ai claude --ai qwen

# All AI assistants
specify init my-project --ai copilot --ai cursor --ai gemini --ai claude --ai qwen --ai windsurf --ai opencode
```

### Interactive Selection

When you run `specify init` without the `--ai` flag, you'll get an interactive multi-selection interface:

```bash
specify init my-project
```

**Interactive Controls:**
- `↑/↓` - Navigate between options
- `Space` - Select/deselect AI assistants  
- `Enter` - Confirm selections
- `Esc` - Cancel

The interface shows your selections with checkmarks:
```
Choose your AI assistant(s) (Space to select, Enter to confirm):
▶ [✓] copilot (GitHub Copilot)
  [✓] cursor (Cursor)  
  [✓] gemini (Gemini CLI)
  [ ] claude (Claude Code)
  [ ] qwen (Qwen Code)
  [ ] windsurf (Windsurf)
  [ ] opencode (opencode)
```

## Generated Project Structure

When multiple AIs are selected, the project will include directories and configuration files for each:

```
my-project/
├── .github/prompts/           # GitHub Copilot commands
│   ├── constitution.prompt.md
│   ├── specify.prompt.md
│   ├── plan.prompt.md
│   ├── tasks.prompt.md
│   └── implement.prompt.md
├── .cursor/commands/          # Cursor commands
│   ├── constitution.md
│   ├── specify.md
│   ├── plan.md
│   ├── tasks.md
│   └── implement.md
├── .gemini/commands/          # Gemini CLI commands
│   ├── constitution.toml
│   ├── specify.toml
│   ├── plan.toml
│   ├── tasks.toml
│   └── implement.toml
├── .claude/commands/          # Claude Code commands (if selected)
├── .qwen/commands/            # Qwen commands (if selected)
├── .windsurf/workflows/       # Windsurf workflows (if selected)
├── .opencode/command/         # opencode commands (if selected)
└── .specify/                  # Shared Spec-Driven Development files
    ├── memory/
    │   └── constitution.md
    ├── scripts/
    │   ├── bash/
    │   └── powershell/
    └── templates/
```

## Using Multiple AIs in Practice

### Recommended Workflows

**Development Phase Specialization:**
- **Specification**: Use Claude for detailed reasoning and specification creation
- **Planning**: Use Gemini CLI for architectural decisions
- **Implementation**: Use Copilot + Cursor for code writing and editing
- **Testing**: Use any AI for test generation and validation

**Tool Ecosystem Approach:**
- **VS Code Users**: `--ai copilot --ai cursor`
- **CLI Power Users**: `--ai gemini --ai claude --ai qwen`
- **Hybrid Users**: `--ai copilot --ai gemini` (GUI + CLI)

### Command Usage Examples

Once your project is set up with multiple AIs, you can use the appropriate commands for each:

```bash
# In VS Code with GitHub Copilot
# Use: /specify, /plan, /tasks, /implement

# In Cursor IDE  
# Use: specify, plan, tasks, implement

# In Terminal with Gemini CLI
gemini run specify "Create user authentication system"
gemini run plan
gemini run tasks

# In Terminal with Claude Code
claude run specify "Add payment processing"
claude run plan
```

## Benefits

✅ **Flexibility**: Choose the right AI for the right task  
✅ **No Lock-in**: Switch between AIs without losing project structure  
✅ **Team Compatibility**: Team members can use their preferred AI tools  
✅ **Experimentation**: Compare AI responses across different models  
✅ **Redundancy**: If one AI service is down, use another  

## Tool Requirements

The CLI will check for required tools based on your selections:

- **copilot**: No CLI tool required (works in VS Code)
- **cursor**: No CLI tool required (works in Cursor IDE)  
- **gemini**: Requires `gemini` CLI tool
- **claude**: Requires `claude` CLI tool
- **qwen**: Requires `qwen` CLI tool
- **windsurf**: No CLI tool required (works in Windsurf IDE)
- **opencode**: Requires `opencode` CLI tool

Use `--ignore-agent-tools` to skip tool checks during initialization.

## Migration from Single AI

If you have an existing project with a single AI assistant, you can add additional AIs by:

1. Running `specify init --here --ai <additional-ais>` in your project directory
2. The new AI directories will be added without affecting existing ones
3. All AIs will share the same `.specify/` directory structure

---

*This multi-AI approach gives you the flexibility to use the best AI tool for each development phase while maintaining a consistent Spec-Driven Development workflow.*