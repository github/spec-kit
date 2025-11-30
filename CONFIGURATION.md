# Spectrena Configuration

Complete reference for `.spectrena/config.yml`.

## Location

Configuration is stored in `.spectrena/config.yml` in your project root. Created by `spectrena init`.

## Full Example

```yaml
spec_id:
  template: "{component}-{NNN}-{slug}"
  padding: 3
  project: "MYPROJECT"
  components: [CORE, API, UI, INFRA, DOCS]
  numbering_source: "directory"

spectrena:
  enabled: true
  db_type: "surrealdb"
  lineage_db: "surrealkv://.spectrena/lineage"
  auto_register: true

workflow:
  require_component_flag: true
  validate_components: true
  max_clarifications: 3
```

---

## Spec ID Configuration

### `spec_id.template`

Pattern for generating spec IDs.

| Token | Description | Example |
|-------|-------------|---------|
| `{NNN}` | Zero-padded number | `001`, `042` |
| `{N}` | Unpadded number | `1`, `42` |
| `{component}` | Component prefix | `CORE`, `API` |
| `{slug}` | Kebab-case description | `user-auth` |
| `{project}` | Project prefix | `MYPROJ` |

**Examples:**
```yaml
# Component-based (recommended for multi-module)
template: "{component}-{NNN}-{slug}"
# → CORE-001-user-auth

# Simple sequential
template: "{NNN}-{slug}"
# → 001-user-auth

# Project prefix
template: "{project}-{NNN}-{slug}"
# → MYPROJ-001-user-auth
```

### `spec_id.padding`

Number of digits for `{NNN}`. Default: `3`

```yaml
padding: 3  # → 001, 002, 099
padding: 4  # → 0001, 0002, 0099
```

### `spec_id.project`

Project prefix for `{project}` token.

```yaml
project: "ALTAIR"
# With template "{project}-{NNN}" → ALTAIR-001
```

### `spec_id.components`

Valid component names. Empty list = any component allowed.

```yaml
components: [CORE, API, UI, INFRA, DOCS]
```

**Validation:** If `workflow.validate_components: true`, only these components are accepted.

### `spec_id.numbering_source`

Where to get the next spec number.

| Value | Description |
|-------|-------------|
| `directory` | Count existing `specs/` directories (default) |
| `database` | Query lineage database |
| `component` | Per-component numbering from directories |

```yaml
# Per-component numbering (recommended)
numbering_source: "component"
# CORE-001, CORE-002, API-001, API-002

# Global numbering
numbering_source: "directory"
# 001, 002, 003 (regardless of component)
```

---

## Lineage Configuration

### `spectrena.enabled`

Enable lineage tracking. Default: `false`

```yaml
spectrena:
  enabled: true
```

### `spectrena.db_type`

Database backend.

| Value | Description |
|-------|-------------|
| `surrealdb` | SurrealDB (recommended) |
| `sqlite` | SQLite fallback |

### `spectrena.lineage_db`

Database connection string.

**SurrealDB options:**
```yaml
# Embedded (recommended - no server needed)
lineage_db: "surrealkv://.spectrena/lineage"

# With versioning for temporal queries
lineage_db: "surrealkv+versioned://.spectrena/lineage"

# In-memory (testing only)
lineage_db: "memory"

# Remote server (team use)
lineage_db: "ws://localhost:8000"
```

**SQLite option:**
```yaml
lineage_db: ".spectrena/lineage.db"
```

### `spectrena.auto_register`

Automatically register specs/tasks in database. Default: `true`

```yaml
auto_register: true
```

---

## Workflow Configuration

### `workflow.require_component_flag`

Require `-c COMPONENT` flag for `spectrena new`. Default: `true`

```yaml
require_component_flag: true
# spectrena new "feature"  → Error: component required
# spectrena new -c CORE "feature"  → OK

require_component_flag: false
# spectrena new "feature"  → OK (no component)
```

### `workflow.validate_components`

Validate component against `spec_id.components` list. Default: `true`

```yaml
validate_components: true
# spectrena new -c INVALID "x"  → Error: unknown component
```

### `workflow.max_clarifications`

Maximum clarification rounds in `/spectrena.clarify`. Default: `3`

```yaml
max_clarifications: 3
```

---

## Environment Variables

Override config via environment:

| Variable | Overrides |
|----------|-----------|
| `SPECTRENA_PROJECT_ROOT` | Project root directory |
| `SPECTRENA_DB_URL` | `spectrena.lineage_db` |
| `SPECTRENA_ENABLED` | `spectrena.enabled` |

```bash
SPECTRENA_DB_URL="ws://localhost:8000" spectrena-mcp
```

---

## Migration

### From spec-kit

If you have an existing spec-kit project:

```bash
# Preview changes
spectrena config --migrate --dry-run

# Apply migration
spectrena config --migrate
```

This will:
1. Create `.spectrena/config.yml`
2. Rename `.specify/` to `.spectrena/` (if exists)
3. Update spec directory names to match new format

### Changing Format Mid-Project

```bash
# Change template
spectrena config --set spec_id.template="{project}-{NNN}-{slug}"

# Preview rename
spectrena config --migrate --dry-run

# Apply
spectrena config --migrate
```

---

## Minimal Configs

### Simple Project (no components)

```yaml
spec_id:
  template: "{NNN}-{slug}"
  padding: 3

workflow:
  require_component_flag: false
```

### Multi-Component Project

```yaml
spec_id:
  template: "{component}-{NNN}-{slug}"
  padding: 3
  components: [CORE, API, UI]
  numbering_source: "component"

workflow:
  require_component_flag: true
  validate_components: true
```

### Full Lineage Tracking

```yaml
spec_id:
  template: "{component}-{NNN}-{slug}"
  padding: 3
  components: [CORE, API, UI, INFRA]
  numbering_source: "database"

spectrena:
  enabled: true
  db_type: "surrealdb"
  lineage_db: "surrealkv://.spectrena/lineage"
  auto_register: true

workflow:
  require_component_flag: true
  validate_components: true
```
