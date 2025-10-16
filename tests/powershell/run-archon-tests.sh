#!/bin/bash
# Test Runner for PowerShell Archon Integration Tests
# Usage: bash run-archon-tests.sh

set -e

# Check if PowerShell is installed
if ! command -v pwsh &> /dev/null; then
    echo "ERROR: PowerShell 7+ is required to run these tests"
    echo "Installation instructions:"
    echo "  macOS:   brew install powershell"
    echo "  Linux:   See https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-linux"
    echo "  Windows: winget install Microsoft.PowerShell"
    exit 1
fi

# Check PowerShell version
PS_VERSION=$(pwsh -NoProfile -Command '$PSVersionTable.PSVersion.Major')
if [ "$PS_VERSION" -lt 7 ]; then
    echo "ERROR: PowerShell 7 or later is required (found version $PS_VERSION)"
    exit 1
fi

echo "Running PowerShell Archon Integration Tests..."
echo "PowerShell Version: $(pwsh -NoProfile -Command '$PSVersionTable.PSVersion')"
echo ""

# Install Pester if not already installed
pwsh -NoProfile -Command "
    if (-not (Get-Module -ListAvailable -Name Pester)) {
        Write-Host 'Installing Pester module...'
        Install-Module -Name Pester -Force -SkipPublisherCheck -Scope CurrentUser
    }
"

# Run all tests in the PowerShell test directory
echo "Running archon-fixes.Tests.ps1..."
pwsh -NoProfile -Command "
    Set-Location '$PWD'
    Invoke-Pester -Path tests/powershell/archon-fixes.Tests.ps1 -Output Detailed
"

echo ""
echo "Test run complete!"
