# [Qwen Code CLI](https://github.com/QwenLM/qwen-code)

## Table of Contents
1. Introduction
2. Install
3. Authorization (OAuth Recommended)
4. Quickstart: Create and Iterate Entirely via `qwen`
5. Tips
6. References

## Introduction
Use the Qwen Code CLI (free) as the core agent for repo analysis, and automation. Cursor is just an IDE if you prefer; every action below runs directly with the `qwen` CLI.

## [Install](https://github.com/QwenLM/qwen-code?tab=readme-ov-file#install-from-npm)
```bash
npm install -g @qwen-code/qwen-code@latest

qwen --version
# verify
qwen --help
```

## [Authorization](https://github.com/QwenLM/qwen-code?tab=readme-ov-file#authorization) (Qwen OAuth Recommended)
Choose your preferred authentication method based on your needs.

1. Qwen OAuth (🚀 Recommended – start in ~30 seconds)

```bash
# Just run this command and follow the browser authentication
qwen
```

What happens:
- Instant Setup: CLI opens your browser automatically
- One-Click Login: Authenticate with your qwen.ai account
- Automatic Management: Credentials cached locally for future use
- No Configuration: Zero setup required – just start coding!

Free Tier Benefits:
- ✅ 2,000 requests/day (no token counting needed)
- ✅ 60 requests/minute rate limit
- ✅ Automatic credential refresh
- ✅ Zero cost for individual users
- ℹ️ Note: Model fallback may occur to maintain service quality

## Quickstart: Create and Iterate Entirely via `qwen`
All steps are executed by Qwen; no IDE automation required. You can use qwen directly or in yolo mode: i.e: `qwen --yolo`

### 1) Initialize a uv project

```bash
"""
Create a Python 3.12 project called 'hello-world-qwen' using uv. Print the exact shell commands and then run them.

1. Initialize with uv init hello-world-qwen
2. Update main.py at project root file with:
   - A colorful hello world function using rich library (for consistent styling)
   - Input to get user's name
   - Display personalized greeting using rich library
3. Add dependencies: rich
4. Create a tests folder with pytest tests
5. Add a README.md with project description
6. Create a .gitignore file for Python projects
7. Set up pre-commit hooks with black and flake8

Execute all necessary commands and create all files. After completion document this prompt and the output in /prompts/** directory. Create a Numbered file i.e: 0001-init-project.prompt.md
"""
```

### 2) TDD: tests first, then implementation
```bash
"""
Review and write missing pytest tests for a function implemented in main.py. Test and update main.py to pass tests, and again run the tests. Output diffs and the exact commands executed. Continue to document prompt and effect in prompts dir.
"""
```

### 3) Run
```bash
uv run main.py
uv run pytest
```

## Tips
- Keep prompts in `prompts/` for SDD history
- Pair with Gemini CLI (free) for long‑context scripting if desired
- Create Specialized SubAgents for different parts of your stack.

## References
- Qwen Code CLI docs: https://github.com/QwenLM/qwen-code/tree/main/docs
- Checkpointing: https://github.com/QwenLM/qwen-code/blob/main/docs/checkpointing.md
- Sandbox: https://github.com/QwenLM/qwen-code/blob/main/docs/deployment.md
- Qwen Code Keyboard Shortcuts: https://github.com/QwenLM/qwen-code/blob/main/docs/keyboard-shortcuts.md
- Subagents: https://github.com/QwenLM/qwen-code/blob/main/docs/subagents.md