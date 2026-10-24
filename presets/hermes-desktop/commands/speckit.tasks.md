# /speckit.tasks

Generate task list from implementation plan.

## Usage

```bash
/speckit.tasks <feature_name> [--interactive] [--parallel-groups]
```

## Options

- `--interactive` — Open TaskBoard pane in Hermes Desktop
- `--parallel-groups` — Auto-detect [P] parallel groups

## Process

1. Read plan.md
2. Decompose into atomic tasks
3. Identify [P] parallel groups and [US#] story labels
4. Create Kanban cards via `host.request('kanban.create')`
5. Write to `.specify/specs/<feature_name>/tasks.md`

## Task Format

```markdown
- [ ] **T-1**: Task description [P:group] [US#123]
- [ ] **T-2**: Task description [P:group] [US#124]
```
