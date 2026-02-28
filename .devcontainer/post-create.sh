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

echo -e "\n🤖 Installing Kiro CLI..."
# https://kiro.dev/docs/cli/
KIRO_INSTALLER_URL="https://cli.kiro.dev/install"
KIRO_INSTALLER_PATH="$(mktemp)"

cleanup_kiro_installer() {
  rm -f "$KIRO_INSTALLER_PATH"
}
trap cleanup_kiro_installer EXIT

run_command "curl -fsSL \"$KIRO_INSTALLER_URL\" -o \"$KIRO_INSTALLER_PATH\""

if [ -n "${KIRO_INSTALLER_SHA256:-}" ]; then
  run_command "echo \"$KIRO_INSTALLER_SHA256  $KIRO_INSTALLER_PATH\" | sha256sum -c -"
elif [ "${KIRO_SKIP_KIRO_INSTALLER_VERIFY:-0}" = "1" ]; then
  echo -e "\033[0;33m[WARN] KIRO_INSTALLER_SHA256 is not set; proceeding without installer checksum verification.\033[0m" >&2
  echo -e "\033[0;33m[WARN] Set KIRO_INSTALLER_SHA256 to enforce verification, or intentionally override with KIRO_SKIP_KIRO_INSTALLER_VERIFY=1.\033[0m" >&2
else
  echo -e "\033[0;31m[ERROR] Refusing to run unverified Kiro installer.\033[0m" >&2
  echo -e "\033[0;31mSet KIRO_INSTALLER_SHA256 (recommended) or explicitly set KIRO_SKIP_KIRO_INSTALLER_VERIFY=1 to proceed.\033[0m" >&2
  exit 1
fi

run_command "bash \"$KIRO_INSTALLER_PATH\""

kiro_binary=""
if command -v kiro-cli >/dev/null 2>&1; then
  kiro_binary="kiro-cli"
elif command -v kiro >/dev/null 2>&1; then
  kiro_binary="kiro"
else
  echo -e "\033[0;31m[ERROR] Kiro CLI installation did not create 'kiro-cli' or 'kiro' in PATH.\033[0m" >&2
  exit 1
fi

run_command "$kiro_binary --help > /dev/null"
echo "✅ Done"

echo -e "\n🤖 Installing CodeBuddy CLI..."
run_command "npm install -g @tencent-ai/codebuddy-code@latest"
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
