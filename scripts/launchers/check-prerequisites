#!/usr/bin/env bash
# Auto-generated OS-agnostic launcher for check-prerequisites
# This script detects the operating system and delegates to the appropriate implementation
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

detect_os() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      echo "windows"
      ;;
    Linux*)
      echo "linux"
      ;;
    Darwin*)
      echo "macos"
      ;;
    *)
      echo "unknown"
      ;;
  esac
}

OS_TYPE=$(detect_os)

if [[ "$OS_TYPE" == "windows" ]]; then
  # Windows: prefer PowerShell
  if command -v pwsh &> /dev/null; then
    exec pwsh -File "$SCRIPT_DIR/../powershell/check-prerequisites.ps1" "$@"
  elif command -v powershell &> /dev/null; then
    exec powershell -File "$SCRIPT_DIR/../powershell/check-prerequisites.ps1" "$@"
  else
    # Fallback to bash if PowerShell not available (e.g., Git Bash on Windows)
    exec bash "$SCRIPT_DIR/../bash/check-prerequisites.sh" "$@"
  fi
else
  # Unix/Linux/macOS: use bash
  exec bash "$SCRIPT_DIR/../bash/check-prerequisites.sh" "$@"
fi
