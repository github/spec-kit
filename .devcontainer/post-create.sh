#!/bin/bash

set -e
set -o pipefail

# Function to run a command and show logs only on error
run_command() {
    output=$(eval "$*" 2>&1)
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "[ERROR] Command failed: $*"
        echo "$output"
        exit $exit_code
    fi
}

# Note: We use Bun (instead of npm) as our package manager for its speed and overall efficiency
# It is a drop-in replacement for Node.js, so we can install npm packages through it without issues
echo "📦 Installing Bun Package Manager..."
run_command "curl -fsSL https://bun.sh/install | bash"
source ~/.bashrc

export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Installing CLI-based AI Agents

echo "🤖 Installing Copilot CLI..."
run_command "bun add --global @github/copilot@latest"
echo "✅ Done"

echo "🤖 Installing Claude CLI..."
run_command "bun add --global @anthropic-ai/claude-code@latest"
echo "✅ Done"

echo "🤖 Installing Codex CLI..."
run_command "bun add --global @openai/codex@latest"
echo "✅ Done"

echo "🤖 Installing Gemini CLI..."
run_command "bun add --global @google/gemini-cli@latest"
echo "✅ Done"

echo "🤖 Installing Augie CLI..."
run_command "bun add --global @augmentcode/auggie@latest"
echo "✅ Done"

echo "🤖 Installing Qwen Code CLI..."
run_command "bun add --global @qwen-code/qwen-code@latest"
echo "✅ Done"

echo "🤖 Installing OpenCode CLI..."
run_command "bun add --global opencode-ai@latest"
echo "✅ Done"

# Installing DocFx (for documentation site)
echo "📚 Installing DocFx..."
run_command "dotnet tool update -g docfx"
echo "✅ Done"

# Installing UV (Python package manager)
echo "🐍 Installing UV - Python Package Manager..."
run_command "pip install uv"
echo "✅ Done"

echo "🧹 Cleaning cache..."
run_command "sudo apt-get autoclean"
run_command "sudo apt-get clean"


echo "✅ Setup completed. Happy coding! 🚀"
