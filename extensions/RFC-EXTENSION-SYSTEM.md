# RFC: Spec Kit Extension System

**Status**: Draft
**Author**: Stats Perform Engineering
**Created**: 2026-01-28
**Updated**: 2026-01-28

---

## Table of Contents

1. [Summary](#summary)
2. [Motivation](#motivation)
3. [Design Principles](#design-principles)
4. [Architecture Overview](#architecture-overview)
5. [Extension Manifest Specification](#extension-manifest-specification)
6. [Extension Lifecycle](#extension-lifecycle)
7. [Command Registration](#command-registration)
8. [Configuration Management](#configuration-management)
9. [Hook System](#hook-system)
10. [Extension Discovery & Catalog](#extension-discovery--catalog)
11. [CLI Commands](#cli-commands)
12. [Compatibility & Versioning](#compatibility--versioning)
13. [Security Considerations](#security-considerations)
14. [Migration Strategy](#migration-strategy)
15. [Implementation Phases](#implementation-phases)
16. [Open Questions](#open-questions)
17. [Appendices](#appendices)

---

## Summary

Introduce an extension system to Spec Kit that allows modular integration with external tools (Jira, Linear, Azure DevOps, etc.) without bloating the core framework. Extensions are self-contained packages installed into `.specify/extensions/` with declarative manifests, versioned independently, and discoverable through a central catalog.

---

## Motivation

### Current Problems

1. **Monolithic Growth**: Adding Jira integration to core spec-kit creates:
   - Large configuration files affecting all users
   - Dependencies on Jira MCP server for everyone
   - Merge conflicts as features accumulate

2. **Limited Flexibility**: Different organizations use different tools:
   - GitHub Issues vs Jira vs Linear vs Azure DevOps
   - Custom internal tools
   - No way to support all without bloat

3. **Maintenance Burden**: Every integration adds:
   - Documentation complexity
   - Testing matrix expansion
   - Breaking change surface area

4. **Community Friction**: External contributors can't easily add integrations without core repo PR approval and release cycles.

### Goals

1. **Modularity**: Core spec-kit remains lean, extensions are opt-in
2. **Extensibility**: Clear API for building new integrations
3. **Independence**: Extensions version/release separately from core
4. **Discoverability**: Central catalog for finding extensions
5. **Safety**: Validation, compatibility checks, sandboxing

---

## Design Principles

### 1. Convention Over Configuration

- Standard directory structure (`.specify/extensions/{name}/`)
- Declarative manifest (`extension.yml`)
- Predictable command naming (`speckit.{extension}.{command}`)

### 2. Fail-Safe Defaults

- Missing extensions gracefully degrade (skip hooks)
- Invalid extensions warn but don't break core functionality
- Extension failures isolated from core operations

### 3. Backward Compatibility

- Core commands remain unchanged
- Extensions additive only (no core modifications)
- Old projects work without extensions

### 4. Developer Experience

- Simple installation: `specify extension add jira`
- Clear error messages for compatibility issues
- Local development mode for testing extensions

### 5. Security First

- Extensions run in same context as AI agent (trust boundary)
- Manifest validation prevents malicious code
- Verify signatures for official extensions (future)

---

## Architecture Overview

### Directory Structure

```text
project/
├── .specify/
│   ├── scripts/                 # Core scripts (unchanged)
│   ├── templates/               # Core templates (unchanged)
│   ├── memory/                  # Session memory
│   ├── extensions/              # Extensions directory (NEW)
│   │   ├── .registry            # Installed extensions metadata (NEW)
│   │   ├── jira/                # Jira extension
│   │   │   ├── extension.yml    # Manifest
│   │   │   ├── jira-config.yml  # Extension config
│   │   │   ├── commands/        # Command files
│   │   │   ├── scripts/         # Helper scripts
│   │   │   └── docs/            # Documentation
│   │   └── linear/              # Linear extension (example)
│   └── extensions.yml           # Project extension configuration (NEW)
└── .gitignore                   # Ignore local extension configs
```

### Component Diagram

```text
┌─────────────────────────────────────────────────────────┐
│                    Spec Kit Core                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  CLI (specify)                                   │   │
│  │  - init, check                                   │   │
│  │  - extension add/remove/list/update  ← NEW       │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Extension Manager  ← NEW                        │   │
│  │  - Discovery, Installation, Validation           │   │
│  │  - Command Registration, Hook Execution          │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Core Commands                                   │   │
│  │  - /speckit.specify                              │   │
│  │  - /speckit.tasks                                │   │
│  │  - /speckit.implement                            │   │
│  └─────────┬────────────────────────────────────────┘   │
└────────────┼────────────────────────────────────────────┘
             │ Hook Points (after_tasks, after_implement)
             ↓
┌─────────────────────────────────────────────────────────┐
│                    Extensions                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Jira Extension                                  │   │
│  │  - /speckit.jira.specstoissues                   │   │
│  │  - /speckit.jira.discover-fields                 │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Linear Extension                                │   │
│  │  - /speckit.linear.sync                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
             │ Calls external tools
             ↓
┌─────────────────────────────────────────────────────────┐
│                    External Tools                       │
│  - Jira MCP Server                                      │
│  - Linear API                                           │
│  - GitHub API                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Extension Manifest Specification

### Schema: `extension.yml`

```yaml
# Extension Manifest Schema v1.0
# All extensions MUST include this file at root

# Schema version for compatibility
schema_version: "1.0"

# Extension metadata (REQUIRED)
extension:
  id: "jira"                    # Unique identifier (lowercase, alphanumeric, hyphens)
  name: "Jira Integration"      # Human-readable name
  version: "1.0.0"              # Semantic version
  description: "Create Jira Epics, Stories, and Issues from spec-kit artifacts"
  author: "Stats Perform"       # Author/organization
  repository: "https://github.com/statsperform/spec-kit-jira"
  license: "MIT"                # SPDX license identifier
  homepage: "https://github.com/statsperform/spec-kit-jira/blob/main/README.md"

# Compatibility requirements (REQUIRED)
requires:
  # Spec-kit version (semantic version range)
  speckit_version: ">=0.1.0,<2.0.0"

  # External tools required by extension
  tools:
    - name: "jira-mcp-server"
      required: true
      version: ">=1.0.0"          # Optional: version constraint
      description: "Jira MCP server for API access"
      install_url: "https://github.com/your-org/jira-mcp-server"
      check_command: "jira --version"  # Optional: CLI command to verify

  # Core spec-kit commands this extension depends on
  commands:
    - "speckit.tasks"             # Extension needs tasks command

  # Core scripts required
  scripts:
    - "check-prerequisites.sh"

# What this extension provides (REQUIRED)
provides:
  # Commands added to AI agent
  commands:
    - name: "speckit.jira.specstoissues"
      file: "commands/specstoissues.md"
      description: "Create Jira hierarchy from spec and tasks"
      aliases: ["speckit.specstoissues"]  # Alternate names

    - name: "speckit.jira.discover-fields"
      file: "commands/discover-fields.md"
      description: "Discover Jira custom fields for configuration"

    - name: "speckit.jira.sync-status"
      file: "commands/sync-status.md"
      description: "Sync task completion status to Jira"

  # Configuration files
  config:
    - name: "jira-config.yml"
      template: "jira-config.template.yml"
      description: "Jira integration configuration"
      required: true              # User must configure before use

  # Helper scripts
  scripts:
    - name: "parse-jira-config.sh"
      file: "scripts/parse-jira-config.sh"
      description: "Parse jira-config.yml to JSON"
      executable: true            # Make executable on install

# Extension configuration defaults (OPTIONAL)
defaults:
  project:
    key: null                     # No default, user must configure
  hierarchy:
    issue_type: "subtask"
  update_behavior:
    mode: "update"
    sync_completion: true

# Configuration schema for validation (OPTIONAL)
config_schema:
  type: "object"
  required: ["project"]
  properties:
    project:
      type: "object"
      required: ["key"]
      properties:
        key:
          type: "string"
          pattern: "^[A-Z]{2,10}$"
          description: "Jira project key (e.g., MSATS)"

# Integration hooks (OPTIONAL)
hooks:
  # Hook fired after /speckit.tasks completes
  after_tasks:
    command: "speckit.jira.specstoissues"
    optional: true
    prompt: "Create Jira issues from tasks?"
    description: "Automatically create Jira hierarchy after task generation"

  # Hook fired after /speckit.implement completes
  after_implement:
    command: "speckit.jira.sync-status"
    optional: true
    prompt: "Sync completion status to Jira?"

# Tags for discovery (OPTIONAL)
tags:
  - "issue-tracking"
  - "jira"
  - "atlassian"
  - "project-management"

# Changelog URL (OPTIONAL)
changelog: "https://github.com/statsperform/spec-kit-jira/blob/main/CHANGELOG.md"

# Support information (OPTIONAL)
support:
  documentation: "https://github.com/statsperform/spec-kit-jira/blob/main/docs/"
  issues: "https://github.com/statsperform/spec-kit-jira/issues"
  discussions: "https://github.com/statsperform/spec-kit-jira/discussions"
  email: "support@statsperform.com"
```

### Validation Rules

1. **MUST have** `schema_version`, `extension`, `requires`, `provides`
2. **MUST follow** semantic versioning for `version`
3. **MUST have** unique `id` (no conflicts with other extensions)
4. **MUST declare** all external tool dependencies
5. **SHOULD include** `config_schema` if extension uses config
6. **SHOULD include** `support` information
7. Command `file` paths **MUST be** relative to extension root
8. Hook `command` names **MUST match** a command in `provides.commands`

---

## Extension Lifecycle

### 1. Discovery

```bash
specify extension search jira
# Searches catalog for extensions matching "jira"
```

**Process:**

1. Fetch extension catalog from GitHub
2. Filter by search term (name, tags, description)
3. Display results with metadata

### 2. Installation

```bash
specify extension add jira
```

**Process:**

1. **Resolve**: Look up extension in catalog
2. **Download**: Fetch extension package (ZIP from GitHub release)
3. **Validate**: Check manifest schema, compatibility
4. **Extract**: Unpack to `.specify/extensions/jira/`
5. **Configure**: Copy config templates
6. **Register**: Add commands to AI agent config
7. **Record**: Update `.specify/extensions/.registry`

**Registry Format** (`.specify/extensions/.registry`):

```json
{
  "schema_version": "1.0",
  "extensions": {
    "jira": {
      "version": "1.0.0",
      "installed_at": "2026-01-28T14:30:00Z",
      "source": "catalog",
      "manifest_hash": "sha256:abc123...",
      "enabled": true
    }
  }
}
```

### 3. Configuration

```bash
# User edits extension config
vim .specify/extensions/jira/jira-config.yml
```

**Config discovery order:**

1. Extension defaults (`extension.yml` → `defaults`)
2. Project config (`jira-config.yml`)
3. Local overrides (`jira-config.local.yml` - gitignored)
4. Environment variables (`SPECKIT_JIRA_*`)

### 4. Usage

```bash
claude
> /speckit.jira.specstoissues
```

**Command resolution:**

1. AI agent finds command in `.claude/commands/speckit.jira.specstoissues.md`
2. Command file references extension scripts/config
3. Extension executes with full context

### 5. Update

```bash
specify extension update jira
```

**Process:**

1. Check catalog for newer version
2. Download new version
3. Validate compatibility
4. Back up current config
5. Extract new version (preserve config)
6. Re-register commands
7. Update registry

### 6. Removal

```bash
specify extension remove jira
```

**Process:**

1. Confirm with user (show what will be removed)
2. Unregister commands from AI agent
3. Remove from `.specify/extensions/jira/`
4. Update registry
5. Optionally preserve config for reinstall

---

## Command Registration

### Per-Agent Registration

Extensions provide **universal command format** (Markdown-based), and CLI converts to agent-specific format during registration.

#### Universal Command Format

**Location**: Extension's `commands/specstoissues.md`

```markdown
---
# Universal metadata (parsed by all agents)
description: "Create Jira hierarchy from spec and tasks"
tools:
  - 'jira-mcp-server/epic_create'
  - 'jira-mcp-server/story_create'
scripts:
  sh: ../../scripts/bash/check-prerequisites.sh --json
  ps: ../../scripts/powershell/check-prerequisites.ps1 -Json
---

# Command implementation
## User Input
$ARGUMENTS

## Steps
1. Load jira-config.yml
2. Parse spec.md and tasks.md
3. Create Jira items
```

#### Claude Code Registration

**Output**: `.claude/commands/speckit.jira.specstoissues.md`

```markdown
---
description: "Create Jira hierarchy from spec and tasks"
tools:
  - 'jira-mcp-server/epic_create'
  - 'jira-mcp-server/story_create'
scripts:
  sh: .specify/scripts/bash/check-prerequisites.sh --json
  ps: .specify/scripts/powershell/check-prerequisites.ps1 -Json
---

# Command implementation (copied from extension)
## User Input
$ARGUMENTS

## Steps
1. Load jira-config.yml from .specify/extensions/jira/
2. Parse spec.md and tasks.md
3. Create Jira items
```

**Transformation:**

- Copy frontmatter with adjustments
- Rewrite script paths (relative to repo root)
- Add extension context (config location)

#### Gemini CLI Registration

**Output**: `.gemini/commands/speckit.jira.specstoissues.toml`

```toml
[command]
name = "speckit.jira.specstoissues"
description = "Create Jira hierarchy from spec and tasks"

[command.tools]
tools = [
  "jira-mcp-server/epic_create",
  "jira-mcp-server/story_create"
]

[command.script]
sh = ".specify/scripts/bash/check-prerequisites.sh --json"
ps = ".specify/scripts/powershell/check-prerequisites.ps1 -Json"

[command.template]
content = """
# Command implementation
## User Input
{{args}}

## Steps
1. Load jira-config.yml from .specify/extensions/jira/
2. Parse spec.md and tasks.md
3. Create Jira items
"""
```

**Transformation:**

- Convert Markdown frontmatter to TOML
- Convert `$ARGUMENTS` to `{{args}}`
- Rewrite script paths

### Registration Code

**Location**: `src/specify_cli/extensions.py`

```python
def register_extension_commands(
    project_path: Path,
    ai_assistant: str,
    manifest: dict
) -> None:
    """Register extension commands with AI agent."""

    agent_config = AGENT_CONFIG.get(ai_assistant)
    if not agent_config:
        console.print(f"[yellow]Unknown agent: {ai_assistant}[/yellow]")
        return

    ext_id = manifest['extension']['id']
    ext_dir = project_path / ".specify" / "extensions" / ext_id
    agent_commands_dir = project_path / agent_config['folder'].rstrip('/') / "commands"
    agent_commands_dir.mkdir(parents=True, exist_ok=True)

    for cmd_info in manifest['provides']['commands']:
        cmd_name = cmd_info['name']
        source_file = ext_dir / cmd_info['file']

        if not source_file.exists():
            console.print(f"[red]Command file not found:[/red] {cmd_info['file']}")
            continue

        # Convert to agent-specific format
        if ai_assistant == "claude":
            dest_file = agent_commands_dir / f"{cmd_name}.md"
            convert_to_claude(source_file, dest_file, ext_dir)
        elif ai_assistant == "gemini":
            dest_file = agent_commands_dir / f"{cmd_name}.toml"
            convert_to_gemini(source_file, dest_file, ext_dir)
        elif ai_assistant == "copilot":
            dest_file = agent_commands_dir / f"{cmd_name}.md"
            convert_to_copilot(source_file, dest_file, ext_dir)
        # ... other agents

        console.print(f"  ✓ Registered: {cmd_name}")

def convert_to_claude(
    source: Path,
    dest: Path,
    ext_dir: Path
) -> None:
    """Convert universal command to Claude format."""

    # Parse universal command
    content = source.read_text()
    frontmatter, body = parse_frontmatter(content)

    # Adjust script paths (relative to repo root)
    if 'scripts' in frontmatter:
        for key in frontmatter['scripts']:
            frontmatter['scripts'][key] = adjust_path_for_repo_root(
                frontmatter['scripts'][key]
            )

    # Inject extension context
    body = inject_extension_context(body, ext_dir)

    # Write Claude command
    dest.write_text(render_frontmatter(frontmatter) + "\n" + body)
```

---

## Configuration Management

### Configuration File Hierarchy

```yaml
# .specify/extensions/jira/jira-config.yml (Project config)
project:
  key: "MSATS"

hierarchy:
  issue_type: "subtask"

defaults:
  epic:
    labels: ["spec-driven", "typescript"]
```

```yaml
# .specify/extensions/jira/jira-config.local.yml (Local overrides - gitignored)
project:
  key: "MYTEST"  # Override for local testing
```

```bash
# Environment variables (highest precedence)
export SPECKIT_JIRA_PROJECT_KEY="DEVTEST"
```

### Config Loading Function

**Location**: Extension command (e.g., `commands/specstoissues.md`)

````markdown
## Load Configuration

1. Run helper script to load and merge config:

```bash
config_json=$(bash .specify/extensions/jira/scripts/parse-jira-config.sh)
echo "$config_json"
```

1. Parse JSON and use in subsequent steps
````

**Script**: `.specify/extensions/jira/scripts/parse-jira-config.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

EXT_DIR=".specify/extensions/jira"
CONFIG_FILE="$EXT_DIR/jira-config.yml"
LOCAL_CONFIG="$EXT_DIR/jira-config.local.yml"

# Start with defaults from extension.yml
defaults=$(yq eval '.defaults' "$EXT_DIR/extension.yml" -o=json)

# Merge project config
if [ -f "$CONFIG_FILE" ]; then
  project_config=$(yq eval '.' "$CONFIG_FILE" -o=json)
  defaults=$(echo "$defaults $project_config" | jq -s '.[0] * .[1]')
fi

# Merge local config
if [ -f "$LOCAL_CONFIG" ]; then
  local_config=$(yq eval '.' "$LOCAL_CONFIG" -o=json)
  defaults=$(echo "$defaults $local_config" | jq -s '.[0] * .[1]')
fi

# Apply environment variable overrides
if [ -n "${SPECKIT_JIRA_PROJECT_KEY:-}" ]; then
  defaults=$(echo "$defaults" | jq ".project.key = \"$SPECKIT_JIRA_PROJECT_KEY\"")
fi

# Output merged config as JSON
echo "$defaults"
```

### Config Validation

**In command file**:

````markdown
## Validate Configuration

1. Load config (from previous step)
2. Validate against schema from extension.yml:

```python
import jsonschema

schema = load_yaml(".specify/extensions/jira/extension.yml")['config_schema']
config = json.loads(config_json)

try:
    jsonschema.validate(config, schema)
except jsonschema.ValidationError as e:
    print(f"❌ Invalid jira-config.yml: {e.message}")
    print(f"   Path: {'.'.join(str(p) for p in e.path)}")
    exit(1)
```

1. Proceed with validated config
````

---

## Hook System

### Hook Definition

**In extension.yml:**

```yaml
hooks:
  after_tasks:
    command: "speckit.jira.specstoissues"
    optional: true
    prompt: "Create Jira issues from tasks?"
    description: "Automatically create Jira hierarchy"
    condition: "config.project.key is set"
```

### Hook Registration

**During extension installation**, record hooks in project config:

**File**: `.specify/extensions.yml` (project-level extension config)

```yaml
# Extensions installed in this project
installed:
  - jira
  - linear

# Global extension settings
settings:
  auto_execute_hooks: true  # Prompt for optional hooks after commands

# Hook configuration
hooks:
  after_tasks:
    - extension: jira
      command: speckit.jira.specstoissues
      enabled: true
      optional: true
      prompt: "Create Jira issues from tasks?"

  after_implement:
    - extension: jira
      command: speckit.jira.sync-status
      enabled: true
      optional: true
      prompt: "Sync completion status to Jira?"
```

### Hook Execution

**In core command** (e.g., `templates/commands/tasks.md`):

Add at end of command:

````markdown
## Extension Hooks

After task generation completes, check for registered hooks:

```bash
# Check if extensions.yml exists and has after_tasks hooks
if [ -f ".specify/extensions.yml" ]; then
  # Parse hooks for after_tasks
  hooks=$(yq eval '.hooks.after_tasks[] | select(.enabled == true)' .specify/extensions.yml -o=json)

  if [ -n "$hooks" ]; then
    echo ""
    echo "📦 Extension hooks available:"

    # Iterate hooks
    echo "$hooks" | jq -c '.' | while read -r hook; do
      extension=$(echo "$hook" | jq -r '.extension')
      command=$(echo "$hook" | jq -r '.command')
      optional=$(echo "$hook" | jq -r '.optional')
      prompt_text=$(echo "$hook" | jq -r '.prompt')

      if [ "$optional" = "true" ]; then
        # Prompt user
        echo ""
        read -p "$prompt_text (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
          echo "▶ Executing: $command"
          # Let AI agent execute the command
          # (AI agent will see this and execute)
          echo "EXECUTE_COMMAND: $command"
        fi
      else
        # Auto-execute mandatory hooks
        echo "▶ Executing: $command (required)"
        echo "EXECUTE_COMMAND: $command"
      fi
    done
  fi
fi
```
````

**AI Agent Handling:**

The AI agent sees `EXECUTE_COMMAND: speckit.jira.specstoissues` in output and automatically invokes that command.

**Alternative**: Direct call in agent context (if agent supports it):

```python
# In AI agent's command execution engine
def execute_command_with_hooks(command_name: str, args: str):
    # Execute main command
    result = execute_command(command_name, args)

    # Check for hooks
    hooks = load_hooks_for_phase(f"after_{command_name}")
    for hook in hooks:
        if hook.optional:
            if confirm(hook.prompt):
                execute_command(hook.command, args)
        else:
            execute_command(hook.command, args)

    return result
```

### Hook Conditions

Extensions can specify **conditions** for hooks:

```yaml
hooks:
  after_tasks:
    command: "speckit.jira.specstoissues"
    optional: true
    condition: "config.project.key is set and config.enabled == true"
```

**Condition evaluation** (in hook executor):

```python
def should_execute_hook(hook: dict, config: dict) -> bool:
    """Evaluate hook condition."""
    condition = hook.get('condition')
    if not condition:
        return True  # No condition = always eligible

    # Simple expression evaluator
    # "config.project.key is set" → check if config['project']['key'] exists
    # "config.enabled == true" → check if config['enabled'] is True

    return eval_condition(condition, config)
```

---

## Extension Discovery & Catalog

### Central Catalog

**URL**: `https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.json`

**Format**:

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-01-28T14:30:00Z",
  "extensions": {
    "jira": {
      "name": "Jira Integration",
      "id": "jira",
      "description": "Create Jira Epics, Stories, and Issues from spec-kit artifacts",
      "author": "Stats Perform",
      "version": "1.0.0",
      "download_url": "https://github.com/statsperform/spec-kit-jira/releases/download/v1.0.0/spec-kit-jira-1.0.0.zip",
      "repository": "https://github.com/statsperform/spec-kit-jira",
      "homepage": "https://github.com/statsperform/spec-kit-jira/blob/main/README.md",
      "documentation": "https://github.com/statsperform/spec-kit-jira/blob/main/docs/",
      "changelog": "https://github.com/statsperform/spec-kit-jira/blob/main/CHANGELOG.md",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=0.1.0,<2.0.0",
        "tools": [
          {
            "name": "jira-mcp-server",
            "version": ">=1.0.0"
          }
        ]
      },
      "tags": ["issue-tracking", "jira", "atlassian", "project-management"],
      "verified": true,
      "downloads": 1250,
      "stars": 45
    },
    "linear": {
      "name": "Linear Integration",
      "id": "linear",
      "description": "Sync spec-kit tasks with Linear issues",
      "author": "Community",
      "version": "0.9.0",
      "download_url": "https://github.com/example/spec-kit-linear/releases/download/v0.9.0/spec-kit-linear-0.9.0.zip",
      "repository": "https://github.com/example/spec-kit-linear",
      "requires": {
        "speckit_version": ">=0.1.0"
      },
      "tags": ["issue-tracking", "linear"],
      "verified": false
    }
  }
}
```

### Catalog Discovery Commands

```bash
# List all available extensions
specify extension search

# Search by keyword
specify extension search jira

# Search by tag
specify extension search --tag issue-tracking

# Show extension details
specify extension info jira
```

### Custom Catalogs

Organizations can host private catalogs:

```bash
# Add custom catalog
specify extension add-catalog https://internal.company.com/spec-kit/catalog.json

# Set as default
specify extension set-catalog --default https://internal.company.com/spec-kit/catalog.json

# List catalogs
specify extension catalogs
```

**Catalog priority**:

1. Project-specific catalog (`.specify/extension-catalogs.yml`)
2. User-level catalog (`~/.specify/extension-catalogs.yml`)
3. Default GitHub catalog

---

## CLI Commands

### `specify extension` Subcommands

#### `specify extension list`

List installed extensions in current project.

```bash
$ specify extension list

Installed Extensions:
  ✓ jira (v1.0.0) - Jira Integration
    Commands: 3 | Hooks: 2 | Status: Enabled

  ✓ linear (v0.9.0) - Linear Integration
    Commands: 1 | Hooks: 1 | Status: Enabled
```

**Options:**

- `--available`: Show available (not installed) extensions from catalog
- `--all`: Show both installed and available

#### `specify extension search [QUERY]`

Search extension catalog.

```bash
$ specify extension search jira

Found 1 extension:

┌─────────────────────────────────────────────────────────┐
│ jira (v1.0.0) ✓ Verified                                │
│ Jira Integration                                        │
│                                                         │
│ Create Jira Epics, Stories, and Issues from spec-kit   │
│ artifacts                                               │
│                                                         │
│ Author: Stats Perform                                   │
│ Tags: issue-tracking, jira, atlassian                   │
│ Downloads: 1,250                                        │
│                                                         │
│ Repository: github.com/statsperform/spec-kit-jira       │
│ Documentation: github.com/.../docs                      │
└─────────────────────────────────────────────────────────┘

Install: specify extension add jira
```

**Options:**

- `--tag TAG`: Filter by tag
- `--author AUTHOR`: Filter by author
- `--verified`: Show only verified extensions

#### `specify extension info NAME`

Show detailed information about an extension.

```bash
$ specify extension info jira

Jira Integration (jira) v1.0.0

Description:
  Create Jira Epics, Stories, and Issues from spec-kit artifacts

Author: Stats Perform
License: MIT
Repository: https://github.com/statsperform/spec-kit-jira
Documentation: https://github.com/statsperform/spec-kit-jira/blob/main/docs/

Requirements:
  • Spec Kit: >=0.1.0,<2.0.0
  • Tools: jira-mcp-server (>=1.0.0)

Provides:
  Commands:
    • speckit.jira.specstoissues - Create Jira hierarchy from spec and tasks
    • speckit.jira.discover-fields - Discover Jira custom fields
    • speckit.jira.sync-status - Sync task completion status

  Hooks:
    • after_tasks - Prompt to create Jira issues
    • after_implement - Prompt to sync status

Tags: issue-tracking, jira, atlassian, project-management

Downloads: 1,250 | Stars: 45 | Verified: ✓

Install: specify extension add jira
```

#### `specify extension add NAME`

Install an extension.

```bash
$ specify extension add jira

Installing extension: Jira Integration

✓ Downloaded spec-kit-jira-1.0.0.zip (245 KB)
✓ Validated manifest
✓ Checked compatibility (spec-kit 0.1.0 ≥ 0.1.0)
✓ Extracted to .specify/extensions/jira/
✓ Registered 3 commands with claude
✓ Installed config template (jira-config.yml)

⚠  Configuration required:
   Edit .specify/extensions/jira/jira-config.yml to set your Jira project key

Extension installed successfully!

Next steps:
  1. Configure: vim .specify/extensions/jira/jira-config.yml
  2. Discover fields: /speckit.jira.discover-fields
  3. Use commands: /speckit.jira.specstoissues
```

**Options:**

- `--from URL`: Install from custom URL or Git repo
- `--version VERSION`: Install specific version
- `--dev PATH`: Install from local path (development mode)
- `--no-register`: Skip command registration (manual setup)

#### `specify extension remove NAME`

Uninstall an extension.

```bash
$ specify extension remove jira

⚠  This will remove:
   • 3 commands from AI agent
   • Extension directory: .specify/extensions/jira/
   • Config file: jira-config.yml (will be backed up)

Continue? (yes/no): yes

✓ Unregistered commands
✓ Backed up config to .specify/extensions/.backup/jira-config.yml
✓ Removed extension directory
✓ Updated registry

Extension removed successfully.

To reinstall: specify extension add jira
```

**Options:**

- `--keep-config`: Don't remove config file
- `--force`: Skip confirmation

#### `specify extension update [NAME]`

Update extension(s) to latest version.

```bash
$ specify extension update jira

Checking for updates...

jira: 1.0.0 → 1.1.0 available

Changes in v1.1.0:
  • Added support for custom workflows
  • Fixed issue with parallel tasks
  • Improved error messages

Update? (yes/no): yes

✓ Downloaded spec-kit-jira-1.1.0.zip
✓ Validated manifest
✓ Backed up current version
✓ Extracted new version
✓ Preserved config file
✓ Re-registered commands

Extension updated successfully!

Changelog: https://github.com/statsperform/spec-kit-jira/blob/main/CHANGELOG.md#v110
```

**Options:**

- `--all`: Update all extensions
- `--check`: Check for updates without installing
- `--force`: Force update even if already latest

#### `specify extension enable/disable NAME`

Enable or disable an extension without removing it.

```bash
$ specify extension disable jira

✓ Disabled extension: jira
  • Commands unregistered (but files preserved)
  • Hooks will not execute

To re-enable: specify extension enable jira
```

---

## Compatibility & Versioning

### Semantic Versioning

Extensions follow [SemVer 2.0.0](https://semver.org/):

- **MAJOR**: Breaking changes (command API changes, config schema changes)
- **MINOR**: New features (new commands, new config options)
- **PATCH**: Bug fixes (no API changes)

### Compatibility Checks

**At installation:**

```python
def check_compatibility(extension_manifest: dict) -> bool:
    """Check if extension is compatible with current environment."""

    requires = extension_manifest['requires']

    # 1. Check spec-kit version
    current_speckit = get_speckit_version()  # e.g., "0.1.5"
    required_speckit = requires['speckit_version']  # e.g., ">=0.1.0,<2.0.0"

    if not version_satisfies(current_speckit, required_speckit):
        raise IncompatibleVersionError(
            f"Extension requires spec-kit {required_speckit}, "
            f"but {current_speckit} is installed. "
            f"Upgrade spec-kit with: uv tool install specify-cli --force"
        )

    # 2. Check required tools
    for tool in requires.get('tools', []):
        tool_name = tool['name']
        tool_version = tool.get('version')

        if tool.get('required', True):
            if not check_tool(tool_name):
                raise MissingToolError(
                    f"Extension requires tool: {tool_name}\n"
                    f"Install from: {tool.get('install_url', 'N/A')}"
                )

            if tool_version:
                installed = get_tool_version(tool_name, tool.get('check_command'))
                if not version_satisfies(installed, tool_version):
                    raise IncompatibleToolVersionError(
                        f"Extension requires {tool_name} {tool_version}, "
                        f"but {installed} is installed"
                    )

    # 3. Check required commands
    for cmd in requires.get('commands', []):
        if not command_exists(cmd):
            raise MissingCommandError(
                f"Extension requires core command: {cmd}\n"
                f"Update spec-kit to latest version"
            )

    return True
```

### Deprecation Policy

**Extension manifest can mark features as deprecated:**

```yaml
provides:
  commands:
    - name: "speckit.jira.old-command"
      file: "commands/old-command.md"
      deprecated: true
      deprecated_message: "Use speckit.jira.new-command instead"
      removal_version: "2.0.0"
```

**At runtime, show warning:**

```text
⚠️  Warning: /speckit.jira.old-command is deprecated
   Use /speckit.jira.new-command instead
   This command will be removed in v2.0.0
```

---

## Security Considerations

### Trust Model

Extensions run with **same privileges as AI agent**:

- Can execute shell commands
- Can read/write files in project
- Can make network requests

**Trust boundary**: User must trust extension author.

### Verification

**Verified Extensions** (in catalog):

- Published by known organizations (GitHub, Stats Perform, etc.)
- Code reviewed by spec-kit maintainers
- Marked with ✓ badge in catalog

**Community Extensions**:

- Not verified, use at own risk
- Show warning during installation:

  ```text
  ⚠️  This extension is not verified.
     Review code before installing: https://github.com/...

     Continue? (yes/no):
  ```

### Sandboxing (Future)

**Phase 2** (not in initial release):

- Extensions declare required permissions in manifest
- CLI enforces permission boundaries
- Example permissions: `filesystem:read`, `network:external`, `env:read`

```yaml
# Future extension.yml
permissions:
  - "filesystem:read:.specify/extensions/jira/"  # Can only read own config
  - "filesystem:write:.specify/memory/"          # Can write to memory
  - "network:external:*.atlassian.net"           # Can call Jira API
  - "env:read:SPECKIT_JIRA_*"                    # Can read own env vars
```

### Package Integrity

**Future**: Sign extension packages with GPG/Sigstore

```yaml
# catalog.json
"jira": {
  "download_url": "...",
  "checksum": "sha256:abc123...",
  "signature": "https://github.com/.../spec-kit-jira-1.0.0.sig",
  "signing_key": "https://github.com/statsperform.gpg"
}
```

CLI verifies signature before extraction.

---

## Migration Strategy

### Backward Compatibility

**Goal**: Existing spec-kit projects work without changes.

**Strategy**:

1. **Core commands unchanged**: `/speckit.tasks`, `/speckit.implement`, etc. remain in core

2. **Optional extensions**: Users opt-in to extensions

3. **Gradual migration**: Existing `taskstoissues` stays in core, Jira extension is alternative

4. **Deprecation timeline**:
   - **v0.2.0**: Introduce extension system, keep core `taskstoissues`
   - **v0.3.0**: Mark core `taskstoissues` as "legacy" (still works)
   - **v1.0.0**: Consider removing core `taskstoissues` in favor of extension

### Migration Path for Users

**Scenario 1**: User has no `taskstoissues` usage

- No migration needed, extensions are opt-in

**Scenario 2**: User uses core `taskstoissues` (GitHub Issues)

- Works as before
- Optional: Migrate to `github-projects` extension for more features

**Scenario 3**: User wants Jira (new requirement)

- `specify extension add jira`
- Configure and use

**Scenario 4**: User has custom scripts calling `taskstoissues`

- Scripts still work (core command preserved)
- Migration guide shows how to call extension commands instead

### Extension Migration Guide

**For extension authors** (if core command becomes extension):

```bash
# Old (core command)
/speckit.taskstoissues

# New (extension command)
specify extension add github-projects
/speckit.github.taskstoissues
```

**Compatibility shim** (if needed):

```yaml
# extension.yml
provides:
  commands:
    - name: "speckit.github.taskstoissues"
      file: "commands/taskstoissues.md"
      aliases: ["speckit.taskstoissues"]  # Backward compatibility
```

AI agent registers both names, so old scripts work.

---

## Implementation Phases

### Phase 1: Core Extension System (Week 1-2)

**Goal**: Basic extension infrastructure

**Deliverables**:

- [ ] Extension manifest schema (`extension.yml`)
- [ ] Extension directory structure
- [ ] CLI commands:
  - [ ] `specify extension list`
  - [ ] `specify extension add` (from URL)
  - [ ] `specify extension remove`
- [ ] Extension registry (`.specify/extensions/.registry`)
- [ ] Command registration (Claude only initially)
- [ ] Basic validation (manifest schema, compatibility)
- [ ] Documentation (extension development guide)

**Testing**:

- [ ] Unit tests for manifest parsing
- [ ] Integration test: Install dummy extension
- [ ] Integration test: Register commands with Claude

### Phase 2: Jira Extension (Week 3)

**Goal**: First production extension

**Deliverables**:

- [ ] Create `spec-kit-jira` repository
- [ ] Port Jira functionality to extension
- [ ] Create `jira-config.yml` template
- [ ] Commands:
  - [ ] `specstoissues.md`
  - [ ] `discover-fields.md`
  - [ ] `sync-status.md`
- [ ] Helper scripts
- [ ] Documentation (README, configuration guide, examples)
- [ ] Release v1.0.0

**Testing**:

- [ ] Test on `eng-msa-ts` project
- [ ] Verify spec→Epic, phase→Story, task→Issue mapping
- [ ] Test configuration loading and validation
- [ ] Test custom field application

### Phase 3: Extension Catalog (Week 4)

**Goal**: Discovery and distribution

**Deliverables**:

- [ ] Central catalog (`extensions/catalog.json` in spec-kit repo)
- [ ] Catalog fetch and parsing
- [ ] CLI commands:
  - [ ] `specify extension search`
  - [ ] `specify extension info`
- [ ] Catalog publishing process (GitHub Action)
- [ ] Documentation (how to publish extensions)

**Testing**:

- [ ] Test catalog fetch
- [ ] Test extension search/filtering
- [ ] Test catalog caching

### Phase 4: Advanced Features (Week 5-6)

**Goal**: Hooks, updates, multi-agent support

**Deliverables**:

- [ ] Hook system (`hooks` in extension.yml)
- [ ] Hook registration and execution
- [ ] Project extensions config (`.specify/extensions.yml`)
- [ ] CLI commands:
  - [ ] `specify extension update`
  - [ ] `specify extension enable/disable`
- [ ] Command registration for multiple agents (Gemini, Copilot)
- [ ] Extension update notifications
- [ ] Configuration layer resolution (project, local, env)

**Testing**:

- [ ] Test hooks in core commands
- [ ] Test extension updates (preserve config)
- [ ] Test multi-agent registration

### Phase 5: Polish & Documentation (Week 7)

**Goal**: Production ready

**Deliverables**:

- [ ] Comprehensive documentation:
  - [ ] User guide (installing/using extensions)
  - [ ] Extension development guide
  - [ ] Extension API reference
  - [ ] Migration guide (core → extension)
- [ ] Error messages and validation improvements
- [ ] CLI help text updates
- [ ] Example extension template (cookiecutter)
- [ ] Blog post / announcement
- [ ] Video tutorial

**Testing**:

- [ ] End-to-end testing on multiple projects
- [ ] Community beta testing
- [ ] Performance testing (large projects)

---

## Open Questions

### 1. Extension Namespace

**Question**: Should extension commands use namespace prefix?

**Options**:

- A) Prefixed: `/speckit.jira.specstoissues` (explicit, avoids conflicts)
- B) Short alias: `/jira.specstoissues` (shorter, less verbose)
- C) Both: Register both names, prefer prefixed in docs

**Recommendation**: C (both), prefixed is canonical

---

### 2. Config File Location

**Question**: Where should extension configs live?

**Options**:

- A) Extension directory: `.specify/extensions/jira/jira-config.yml` (encapsulated)
- B) Root level: `.specify/jira-config.yml` (more visible)
- C) Unified: `.specify/extensions.yml` (all extension configs in one file)

**Recommendation**: A (extension directory), cleaner separation

---

### 3. Command File Format

**Question**: Should extensions use universal format or agent-specific?

**Options**:

- A) Universal Markdown: Extensions write once, CLI converts per-agent
- B) Agent-specific: Extensions provide separate files for each agent
- C) Hybrid: Universal default, agent-specific overrides

**Recommendation**: A (universal), reduces duplication

---

### 4. Hook Execution Model

**Question**: How should hooks execute?

**Options**:

- A) AI agent interprets: Core commands output `EXECUTE_COMMAND: name`
- B) CLI executes: Core commands call `specify extension hook after_tasks`
- C) Agent built-in: Extension system built into AI agent (Claude SDK)

**Recommendation**: A initially (simpler), move to C long-term

---

### 5. Extension Distribution

**Question**: How should extensions be packaged?

**Options**:

- A) ZIP archives: Downloaded from GitHub releases
- B) Git repos: Cloned directly (`git clone`)
- C) Python packages: Installable via `uv tool install`

**Recommendation**: A (ZIP), simpler for non-Python extensions in future

---

### 6. Multi-Version Support

**Question**: Can multiple versions of same extension coexist?

**Options**:

- A) Single version: Only one version installed at a time
- B) Multi-version: Side-by-side versions (`.specify/extensions/jira@1.0/`, `.specify/extensions/jira@2.0/`)
- C) Per-branch: Different branches use different versions

**Recommendation**: A initially (simpler), consider B in future if needed

---

## Appendices

### Appendix A: Example Extension Structure

**Complete structure of `spec-kit-jira` extension:**

```text
spec-kit-jira/
├── README.md                        # Overview, features, installation
├── LICENSE                          # MIT license
├── CHANGELOG.md                     # Version history
├── .gitignore                       # Ignore local configs
│
├── extension.yml                    # Extension manifest (required)
├── jira-config.template.yml         # Config template
│
├── commands/                        # Command files
│   ├── specstoissues.md            # Main command
│   ├── discover-fields.md          # Helper: Discover custom fields
│   └── sync-status.md              # Helper: Sync completion status
│
├── scripts/                         # Helper scripts
│   ├── parse-jira-config.sh        # Config loader (bash)
│   ├── parse-jira-config.ps1       # Config loader (PowerShell)
│   └── validate-jira-connection.sh # Connection test
│
├── docs/                            # Documentation
│   ├── installation.md             # Installation guide
│   ├── configuration.md            # Configuration reference
│   ├── usage.md                    # Usage examples
│   ├── troubleshooting.md          # Common issues
│   └── examples/
│       ├── eng-msa-ts-config.yml   # Real-world config example
│       └── simple-project.yml      # Minimal config example
│
├── tests/                           # Tests (optional)
│   ├── test-extension.sh           # Extension validation
│   └── test-commands.sh            # Command execution tests
│
└── .github/                         # GitHub integration
    └── workflows/
        └── release.yml              # Automated releases
```

### Appendix B: Extension Development Guide (Outline)

**Documentation for creating new extensions:**

1. **Getting Started**
   - Prerequisites (tools needed)
   - Extension template (cookiecutter)
   - Directory structure

2. **Extension Manifest**
   - Schema reference
   - Required vs optional fields
   - Versioning guidelines

3. **Command Development**
   - Universal command format
   - Frontmatter specification
   - Template variables
   - Script references

4. **Configuration**
   - Config file structure
   - Schema validation
   - Layered config resolution
   - Environment variable overrides

5. **Hooks**
   - Available hook points
   - Hook registration
   - Conditional execution
   - Best practices

6. **Testing**
   - Local development setup
   - Testing with `--dev` flag
   - Validation checklist
   - Integration testing

7. **Publishing**
   - Packaging (ZIP format)
   - GitHub releases
   - Catalog submission
   - Versioning strategy

8. **Examples**
   - Minimal extension
   - Extension with hooks
   - Extension with configuration
   - Extension with multiple commands

### Appendix C: Compatibility Matrix

**Planned support matrix:**

| Extension Feature | Spec Kit Version | AI Agent Support |
|-------------------|------------------|------------------|
| Basic commands | 0.2.0+ | Claude, Gemini, Copilot |
| Hooks (after_tasks) | 0.3.0+ | Claude, Gemini |
| Config validation | 0.2.0+ | All |
| Multiple catalogs | 0.4.0+ | All |
| Permissions (sandboxing) | 1.0.0+ | TBD |

### Appendix D: Extension Catalog Schema

**Full schema for `catalog.json`:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["schema_version", "updated_at", "extensions"],
  "properties": {
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    },
    "extensions": {
      "type": "object",
      "patternProperties": {
        "^[a-z0-9-]+$": {
          "type": "object",
          "required": ["name", "id", "version", "download_url", "repository"],
          "properties": {
            "name": { "type": "string" },
            "id": { "type": "string", "pattern": "^[a-z0-9-]+$" },
            "description": { "type": "string" },
            "author": { "type": "string" },
            "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
            "download_url": { "type": "string", "format": "uri" },
            "repository": { "type": "string", "format": "uri" },
            "homepage": { "type": "string", "format": "uri" },
            "documentation": { "type": "string", "format": "uri" },
            "changelog": { "type": "string", "format": "uri" },
            "license": { "type": "string" },
            "requires": {
              "type": "object",
              "properties": {
                "speckit_version": { "type": "string" },
                "tools": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                      "name": { "type": "string" },
                      "version": { "type": "string" }
                    }
                  }
                }
              }
            },
            "tags": {
              "type": "array",
              "items": { "type": "string" }
            },
            "verified": { "type": "boolean" },
            "downloads": { "type": "integer" },
            "stars": { "type": "integer" },
            "checksum": { "type": "string" }
          }
        }
      }
    }
  }
}
```

---

## Summary & Next Steps

This RFC proposes a comprehensive extension system for Spec Kit that:

1. **Keeps core lean** while enabling unlimited integrations
2. **Supports multiple agents** (Claude, Gemini, Copilot, etc.)
3. **Provides clear extension API** for community contributions
4. **Enables independent versioning** of extensions and core
5. **Includes safety mechanisms** (validation, compatibility checks)

### Immediate Next Steps

1. **Review this RFC** with stakeholders
2. **Gather feedback** on open questions
3. **Refine design** based on feedback
4. **Proceed to Phase A**: Implement core extension system
5. **Then Phase B**: Build Jira extension as proof-of-concept

---

## Questions for Discussion

1. Does the extension architecture meet your needs for Jira integration?
2. Are there additional hook points we should consider?
3. Should we support extension dependencies (extension A requires extension B)?
4. How should we handle extension deprecation/removal from catalog?
5. What level of sandboxing/permissions do we need in v1.0?
