# Extension API Reference

Technical reference for Spec Kit extension system APIs and manifest schema.

## Table of Contents

1. [Extension Manifest](#extension-manifest)
2. [Python API](#python-api)
3. [Command File Format](#command-file-format)
4. [Configuration Schema](#configuration-schema)
5. [Hook System](#hook-system)
6. [CLI Commands](#cli-commands)

---

## Extension Manifest

### Schema Version 1.0

File: `extension.yml`

```yaml
schema_version: "1.0"  # Required

extension:
  id: string           # Required, pattern: ^[a-z0-9-]+$
  name: string         # Required, human-readable name
  version: string      # Required, semantic version (X.Y.Z)
  description: string  # Required, brief description (<200 chars)
  author: string       # Required
  repository: string   # Required, valid URL
  license: string      # Required (e.g., "MIT", "Apache-2.0")
  homepage: string     # Optional, valid URL

requires:
  speckit_version: string  # Required, version specifier (>=X.Y.Z)
  tools:                   # Optional, array of tool requirements
    - name: string         # Tool name
      version: string      # Optional, version specifier
      required: boolean    # Optional, default: false

provides:
  commands:              # Required, at least one command
    - name: string       # Required, pattern: ^speckit\.[a-z0-9-]+\.[a-z0-9-]+$
      file: string       # Required, relative path to command file
      description: string # Required
      aliases: [string]  # Optional, array of alternate names

  config:                # Optional, array of config files
    - name: string       # Config file name
      template: string   # Template file path
      description: string
      required: boolean  # Default: false

hooks:                   # Optional, event hooks
  event_name:            # e.g., "after_tasks", "after_implement"
    command: string      # Command to execute
    optional: boolean    # Default: true
    prompt: string       # Prompt text for optional hooks
    description: string  # Hook description
    condition: string    # Optional, condition expression

tags:                    # Optional, array of tags (2-10 recommended)
  - string

defaults:                # Optional, default configuration values
  key: value             # Any YAML structure
```

### Field Specifications

#### `extension.id`

- **Type**: string
- **Pattern**: `^[a-z0-9-]+$`
- **Description**: Unique extension identifier
- **Examples**: `jira`, `linear`, `azure-devops`
- **Invalid**: `Jira`, `my_extension`, `extension.id`

#### `extension.version`

- **Type**: string
- **Format**: Semantic versioning (X.Y.Z)
- **Description**: Extension version
- **Examples**: `1.0.0`, `0.9.5`, `2.1.3`
- **Invalid**: `v1.0`, `1.0`, `1.0.0-beta`

#### `requires.speckit_version`

- **Type**: string
- **Format**: Version specifier
- **Description**: Required spec-kit version range
- **Examples**:
  - `>=0.1.0` - Any version 0.1.0 or higher
  - `>=0.1.0,<2.0.0` - Version 0.1.x or 1.x
  - `==0.1.0` - Exactly 0.1.0
- **Invalid**: `0.1.0`, `>= 0.1.0` (space), `latest`

#### `provides.commands[].name`

- **Type**: string
- **Pattern**: `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`
- **Description**: Namespaced command name
- **Format**:  `speckit.{extension-id}.{command-name}`
- **Examples**: `speckit.jira.specstoissues`, `speckit.linear.sync`
- **Invalid**: `jira.specstoissues`, `speckit.command`, `speckit.jira.CreateIssues`

#### `hooks`

- **Type**: object
- **Keys**: Event names (e.g., `after_tasks`, `after_implement`, `before_commit`)
- **Description**: Hooks that execute at lifecycle events
- **Events**: Defined by core spec-kit commands

---

## Python API

### ExtensionManifest

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionManifest

manifest = ExtensionManifest(Path("extension.yml"))
```

**Properties**:

```python
manifest.id                        # str: Extension ID
manifest.name                      # str: Extension name
manifest.version                   # str: Version
manifest.description               # str: Description
manifest.requires_speckit_version  # str: Required spec-kit version
manifest.commands                  # List[Dict]: Command definitions
manifest.hooks                     # Dict: Hook definitions
```

**Methods**:

```python
manifest.get_hash()  # str: SHA256 hash of manifest file
```

**Exceptions**:

```python
ValidationError       # Invalid manifest structure
CompatibilityError    # Incompatible with current spec-kit version
```

### ExtensionRegistry

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionRegistry

registry = ExtensionRegistry(extensions_dir)
```

**Methods**:

```python
# Add extension to registry
registry.add(extension_id: str, metadata: dict)

# Remove extension from registry
registry.remove(extension_id: str)

# Get extension metadata
metadata = registry.get(extension_id: str)  # Optional[dict]

# List all extensions
extensions = registry.list()  # Dict[str, dict]

# Check if installed
is_installed = registry.is_installed(extension_id: str)  # bool
```

**Registry Format**:

```json
{
  "schema_version": "1.0",
  "extensions": {
    "jira": {
      "version": "1.0.0",
      "source": "catalog",
      "manifest_hash": "sha256...",
      "enabled": true,
      "registered_commands": ["speckit.jira.specstoissues", ...],
      "installed_at": "2026-01-28T..."
    }
  }
}
```

### ExtensionManager

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionManager

manager = ExtensionManager(project_root)
```

**Methods**:

```python
# Install from directory
manifest = manager.install_from_directory(
    source_dir: Path,
    speckit_version: str,
    register_commands: bool = True
)  # Returns: ExtensionManifest

# Install from ZIP
manifest = manager.install_from_zip(
    zip_path: Path,
    speckit_version: str
)  # Returns: ExtensionManifest

# Remove extension
success = manager.remove(
    extension_id: str,
    keep_config: bool = False
)  # Returns: bool

# List installed extensions
extensions = manager.list_installed()  # List[Dict]

# Get extension manifest
manifest = manager.get_extension(extension_id: str)  # Optional[ExtensionManifest]

# Check compatibility
manager.check_compatibility(
    manifest: ExtensionManifest,
    speckit_version: str
)  # Raises: CompatibilityError if incompatible
```

### ExtensionCatalog

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionCatalog

catalog = ExtensionCatalog(project_root)
```

**Methods**:

```python
# Fetch catalog
catalog_data = catalog.fetch_catalog(force_refresh: bool = False)  # Dict

# Search extensions
results = catalog.search(
    query: Optional[str] = None,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    verified_only: bool = False
)  # Returns: List[Dict]

# Get extension info
ext_info = catalog.get_extension_info(extension_id: str)  # Optional[Dict]

# Check cache validity
is_valid = catalog.is_cache_valid()  # bool

# Clear cache
catalog.clear_cache()
```

### HookExecutor

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import HookExecutor

hook_executor = HookExecutor(project_root)
```

**Methods**:

```python
# Get project config
config = hook_executor.get_project_config()  # Dict

# Save project config
hook_executor.save_project_config(config: Dict)

# Register hooks
hook_executor.register_hooks(manifest: ExtensionManifest)

# Unregister hooks
hook_executor.unregister_hooks(extension_id: str)

# Get hooks for event
hooks = hook_executor.get_hooks_for_event(event_name: str)  # List[Dict]

# Check if hook should execute
should_run = hook_executor.should_execute_hook(hook: Dict)  # bool

# Format hook message
message = hook_executor.format_hook_message(
    event_name: str,
    hooks: List[Dict]
)  # str
```

### CommandRegistrar

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import CommandRegistrar

registrar = CommandRegistrar()
```

**Methods**:

```python
# Register commands for Claude Code
registered = registrar.register_commands_for_claude(
    manifest: ExtensionManifest,
    extension_dir: Path,
    project_root: Path
)  # Returns: List[str] (command names)

# Parse frontmatter
frontmatter, body = registrar.parse_frontmatter(content: str)

# Render frontmatter
yaml_text = registrar.render_frontmatter(frontmatter: Dict)  # str
```

---

## Command File Format

### Universal Command Format

**File**: `commands/{command-name}.md`

```markdown
---
description: "Command description"
tools:
  - 'mcp-server/tool_name'
  - 'other-mcp-server/other_tool'
---

# Command Title

Command documentation in Markdown.

## Prerequisites

1. Requirement 1
2. Requirement 2

## User Input

$ARGUMENTS

## Steps

### Step 1: Description

Instruction text...

\`\`\`bash
# Shell commands
\`\`\`

### Step 2: Another Step

More instructions...

## Configuration Reference

Information about configuration options.

## Notes

Additional notes and tips.
```

### Frontmatter Fields

```yaml
description: string   # Required, brief command description
tools: [string]       # Optional, MCP tools required
```

### Special Variables

- `$ARGUMENTS` - Placeholder for user-provided arguments
- Extension context automatically injected:

  ```markdown
  <!-- Extension: {extension-id} -->
  <!-- Config: .specify/extensions/{extension-id}/ -->
  ```

---

## Configuration Schema

### Extension Config File

**File**: `.specify/extensions/{extension-id}/{extension-id}-config.yml`

Extensions define their own config schema. Common patterns:

```yaml
# Connection settings
connection:
  url: string
  api_key: string

# Project settings
project:
  key: string
  workspace: string

# Feature flags
features:
  enabled: boolean
  auto_sync: boolean

# Defaults
defaults:
  labels: [string]
  assignee: string

# Custom fields
field_mappings:
  internal_name: "external_field_id"
```

### Config Layers

1. **Extension Defaults** (from `extension.yml` `defaults` section)
2. **Project Config** (`{extension-id}-config.yml`)
3. **Local Override** (`{extension-id}-config.local.yml`, gitignored)
4. **Environment Variables** (`SPECKIT_{EXTENSION}_*`)

### Environment Variable Pattern

Format: `SPECKIT_{EXTENSION}_{KEY}`

Examples:

- `SPECKIT_JIRA_PROJECT_KEY`
- `SPECKIT_LINEAR_API_KEY`
- `SPECKIT_GITHUB_TOKEN`

---

## Hook System

### Hook Definition

**In extension.yml**:

```yaml
hooks:
  after_tasks:
    command: "speckit.jira.specstoissues"
    optional: true
    prompt: "Create Jira issues from tasks?"
    description: "Automatically create Jira hierarchy"
    condition: null
```

### Hook Events

Standard events (defined by core):

- `after_tasks` - After task generation
- `after_implement` - After implementation
- `before_commit` - Before git commit
- `after_commit` - After git commit

### Hook Configuration

**In `.specify/extensions.yml`**:

```yaml
hooks:
  after_tasks:
    - extension: jira
      command: speckit.jira.specstoissues
      enabled: true
      optional: true
      prompt: "Create Jira issues from tasks?"
      description: "..."
      condition: null
```

### Hook Message Format

```markdown
## Extension Hooks

**Optional Hook**: {extension}
Command: `/{command}`
Description: {description}

Prompt: {prompt}
To execute: `/{command}`
```

Or for mandatory hooks:

```markdown
**Automatic Hook**: {extension}
Executing: `/{command}`
EXECUTE_COMMAND: {command}
```

---

## CLI Commands

### extension list

**Usage**: `specify extension list [OPTIONS]`

**Options**:

- `--available` - Show available extensions from catalog
- `--all` - Show both installed and available

**Output**: List of installed extensions with metadata

### extension add

**Usage**: `specify extension add EXTENSION [OPTIONS]`

**Options**:

- `--from URL` - Install from custom URL
- `--dev PATH` - Install from local directory
- `--version VERSION` - Install specific version
- `--no-register` - Skip command registration

**Arguments**:

- `EXTENSION` - Extension name or URL

### extension remove

**Usage**: `specify extension remove EXTENSION [OPTIONS]`

**Options**:

- `--keep-config` - Preserve config files
- `--force` - Skip confirmation

**Arguments**:

- `EXTENSION` - Extension ID

### extension search

**Usage**: `specify extension search [QUERY] [OPTIONS]`

**Options**:

- `--tag TAG` - Filter by tag
- `--author AUTHOR` - Filter by author
- `--verified` - Show only verified extensions

**Arguments**:

- `QUERY` - Optional search query

### extension info

**Usage**: `specify extension info EXTENSION`

**Arguments**:

- `EXTENSION` - Extension ID

### extension update

**Usage**: `specify extension update [EXTENSION]`

**Arguments**:

- `EXTENSION` - Optional, extension ID (default: all)

### extension enable

**Usage**: `specify extension enable EXTENSION`

**Arguments**:

- `EXTENSION` - Extension ID

### extension disable

**Usage**: `specify extension disable EXTENSION`

**Arguments**:

- `EXTENSION` - Extension ID

---

## Exceptions

### ValidationError

Raised when extension manifest validation fails.

```python
from specify_cli.extensions import ValidationError

try:
    manifest = ExtensionManifest(path)
except ValidationError as e:
    print(f"Invalid manifest: {e}")
```

### CompatibilityError

Raised when extension is incompatible with current spec-kit version.

```python
from specify_cli.extensions import CompatibilityError

try:
    manager.check_compatibility(manifest, "0.1.0")
except CompatibilityError as e:
    print(f"Incompatible: {e}")
```

### ExtensionError

Base exception for all extension-related errors.

```python
from specify_cli.extensions import ExtensionError

try:
    manager.install_from_directory(path, "0.1.0")
except ExtensionError as e:
    print(f"Extension error: {e}")
```

---

## Version Functions

### version_satisfies

Check if a version satisfies a specifier.

```python
from specify_cli.extensions import version_satisfies

# True if 1.2.3 satisfies >=1.0.0,<2.0.0
satisfied = version_satisfies("1.2.3", ">=1.0.0,<2.0.0")  # bool
```

---

## File System Layout

```text
.specify/
├── extensions/
│   ├── .registry               # Extension registry (JSON)
│   ├── .cache/                 # Catalog cache
│   │   ├── catalog.json
│   │   └── catalog-metadata.json
│   ├── .backup/                # Config backups
│   │   └── {ext}-{config}.yml
│   ├── {extension-id}/         # Extension directory
│   │   ├── extension.yml       # Manifest
│   │   ├── {ext}-config.yml    # User config
│   │   ├── {ext}-config.local.yml  # Local overrides (gitignored)
│   │   ├── {ext}-config.template.yml  # Template
│   │   ├── commands/           # Command files
│   │   │   └── *.md
│   │   ├── scripts/            # Helper scripts
│   │   │   └── *.sh
│   │   ├── docs/               # Documentation
│   │   └── README.md
│   └── extensions.yml          # Project extension config
└── scripts/                    # (existing spec-kit)

.claude/
└── commands/
    └── speckit.{ext}.{cmd}.md  # Registered commands
```

---

*Last Updated: 2026-01-28*
*API Version: 1.0*
*Spec Kit Version: 0.1.0*
