# Data Model: AI Model Switching and Task Tracking UI

**Feature**: 001-ai-model-switching
**Created**: 2025-09-13
**Status**: Complete

## Core Entities

### ProjectConfig
**Purpose**: Stores project-level configuration and AI model state
**Storage**: `.specify/config/project.json`

```json
{
  "version": "2.1.0",
  "created": "2025-09-13T10:00:00Z",
  "updated": "2025-09-13T10:30:00Z",
  "ai_model": {
    "current": "claude",
    "version": "3.5-sonnet",
    "provider": "anthropic"
  },
  "features": {
    "task_tracking": true,
    "auto_detection": true
  },
  "project_id": "uuid-v4",
  "name": "My Project"
}
```

**Fields**:
- `version`: Project schema version (for migrations)
- `created`/`updated`: Timestamps for tracking
- `ai_model.current`: Active AI model (claude, gemini, gpt4)
- `ai_model.version`: Specific model version
- `ai_model.provider`: Provider (anthropic, google, openai)
- `features`: Enabled feature flags
- `project_id`: Unique identifier
- `name`: Human-readable project name

**Validation Rules**:
- version must match semver pattern
- ai_model.current must be in allowed list
- timestamps must be ISO 8601 format
- project_id must be valid UUID v4

### AIModelSettings
**Purpose**: Model-specific configuration and capabilities
**Storage**: `.specify/config/models/{model-name}.json`

```json
{
  "model": "claude",
  "display_name": "Claude 3.5 Sonnet",
  "provider": "anthropic",
  "capabilities": {
    "context_length": 200000,
    "supports_artifacts": true,
    "supports_vision": true,
    "rate_limits": {
      "requests_per_minute": 50,
      "tokens_per_minute": 40000
    }
  },
  "config": {
    "temperature": 0.7,
    "max_tokens": 4096,
    "stop_sequences": ["</function_calls>"]
  },
  "migration_compatibility": ["gemini", "gpt4"]
}
```

**Fields**:
- `model`: Internal model identifier
- `display_name`: Human-readable name
- `provider`: API provider
- `capabilities`: Model technical capabilities
- `config`: Default model parameters
- `migration_compatibility`: Models this can migrate from/to

### TaskState
**Purpose**: Individual task execution status and metadata
**Storage**: `.specify/state/task-state.json`

```json
{
  "tasks": {
    "task-001": {
      "id": "task-001",
      "name": "Initialize project structure",
      "status": "completed",
      "created": "2025-09-13T10:00:00Z",
      "started": "2025-09-13T10:00:05Z",
      "completed": "2025-09-13T10:00:10Z",
      "duration_ms": 5000,
      "output": "Created src/, tests/, docs/ directories",
      "error": null,
      "progress": 100,
      "dependencies": [],
      "tags": ["setup", "filesystem"]
    }
  },
  "session": {
    "id": "session-uuid",
    "started": "2025-09-13T10:00:00Z",
    "command": "specify plan",
    "total_tasks": 15,
    "completed_tasks": 12,
    "failed_tasks": 1,
    "active_task": "task-014"
  }
}
```

**Task Fields**:
- `id`: Unique task identifier
- `name`: Human-readable task description
- `status`: pending, running, completed, failed
- `created`/`started`/`completed`: Lifecycle timestamps
- `duration_ms`: Execution time in milliseconds
- `output`: Task success output
- `error`: Error message if failed
- `progress`: 0-100 percentage for long tasks
- `dependencies`: List of task IDs that must complete first
- `tags`: Categorization tags for filtering

**Session Fields**:
- `id`: Unique session identifier
- `started`: Session start timestamp
- `command`: CLI command that started the session
- `total_tasks`/`completed_tasks`/`failed_tasks`: Counters
- `active_task`: Currently executing task ID

### MigrationState
**Purpose**: Tracks AI model switching progress and rollback data
**Storage**: `.specify/state/migration-state.json`

```json
{
  "migration_id": "migration-uuid",
  "started": "2025-09-13T10:00:00Z",
  "status": "in_progress",
  "from_model": "gemini",
  "to_model": "claude",
  "steps": [
    {
      "step": "backup_config",
      "status": "completed",
      "completed": "2025-09-13T10:00:01Z",
      "backup_location": ".specify/backups/migration-uuid/"
    },
    {
      "step": "validate_compatibility",
      "status": "completed",
      "completed": "2025-09-13T10:00:02Z"
    },
    {
      "step": "migrate_config",
      "status": "running",
      "started": "2025-09-13T10:00:03Z"
    }
  ],
  "rollback_available": true,
  "backup_location": ".specify/backups/migration-uuid/"
}
```

**Fields**:
- `migration_id`: Unique migration identifier
- `started`: Migration start timestamp
- `status`: not_started, in_progress, completed, failed, rolled_back
- `from_model`/`to_model`: Source and target AI models
- `steps`: Array of migration step statuses
- `rollback_available`: Whether rollback is possible
- `backup_location`: Path to backup files

## Entity Relationships

### ProjectConfig ↔ AIModelSettings
- ProjectConfig.ai_model.current references AIModelSettings.model
- One-to-many: One project, multiple available models
- Constraint: current model must exist in models directory

### TaskState ↔ ProjectConfig
- TaskState belongs to a project session
- Tasks may reference project configuration
- Lifecycle: TaskState cleaned up periodically, ProjectConfig persists

### MigrationState ↔ ProjectConfig
- Migration updates ProjectConfig.ai_model fields
- Backup contains previous ProjectConfig state
- Constraint: Only one active migration per project

### TaskState Dependencies
- Tasks can depend on other tasks (dependencies array)
- Directed acyclic graph (DAG) structure
- Constraint: No circular dependencies allowed

## State Transitions

### Task Status Flow
```
pending → running → completed
              ↓
            failed
```

### Migration Status Flow
```
not_started → in_progress → completed
                    ↓
                  failed → rolled_back
```

### Project Lifecycle
```
new → initialized → configured → active → archived
```

## Data Validation

### Schema Validation
- JSON Schema files for each entity type
- Runtime validation on read/write operations
- Version-aware validation for migrations

### Business Rules
- Task dependencies must not create cycles
- Only one migration can be active per project
- Model compatibility must be checked before migration
- Backup must exist before irreversible operations

### Data Integrity
- Atomic file operations prevent partial writes
- Checksums for critical configuration files
- Orphaned state cleanup on startup
- Consistency checks between related entities

---

**Data Model Status**: ✅ Complete - All entities and relationships defined