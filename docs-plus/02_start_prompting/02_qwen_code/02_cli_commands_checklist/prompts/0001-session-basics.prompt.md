---
description: "Drill the core session commands: help, stats, copy, chat, shell toggle"
---

Objective: Build muscle memory for baseline CLI fluency.

Steps
1. Change into the project and start session:
   - `cd docs-plus/02_start_prompting/02_qwen_code/01_hello_qwen`
   - `qwen`
2. Run: `/help`, `/stats`, `/copy`
3. Toggle shell mode: type `!` (on its own). Then run: `ls -la`, `git status`. Exit shell mode by pressing Enter on empty line.
4. Save and resume chat:
   - `/chat save qwen-101`
   - `/chat list`
   - `/chat resume qwen-101`

Acceptance
- You can list and resume the saved checkpoint.
- You can enter and leave shell mode and see outputs inline.



