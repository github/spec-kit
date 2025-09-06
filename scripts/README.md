# Spec-Kit PowerShell Scripts

This directory contains PowerShell implementations of the Spec-Kit command-line tools. These scripts provide the same functionality as their shell script counterparts but are designed to work natively on Windows and cross-platform with PowerShell Core.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Available Commands](#available-commands)
  - [Common.psm1](#commonpsm1)
  - [Check-TaskPrerequisites.ps1](#check-taskprerequisitesps1)
  - [New-Feature.ps1](#new-featureps1)
  - [Get-FeaturePaths.ps1](#get-featurepathsps1)
  - [Initialize-Plan.ps1](#initialize-planps1)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [License](#license)

## Prerequisites

- PowerShell 5.1 or later (Windows PowerShell) or PowerShell Core 6+
- Git
- Python 3.11+ (for some template processing)

## Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/your-org/spec-kit.git
   cd spec-kit/scripts
   ```

2. Make the scripts executable (on Unix-like systems):
   ```bash
   chmod +x *.ps1
   ```

3. (Optional) Add the scripts directory to your PATH for global access.

## Available Commands

### Common.psm1

A PowerShell module containing shared functions used by other scripts. This module is automatically imported by other scripts and doesn't need to be run directly.

### Check-TaskPrerequisites.ps1

Verifies that required files exist for the current feature branch.

```powershell
.\Check-TaskPrerequisites.ps1 [-Json]
```

**Options:**
- `-Json`: Output results in JSON format

### New-Feature.ps1

Creates a new feature branch and directory structure.

```powershell
.\New-Feature.ps1 -FeatureDescription "description of feature" [-Json]
```

**Parameters:**
- `-FeatureDescription`: Description of the new feature (required)
- `-Json`: Output results in JSON format

### Get-FeaturePaths.ps1

Outputs the paths for the current feature branch's files and directories.

```powershell
.\Get-FeaturePaths.ps1
```

### Initialize-Plan.ps1

Sets up the implementation plan structure for the current branch.

```powershell
.\Initialize-Plan.ps1 [-Json]
```

**Options:**
- `-Json`: Output results in JSON format

## Usage Examples

### Create a new feature

```powershell
# Navigate to the scripts directory
cd path\to\spec-kit\scripts

# Create a new feature
.\New-Feature.ps1 -FeatureDescription "Add user authentication"

# Initialize the implementation plan
.\Initialize-Plan.ps1

# Check prerequisites
.\Check-TaskPrerequisites.ps1
```

### Using JSON output

```powershell
# Get feature information in JSON format
$featureInfo = .\New-Feature.ps1 -FeatureDescription "Add user authentication" -Json | ConvertFrom-Json

# Access properties
Write-Host "Created feature branch: $($featureInfo.branch)"
```

## Development

### Testing

To test the scripts, you can use Pester:

```powershell
# Install Pester if not already installed
if (-not (Get-Module -Name Pester -ListAvailable)) {
    Install-Module -Name Pester -Force -SkipPublisherCheck
}

# Run tests
Invoke-Pester
```

### Adding New Scripts

1. Place new PowerShell scripts in this directory
2. Use the `Common.psm1` module for shared functionality
3. Follow the same parameter naming and structure as existing scripts
4. Include comprehensive help documentation

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
