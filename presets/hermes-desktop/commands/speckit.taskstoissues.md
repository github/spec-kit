# /speckit.taskstoissues

Export Kanban tasks to GitHub Issues.

## Usage

```bash
/speckit.taskstoissues <feature_name> [--repo=<owner/repo>] [--dry-run]
```

## Options

- `--repo` — Target repository (default: current repo)
- `--dry-run` — Preview issues without creating

## Process

1. Read tasks.md and Kanban state
2. Create GitHub Issues for each task
3. Link issues to Kanban cards via metadata
4. Sync status bidirectionally

## Hermes Desktop Integration

In Hermes Desktop, available as "Export to GitHub" in TaskBoard pane.
