#!/bin/bash

# Exit immediately on error, treat unset variables as an error, and fail if any command in a pipeline fails.
set -euo pipefail

# Function to run a command and show logs only on error
run_command() {
    local command_to_run="$*"
    local output
    local exit_code
    
    # Capture all output (stdout and stderr)
    output=$(eval "$command_to_run" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    
    if [ $exit_code -ne 0 ]; then
        echo -e "\033[0;31m[ERROR] Command failed (Exit Code $exit_code): $command_to_run\033[0m" >&2
        echo -e "\033[0;31m$output\033[0m" >&2
        
        return $exit_code
    fi
}

# Note: We use Bun (instead of npm) as our package manager for its speed and overall efficiency
# It is a drop-in replacement for Node.js, so we can install npm packages through it without issues
echo "📦 Installing Bun Package Manager..."
run_command "curl -fsSL https://bun.sh/install | bash"
run_command "source ~/.bashrc"
echo "✅ Done"

export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Installing CLI-based AI Agents

echo -e "\n🤖 Installing Copilot CLI..."
run_command "bun add --global @github/copilot@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Claude CLI..."
run_command "bun add --global @anthropic-ai/claude-code@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Codex CLI..."
run_command "bun add --global @openai/codex@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Gemini CLI..."
run_command "bun add --global @google/gemini-cli@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Augie CLI..."
run_command "bun add --global @augmentcode/auggie@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Qwen Code CLI..."
run_command "bun add --global @qwen-code/qwen-code@latest"
echo "✅ Done"

echo -e "\n🤖 Installing OpenCode CLI..."
run_command "bun add --global opencode-ai@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Amazon Developer Q CLI..."
run_command "curl --proto '=https' --tlsv1.2 -sSf \"https://desktop-release.q.us-east-1.amazonaws.com/latest/q-x86_64-linux.zip\" -o \"q.zip\""
run_command "unzip q.zip && rm q.zip"
run_command "./q/install.sh --no-confirm"
run_command "rm -rf ./q"
echo "✅ Done"

# Installing UV (Python package manager)
echo -e "\n🐍 Installing UV - Python Package Manager..."
run_command "pipx install uv"
echo "✅ Done"

# Installing DocFx (for documentation site)
echo -e "\n📚 Installing DocFx..."
run_command "dotnet tool update -g docfx"
echo "✅ Done"

echo -e "\n🧹 Cleaning cache..."
run_command "sudo apt-get autoclean"
run_command "sudo apt-get clean"

echo "✅ Setup completed. Happy coding! 🚀"
