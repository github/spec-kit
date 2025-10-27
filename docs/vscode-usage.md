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

If you prefer the command line, you can install the extension with the VS Code CLI. Open PowerShell and run:

```powershell
# Install the Copilot Chat extension
code --install-extension GitHub.copilot-chat

# Open VS Code (if not already open)
code .
```

After launching VS Code you may still need to follow the sign-in flow the first time the extension runs.

### Where to run `specify` and other CLI commands

The Copilot Chat input is a conversational interface only — it does not run shell/CLI commands on your machine. To actually run `specify` (or any other CLI command supplied by this repo), use the VS Code integrated terminal:

1. Open the integrated terminal (View > Terminal or Ctrl+`).
2. Make sure you're in the project folder (the same folder that contains the repository files).
3. Activate your Python environment and install the project if needed (example using a virtual environment):

```powershell
# create a venv (first time)
python -m venv .venv

# allow script execution for the current session if required (temporary)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# activate the venv
.\.venv\Scripts\Activate.ps1

# install the project in editable mode (if the project exposes a CLI entrypoint)
pip install -e .

# run the CLI (example)
specify --help
```

If the project exposes a console script named `specify`, the last command will run it. If not, you can often run a module directly:

```powershell
python -m specify_cli --help
```

Replace `specify_cli` above with the actual module name or entrypoint if different.

### Why commands typed into Copilot Chat don't run

The chat is a text/AI interface. Typing `/specify` there is treated as part of your message to the assistant, not as a shell invocation. To run the command you must execute it in a terminal, or build a VS Code task/extension that runs it for you.

### Helpful tips for newcomers

- If you're new to Python projects, create and activate a virtual environment before installing.
- Use the integrated terminal for all CLI work — you can split terminals, run tasks, and see output inside VS Code.
- To run common workflows with one click, consider adding a VS Code Task or an npm/powershell script that runs the command you need.

### Troubleshooting common issues

1. **PowerShell execution policy blocks activation**
   - Solution: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` to temporarily allow script execution
   
2. **Command not found after installation**
   - Make sure you're in your virtual environment (you should see `(.venv)` in your terminal prompt)
   - Try reinstalling with `pip install -e .` from the project root
   
3. **Copilot Chat not showing up**
   - Verify you're signed in to GitHub in VS Code
   - Try reloading VS Code (Command Palette > Developer: Reload Window)