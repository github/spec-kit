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

        exit $exit_code
    fi
}

# Function to run an optional command and continue on error
run_optional_command() {
    local command_to_run="$*"
    local output
    local exit_code

    output=$(eval "$command_to_run" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    if [ $exit_code -ne 0 ]; then
        echo -e "\033[0;33m[WARN] Optional command failed (Exit Code $exit_code): $command_to_run\033[0m" >&2
        echo -e "\033[0;33m$output\033[0m" >&2
        return $exit_code
    fi

    return 0
}

# Installing CLI-based AI Agents

echo -e "\n🤖 Installing Copilot CLI..."
run_command "npm install -g @github/copilot@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Claude CLI..."
run_command "npm install -g @anthropic-ai/claude-code@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Codex CLI..."
run_command "npm install -g @openai/codex@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Gemini CLI..."
run_command "npm install -g @google/gemini-cli@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Augie CLI..."
run_command "npm install -g @augmentcode/auggie@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Qwen Code CLI..."
run_command "npm install -g @qwen-code/qwen-code@latest"
echo "✅ Done"

echo -e "\n🤖 Installing OpenCode CLI..."
run_command "npm install -g opencode-ai@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Junie CLI..."
run_command "npm install -g @jetbrains/junie-cli@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Pi Coding Agent..."
run_command "npm install -g @earendil-works/pi-coding-agent@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Kiro CLI..."
# https://kiro.dev/docs/cli/
KIRO_INSTALLER_URL="https://kiro.dev/install.sh"
KIRO_INSTALLER_SHA256="7487a65cf310b7fb59b357c4b5e6e3f3259d383f4394ecedb39acf70f307cffb"
KIRO_INSTALLER_PATH="$(mktemp)"

cleanup_kiro_installer() {
  rm -f "$KIRO_INSTALLER_PATH"
}
trap cleanup_kiro_installer EXIT

kiro_install_ok=true

run_optional_command "curl -fsSL \"$KIRO_INSTALLER_URL\" -o \"$KIRO_INSTALLER_PATH\"" || kiro_install_ok=false

if [ "$kiro_install_ok" = true ]; then
  run_optional_command "echo \"$KIRO_INSTALLER_SHA256  $KIRO_INSTALLER_PATH\" | sha256sum -c -" || kiro_install_ok=false
fi

if [ "$kiro_install_ok" = true ]; then
  run_optional_command "bash \"$KIRO_INSTALLER_PATH\"" || kiro_install_ok=false
fi

if [ "$kiro_install_ok" = true ]; then
  kiro_binary=""
  if command -v kiro-cli >/dev/null 2>&1; then
    kiro_binary="kiro-cli"
  elif command -v kiro >/dev/null 2>&1; then
    kiro_binary="kiro"
  else
    echo -e "\033[0;33m[WARN] Kiro CLI installation did not create 'kiro-cli' or 'kiro' in PATH.\033[0m" >&2
    kiro_install_ok=false
  fi
fi

if [ "$kiro_install_ok" = true ]; then
  run_optional_command "$kiro_binary --help > /dev/null" || kiro_install_ok=false
fi

if [ "$kiro_install_ok" = true ]; then
  echo "✅ Done"
else
  echo -e "\033[0;33m[WARN] Skipping Kiro CLI installation; continuing devcontainer setup.\033[0m" >&2
fi

echo -e "\n🤖 Installing Kimi Code CLI..."
# https://code.kimi.com
run_command "npm install -g @moonshot-ai/kimi-code@latest"
echo "✅ Done"

echo -e "\n🤖 Installing CodeBuddy CLI..."
run_command "npm install -g @tencent-ai/codebuddy-code@latest"
echo "✅ Done"

echo -e "\n🤖 Installing Factory Droid CLI..."
run_command "npm install -g droid@latest"

if ! command -v droid >/dev/null 2>&1; then
  echo -e "\033[0;31m[ERROR] Droid CLI installation did not create 'droid' in PATH.\033[0m" >&2
  exit 1
fi

run_command "droid --version > /dev/null"
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
