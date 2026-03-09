#!/usr/bin/env bash

# Post-create script for Spec Kit devcontainer
# This script runs after the devcontainer is created to install
# additional tools and dependencies.

set -euo pipefail

echo "🔧 Running post-create setup..."

#==============================================================================
# Install Kiro CLI
#==============================================================================

echo "📦 Installing Kiro CLI..."

KIRO_INSTALLER_SHA256="7487a65cf310b7fb59b357c4b5e6e3f3259d383f4394ecedb39acf70f307cffb"
KIRO_INSTALLER_URL="https://kiro.dev/install.sh"
KIRO_INSTALLER_PATH="/tmp/kiro-installer.sh"

# Download installer
curl -fsSL "$KIRO_INSTALLER_URL" -o "$KIRO_INSTALLER_PATH"

# Verify checksum
echo "$KIRO_INSTALLER_SHA256  $KIRO_INSTALLER_PATH" | sha256sum -c -

# Run installer
bash "$KIRO_INSTALLER_PATH"

# Cleanup
rm -f "$KIRO_INSTALLER_PATH"

echo "✅ Kiro CLI installed"

#==============================================================================
# Install Kimi CLI
#==============================================================================

echo "📦 Installing Kimi CLI..."

curl -LsSf https://code.kimi.com/install.sh | bash

echo "✅ Kimi CLI installed"

#==============================================================================
# Summary
#==============================================================================

echo ""
echo "🎉 Post-create setup complete!"
echo ""
echo "Installed tools:"
echo "  - Kiro CLI"
echo "  - Kimi CLI"
