# Spectrena

**Spec-driven development with lineage tracking for AI-assisted coding.**

Spectrena extends [spec-kit](https://github.com/github/spec-kit) with configurable spec IDs, discovery phases, parallel development via git worktrees, and full traceability from specs → tasks → code.

## Quick Start

```bash
# Install
uv tool install spectrena[lineage-surreal]

# Initialize a project
cd my-project
spectrena init

# Create your first spec
spectrena new -c CORE "User authentication"

# In Claude Code, use slash commands
/spectrena.specify "OAuth integration"
/spectrena.plan
/spectrena.deps
```

## What It Does

| Feature | Description |
|---------|-------------|
| **Configurable Spec IDs** | `{component}-{NNN}-{slug}` patterns with per-component numbering |
| **Discovery Phase** | Explore ideas before committing to architecture |
| **Parallel Development** | Git worktrees with dependency-aware task selection |
| **Lineage Tracking** | Trace specs → plans → tasks → code changes |
| **Serena Integration** | Automatic code change recording with symbol-level tracking |
| **AI-Native Workflow** | MCP tools + slash commands for Claude Code |

## Installation

### From Git (recommended during development)

```bash
# Install from GitHub
uv tool install "git+https://github.com/rghsoftware/spectrena"

# With lineage tracking
uv tool install "git+https://github.com/rghsoftware/spectrena[lineage-surreal]"

# One-off execution without installing
uvx --from "git+https://github.com/rghsoftware/spectrena" spectrena --help
```

### From PyPI (when published)

```bash
# Basic install
uv tool install spectrena

# With lineage tracking (recommended)
uv tool install spectrena[lineage-surreal]
```

### With Serena Fork (full traceability)

```bash
# Install both Spectrena and the Serena fork
uv tool install "git+https://github.com/rghsoftware/spectrena[lineage-surreal]"
uv tool install "git+https://github.com/rghsoftware/serena-lineage"
```

### Verify Installation

```bash
spectrena --help
sw --help
spectrena-mcp --help
```

## Project Structure

After `spectrena init`, your project will have:

```
my-project/
├── .spectrena/              # Internal state
│   ├── config.yml           # Project configuration (commit this)
│   ├── discovery.md         # Discovery phase output (commit this)
│   └── lineage/             # Lineage database (gitignore this)
├── templates/               # User-editable templates
│   ├── spec-template.md
│   ├── plan-template.md
│   └── commands/            # Slash command prompts
├── specs/                   # Spec directories
│   └── CORE-001-user-auth/
│       ├── spec.md
│       └── plan.md
├── deps.mermaid             # Dependency graph (Mermaid format)
├── AGENTS.md                # Multi-agent support documentation
├── CLAUDE.md                # Claude-specific agent context
└── .mcp.json                # MCP server config
```

## Recommended .gitignore

```gitignore
# Spectrena - lineage database (local state, not shared)
.spectrena/lineage/

# Optional: ignore discovery if you prefer not to commit exploration docs
# .spectrena/discovery.md
```

**What to commit vs ignore:**

| Path | Commit? | Reason |
|------|---------|--------|
| `.spectrena/config.yml` | ✅ Yes | Project configuration, share with team |
| `.spectrena/discovery.md` | ✅ Yes | Exploration context, useful history |
| `.spectrena/lineage/` | ❌ No | Local database state |
| `templates/` | ✅ Yes | User-customized templates |
| `specs/` | ✅ Yes | The whole point! |
| `deps.mermaid` | ✅ Yes | Dependency graph |
| `AGENTS.md` | ✅ Yes | Multi-agent support documentation |
| `CLAUDE.md` | ✅ Yes | Claude-specific agent context |
| `.mcp.json` | ✅ Yes | MCP configuration |

## CLI Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `spectrena init` | Initialize project with wizard |
| `spectrena init --from-discovery` | Use discovery.md recommendations |
| `spectrena discover "description"` | Generate discovery doc (Phase -2) |
| `spectrena new "description"` | Create new spec + branch |
| `spectrena new -c CORE "desc"` | Create spec with component |
| `spectrena plan-init` | Initialize plan artifacts |
| `spectrena doctor` | Check dependencies |
| `spectrena config --show` | Display configuration |
| `spectrena config --migrate` | Migrate existing specs |

### Worktree Commands (`sw`)

| Command | Description |
|---------|-------------|
| `sw list` | List spec branches with status |
| `sw ready` | Show specs with deps satisfied |
| `sw create <branch>` | Create worktree for spec |
| `sw open <branch>` | Open in new terminal |
| `sw merge <branch>` | Merge and cleanup |
| `sw status` | Show active worktrees |

### Dependency Commands (`sw dep`)

| Command | Description |
|---------|-------------|
| `sw dep add X Y` | X depends on Y |
| `sw dep rm X Y` | Remove dependency |
| `sw dep check` | Validate graph |
| `sw dep show` | ASCII visualization |
| `sw dep show --mermaid` | Raw Mermaid output |
| `sw dep sync` | Sync file ↔ lineage DB |

**AI-assisted:** Use `/spectrena.deps` in Claude Code for automatic analysis.

## Slash Commands (Claude Code)

| Command | Description |
|---------|-------------|
| `/spectrena.specify "Feature"` | Create new spec |
| `/spectrena.clarify` | Refine current spec |
| `/spectrena.plan` | Generate implementation plan |
| `/spectrena.tasks` | Break plan into tasks |
| `/spectrena.deps` | Analyze and generate dependency graph |

## Configuration

**`.spectrena/config.yml`:**

```yaml
spec_id:
  template: "{component}-{NNN}-{slug}"
  padding: 3
  components: [CORE, API, UI, INFRA]
  numbering_source: "directory"  # or "database"

spectrena:
  enabled: true
  db_type: "surrealdb"
  lineage_db: "surrealkv://.spectrena/lineage"

workflow:
  require_component_flag: true
  validate_components: true
```

## Dependency Graph

Dependencies use **Mermaid format** for Claude-native generation:

**`deps.mermaid`:**
```mermaid
graph TD
    CORE-001-user-auth
    CORE-002-data-sync --> CORE-001-user-auth
    API-001-rest-endpoints --> CORE-001-user-auth
    API-001-rest-endpoints --> CORE-002-data-sync
```

Generate automatically with `/spectrena.deps` or manually with `sw dep add`.

## MCP Integration

**`.mcp.json`:**
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

**Available MCP tools:**

| Tool | Description |
|------|-------------|
| `phase_get()` | Get current phase and active task |
| `task_start(task_id)` | Begin working on a task |
| `task_complete(task_id, minutes)` | Mark task done |
| `task_context(task_id)` | Get full context |
| `ready_specs()` | List unblocked specs |
| `dep_graph_analyze()` | Get specs for dependency analysis |
| `dep_graph_save(mermaid)` | Save dependency graph |

## Lineage Tracking

When enabled, Spectrena tracks:

- **Specs** → status, component, weight, dependencies
- **Plans** → linked to specs
- **Tasks** → time tracking, completion status
- **Code changes** → file, symbol, task context (via Serena)

**Query examples:**
```bash
# What breaks if CORE-001 slips?
spectrena impact CORE-001

# What's ready to work on?
sw ready

# Velocity over last 7 days
spectrena velocity --days 7
```

## Workflow

### 1. Discovery (Optional)

```bash
spectrena discover "Task management app for ADHD users"
# Creates .spectrena/discovery.md with recommendations
```

### 2. Initialize

```bash
spectrena init --from-discovery
# Or interactive: spectrena init
```

### 3. Create Specs

**Option A: Two-step (CLI + Claude)**
```bash
# Step 1: Create scaffold (brief title is fine)
spectrena new -c CORE "User authentication"
# Creates specs/CORE-001-user-auth/ with template
```

Then in Claude Code:
```
# Step 2: Generate detailed content (Claude asks clarifying questions)
/spectrena.specify
```

**Option B: One-step (Claude only)**
```
/spectrena.specify "User authentication" -c CORE
# Claude asks clarifying questions, then generates full spec
```

Brief descriptions are fine - Claude will ask 2-3 clarifying questions if needed.

### 4. Plan & Implement

```bash
spectrena plan-init specs/CORE-001-user-auth
```

Or in Claude Code:
```
/spectrena.plan
/spectrena.tasks
```

### 5. Parallel Development

```bash
# Set up dependencies
/spectrena.deps  # In Claude Code

# Work on unblocked specs
sw ready
sw create spec/CORE-001-user-auth
# ... implement ...
sw merge spec/CORE-001-user-auth
```

## Development

```bash
# Clone
git clone https://github.com/rghsoftware/spectrena
cd spectrena

# Install editable
uv tool install -e ".[lineage-surreal]"

# Run tests
uv pip install -e ".[dev]"
pytest
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SPECTRENA                               │
├─────────────────────────────────────────────────────────────────┤
│  CLI Layer (pure Python)                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ discover │  │   new    │  │plan-init │  │  sw dep  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                 │
│  MCP Servers                                                    │
│  ┌────────────────────────┐    ┌────────────────────────┐      │
│  │    spectrena-mcp       │    │    serena-mcp          │      │
│  │  (spec/task mgmt)      │    │  (semantic editing)    │      │
│  └───────────┬────────────┘    └───────────┬────────────┘      │
│              └──────────┬──────────────────┘                    │
│                         ▼                                       │
│  Data Layer  ┌─────────────────────────────────────────────┐   │
│              │ .spectrena/lineage (SurrealDB)               │   │
│              └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## License

MIT

## Credits

- Based on [spec-kit](https://github.com/github/spec-kit) by GitHub
- Semantic editing via [Serena](https://github.com/oraios/serena) fork
