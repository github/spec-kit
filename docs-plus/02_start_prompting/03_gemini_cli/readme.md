# [Gemini CLI](https://github.com/google-gemini/gemini-cli) (Free)

## Table of Contents
1. Introduction
2. Install
3. Authentication Options
4. Quickstart: Create and Iterate via `gemini`
5. Tips
6. References

## Introduction
Use the official Gemini CLI as the core terminal agent for large‑context prompts, code generation, repo analysis, and automation. Everything below runs directly with the `gemini` CLI.

## Install
```bash
brew install gemini-cli
# OR
npm install -g @google/gemini-cli

# verify
gemini --version
```

Note: Qwen CLI ships with Gemini Binary so you will already have gemini installed on your system. If you want to get latest version then install it with a different package manager. i.e: For Mac I updated paths to prioritize Homebrew’s gemini, while still run Qwen with qwen.

## Authentication Options
Choose the auth that fits your needs:

1) Login with Google (OAuth)
```bash
gemini
# when prompted, choose Login with Google and complete browser auth
```
Benefits (per official docs): free tier ~60 requests/min and 1,000 requests/day, 1M‑token context on Gemini 2.5 Pro; no key management.

## [Basic Usage](https://github.com/google-gemini/gemini-cli?tab=readme-ov-file#-getting-started)

## Quickstart: Create and Iterate via `gemini`
All steps are issued to the Gemini CLI; no IDE automation required. You can use yolo mode: `gemini --yolo`


### 1) Initialize a uv project

```bash
"""
Create a Python 3.12 project called 'hello-world-gemini' using uv. Print the exact shell commands and then run them.

1. Initialize with uv init hello-world-gemini
2. Update main.py at project root file with:
   - A colorful hello world function using rich library (for consistent styling)
   - Input to get user's name
   - Display personalized greeting using rich library
3. Add dependencies: rich
4. Create a tests folder with pytest tests
5. Add a README.md with project description
6. Create a .gitignore file for Python projects
7. Set up pre-commit hooks with black and flake8

Execute all necessary commands and create all files. Use CLI commands where it;s efficient istead of writing files i.e: when creating a new project use uv init <proj_name> tog et boilerplate code. After completion document this prompt and the output in /prompts/** directory. Create a Numbered file i.e: 0001-init-project.prompt.md
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
- Keep prompts in `prompts/` to track the SDD history
- Pair with Qwen Code (free) for repo analysis/git automation if desired

## References
- Gemini CLI repo: https://github.com/google-gemini/gemini-cli
- Docs: https://github.com/google-gemini/gemini-cli?tab=readme-ov-file#-documentation

## Add-ons for Gemini CLI

**Gemini CLI does have a VS Code plugin.** It’s the official **“Gemini CLI Companion”** extension that pairs directly with the Gemini CLI:

https://marketplace.visualstudio.com/items?itemName=Google.gemini-cli-vscode-ide-companion

You can also set it up:

**From VS Code (Marketplace)**

* Open VS Code → Extensions → search **“Gemini CLI Companion”** → Install. 

* The extension is meant to work *with* the CLI (you’ll run prompts in the integrated terminal; the companion adds editor-aware goodies like diffing and context):

https://developers.googleblog.com/en/gemini-cli-vs-code-native-diffing-context-aware-workflows/

* If you’re using **Gemini Code Assist** in VS Code, that’s a separate (but related) extension for completions/transformations—and Cloud Code will even install it for you. It’s not the same as the CLI companion, but many folks use both:

https://marketplace.visualstudio.com/items?itemName=Google.geminicodeassist

Also checkout:

https://marketplace.visualstudio.com/items?itemName=BoonBoonsiri.gemini-autocomplete




