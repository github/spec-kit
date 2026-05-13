---
description: Execute the implementation plan by splitting tasks.md into workflow handoff shards
---

## User Input

```text
$ARGUMENTS
```

Run the orchestrated implementation workflow from the repository root:

```sh
specify workflow run speckit-orchestrated-implement -i integration=__AGENT__ -i args="$ARGUMENTS"
```

Wait for the workflow to complete. If it fails while building handoff shards, report the error and do not run `speckit.implement` manually. If a shard fails during fan-out, report the failing shard and preserve the generated handoff files for resume or debugging.
