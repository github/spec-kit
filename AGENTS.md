# AGENTS.md

## About Spec Kit and Specify

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework. It sets up the necessary directory structures, templates, and AI agent integrations to support the Spec-Driven Development workflow.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## General practices

- Any changes to `__init__.py` for the Specify CLI require a version rev in `pyproject.toml` and addition of entries to `CHANGELOG.md`.

### ⚠️ CRITICAL: Never Use TODOs in Prompts or Templates

**RULE:** Never add TODO comments to prompt files (`.md` files in `templates/commands/`) or template files. TODOs in prompts can confuse AI agents, causing them to misinterpret instructions or attempt to execute the TODO items instead of their primary task.

**Why this matters:**

- AI agents read prompts as instructions
- TODO comments can be interpreted as tasks to perform
- Scattered TODOs across files make tracking difficult
- Can lead to unexpected agent behavior

**Instead:**

- **Always** add improvements to `/IMPROVEMENTS.md` (centralized tracking)
- Use clear priority levels (High/Medium/Low)
- Link to related issues/PRs
- Group by category for easy review

**Example - Wrong:**

```markdown
<!-- templates/commands/specify.md -->
---
description: Create feature specification
# TODO: Add validation
# TODO: Improve error messages
---
```

**Example - Correct:**

```markdown
<!-- IMPROVEMENTS.md -->
## 🔴 High Priority
- [ ] Add validation of interactive input format
- [ ] Improve error messages with examples
```

**Where to document improvements:**

- `/IMPROVEMENTS.md` - All future enhancements and known limitations
- GitHub Issues - For discussion and tracking
- Pull Requests - When implementing improvements

**Benefits of centralized tracking:**

- ✅ All improvements visible in one place
- ✅ Easy to prioritize and plan sprints
- ✅ No risk of confusing AI agents
- ✅ Clear completion tracking with checkboxes
- ✅ Better collaboration and visibility

### Pre-Commit Quality Checks

**RULE:** Always run quality checks before committing to catch errors early.

**Required checks before every commit:**

1. **Markdownlint** - Check all markdown files for formatting issues

   ```bash
   # Install markdownlint-cli2 (first time only)
   npm install -g markdownlint-cli2

   # Run from repository root
   markdownlint-cli2 "**/*.md"
   ```

   **Common markdownlint errors to fix:**

   - **MD032** - Blank lines around lists: Add blank line before/after lists
   - **MD031** - Blank lines around code fences: Add blank line before/after code blocks
   - **MD036** - No emphasis as heading: Use proper headings (##) not emphasis (*text*)
   - **MD007** - List indentation: Use 0-space indentation for lists at document root
   - **MD040** - Code language: Specify language for fenced code blocks (bash, markdown, text, etc.)

2. **Spell check** - Review for typos and grammar (manual or with tools)

3. **Test scripts** - If modifying bash/PowerShell scripts, test them locally

   ```bash
   # Test bash scripts
   bash scripts/bash/create-new-feature.sh --help

   # Test PowerShell scripts (if on Windows/PowerShell)
   pwsh scripts/powershell/create-new-feature.ps1 -Help
   ```

**Why this matters:**

- ✅ Catches errors before CI fails
- ✅ Keeps codebase clean and consistent
- ✅ Saves time in code review
- ✅ Prevents broken builds
- ✅ Maintains professional quality

**CI checks that will run automatically:**

- Markdownlint on all `.md` files
- (Add more as CI pipeline grows)

**Quick pre-commit checklist:**

- [ ] Ran markdownlint and fixed all errors
- [ ] No TODOs added to prompt files
- [ ] Updated IMPROVEMENTS.md if needed
- [ ] Tested any script changes locally
- [ ] Commit message is clear and descriptive

### Corporate Guidelines System

**FEATURE:** Spec Kit now supports corporate development guidelines to customize prompts for organizational standards.

#### What Are Guidelines?

Guidelines are markdown files in the `/.guidelines/` directory that specify:

- Corporate scaffolding commands (e.g., `npx @acmecorp/create-react-app`)
- Mandatory corporate libraries (e.g., `@acmecorp/ui-components`, `@acmecorp/idm-client`)
- Internal package registries (Artifactory, Nexus, Azure Artifacts)
- Banned public libraries (security/licensing requirements)
- Architecture patterns and coding standards
- Security and compliance requirements

#### Directory Structure

```text
.guidelines/
├── README.md                    # Guidelines overview and customization instructions
├── branch-config.json           # Branch naming configuration (Phase 2)
├── stack-mapping.json           # Multi-stack path mapping (Phase 3)
├── branching-guidelines.md      # Branch naming conventions
├── reactjs-guidelines.md        # React/frontend standards
├── java-guidelines.md           # Java/Spring Boot standards
├── dotnet-guidelines.md         # .NET/C# standards
├── nodejs-guidelines.md         # Node.js/Express standards
└── python-guidelines.md         # Python/Django/Flask standards
```

#### How Guidelines Work

1. **Auto-Detection**: Prompts detect tech stack from project files (`package.json`, `pom.xml`, `*.csproj`, etc.)
2. **Loading**: Applicable guideline files are read based on detected tech stack
3. **Application**: Guidelines are applied with priority: Constitution > Corporate Guidelines > Spec Kit Defaults
4. **Multi-Stack**: For projects with multiple tech stacks (e.g., React + Java), both guideline files are loaded and applied contextually

#### Which Prompts Use Guidelines

- **`plan.md` (CRITICAL)**: Architecture decisions use corporate libraries and patterns
- **`implement.md` (CRITICAL)**: Code generation uses corporate libraries and follows coding standards
- **`analyze.md`**: Compliance checking validates guideline adherence
- **`tasks.md`**: Task generation includes corporate setup commands and libraries

#### Customization

**For Specify Users:**

1. Copy `.guidelines/` directory from Spec Kit release package to your project root
2. Edit each `*-guidelines.md` file to match your organization:
   - Replace `@YOUR_ORG` placeholders with your actual organization name
   - Update package registry URLs (Artifactory, Nexus, etc.)
   - Specify mandatory corporate libraries with versions
   - List banned libraries
   - Document corporate scaffolding commands
3. Commit `.guidelines/` to your repository
4. Prompts automatically detect and apply guidelines

**For Spec Kit Contributors:**

Guidelines are **templates with generic placeholders**. Never commit actual corporate-specific information to Spec Kit repository.

**Example placeholder**:

```markdown
## Scaffolding

Use corporate scaffolding command:

```bash
npx @YOUR_ORG/create-react-app my-app
```

**Example after customization** (in user's project):

```markdown
## Scaffolding

Use corporate scaffolding command:

```bash
npx @acmecorp/create-react-app my-app
```

#### Priority Hierarchy

When making decisions, prompts follow this order:

1. **Constitution** (`/memory/constitution.md`) - Project-specific principles (HIGHEST)
2. **Corporate Guidelines** (`/.guidelines/*.md`) - Organizational standards (MEDIUM)
3. **Spec Kit Defaults** - Built-in best practices (LOWEST)

**Example conflict resolution**:

- Constitution: "MUST use PostgreSQL"
- Guidelines: "Prefer MySQL"
- **Result**: PostgreSQL wins (constitution has highest priority)

#### Non-Compliance Handling

Guidelines are **recommendations, not blockers**:

- Prompts warn about violations
- Create `.guidelines-todo.md` file in feature directory listing violations
- Implementation continues (doesn't block workflow)
- Team can address violations later or request exceptions

#### Implementation Status

**Phase 1** (DONE):

- ✅ Guideline template files created
- ✅ Prompt integration (plan, implement, analyze, tasks)
- ✅ Auto-detection of tech stack
- ✅ Basic multi-stack support
- ✅ Non-compliance handling

**Phase 2** (DONE):

- ✅ Branch naming configuration (`branch-config.json`)
- ✅ Configurable Jira patterns and validation
- ✅ Optional Jira requirement
- ✅ Custom branch prefixes and formats
- ✅ Script integration with configuration
- ✅ Backward compatibility for projects without config

**Phase 3** (DONE):

- ✅ Advanced multi-stack coordination with intelligent path mapping
- ✅ Stack mapping configuration (`stack-mapping.json`)
- ✅ Guideline precedence rules (explicit > extension > convention > auto-detect)
- ✅ Version management for guidelines and configurations
- ✅ Guideline validation tool (`scripts/validate-guidelines.py`)
- ✅ Token optimization for multi-stack projects
- ✅ Enhanced tasks.md prompt for multi-stack task generation
- ✅ Enhanced analyze.md prompt for multi-stack compliance checking
- ✅ Cross-stack integration validation
- ✅ Documentation and examples

#### Example Use Cases

##### Use Case 1: Corporate React Library

```markdown
# .guidelines/reactjs-guidelines.md

## Mandatory Libraries

MUST use @acmecorp/ui-components v2.x:

```bash
npm install @acmecorp/ui-components@^2.0.0
```

**Result**: When running `/specify implement`, agent generates:

```typescript
import { Button } from '@acmecorp/ui-components';  // ✅ Corporate library
// NOT: import { Button } from '@mui/material';     // ❌ Banned
```

##### Use Case 2: Java Corporate SDK

```markdown
# .guidelines/java-guidelines.md

## Mandatory Libraries

MUST use corporate API client:

```xml
<dependency>
    <groupId>com.acmecorp</groupId>
    <artifactId>acmecorp-api-client</artifactId>
    <version>1.8.0</version>
</dependency>
```

**Result**: When running `/specify plan`, agent includes corporate SDK in architecture instead of building custom HTTP clients.

##### Use Case 3: Multi-Stack Project (React + Java)

```json
// .guidelines/stack-mapping.json

{
  "stacks": [
    {
      "name": "reactjs",
      "guideline": "reactjs-guidelines.md",
      "paths": ["frontend/**"],
      "extensions": [".tsx", ".jsx"]
    },
    {
      "name": "java",
      "guideline": "java-guidelines.md",
      "paths": ["backend/**"],
      "extensions": [".java"]
    }
  ]
}
```

**Result**: When running `/specify tasks`:

- Frontend tasks (in `frontend/**`) → Apply React guidelines
- Backend tasks (in `backend/**`) → Apply Java guidelines
- Tasks labeled with `[Frontend]` and `[Backend]` for clarity
- Cross-stack integration validated against both guidelines

##### Use Case 4: Guideline Validation

```bash
# Run validation before committing changes
python3 scripts/validate-guidelines.py

# Output:
✅ PASSED CHECKS: 21
✓ All stack mappings valid
✓ All referenced guideline files exist
✓ Path patterns are valid
```

#### Best Practices

**For Spec Kit Contributors:**

- Keep guidelines as generic templates
- Use `@YOUR_ORG` placeholders
- Provide clear examples of what to customize
- Document all sections thoroughly
- Never commit actual corporate information

**For Specify Users:**

- Customize guidelines for your organization
- Update quarterly or when standards change
- Version guidelines with your project
- Document rationale for banned libraries
- Provide code examples for corporate libraries

#### See Also

- `.guidelines/README.md` - Detailed guidelines customization guide
- `GUIDELINES-IMPLEMENTATION-PLAN.md` - Full implementation roadmap
- `IMPROVEMENTS.md` - Planned Phase 2 and 3 enhancements

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
| **Codex CLI** | `.codex/commands/` | Markdown | `codex` | Codex CLI |
| **Windsurf** | `.windsurf/workflows/` | Markdown | N/A (IDE-based) | Windsurf IDE workflows |
| **Kilo Code** | `.kilocode/rules/` | Markdown | N/A (IDE-based) | Kilo Code IDE |
| **Auggie CLI** | `.augment/rules/` | Markdown | `auggie` | Auggie CLI |
| **Roo Code** | `.roo/rules/` | Markdown | N/A (IDE-based) | Roo Code IDE |
| **CodeBuddy CLI** | `.codebuddy/commands/` | Markdown | `codebuddy` | CodeBuddy CLI |
| **Amazon Q Developer CLI** | `.amazonq/prompts/` | Markdown | `q` | Amazon Q Developer CLI |
| **Amp** | `.agents/commands/` | Markdown | `amp` | Amp CLI |

### Step-by-Step Integration Guide

Follow these steps to add a new agent (using a hypothetical new agent as an example):

#### 1. Add to AGENT_CONFIG

**IMPORTANT**: Use the actual CLI tool name as the key, not a shortened version.

Add the new agent to the `AGENT_CONFIG` dictionary in `src/specify_cli/__init__.py`. This is the **single source of truth** for all agent metadata:

```python
AGENT_CONFIG = {
    # ... existing agents ...
    "new-agent-cli": {  # Use the ACTUAL CLI tool name (what users type in terminal)
        "name": "New Agent Display Name",
        "folder": ".newagent/",  # Directory for agent files
        "install_url": "https://example.com/install",  # URL for installation docs (or None if IDE-based)
        "requires_cli": True,  # True if CLI tool required, False for IDE-based agents
    },
}
```

**Key Design Principle**: The dictionary key should match the actual executable name that users install. For example:

- ✅ Use `"cursor-agent"` because the CLI tool is literally called `cursor-agent`
- ❌ Don't use `"cursor"` as a shortcut if the tool is `cursor-agent`

This eliminates the need for special-case mappings throughout the codebase.

**Field Explanations**:

- `name`: Human-readable display name shown to users
- `folder`: Directory where agent-specific files are stored (relative to project root)
- `install_url`: Installation documentation URL (set to `None` for IDE-based agents)
- `requires_cli`: Whether the agent requires a CLI tool check during initialization

#### 2. Update CLI Help Text

Update the `--ai` parameter help text in the `init()` command to include the new agent:

```python
ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, new-agent-cli, or q"),
```

Also update any function docstrings, examples, and error messages that list available agents.

#### 3. Update README Documentation

Update the **Supported AI Agents** section in `README.md` to include the new agent:

- Add the new agent to the table with appropriate support level (Full/Partial)
- Include the agent's official website link
- Add any relevant notes about the agent's implementation
- Ensure the table formatting remains aligned and consistent

#### 4. Update Release Package Script

Modify `.github/workflows/scripts/create-release-packages.sh`:

##### Add to ALL_AGENTS array

```bash
ALL_AGENTS=(claude gemini copilot cursor-agent qwen opencode windsurf q)
```

##### Add case statement for directory structure

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

##### Bash script (`scripts/bash/update-agent-context.sh`)

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

##### PowerShell script (`scripts/powershell/update-agent-context.ps1`)

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

**Note**: CLI tool checks are now handled automatically based on the `requires_cli` field in AGENT_CONFIG. No additional code changes needed in the `check()` or `init()` commands - they automatically loop through AGENT_CONFIG and check tools as needed.

## Important Design Decisions

### Using Actual CLI Tool Names as Keys

**CRITICAL**: When adding a new agent to AGENT_CONFIG, always use the **actual executable name** as the dictionary key, not a shortened or convenient version.

**Why this matters:**

- The `check_tool()` function uses `shutil.which(tool)` to find executables in the system PATH
- If the key doesn't match the actual CLI tool name, you'll need special-case mappings throughout the codebase
- This creates unnecessary complexity and maintenance burden

**Example - The Cursor Lesson:**

❌ **Wrong approach** (requires special-case mapping):

```python
AGENT_CONFIG = {
    "cursor": {  # Shorthand that doesn't match the actual tool
        "name": "Cursor",
        # ...
    }
}

# Then you need special cases everywhere:
cli_tool = agent_key
if agent_key == "cursor":
    cli_tool = "cursor-agent"  # Map to the real tool name
```

✅ **Correct approach** (no mapping needed):

```python
AGENT_CONFIG = {
    "cursor-agent": {  # Matches the actual executable name
        "name": "Cursor",
        # ...
    }
}

# No special cases needed - just use agent_key directly!
```

**Benefits of this approach:**

- Eliminates special-case logic scattered throughout the codebase
- Makes the code more maintainable and easier to understand
- Reduces the chance of bugs when adding new agents
- Tool checking "just works" without additional mappings

#### 7. Update Devcontainer files (Optional)

For agents that have VS Code extensions or require CLI installation, update the devcontainer configuration files:

##### VS Code Extension-based Agents

For agents available as VS Code extensions, add them to `.devcontainer/devcontainer.json`:

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        // ... existing extensions ...
        // [New Agent Name]
        "[New Agent Extension ID]"
      ]
    }
  }
}
```

##### CLI-based Agents

For agents that require CLI tools, add installation commands to `.devcontainer/post-create.sh`:

```bash
#!/bin/bash

# Existing installations...

echo -e "\n🤖 Installing [New Agent Name] CLI..."
# run_command "npm install -g [agent-cli-package]@latest" # Example for node-based CLI
# or other installation instructions (must be non-interactive and compatible with Linux Debian "Trixie" or later)...
echo "✅ Done"

```

**Quick Tips:**

- **Extension-based agents**: Add to the `extensions` array in `devcontainer.json`
- **CLI-based agents**: Add installation scripts to `post-create.sh`
- **Hybrid agents**: May require both extension and CLI installation
- **Test thoroughly**: Ensure installations work in the devcontainer environment

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

### IDE-Based Agents

Work within integrated development environments:

- **GitHub Copilot**: Built into VS Code/compatible editors
- **Windsurf**: Built into Windsurf IDE

## Command File Formats

### Markdown Format

Used by: Claude, Cursor, opencode, Windsurf, Amazon Q Developer, Amp

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

- **Markdown/prompt-based**: `$ARGUMENTS`
- **TOML-based**: `{{args}}`
- **Script placeholders**: `{SCRIPT}` (replaced with actual script path)
- **Agent placeholders**: `__AGENT__` (replaced with agent name)

## Testing New Agent Integration

1. **Build test**: Run package creation script locally
2. **CLI test**: Test `specify init --ai <agent>` command
3. **File generation**: Verify correct directory structure and files
4. **Command validation**: Ensure generated commands work with the agent
5. **Context update**: Test agent context update scripts

## Common Pitfalls

1. **Using shorthand keys instead of actual CLI tool names**: Always use the actual executable name as the AGENT_CONFIG key (e.g., `"cursor-agent"` not `"cursor"`). This prevents the need for special-case mappings throughout the codebase.
2. **Forgetting update scripts**: Both bash and PowerShell scripts must be updated when adding new agents.
3. **Incorrect `requires_cli` value**: Set to `True` only for agents that actually have CLI tools to check; set to `False` for IDE-based agents.
4. **Wrong argument format**: Use correct placeholder format for each agent type (`$ARGUMENTS` for Markdown, `{{args}}` for TOML).
5. **Directory naming**: Follow agent-specific conventions exactly (check existing agents for patterns).
6. **Help text inconsistency**: Update all user-facing text consistently (help strings, docstrings, README, error messages).

## Future Considerations

When adding new agents:

- Consider the agent's native command/workflow patterns
- Ensure compatibility with the Spec-Driven Development process
- Document any special requirements or limitations
- Update this guide with lessons learned
- Verify the actual CLI tool name before adding to AGENT_CONFIG

---

*This documentation should be updated whenever new agents are added to maintain accuracy and completeness.*
