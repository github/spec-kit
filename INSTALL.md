# Installation Guide - Domain Analysis Tool

This guide provides comprehensive installation instructions for the Domain Analysis Tool across different platforms and environments.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Platform-Specific Installation](#platform-specific-installation)
- [Development Installation](#development-installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## System Requirements

### Minimum Requirements

- **Python**: 3.11 or higher
- **Operating System**:
  - Linux (Ubuntu 20.04+, CentOS 8+, Debian 10+)
  - macOS 10.15+ (Catalina or later)
  - Windows 10/11 (with PowerShell 5.1+ or PowerShell Core 7+)
- **Memory**: 512 MB RAM available
- **Storage**: 50 MB free disk space
- **Shell**: bash (Linux/macOS) or PowerShell (Windows)

### Recommended Requirements

- **Python**: 3.11 or 3.12 (latest stable)
- **Memory**: 2 GB RAM available
- **Storage**: 200 MB free disk space (for sample data and logs)
- **Git**: For version control and updates

### Dependencies

**Required Python Packages**:
- `pyyaml>=6.0` - YAML configuration file support

**Optional Dependencies**:
- `pytest>=7.0.0` - For running tests
- `pytest-cov>=4.0.0` - For test coverage reports

## Quick Installation

### Option 1: Clone Repository (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/domain-analysis-tool.git
cd domain-analysis-tool

# Install dependencies
pip install pyyaml

# Make scripts executable (Linux/macOS only)
chmod +x scripts/bash/analyze-domain.sh
chmod +x scripts/bash/common.sh

# Verify installation
./scripts/bash/analyze-domain.sh --help
```

### Option 2: Download Release Archive

1. Download the latest release from [GitHub Releases](https://github.com/your-username/domain-analysis-tool/releases)
2. Extract the archive:
   ```bash
   tar -xzf domain-analysis-tool-v1.0.0.tar.gz
   cd domain-analysis-tool-v1.0.0
   ```
3. Follow the same dependency installation steps as Option 1

## Platform-Specific Installation

### Linux (Ubuntu/Debian)

```bash
# Update package manager
sudo apt update

# Install Python 3.11+ if not available
sudo apt install python3.11 python3.11-pip python3.11-venv

# Clone and setup project
git clone https://github.com/your-username/domain-analysis-tool.git
cd domain-analysis-tool

# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pyyaml

# Make scripts executable
chmod +x scripts/bash/*.sh

# Test installation
./scripts/bash/analyze-domain.sh --version
```

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Clone and setup project
git clone https://github.com/your-username/domain-analysis-tool.git
cd domain-analysis-tool

# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pyyaml

# Make scripts executable
chmod +x scripts/bash/*.sh

# Test installation
./scripts/bash/analyze-domain.sh --version
```

### Windows

#### Option A: Using PowerShell (Recommended)

```powershell
# Check PowerShell version (should be 5.1+)
$PSVersionTable.PSVersion

# Install Python 3.11+ from Microsoft Store or python.org
# Verify Python installation
python --version

# Clone repository (requires Git for Windows)
git clone https://github.com/your-username/domain-analysis-tool.git
cd domain-analysis-tool

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\Activate.ps1

# Install dependencies
pip install pyyaml

# Test installation
scripts\powershell\analyze-domain.ps1 -Help
```

#### Option B: Using WSL (Windows Subsystem for Linux)

```bash
# Install WSL2 and Ubuntu (if not already installed)
wsl --install -d Ubuntu

# Launch WSL and follow Linux installation instructions
wsl

# Inside WSL, follow the Linux installation steps above
```

## Development Installation

For contributors and advanced users who want to modify the code:

```bash
# Clone repository
git clone https://github.com/your-username/domain-analysis-tool.git
cd domain-analysis-tool

# Create development virtual environment
python3.11 -m venv dev-env
source dev-env/bin/activate  # Linux/macOS
# OR
dev-env\Scripts\Activate.ps1  # Windows

# Install dependencies including development tools
pip install pyyaml pytest pytest-cov

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Run tests to verify development setup
pytest tests/

# Make scripts executable (Linux/macOS)
chmod +x scripts/bash/*.sh
```

### IDE Configuration

**VS Code Setup**:
```json
{
  "python.defaultInterpreterPath": "./dev-env/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

**PyCharm Setup**:
1. Open project in PyCharm
2. Go to File → Settings → Project → Python Interpreter
3. Add interpreter from `./dev-env/bin/python`
4. Configure test runner: Settings → Tools → Python Integrated Tools → Testing: pytest

## Configuration

### Environment Variables

Set up optional environment variables for enhanced functionality:

```bash
# Linux/macOS
export DOMAIN_ANALYSIS_LOG_LEVEL=INFO
export DOMAIN_ANALYSIS_CONFIG_DIR=~/.config/domain-analysis
export DOMAIN_ANALYSIS_DATA_DIR=~/data/domain-analysis

# Windows PowerShell
$env:DOMAIN_ANALYSIS_LOG_LEVEL="INFO"
$env:DOMAIN_ANALYSIS_CONFIG_DIR="$env:USERPROFILE\.config\domain-analysis"
$env:DOMAIN_ANALYSIS_DATA_DIR="$env:USERPROFILE\data\domain-analysis"
```

### Global Configuration

Create global configuration directory:

```bash
# Linux/macOS
mkdir -p ~/.config/domain-analysis
cd ~/.config/domain-analysis

# Windows
mkdir "$env:USERPROFILE\.config\domain-analysis"
cd "$env:USERPROFILE\.config\domain-analysis"
```

### Shell Integration

Add domain analysis tool to your PATH for global access:

**Linux/macOS** (add to `~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$PATH:/path/to/domain-analysis-tool/scripts/bash"
alias analyze-domain='analyze-domain.sh'
```

**Windows PowerShell** (add to PowerShell profile):
```powershell
$env:PATH += ";C:\path\to\domain-analysis-tool\scripts\powershell"
Set-Alias -Name analyze-domain -Value analyze-domain.ps1
```

## Verification

### Basic Functionality Test

```bash
# Linux/macOS
./scripts/bash/analyze-domain.sh --help
./scripts/bash/analyze-domain.sh --version

# Windows
scripts\powershell\analyze-domain.ps1 -Help
scripts\powershell\analyze-domain.ps1 -Version
```

### Sample Data Analysis Test

```bash
# Test with provided sample data
./scripts/bash/analyze-domain.sh --data-dir=./sample-data/financial

# Expected output: Analysis of financial entities, rules, and integrations
# Should complete without critical errors
```

### Python Module Test

```bash
# Test Python modules directly
cd src/specify_cli
python domain_analysis.py --help
python domain_config.py --list-templates

# Test interactive mode
python interactive_domain_analysis.py
```

### Unit Tests (Development)

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/specify_cli/ --cov-report=html

# Run specific test categories
pytest tests/test_domain_analysis.py -v
pytest tests/test_shell_integration.py -k "not powershell"
```

## Troubleshooting

### Common Issues

#### Python Version Issues

**Problem**: `python: command not found` or wrong Python version
```bash
# Solution: Check Python installation
which python3
python3 --version

# If Python 3.11+ not available, install it:
# Ubuntu/Debian: sudo apt install python3.11
# macOS: brew install python@3.11
# Windows: Download from python.org
```

#### Permission Denied Errors

**Problem**: `Permission denied` when running scripts

**Linux/macOS Solution**:
```bash
chmod +x scripts/bash/analyze-domain.sh
chmod +x scripts/bash/common.sh
```

**Windows Solution**:
```powershell
# Check execution policy
Get-ExecutionPolicy

# Set execution policy (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

#### Missing Dependencies

**Problem**: `ModuleNotFoundError: No module named 'yaml'`
```bash
# Solution: Install required dependencies
pip install pyyaml

# For development dependencies
pip install pytest pytest-cov
```

#### File Path Issues

**Problem**: Scripts can't find Python modules

**Solution**: Ensure you're running from the correct directory
```bash
# Make sure you're in the project root
pwd
# Should show: /path/to/domain-analysis-tool

# If not, navigate to project root
cd /path/to/domain-analysis-tool
```

### Shell-Specific Issues

#### Bash Issues (Linux/macOS)

**Problem**: `bash: ./scripts/bash/analyze-domain.sh: No such file or directory`
```bash
# Check file exists
ls -la scripts/bash/analyze-domain.sh

# Check line endings (Windows files on Unix)
file scripts/bash/analyze-domain.sh
# Should show: ASCII text, not "with CRLF line terminators"

# Fix line endings if needed
dos2unix scripts/bash/analyze-domain.sh
```

#### PowerShell Issues (Windows)

**Problem**: PowerShell script execution blocked
```powershell
# Check current execution policy
Get-ExecutionPolicy

# Set appropriate policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Problem**: Path contains spaces causing issues
```powershell
# Use quotes around paths
scripts\powershell\analyze-domain.ps1 -DataDir "C:\path with spaces\data"
```

### Performance Issues

#### Large Dataset Timeouts

```bash
# Increase timeout and use parallel processing
./scripts/bash/analyze-domain.sh --data-dir=./large-data --timeout=300 --parallel

# Or process files in batches
./scripts/bash/analyze-domain.sh --data-dir=./large-data --max-files=50
```

#### Memory Issues

```bash
# Monitor memory usage
./scripts/bash/analyze-domain.sh --data-dir=./data --memory-limit=1GB

# Or use confidence threshold to reduce processing
./scripts/bash/analyze-domain.sh --data-dir=./data --confidence=0.9
```

### Getting Help

#### Log File Analysis

```bash
# Enable debug logging
export DOMAIN_ANALYSIS_LOG_LEVEL=DEBUG
./scripts/bash/analyze-domain.sh --data-dir=./data --log-file=debug.log

# Review log file
tail -f debug.log
```

#### System Information

```bash
# Gather system information for bug reports
echo "Python version: $(python3 --version)"
echo "OS: $(uname -a)"
echo "Shell: $SHELL"
echo "PWD: $(pwd)"
ls -la scripts/bash/
```

## Uninstallation

### Standard Uninstallation

```bash
# Remove project directory
rm -rf /path/to/domain-analysis-tool

# Remove configuration (optional)
rm -rf ~/.config/domain-analysis

# Remove Python virtual environment (if created)
rm -rf venv
```

### Complete Cleanup

```bash
# Remove shell aliases and PATH modifications
# Edit ~/.bashrc, ~/.zshrc, or PowerShell profile
# Remove lines containing domain-analysis-tool

# Remove environment variables
unset DOMAIN_ANALYSIS_LOG_LEVEL
unset DOMAIN_ANALYSIS_CONFIG_DIR
unset DOMAIN_ANALYSIS_DATA_DIR

# Clear any cached files
rm -rf ~/.cache/domain-analysis
```

### Windows Cleanup

```powershell
# Remove PowerShell aliases
Remove-Alias -Name analyze-domain -Force

# Remove environment variables
[Environment]::SetEnvironmentVariable("DOMAIN_ANALYSIS_LOG_LEVEL", $null, "User")
[Environment]::SetEnvironmentVariable("DOMAIN_ANALYSIS_CONFIG_DIR", $null, "User")

# Remove directories
Remove-Item -Recurse -Force "C:\path\to\domain-analysis-tool"
Remove-Item -Recurse -Force "$env:USERPROFILE\.config\domain-analysis"
```

## Next Steps

After successful installation:

1. **Read the Usage Guide**: See [USAGE.md](USAGE.md) for comprehensive examples
2. **Try Sample Data**: Analyze the provided sample datasets in `sample-data/`
3. **Run Setup Wizard**: Use `--setup` flag to configure domain-specific preferences
4. **Explore Interactive Mode**: Use `--interactive` flag for guided analysis
5. **Join the Community**: See [CONTRIBUTING.md](CONTRIBUTING.md) for ways to contribute

## Support

If you encounter issues not covered in this guide:

- **Check GitHub Issues**: [Project Issues](https://github.com/your-username/domain-analysis-tool/issues)
- **Create Bug Report**: Include system information and error logs
- **Join Discussions**: [GitHub Discussions](https://github.com/your-username/domain-analysis-tool/discussions)

## Updates

To update to the latest version:

```bash
# If installed via git clone
cd domain-analysis-tool
git pull origin main
pip install --upgrade pyyaml

# If installed via release archive
# Download and extract new release, then follow installation steps
```