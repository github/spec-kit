### Qwen Code CLI — Use Cases (Hands‑On, Simple English)

Use the code from the last step (01_hello_qwen). Start inside the project:
- `cd hello_qwen && qwen`
- Prefer relative paths like `@main.py`, `@./`, `tests/test_main.py`.

Use cases
- Understand the CLI quickly
  - `/help` → list commands and shortcuts
  - `/tools` → see available tools
  - `/about` → version info

- Snapshot and cost awareness
  - `/stats tools` → session Tool Stats  
  - `/stats model` → token and latency breakdown
  - `/copy` → copy last output to clipboard

- Bring code into context (work on real files)
  - `@main.py Summarize this module.`
  - `@./ Outline the project structure.`
  - If you started outside the folder: `/directory add <path-to-01_hello_qwen>` then `/directory show`

- History and memory
  - `/compress` → shrink history, keep the essence
  - `/summary` → write `.qwen/PROJECT_SUMMARY.md`
  - `/chat save my-tag`, `/chat list`, `/chat resume my-tag`

- Shell and tests (stay inside Qwen)
  - `!uv run pytest -q tests/test_main.py`
  - Non-interactive once from a separate shell: `qwen -p "Explain the functions in main.py"`

Tips
- Escape spaces in paths like `@My\ Documents/file.txt`.
- Keyboard: Ctrl+C cancels; Up/Down navigate history.
 