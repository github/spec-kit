# [Gemini CLI](https://github.com/google-gemini/gemini-cli) (Free)

## Table of Contents

1. Introduction
2. Why Gemini CLI for developers
3. Prerequisites
4. Install
5. Authentication Options
6. Configuration via `settings.json`
7. Extend Gemini with MCP servers
8. Core developer workflows
9. Quickstart: Create and Iterate via `gemini`
10. Prompt logbook pattern
11. Troubleshooting
12. Tips & integrations
13. Add-ons for Gemini CLI
14. References

## Introduction

Use the official Gemini CLI as the core terminal agent for large‑context prompts, code generation, repo analysis, and automation. Everything below runs directly with the `gemini` CLI.

## Why Gemini CLI for developers

- **Terminal-native agent**: Automate repo scaffolding, testing, and refactors without leaving the shell.
- **Large context windows**: Paste long specifications or files and still receive consistent plans.
- **Yolo execution**: Let Gemini run shell commands it suggests (`gemini --yolo`) when you want hands-free automation.
- **Prompt-first workflow**: Every exchange can be saved, versioned, and replayed—ideal for Spec-Driven Development.

## Prerequisites

- Google account with access to Gemini models (free tier is enough for interactive experimentation and normal development).
- macOS, Linux, or Windows terminal with either Homebrew, npm, or binaries available.
- (Optional) `uv`, `pytest`, and other tools if you plan to follow the Python quickstart below.
- Sign in to Chrome or another browser to complete OAuth.

## Install

```bash
brew install gemini-cli
# OR
npm install -g @google/gemini-cli

# verify
gemini --version
```

## Authentication Options

Choose the auth that fits your needs:

1. Login with Google (OAuth)

```bash
gemini
# when prompted, choose Login with Google and complete browser auth
```

Benefits (per official docs): free tier ~60 requests/min and 1,000 requests/day, 1M‑token context on Gemini 2.5 Pro; no key management.

## Configuration via `settings.json`

Gemini CLI remembers your theme, authentication flow, and other preferences by persisting them to `settings.json`. The file is loaded on every run using the following precedence (highest wins):

1. **System**: `/etc/gemini-cli/settings.json`
2. **Workspace**: `.gemini/settings.json` (project-level overrides)
3. **User**: `~/.gemini/settings.json`

Platform-specific user paths look like:

- **macOS / Linux**: `~/.gemini/settings.json`
- **Windows**: `%USERPROFILE%\.gemini\settings.json`

We will use it particularly to setup and manage MCP servers at project level.

## Extend Gemini with MCP servers

MCP servers give Gemini hands-on tools—launch headless browsers, expand context, or query knowledge bases without leaving the CLI.

### Setup principles

- Work inside your project folder (for example, `hello-world-gemini`) when you run `gemini` so workspace settings apply.
- Before and after changes, run `gemini mcp list` at the shell and, once inside chat, type `/mcp` to confirm available tools and auth status.

### Configure workspace settings

Create or extend `.gemini/settings.json` with the `mcpServers` block below. Gemini merges workspace settings on launch, so everyone in the repo inherits the configuration automatically.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "context7": {
      "command": "npx",
      "args": [
        "-y",
        "@upstash/context7-mcp",
        "--api-key",
        "YOUR_CONTEXT7_API_KEY"
      ]
    }
  }
}
```

Restart the CLI (`Ctrl+C` then `gemini` again) and re-run `gemini mcp list`. Inside the session, `/mcp` should show both servers along with their tools. You can also move the Context7 API key to an environment variable (`export CONTEXT7_API_KEY=...`) and replace the inline value with `"--api-key", "$CONTEXT7_API_KEY"`.

## Core developer workflows

Start with the quickstart below and adopt these day-to-day flows:

1. **Interactive build loop**

   - Run `gemini` to enter chat mode.
   - Paste or reference specs, then iterate on tasks. Use `Ctrl+C` to exit.
   - When Gemini suggests shell commands, copy them or enable automation with `--yolo`.

2. **Hands-free execution**
   - Launch with `gemini --yolo` to allow the agent to run shell commands after confirming each plan.
   - Review every queued command; reject with `n` if it looks risky.

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

## Prompt logbook pattern

- Create a `prompts/` folder in each project and store numbered markdown files (`0001-init.prompt.md`, `0002-test.prompt.md`, ...).
- Capture both the prompt and the CLI output (see `prompts/0001-init-project.prompt.md` in this repo for an example).
- Commit prompt files alongside code to reconstruct decisions and demonstrate Spec-Driven Development history.
- When a conversation produces additional commands or follow-ups, append them to the same prompt file so teammates can replay the full exchange.

## Troubleshooting

- **`gemini: command not found`** — Re-open your terminal after install and confirm `which gemini` points to Homebrew or npm bin.
- **OAuth loop or expired login** — Delete `~/.gemini/settings.json` and rerun `gemini` to trigger a fresh sign-in.
- **MCP server missing** — Check `.gemini/settings.json` for typos, re-run `gemini mcp list`, and confirm API keys are exported in your shell.
- **Automation blocked** — Toggle approval mode with `/approval-mode` or decline a single command with `n` during yolo sessions.

## Tips & integrations

- Keep project-level `.gemini/settings.json` under version control only if it’s secret-free.
- Pair Gemini CLI with Playwright MCP for browser verification and Context7 for quick doc research.
- Use the VS Code Gemini CLI Companion to review diffs in-editor while the CLI runs commands.
- Export transcripts periodically (terminal scrollback or `script` command) and attach them to specs/ADRs for audit trails.

## Add-ons for Gemini CLI

**Gemini CLI does have a VS Code plugin.** It’s the official **“Gemini CLI Companion”** extension that pairs directly with the Gemini CLI:

https://marketplace.visualstudio.com/items?itemName=Google.gemini-cli-vscode-ide-companion

You can also set it up:

**From VS Code (Marketplace)**

- Open VS Code → Extensions → search **“Gemini CLI Companion”** → Install.

- The extension is meant to work _with_ the CLI (you’ll run prompts in the integrated terminal; the companion adds editor-aware goodies like diffing and context):

https://developers.googleblog.com/en/gemini-cli-vs-code-native-diffing-context-aware-workflows/

- If you’re using **Gemini Code Assist** in VS Code, that’s a separate (but related) extension for completions/transformations—and Cloud Code will even install it for you. It’s not the same as the CLI companion, but many folks use both:

https://marketplace.visualstudio.com/items?itemName=Google.geminicodeassist

Also checkout:

https://marketplace.visualstudio.com/items?itemName=BoonBoonsiri.gemini-autocomplete

## References

- Gemini CLI repo: https://github.com/google-gemini/gemini-cli
- Docs: https://github.com/google-gemini/gemini-cli?tab=readme-ov-file#-documentation
- [getting started guide](https://github.com/google-gemini/gemini-cli?tab=readme-ov-file#-getting-started)
