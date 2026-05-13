---
description: Execute the implementation plan by splitting tasks.md into workflow handoff shards
---

## User Input

```text
$ARGUMENTS
```

If the user input references a handoff JSON file, execute that handoff directly:

1. Read the handoff JSON file.
2. Load only the listed `required_context_refs` plus any files needed inside `allowed_read_paths`.
3. Execute only the listed `task_ids`, respecting `allowed_write_paths` and `forbidden_actions`.
4. Mark only the completed listed tasks in `tasks.md`.
5. Run any `validation_commands` from the handoff, plus focused validation for changed files.

Do not run `specify workflow run` while executing a handoff JSON.

Otherwise, run the implementation workflow from the repository root:

```sh
specify workflow run speckit-implement -i integration=__AGENT__ -i args="$ARGUMENTS"
```

Wait for the workflow to complete. If it fails while building handoff shards, report the error and do not run `speckit.implement` manually. If a shard fails during fan-out, report the failing shard and preserve the generated handoff files for resume or debugging.
