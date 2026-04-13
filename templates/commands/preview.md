---
description: Preview the architectural impact and risks of a proposed change across all specifications.
scripts:
  sh: python3 scripts/impact_analyzer.py --change "$ARGUMENTS" --model "${AI_MODEL_ID:-gpt-4o}"
---

## User Input

```text
$ARGUMENTS