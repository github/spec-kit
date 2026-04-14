## Using Spec Kit commands in Visual Studio Code

This page explains where to run Spec Kit commands when you're working inside VS Code and how to install and enable the GitHub Copilot Chat extension.

### Quick answer

- Run CLI commands (like `specify`) in the VS Code integrated terminal, not in the Copilot Chat input. The chat is for conversational prompts and will not execute shell commands.
- To use GitHub Copilot Chat, install the `GitHub Copilot Chat` extension and sign in to GitHub. Instructions below.

### Install & enable GitHub Copilot Chat (GUI)

1. Open VS Code.
2. Open the Extensions view (Ctrl+Shift+X).
3. Search for "Copilot Chat" and install "GitHub Copilot Chat" (published by GitHub).
4. After installation, the extension may prompt you to sign in. Follow the sign-in flow to authenticate with your GitHub account.
5. Open the Copilot Chat panel from the sidebar or use the Command Palette (Ctrl+Shift+P) and run: `Copilot Chat: Open Chat`.

### Install & enable GitHub Copilot Chat (command line)

If you prefer the command line, you can install the extension with the VS Code CLI. Open a terminal (for example, the VS Code integrated terminal) and run:

```sh
# Install the Copilot Chat extension
code --install-extension GitHub.copilot-chat

# Open VS Code (if not already open)
code .
```

After launching VS Code you may still need to follow the sign-in flow the first time the extension runs.

### Where to run `specify` and other CLI commands

The Copilot Chat input is a conversational interface only — it does not run shell/CLI commands on your machine. To actually run `specify` (or any other CLI command supplied by this repo), use the VS Code integrated terminal:

1. Open the integrated terminal (View > Terminal or <kbd>Ctrl</kbd>+<kbd>\`</kbd>).
2. Make sure you're in the project folder (the same folder that contains the repository files).
3. Run the CLI with `uvx` for one-off usage, or install it with `uv tool install` if you expect to use it regularly:

```powershell
# Run once with uvx (no installation needed)
uvx --from git+https://github.com/github/spec-kit.git specify --help

# Or install persistently with uv for regular usage
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify --help
```

To run the CLI from the source repository without installation:

```sh
cd /path/to/spec-kit
uvx --from . specify --help
```

### Where to run commands: Terminal vs AI Assistant

- **CLI commands** (e.g., `specify init`, `specify check`): Run in the VS Code integrated terminal. These are shell commands that execute on your machine.
- **Slash commands** (e.g., `/speckit.specify`, `/speckit.plan`): Run inside an AI assistant chat window (like GitHub Copilot Chat). These are consumed by the AI assistant, not executed as shell commands.

### How Slash Commands Work in Copilot Chat

When you run `specify init` and select **GitHub Copilot** as your AI assistant (or use `--ai copilot`), Spec Kit generates command files into the `.github/prompts/` folder in your project. These prompt files are what make the `/speckit.*` slash commands appear and work in Copilot Chat.

Key points:
- The slash commands are **project-specific** — they only show up when VS Code is opened on the project folder that contains the `.github/prompts/` directory
- If you don't see `/speckit.*` commands, verify that `specify init` was run with `--ai copilot` and that the `.github/prompts/` folder exists
- Other AI agents (Claude, Gemini, etc.) store their commands in different locations (e.g., `.claude/commands/`, `.gemini/commands/`)

### Helpful tips for newcomers

- If you're new to Python projects, create and activate a virtual environment before installing.
- Use the integrated terminal for all CLI work — you can split terminals, run tasks, and see output inside VS Code.
- To run common workflows with one click, consider adding a VS Code Task or an npm/PowerShell script that runs the command you need.

### Troubleshooting common issues

1. **PowerShell execution policy blocks activation**
   - Solution: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` to temporarily allow script execution

2. **Command not found after installation**
   - If you installed with `uv tool install`, ensure the uv tools bin directory is on your `PATH`, then verify the tool is installed with `uv tool list`
   - If needed, reinstall with `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
   - If you're running from the source repository in a virtual environment, make sure the environment is activated (you should see `(.venv)` in your terminal prompt)
   - For that source/venv workflow, try reinstalling with `pip install -e .` from the project root

3. **Copilot Chat not showing up**
   - Verify you're signed in to GitHub in VS Code
   - Try reloading VS Code (Command Palette > Developer: Reload Window)

4. **`/speckit.*` commands are treated as plain text instead of slash commands**
   - Verify you ran `specify init` with `--ai copilot` (or selected Copilot during init) so the `.github/prompts/` folder was created
   - Confirm the `.github/prompts/` directory exists in your project root
   - Make sure VS Code is opened on the **project folder** (not a parent directory), since Copilot discovers commands relative to the open workspace
   - If the folder exists but commands still don't appear, reload VS Code (Command Palette > Developer: Reload Window)