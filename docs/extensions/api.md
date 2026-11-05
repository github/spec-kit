# Extension API Reference

Technical reference for Spec Kit extension system APIs and manifest schema.

## Table of Contents

1. [Extension Manifest](#extension-manifest)
2. [Python API](#python-api)
3. [Command File Format](#command-file-format)
4. [Configuration Schema](#configuration-schema)
5. [Hook System](#hook-system)
6. [Extension Runtime Events](#extension-runtime-events)

---

## Extension Manifest

### Schema Version 1.0

File: `extension.yml`

```yaml
schema_version: "1.0"  # Required

extension:
  id: string           # Required, pattern: ^[a-z0-9-]+$
  name: string         # Required, human-readable name
  version: string      # Required, PEP 440 version; SemVer recommended
  description: string  # Required, brief description
  author: string       # Optional
  repository: string   # Optional, source URL
  license: string      # Optional (e.g., "MIT", "Apache-2.0")
  homepage: string     # Optional, homepage URL

requires:
  speckit_version: string  # Required, version specifier (>=X.Y.Z)
  tools:                   # Optional, array of tool requirements
    - name: string         # Tool name
      version: string      # Optional, version specifier
      required: boolean    # Optional, default: false

provides:
  commands:              # At least one of commands/templates/scripts/hooks/events required
    - name: string       # Required, pattern: ^speckit\.[a-z0-9-]+\.[a-z0-9-]+$
      file: string       # Required, relative path to command file
      description: string # Optional

  templates:             # Optional, array of declared templates. Always resolve
                          # as "replace" -- 'strategy' is not an authorable field here.
    - name: string       # Required, pattern: ^[a-z0-9-]+$
      file: string       # Required, relative path to template file
      description: string # Optional

  scripts:               # Optional, array of declared scripts. Always resolve
                          # as "replace" -- 'strategy' is not an authorable field here.
    - name: string       # Required, pattern: ^[a-z0-9-]+$
      file: string       # Required, relative path to script file
      description: string # Optional
      runtimes: [string] # Optional, subset of: bash, powershell, python

  config:                # Optional, array of config files
    - name: string       # Config file name
      template: string   # Template file path
      description: string
      required: boolean  # Default: false

hooks:                   # Optional, event hooks. Each event accepts either form below.
  event_name:            # e.g., "after_specify", "after_plan", "after_tasks", "after_implement"
    command: string      # Command to execute
    priority: integer    # Optional, >= 1, default 10 (HookExecutor sort metadata)
    optional: boolean    # Default: true
    prompt: string       # Prompt text for optional hooks
    description: string  # Hook description
    condition: string    # Optional, condition expression
  another_event:         # Any event may instead use a list of mappings (multiple commands)
    - command: string    # Same fields as the single mapping, per entry
      priority: integer
    - command: string
      priority: integer

events:                  # Optional, coding-agent lifecycle events
  session_start:
    command: string      # Command template with a runnable scripts entry

tags:                    # Optional, array of tags (2-10 recommended)
  - string

defaults:                # Optional, default configuration values
  key: value             # Any YAML structure

config:                  # Optional, separate from provides.config
  defaults:              # Merged over top-level defaults
    key: value
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
- **Format**: PEP 440; `MAJOR.MINOR.PATCH` is recommended for releases
- **Description**: Extension version
- **Examples**: `1.0.0`, `0.9.5`, `2.1.3`
- **Also accepted**: `v1.0`, `1.0`, `1.0.0-beta`
- **Invalid**: `latest`, `not-a-version`

#### `requires.speckit_version`

- **Type**: string
- **Format**: Version specifier
- **Description**: Required spec-kit version range
- **Examples**:
  - `>=0.1.0` - Any version 0.1.0 or higher
  - `>=0.1.0,<2.0.0` - Version 0.1.x or 1.x
  - `==0.1.0` - Exactly 0.1.0
- **Also accepted**: `>= 0.1.0` (whitespace after the operator)
- **Invalid**: `0.1.0`, `latest`

Manifest loading requires a non-empty string here; the compatibility check
parses it as a `packaging.specifiers.SpecifierSet` and checks the installed
Spec Kit version.

#### `provides.commands[].name`

- **Type**: string
- **Pattern**: `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`
- **Description**: Namespaced command name
- **Format**:  `speckit.{extension-id}.{command-name}`
- **Examples**: `speckit.jira.specstoissues`, `speckit.linear.sync`
- **Invalid**: `another-extension.command`, `speckit.jira.CreateIssues`

Legacy two-segment names `speckit.command` and `<extension-id>.command` are
normalized to `speckit.<extension-id>.command` with a warning. Authors should
use canonical names rather than relying on this compatibility behavior.
Installation also checks that primary names belong to the extension's
namespace and rejects exact command-name or alias collisions with installed
extensions, plus normalized output-name collisions with core commands.

#### `provides.templates[].name` / `provides.scripts[].name`

- **Type**: string
- **Pattern**: `^[a-z0-9-]+$`
- **Description**: Unlike commands, templates and scripts are not invoked by
  name, so they use the same plain slug pattern as `extension.id` rather than
  the namespaced command pattern.
- **Examples**: `myext-template`, `myext-collect`

#### `provides.templates[].strategy` / `provides.scripts[].strategy`

- Not an authorable field. Extension-contributed templates and scripts are
  always resolved as `replace`; a manifest that includes a `strategy` key on
  one of these entries is rejected with a `ValidationError`. Composable
  strategies (`wrap`/`prepend`/`append`) are preset-only.

#### `provides.scripts[].runtimes`

- **Type**: array of strings
- **Values**: `bash`, `powershell`, `python`
- **Description**: Declares which runtimes the script supports. Purely
  informational metadata — it is not used to select or invoke the script.

#### `hooks`

- **Type**: object
- **Keys**: Event names (e.g., `after_specify`, `after_plan`, `after_tasks`, `after_implement`, `before_analyze`)
- **Value**: A single hook mapping, or a list of hook mappings to register multiple commands on one event
- **Description**: Hooks that execute at lifecycle events
- **Events**: Defined by core spec-kit commands
- **Ordering**: Current command templates surface hooks in configured YAML order.
  `HookExecutor.get_hooks_for_event()` instead returns ascending `priority`
  (integer ≥ 1, default 10), with stable authoring order for ties. See
  [Hook configuration](#hook-configuration) for execution limitations.

#### `events`

- **Type**: object
- **Keys**: Canonical coding-agent event names
- **Value**: An event mapping referencing a runnable command
- **Description**: Integration-agnostic declarations translated to installed
  coding agents' native event configuration; see
  [Extension runtime events](#extension-runtime-events).

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
manifest.templates                 # List[Dict]: Declared template definitions
manifest.scripts                   # List[Dict]: Declared script definitions
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
      "source": {"kind": "catalog", "catalog": "my-org"},
      "manifest_hash": "sha256...",
      "enabled": true,
      "priority": 10,
      "registered_commands": {
        "claude": ["speckit.jira.specstoissues"]
      },
      "registered_skills": [],
      "installed_at": "2026-01-28T00:00:00"
    }
  }
}
```

`registered_commands` maps integration keys to registered command names;
`registered_skills` records supplemental skill names. The installer stores
`"local"` as raw local provenance, or a catalog object as shown above.
The CLI's normalized `--json` output uses a separate
[public source shape](cli.md#list-installed-extensions).

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

### CatalogEntry

**Module**: `specify_cli.extensions`

Represents a single catalog in the active catalog stack.

```python
from specify_cli.extensions import CatalogEntry

entry = CatalogEntry(
    url="https://example.com/catalog.json",
    name="default",
    priority=1,
    install_allowed=True,
    description="Built-in catalog of installable extensions",
)
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `url` | `str` | Catalog URL (must use HTTPS, or HTTP for localhost) |
| `name` | `str` | Human-readable catalog name |
| `priority` | `int` | Sort order (lower = higher priority, wins on conflicts) |
| `install_allowed` | `bool` | Whether extensions from this catalog can be installed |
| `description` | `str` | Optional human-readable description of the catalog (default: empty) |

### ExtensionCatalog

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionCatalog

catalog = ExtensionCatalog(project_root)
```

**Class attributes**:

```python
ExtensionCatalog.DEFAULT_CATALOG_URL    # default catalog URL
ExtensionCatalog.COMMUNITY_CATALOG_URL  # community catalog URL
```

**Methods**:

```python
# Get the ordered list of active catalogs
entries = catalog.get_active_catalogs()  # List[CatalogEntry]

# Fetch catalog (primary catalog, backward compat)
catalog_data = catalog.fetch_catalog(force_refresh: bool = False)  # Dict

# Search extensions across all active catalogs
# Each result includes _catalog_name and _install_allowed
results = catalog.search(
    query: Optional[str] = None,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    verified_only: bool = False
)  # Returns: List[Dict]  — each dict includes _catalog_name, _install_allowed

# Get extension info (searches all active catalogs)
# Returns None if not found; includes _catalog_name and _install_allowed
ext_info = catalog.get_extension_info(extension_id: str)  # Optional[Dict]

# Check cache validity (primary catalog)
is_valid = catalog.is_cache_valid()  # bool

# Clear all catalog caches
catalog.clear_cache()
```

**Result annotation fields**:

Each extension dict returned by `search()` and `get_extension_info()` includes:

| Field | Type | Description |
|-------|------|-------------|
| `_catalog_name` | `str` | Name of the source catalog |
| `_install_allowed` | `bool` | Whether installation is allowed from this catalog |

**Catalog config file** (`.specify/extension-catalogs.yml`):

```yaml
catalogs:
  - name: "default"
    url: "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.json"
    priority: 1
    install_allowed: true
    description: "Built-in catalog of installable extensions"
  - name: "community"
    url: "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.community.json"
    priority: 2
    install_allowed: false
    description: "Community-contributed extensions (discovery only)"
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
description: string   # Recommended, brief command description
tools: [string]       # Optional, MCP tools required
```

### Special Variables

- `$ARGUMENTS` - Placeholder for user-provided arguments
- Markdown command output includes extension context comments:

  ```markdown
  <!-- Extension: {extension-id} -->
  <!-- Config: .specify/extensions/{extension-id}/ -->
  ```

Generated skills instead carry provenance in their frontmatter's
`metadata.source` and do not automatically include these HTML comments.
Other output formats use their integration-specific renderer.

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

1. **Extension Defaults** (top-level `defaults` merged with `config.defaults`,
   with `config.defaults` winning on conflicts)
2. **Project Config** (`{extension-id}-config.yml`)
3. **Local Override** (`local-config.yml`, gitignored)
4. **Environment Variables** (`SPECKIT_{EXTENSION}_*`)

`ConfigManager` performs this merge when called; extension commands and scripts
must use it or implement their own loading. It does not interpolate `${...}`
strings in YAML or validate a `config_schema` field. Configuration validation
belongs to the extension's commands or scripts.

### Environment Variable Pattern

Format: `SPECKIT_{EXTENSION}_{KEY}`

The extension ID is uppercased with hyphens changed to underscores. Each
underscore-separated component after that prefix becomes a nested lowercase
key: `SPECKIT_JIRA_PROJECT_KEY` sets `project.key`, not `project_key`.
Environment values remain strings. When installed extension IDs have overlapping
normalized prefixes, the longer matching extension ID owns the variable.

Examples:

- `SPECKIT_JIRA_PROJECT_KEY`
- `SPECKIT_LINEAR_API_KEY`
- `SPECKIT_GITHUB_TOKEN`

---

## Hook System

### Hook Definition

Each event accepts either a single hook mapping or a list of mappings. A list registers multiple commands on the same event.

**Single mapping (in extension.yml)**:

```yaml
hooks:
  after_tasks:
    command: "speckit.jira.specstoissues"
    optional: true
    prompt: "Create Jira issues from tasks?"
    description: "Automatically create Jira hierarchy"
    condition: null
```

**List of mappings with priority**:

```yaml
hooks:
  after_plan:
    - command: "speckit.my-ext.verify"
      priority: 5
      optional: false
      description: "Verify the plan"
    - command: "speckit.my-ext.report"
      priority: 10
      optional: true
      prompt: "Generate the report?"
      description: "Generate a report from the plan"
```

Within a single manifest list, a repeated `command` is deduped as "last wins" and moved to the end, so it also breaks equal-priority ties in authoring order.

### Hook Events

Standard events (defined by core):

- `before_specify` - Before specification generation
- `after_specify` - After specification generation
- `before_plan` - Before implementation planning
- `after_plan` - After implementation planning
- `before_tasks` - Before task generation
- `after_tasks` - After task generation
- `before_implement` - Before implementation
- `after_implement` - After implementation
- `before_analyze` - Before cross-artifact analysis
- `after_analyze` - After cross-artifact analysis
- `before_checklist` - Before checklist generation
- `after_checklist` - After checklist generation
- `before_clarify` - Before spec clarification
- `after_clarify` - After spec clarification
- `before_constitution` - Before constitution update
- `after_constitution` - After constitution update

#### Bundled `bug` extension events (available when the extension is installed)

Hooks are prompts run in the same session; they reuse the resolved `BUG_SLUG` and `BUG_DIR` (and, for post-hooks, the written report) from the conversation, and no variables are injected. Pre-hooks run after slug resolution and prerequisites; post-hooks run after the report is written and before completion is reported.

- `before_bug_assess` - After the bug directory exists, before ingesting the report
- `after_bug_assess` - After writing `assessment.md`; not reached when an unintelligible report causes an early stop
- `before_bug_fix` - Before applying the remediation
- `after_bug_fix` - After writing `fix.md`
- `before_bug_test` - Before running verification
- `after_bug_test` - After writing `test.md`

### Hook Configuration

Spec Kit stores project-level extension registration and hook configuration in
`.specify/extensions.yml`. The `installed` list records installed extension IDs,
`settings` stores project-wide extension settings, and `hooks` groups registered
hooks by event.

```yaml
installed:
  - git
  - my-extension

settings:
  auto_execute_hooks: true

hooks:
  before_implement:
    - extension: git
      command: speckit.git.commit
      enabled: true
      optional: true
      priority: 10
      prompt: "Commit outstanding changes before implementation?"
      description: "Auto-commit before implementation"
      condition: null

  after_implement:
    - extension: my-extension
      command: speckit.my-extension.verify
      enabled: true
      optional: false
      priority: 5
      description: "Run verification after implementation"
```

`auto_execute_hooks` defaults to `true`, but is reserved and is not consulted
when hooks are surfaced or invoked.

| Field | Description |
| --- | --- |
| `extension` | ID of the extension that registered the hook. |
| `command` | Extension command associated with the hook. |
| `enabled` | Whether the hook is active. Hooks with `enabled: false` are skipped. |
| `optional` | If `true`, the hook is presented with its `prompt` and can be skipped. If `false`, it is emitted as an automatic hook with `EXECUTE_COMMAND` markers. |
| `priority` | Integer metadata >= 1, default `10`. Current command templates use configured YAML order, not priority sorting. |
| `prompt` | Message shown when asking whether to run an optional hook. |
| `description` | Human-readable explanation of the hook. |
| `condition` | Optional expression evaluated by `HookExecutor`: `config.<path>` or `env.<VAR>` with `is set`, `==`, or `!=`. Current command templates do not evaluate conditions and skip hooks with a non-empty condition. |

Hook event names identify when a hook is invoked, generally using
`before_<command>` or `after_<command>`, such as `before_implement`,
`after_implement`, `before_tasks`, and `after_tasks`.

Extension manifests reject invalid hook priorities during installation.
For existing registrations, `HookExecutor.get_hooks_for_event()` sorts using
`normalize_priority()`: missing values, booleans, values that `int()` rejects
(including non-finite floats), and values less than `1` fall back to `10`.
Numeric strings and finite floats are coerced with `int()`.
Lower values are returned first, with stable authoring order for ties.
Current command templates read hook lists directly instead of using that
Python API, so they surface hooks in configured YAML order.

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

## Extension Runtime Events

Extensions can react to coding-agent lifecycle events by declaring a top-level
`events` mapping in `extension.yml`:

```yaml
events:
  session_start:
    command: speckit.my-extension.initialize
  pre_tool_use:
    command: speckit.my-extension.validate
```

Event declarations are integration-agnostic. Spec Kit refreshes every installed
event-capable integration, and each integration translates canonical event names
into its coding agent's native event configuration. The supported canonical
events are `session_start`, `pre_tool_use`, `post_tool_use`,
`user_prompt_submit`, `stop`, and `session_end`; an integration may support
only a subset.

Runtime events are distinct from extension hooks. Events react to the coding
agent's lifecycle and execute the referenced command template's `scripts`
entry directly. The referenced command must therefore provide a runnable
script; its Markdown instructions are not sent to the coding agent. Hooks
instead surface extension commands before or after Spec Kit commands such as
`plan`, `tasks`, and `implement`.

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
│   │   ├── local-config.yml    # Local overrides (gitignored)
│   │   ├── {ext}-config.template.yml  # Template
│   │   ├── commands/           # Command files
│   │   │   └── *.md
│   │   ├── scripts/            # Helper scripts
│   │   │   └── *.sh
│   │   ├── docs/               # Documentation
│   │   └── README.md
├── extensions.yml              # Project extension config
└── scripts/                    # (existing spec-kit)

.claude/
└── commands/
    └── speckit.{ext}.{cmd}.md  # Registered commands
```

---

*Last Updated: 2026-01-28*
*API Version: 1.0*
*Spec Kit Version: 0.1.0*

## See also

- [Developing extensions](developing.md)
- [Extension CLI reference](cli.md)
- [Extension catalogs](catalogs.md)
- [Extension user guide](overview.md)
- [Publishing extensions](publishing.md)
