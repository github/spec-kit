#!/usr/bin/env bash
# Global installation script for SpecKit Memory extension
# Usage: bash scripts/memory/install_global.sh

set -e

echo "=== SpecKit Global Memory Installation ==="
echo ""

# Detect platform
PLATFORM="$(uname -s)"
echo "Platform: $PLATFORM"

# Global home directory
GLOBAL_HOME="$HOME/.claude"
echo "Global home: $GLOBAL_HOME"

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$GLOBAL_HOME/memory/projects"
mkdir -p "$GLOBAL_HOME/memory/backups"
mkdir -p "$GLOBAL_HOME/spec-kit/config"

# Create symlink to SpecKit
SPECKIT_SOURCE="${SPEC_KIT_SOURCE:-$HOME/IdeaProjects/spec-kit}"
SPECKIT_LINK="$GLOBAL_HOME/spec-kit"

echo "SpecKit source: $SPECKIT_SOURCE"
echo "SpecKit link: $SPECKIT_LINK"

# Remove existing link if any
if [ -L "$SPECKIT_LINK" ]; then
    echo "Removing existing symlink..."
    rm "$SPECKIT_LINK"
fi

# Create symlink based on platform
case "$PLATFORM" in
    Linux|Darwin)
        echo "Creating symlink (Unix)..."
        ln -s "$SPECKIT_SOURCE" "$SPECKIT_LINK"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Creating symlink (Windows)..."
        # Windows requires admin privileges for symlinks
        # Try Junction first (requires admin), fallback to symlink
        if command -v cmd.exe &> /dev/null; then
            cmd.exe /c "mklink /J \"$SPECKIT_LINK\" \"$SPECKIT_SOURCE\"" 2>/dev/null || \
            echo "  Note: On Windows, run as Administrator for junctions"
        fi
        ;;
    *)
        echo "Unsupported platform: $PLATFORM"
        exit 1
        ;;
esac

# Verify link
if [ -e "$SPECKIT_LINK" ]; then
    echo "✓ Link created successfully"
else
    echo "✗ Failed to create link"
    exit 1
fi

echo ""
echo "=== Installation Complete ==="
echo "Global memory directory: $GLOBAL_HOME/memory/"
echo "SpecKit link: $SPECKIT_LINK"
echo ""
echo "Next: Run verify_install.sh to verify installation"
