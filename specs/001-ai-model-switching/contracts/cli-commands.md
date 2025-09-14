# CLI Commands Contract

**Feature**: AI Model Switching and Task Tracking UI
**Version**: 1.0.0
**Created**: 2025-09-13

## Command Specifications

### `specify switch-model`
**Purpose**: Switch AI model without losing project progress

**Usage**:
```bash
specify switch-model <target-model> [options]
```

**Arguments**:
- `target-model`: Target AI model name (claude, gemini, gpt4)

**Options**:
- `--backup`: Create backup before switching (default: true)
- `--validate`: Validate compatibility before switching (default: true)
- `--force`: Force switch even with warnings (default: false)
- `--dry-run`: Show what would be changed without applying

**Examples**:
```bash
specify switch-model claude
specify switch-model gemini --backup --validate
specify switch-model gpt4 --dry-run
```

**Exit Codes**:
- 0: Success
- 1: Invalid model name
- 2: Compatibility check failed
- 3: Migration failed
- 4: Backup creation failed

**Output Format**:
```json
{
  "success": true,
  "from_model": "gemini",
  "to_model": "claude",
  "migration_id": "uuid",
  "backup_location": ".specify/backups/uuid/",
  "duration_ms": 1250
}
```

### `specify list-models`
**Purpose**: List available AI models and current selection

**Usage**:
```bash
specify list-models [options]
```

**Options**:
- `--format`: Output format (table, json, yaml) (default: table)
- `--show-config`: Include model configuration details

**Examples**:
```bash
specify list-models
specify list-models --format json
specify list-models --show-config
```

**Output Format (table)**:
```
MODEL    PROVIDER    STATUS     COMPATIBLE
claude   anthropic   active     ✓
gemini   google      available  ✓
gpt4     openai      available  ⚠️
```

**Output Format (json)**:
```json
{
  "current_model": "claude",
  "available_models": [
    {
      "name": "claude",
      "provider": "anthropic",
      "status": "active",
      "compatible": true,
      "version": "3.5-sonnet"
    }
  ]
}
```

### `specify detect-project`
**Purpose**: Detect and validate existing spec-kit project

**Usage**:
```bash
specify detect-project [path] [options]
```

**Arguments**:
- `path`: Project directory path (default: current directory)

**Options**:
- `--validate`: Perform full validation (default: true)
- `--repair`: Attempt to repair issues (default: false)
- `--format`: Output format (table, json) (default: table)

**Examples**:
```bash
specify detect-project
specify detect-project /path/to/project --repair
specify detect-project . --format json
```

**Output Format**:
```json
{
  "detected": true,
  "valid": true,
  "project_id": "uuid",
  "version": "2.1.0",
  "ai_model": "claude",
  "issues": [],
  "repair_actions": []
}
```

### `specify reset-project`
**Purpose**: Clean reset project for fresh initialization

**Usage**:
```bash
specify reset-project [options]
```

**Options**:
- `--backup`: Create backup before reset (default: true)
- `--confirm`: Skip confirmation prompt (default: false)
- `--keep-specs`: Keep specification files (default: false)

**Examples**:
```bash
specify reset-project
specify reset-project --keep-specs --confirm
```

**Output Format**:
```json
{
  "success": true,
  "backup_location": ".specify/backups/reset-uuid/",
  "removed_files": [".specify/config/", ".specify/state/"],
  "kept_files": ["specs/"]
}
```

### `specify track-tasks`
**Purpose**: Enable/disable task tracking UI

**Usage**:
```bash
specify track-tasks <command> [options]
```

**Commands**:
- `enable`: Enable task tracking UI
- `disable`: Disable task tracking UI
- `status`: Show current status
- `clear`: Clear task history

**Options**:
- `--sidebar`: Show sidebar (default: true)
- `--format`: Status output format (table, json)

**Examples**:
```bash
specify track-tasks enable
specify track-tasks status --format json
specify track-tasks clear
```

## Error Handling

### Common Error Responses
```json
{
  "success": false,
  "error": {
    "code": "INVALID_MODEL",
    "message": "Model 'invalid-model' is not supported",
    "details": {
      "supported_models": ["claude", "gemini", "gpt4"]
    }
  }
}
```

### Error Codes
- `INVALID_MODEL`: Unsupported AI model name
- `PROJECT_NOT_FOUND`: No spec-kit project detected
- `MIGRATION_FAILED`: Model switching failed
- `BACKUP_FAILED`: Backup creation failed
- `VALIDATION_FAILED`: Project validation failed
- `PERMISSION_DENIED`: Insufficient file permissions
- `CORRUPTION_DETECTED`: Config files are corrupted

## Global Options
All commands support these options:

- `--help`: Show command help
- `--version`: Show version information
- `--verbose`: Verbose output
- `--quiet`: Suppress non-error output
- `--config`: Specify custom config directory
- `--no-color`: Disable colored output

## Environment Variables
- `SPECIFY_CONFIG_DIR`: Custom config directory
- `SPECIFY_LOG_LEVEL`: Log level (debug, info, warn, error)
- `SPECIFY_NO_COLOR`: Disable colored output
- `SPECIFY_AUTO_BACKUP`: Enable automatic backups

---

**Contract Status**: ✅ Complete - All CLI commands specified