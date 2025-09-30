---
description: "Compress, summarize, and clear history while preserving context"
---

Objective: Control token usage and persist session knowledge.

Steps
1. Generate a few turns discussing improvements to `main.py`.
2. Run `/compress` and ask: "What did we decide to do next?"
3. Run `/summary` and confirm `.qwen/PROJECT_SUMMARY.md` was created.
4. Run `/clear` and continue: "Using the summary, list next 3 steps." 

Acceptance
- The model retains key decisions via compressed context and summary.
- You can continue effectively after `/clear`.



