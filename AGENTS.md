# AGENTS.md

## About Spec Kit and Specify

**GitHub Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework. It sets up the necessary directory structures, templates, and AI agent integrations to support the Spec-Driven Development workflow.

The toolkit supports multiple AI coding assistants, allowing teams to use their preferred tools while maintaining consistent project structure and development practices.

---

## General practices

- Any changes to `__init__.py` for the Specify CLI require a version rev in `pyproject.toml` and addition of entries to `CHANGELOG.md`.

### ⚠️ CRITICAL: Chunked File Generation for Large Outputs

**RULE:** When generating large files (function specs, technical specs, implementation code, or any file likely >2000 lines), ALWAYS use chunked generation to prevent "max limit reached" errors and avoid wasted tokens.

**Automatic Chunking Strategy:**

1. **Estimate file size before generation** - If likely >1500 lines, use chunks
2. **Generate in logical sections** - Split by major components/modules
3. **Use append mode** - Write first chunk with `Write`, subsequent chunks with `Edit` (append to end)
4. **No manual intervention required** - Continue automatically between chunks

**Implementation Pattern:**

```markdown
# Step 1: Create file with first chunk
I'll generate the function specification in chunks to avoid token limits.

Chunk 1/4: Core Data Models (lines 1-500)
[Use Write tool to create file with header + first section]

# Step 2: Append remaining chunks
Chunk 2/4: API Endpoints (lines 501-1000)
[Use Edit tool to append to end of file]

Chunk 3/4: Business Logic (lines 1001-1500)
[Use Edit tool to append to end of file]

Chunk 4/4: Utilities and Helpers (lines 1501-2000)
[Use Edit tool to append to end of file]
```

**Chunk Size Guidelines:**

- **Small chunks**: 300-500 lines (safest, use for complex content)
- **Medium chunks**: 500-800 lines (good balance)
- **Large chunks**: 800-1200 lines (only for simple/repetitive content)

**When to Use Chunking:**

- ✅ Function specifications >1000 lines
- ✅ Technical specifications >1500 lines
- ✅ Implementation code >2000 lines
- ✅ Generated configuration files >1000 lines
- ✅ Any file where you're uncertain about size
- ❌ Small utility files <500 lines
- ❌ Configuration files <300 lines

**Benefits:**

- Prevents failed requests due to output token limits
- Avoids wasting tokens on incomplete generations
- No user intervention needed
- Maintains complete file integrity

**Example - Function Spec Generation:**

```markdown
I need to generate a comprehensive function specification for a large e-commerce system.
Estimated size: ~2400 lines. I'll generate in 4 chunks:

**Chunk 1/4: Introduction, Overview, Data Models (lines 1-600)**
[Generate and write with Write tool]

**Chunk 2/4: User Management & Authentication APIs (lines 601-1200)**
[Append with Edit tool: old_string = last few lines of chunk 1, new_string = last lines + chunk 2]

**Chunk 3/4: Product & Inventory APIs (lines 1201-1800)**
[Append with Edit tool: old_string = last few lines of chunk 2, new_string = last lines + chunk 3]

**Chunk 4/4: Order Processing & Reporting (lines 1801-2400)**
[Append with Edit tool: old_string = last few lines of chunk 3, new_string = last lines + chunk 4]
```

**Important:** This applies to ALL file generation tasks including:

- Specification documents (function-spec.md, technical-spec.md)
- Implementation code (large modules, controllers, services)
- Generated configuration (complex configs, large schemas)
- Documentation (comprehensive guides, API docs)
- Test files (extensive test suites)

**Failure Recovery:** If a chunk fails mid-generation, resume from the last successful chunk rather than restarting from the beginning.

### ⚠️ CRITICAL: Never Use TODOs in Prompts or Templates

**RULE:** Never add TODO comments to prompt/template files (`.md` files in `templates/`). TODOs confuse AI agents who interpret them as executable tasks.

**Instead:** Use `/IMPROVEMENTS.md` for centralized tracking with priority levels (High/Medium/Low).

**Why:** Prevents agent confusion, enables better tracking, improves collaboration.

### Pre-Commit Quality Checks

**Required checks:**

1. **Markdownlint**: `npx markdownlint-cli2 "**/*.md"` (configured via `.markdownlint-cli2.jsonc`)
2. **Spell check**: Review for typos/grammar
3. **Test scripts**: If modifying bash/PowerShell, test locally with `--help`

**Checklist:**

- [ ] Ran markdownlint and fixed errors
- [ ] No TODOs in prompt files (use IMPROVEMENTS.md)
- [ ] Tested script changes
- [ ] Clear commit message

### Corporate Guidelines System

Spec Kit supports corporate development guidelines via `/.guidelines/` directory.

**Key concepts:**

- **Auto-detection**: Prompts detect tech stack and load applicable guidelines
- **Priority**: Constitution > Corporate Guidelines > Spec Kit Defaults
- **Multi-stack**: Supports multiple tech stacks (e.g., React + Java) via `stack-mapping.json`
- **Non-blocking**: Violations create `.guidelines-todo.md` but don't block workflow

**For contributors:** Guidelines are templates with `@YOUR_ORG` placeholders. Never commit actual corporate info.

**Implementation:** All phases complete (Phases 1-3). Validation: `python3 scripts/validate-guidelines.py`

**See:** `.guidelines/README.md` for complete documentation and customization guide.

## Adding New Agent Support

This section explains how to add support for new AI agents/assistants to the Specify CLI. Use this guide as a reference when integrating new AI tools into the Spec-Driven Development workflow.

### Overview

Specify generates agent-specific command files and directories. Each agent uses different formats (Markdown/TOML), directory structures (`.claude/commands/`, `.windsurf/workflows/`), invocation patterns (slash commands/CLI), and argument conventions (`$ARGUMENTS`, `{{args}}`).

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

#### 1. Add to AGENT_CONFIG

Add to `AGENT_CONFIG` in `src/specify_cli/__init__.py` (single source of truth):

```python
AGENT_CONFIG = {
    "new-agent-cli": {  # ⚠️ MUST match actual CLI executable name
        "name": "New Agent Display Name",
        "folder": ".newagent/",
        "install_url": "https://example.com/install",  # or None for IDE-based
        "requires_cli": True,  # False for IDE-based agents
    },
}
```

**Critical**: Use actual executable name (e.g., `cursor-agent` not `cursor`) to avoid special-case mappings. Fields: `name` (display), `folder` (files dir), `install_url` (docs or None), `requires_cli` (CLI check needed).

#### 2. Update CLI Help Text

Add agent to `--ai` parameter help in `init()` command. Update function docstrings, examples, and error messages listing available agents.

#### 3. Update README Documentation

Add to **Supported AI Agents** table in `README.md`: support level (Full/Partial), official website link, implementation notes. Maintain table alignment.

#### 4. Update Release Scripts

**Package script** (`.github/workflows/scripts/create-release-packages.sh`):
- Add to `ALL_AGENTS` array
- Add case statement for directory structure

**Release script** (`.github/workflows/scripts/create-github-release.sh`):
- Add agent's zip packages to `gh release create`

#### 5. Update Agent Context Scripts

**Bash** (`scripts/bash/update-agent-context.sh`): Add file variable, add to case statement
**PowerShell** (`scripts/powershell/update-agent-context.ps1`): Add file variable, add to switch statement

#### 6. Update CLI Tool Checks

**Note**: CLI tool checks auto-handled via `requires_cli` field in AGENT_CONFIG. No additional code changes needed in `check()` or `init()` commands.

## Important Design Decisions

### Using Actual CLI Tool Names as Keys

**CRITICAL**: Use **actual executable name** as AGENT_CONFIG key (e.g., `cursor-agent` not `cursor`).

**Why**: `check_tool()` uses `shutil.which(tool)` - mismatched keys require special-case mappings everywhere.

**Benefits**: Eliminates special-case logic, improves maintainability, prevents bugs, tool checking "just works".

#### 7. Update Devcontainer files (Optional)

**VS Code extensions**: Add to `.devcontainer/devcontainer.json` extensions array
**CLI tools**: Add installation to `.devcontainer/post-create.sh`
**Hybrid**: May need both. Test in devcontainer environment.

## Agent Categories

**CLI-Based**: claude, gemini, cursor-agent, qwen, opencode, q, codebuddy, amp
**IDE-Based**: GitHub Copilot (VS Code), Windsurf (Windsurf IDE)

## Command File Formats

**Markdown** (Claude, Cursor, opencode, Windsurf, Q, Amp): Frontmatter + content with `$ARGUMENTS`
**TOML** (Gemini, Qwen): `description` + `prompt` with `{{args}}`

## Conventions

**Directories**: CLI agents use `.<agent-name>/commands/`, IDE agents vary (`.github/prompts/`, `.windsurf/workflows/`)
**Arguments**: Markdown=`$ARGUMENTS`, TOML=`{{args}}`, Scripts=`{SCRIPT}`, Agent=`__AGENT__`

## Testing New Agent Integration

1. Run package creation locally 2. Test `specify init --ai <agent>` 3. Verify directory/files 4. Validate commands work 5. Test context update scripts

## Common Pitfalls

1. Using shorthand keys not actual CLI names (e.g., `cursor` vs `cursor-agent`)
2. Forgetting bash/PowerShell script updates
3. Wrong `requires_cli` value (True=CLI tool, False=IDE-based)
4. Wrong argument format (`$ARGUMENTS`=Markdown, `{{args}}`=TOML)
5. Incorrect directory naming
6. Inconsistent help text updates

## Future Considerations

Consider native patterns, ensure SDD compatibility, document requirements, update guide, verify actual CLI name.

---

*This documentation should be updated whenever new agents are added to maintain accuracy and completeness.*

---

## Markdown Style Guide

Uses markdownlint-cli2 (config: `.markdownlint-cli2.jsonc`). Key rules: ATX headers, asterisk emphasis, 2-space indents. Disabled: MD013 (line length), MD033 (HTML), MD041, MD051.

**Commands**: `npx markdownlint-cli2 "**/*.md"` (check), add `--fix` (auto-fix)

**Best Practices**: Blank lines around blocks, specify code languages, dashes for lists, ~100 char prose (except long commands/URLs)

---

## Documentation Structure

**Repository Development** (`docs/development/`): For devs ON repo (engineering-review, roadmap, architecture, developer README)
**Toolkit Documentation** (`docs/`): For toolkit USERS (guides, examples, quickstart, installation)
**AI Instructions**: `AGENTS.md` (repo dev) vs `.specify/AGENTS.md` (toolkit usage)

**Key Rule**: Separate developer implementation from user-facing docs.
