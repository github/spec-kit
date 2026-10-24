# /speckit.implement

Implement a specific task from the Kanban board.

## Usage

```bash
/speckit.implement <task_id> [--goal] [--model=<name>]
```

## Options

- `--goal` — Run in goal loop until judge agrees complete
- `--model` — Override model for this task

## Process

1. Claim task via `host.request('kanban.claim')`
2. Read task context (spec, plan, parent tasks)
3. Spawn Hermes skill: `hermes chat -Q -q "<context>" -s speckit.implement`
4. On completion, update task via `host.request('kanban.complete')`

## Hermes Desktop Integration

In Hermes Desktop, the TaskBoard pane has an "Implement" button per task.
