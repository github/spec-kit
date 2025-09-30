### Qwen Code CLI — Practical Commands Checklist (Spec-Driven)

Use these short, hands-on drills to build fluency. Each drill references a numbered prompt in `prompts/` and uses the real `01_hello_qwen` project for `@file`-scoped edits and shell tasks.

Setup (do this once per session)
- Change directory into the project, then start Qwen inside it:
  - `cd docs-plus/02_start_prompting/02_qwen_code/01_hello_qwen`
  - `qwen`
  - From here, prefer relative paths like `@main.py`, `@tests/test_main.py`.

- **Prereq**: In repo root, run `qwen` from the terminal. On any step, use `/help`, `/stats`, `/clear`, `/compress`, and `/summary` as needed.

1) **Session basics** (Prompt: 0001)
   - Run: `/help`, `/stats`, `/copy`.
   - Toggle shell mode: `!` then run `ls -la`, exit shell mode by pressing Enter on an empty line.
   - Exit and resume: `/chat save qwen-101`, `/chat list`, `/chat resume qwen-101`.

2) **Context: files and directories** (Prompt: 0002)
   - Add file content: `@main.py Summarize this module.`
   - Add directory context: `@./ Summarize the project structure.`
   - Multi-import + question: `What should we refactor first? @main.py`

3) **History management** (Prompt: 0003)
   - Generate a few replies, then run `/compress` and ask it to recall the plan.
   - Use `/summary` to persist `.qwen/PROJECT_SUMMARY.md`.
   - Use `/clear` to clean the terminal (history may still be recallable by the model).

4) **Non-interactive and shell basics** (Prompt: 0004)
   - Use non-interactive once from a separate shell: `qwen -p "Explain the functions in main.py"`
   - Inside Qwen, practice shell runs: `!uv run pytest -q tests/test_main.py`, `!git status`
   - Optional advanced (later): learn creating custom commands in `.qwen/commands/`.

5) **Sandbox and safety** (Prompt: 0005)
   - Try a non-interactive run: `qwen -s -p "run shell command: env | grep SANDBOX"`.
   - Discuss safe shell, allow/block prefixes, and when to avoid destructive commands.

6) **Refactor practice** (Prompt: 0006)
   - With `@main.py` in context, ask: `/refactor:pure` (or simply: "Refactor to pure functions and explain changes").
   - Apply diffs; run tests: `!uv run pytest -q tests/test_main.py`.

7) **Capstone workflow** (Prompt: 0007)
   - End-to-end: bring in `@main.py`, plan a tiny refactor, `/compress`, `/summary`, `/chat save capstone-hello`, apply change, and test with `!uv run pytest -q tests/test_main.py`. Resume later with `/chat resume capstone-hello`.

Tips
- `@path with spaces` must be escaped like `@My\ Documents/file.txt`.
- If not starting inside project, use `/directory add <absolute-or-relative-path-to-01_hello_qwen>` and `/directory show`.
- Keyboard: Ctrl+C cancels; Up/Down navigate history.

Notes for all levels
- Beginners: Speak in simple requests. Start with `@main.py` then ask for a summary and one tiny improvement.
- Experienced: Ask for diffs only, insist on no behavior changes, run tests inside Qwen with `!uv run pytest`, and checkpoint with `/chat save`.

Familiarize with core commands: /help for list, /compress to summarize history, /clear to reset, @file.py to scope edits, /stats for token usage. Practice: Start session, edit a file (@app.py Optimize function), commit changes. Checklist: Run 10 commands, note flags like --yolo for vision. This builds command fluency.