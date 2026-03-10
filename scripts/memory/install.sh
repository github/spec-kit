#!/usr/bin/env bash
# Global Memory Installation Script for Unix-like systems
# Usage: bash install.sh [--global-home PATH] [--skip-ollama]

set -e

# Default values
GLOBAL_HOME="$HOME/.claude"
SKIP_OLLAMA=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --global-home)
            GLOBAL_HOME="$2"
            shift 2
            ;;
        --skip-ollama)
            SKIP_OLLAMA=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: bash install.sh [--global-home PATH] [--skip-ollama]"
            exit 1
            ;;
    esac
done

echo "=== SpecKit Global Memory Installation ==="
echo ""
echo "Global Home: $GLOBAL_HOME"
echo ""

# Create directory structure
echo "[1/5] Creating directory structure..."
mkdir -p "$GLOBAL_HOME/spec-kit/config"
mkdir -p "$GLOBAL_HOME/spec-kit/templates"
mkdir -p "$GLOBAL_HOME/memory/projects"
mkdir -p "$GLOBAL_HOME/memory/backups"
echo "Directory structure created."

# Copy templates
echo "[2/5] Copying memory templates..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/../../templates/memory" ]; then
    cp -r "$SCRIPT_DIR/../../templates/memory"/* "$GLOBAL_HOME/spec-kit/templates/memory/"
    echo "Templates copied."
else
    echo "Warning: templates/memory not found, skipping template copy."
fi

# Create global memory files
echo "[3/5] Initializing global memory..."
python3 "$SCRIPT_DIR/init_memory.py" --project-id ".global" --project-name "Global Memory" --global-home "$GLOBAL_HOME"

# Check Ollama
echo "[4/5] Checking Ollama availability..."
if [ "$SKIP_OLLAMA" = true ]; then
    echo "Skipping Ollama check (--skip-ollama specified)."
else
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "Ollama detected. Vector memory available."
        else
            echo "Note: Ollama not detected. Vector memory will be disabled."
            echo "To install Ollama: https://ollama.ai/download"
            echo "To use vector memory, install Ollama and run: ollama pull mxbai-embed-large"
        fi
    else
        echo "Note: curl not available, skipping Ollama check."
    fi
fi

# Create version file
echo "[5/5] Creating version file..."
echo "0.1.0" > "$GLOBAL_HOME/spec-kit/config/.version"
echo "Version 0.1.0 installed."

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Memory location: $GLOBAL_HOME/memory/projects/.global"
echo "Config location: $GLOBAL_HOME/spec-kit/config"
echo ""
echo "Next steps:"
echo "1. Verify installation: bash scripts/memory/verify_install.sh"
echo "2. Initialize memory for your project: python3 scripts/memory/init_memory.py"
echo "3. See docs/INSTALL_MEMORY.md for full documentation"
echo ""

exit 0
