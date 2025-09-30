---
description: "Practice @file and @directory context injection"
---

Objective: Learn to bring the right code/text into context and ask precise questions.

Steps
1. In a terminal, `cd docs-plus/02_start_prompting/02_qwen_code/01_hello_qwen` then `qwen` to start inside the project
2. File context: `@main.py Summarize this module.`
3. Directory context: `@./ Summarize this project.`
4. Multi-import + question: `What is the highest-impact refactor? @main.py`
5. Optional: Manage workspaces
   - `/directory add .`
   - `/directory show`

Acceptance
- Model provides useful summaries and identifies candidate refactors.
- `/directory show` lists the added path.



