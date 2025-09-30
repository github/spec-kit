---
description: "Capstone: an end-to-end Qwen workflow on hello_qwen"
---

Objective: Tie everything together in one short, realistic flow.

Steps
1. Start in project and launch Qwen:
   - `cd docs-plus/02_start_prompting/02_qwen_code/01_hello_qwen`
   - `qwen`
2. Understand the code:
   - `@main.py Summarize the purpose and flow.`
3. Plan a small improvement:
   - "Suggest a tiny refactor that improves testability, with no behavior change."
4. Compress and checkpoint:
   - `/compress`
   - `/summary`
   - `/chat save capstone-hello`
5. Make the change:
   - Apply the diff proposed, or ask for a minimal diff.
6. Test quickly:
   - `!uv run pytest -q tests/test_main.py`
7. Review and close:
   - `/stats`
   - "What did we learn? Create a short, plain summary for a teammate."

Acceptance
- You created a checkpoint, compressed context, produced a tiny refactor, and tested it.
- You can resume later with `/chat resume capstone-hello`.


