# Bicep Generator - Installation & Usage Guide

Quick guide to install and use the Bicep Generator command in your projects.

---

## Installation Steps

### Step 1: Install Specify CLI

**Option A: Install from Source (Current Development Version)**

Using the automated installation script (recommended):

```powershell
# Windows (PowerShell)
C:\git\spec-kit-4applens\scripts\powershell\install-local-dev.ps1

# Linux/macOS (Bash)
/path/to/spec-kit-4applens/scripts/bash/install-local-dev.sh
```

Or manually:

```powershell
# Clone the repository
git clone https://github.com/cristhianu/spec-kit-4applens.git
cd spec-kit-4applens

# Install with Bicep support
pip install -e ".[bicep]"

# Verify installation
specify --version
specify --help

# For GitHub Copilot integration, copy the prompt file to your project:
# Windows
New-Item -ItemType Directory -Force -Path ".github\prompts"
Copy-Item ".github\prompts\speckit.bicep.prompt.md" -Destination ".github\prompts\"

# Linux/macOS
mkdir -p .github/prompts
cp .github/prompts/speckit.bicep.prompt.md .github/prompts/
```

**Option B: Install from PyPI (Once Published)**

```powershell
# Install the CLI with Bicep feature
pip install specify-cli[bicep]

# Verify installation
specify --version
```

### Step 2: Verify Bicep Command is Available

```powershell
# Check that bicep command appears
specify --help

# Should show:
# Commands:
#   init    Initialize a new Specify project
#   check   Check that all required tools are installed
#   bicep   Generate Bicep templates for Azure resource deployment
```

### Step 3: Test with Help

```powershell
specify bicep --help

# Output:
# Usage: specify bicep [OPTIONS] [PROJECT_PATH]
# 
# Generate Bicep templates for Azure resource deployment.
# Analyzes your project to detect Azure dependencies...
```

---

## Using the Bicep Command

### Basic Usage

```powershell
# Analyze current directory
specify bicep --analyze-only

# Analyze specific project
specify bicep /path/to/your/project --analyze-only

# Run full analysis (shows next steps)
specify bicep
```

### Command Options

| Option | Description |
|--------|-------------|
| `[PROJECT_PATH]` | Path to analyze (default: current directory) |
| `--analyze-only` | Only show detected resources, don't generate templates |
| `--verbose` `-v` | Show detailed configuration values |
| `--output` `-o` | Output directory for templates (future use) |
| `--help` | Show command help |

---

## Quick Start Example

### Example 1: Analyze a Python Flask Project

```powershell
# Navigate to your project
cd C:\Projects\my-flask-app

# Analyze the project
specify bicep --analyze-only
```

**Expected Output:**
```
🏗️  Bicep Template Generator

📂 Analyzing project: C:\Projects\my-flask-app

📋 Analysis Results:

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Resource Type        ┃ Suggested Na ┃ Confidence ┃ Evidence           ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Azure App Service    │ myapp        │    95%     │ Detected Flask...  │
│ Azure Storage Account│ storage      │    90%     │ Found azure-stor...│
└──────────────────────┴──────────────┴────────────┴────────────────────┘

✅ Detected 2 Azure resource(s)
```

### Example 2: Analyze a Node.js Project

```powershell
# Your Node.js project with Azure SDKs
cd C:\Projects\my-node-api

# Analyze dependencies
specify bicep --analyze-only --verbose
```

---

## What the Command Detects

### Supported Languages & Frameworks

**Python:**
- Flask, Django, FastAPI
- Detects from `requirements.txt`

**Node.js:**
- Express, Next.js, React, Angular, Vue
- Detects from `package.json`

**.NET:**
- ASP.NET Core
- Detects from `.csproj` files

### Azure Services Detected

The command automatically detects these Azure services based on your dependencies:

| Dependency | Detected Service |
|------------|------------------|
| `azure-storage-blob` | Azure Storage Account |
| `azure-keyvault-secrets` | Azure Key Vault |
| `psycopg2` / `psycopg2-binary` | Azure Database for PostgreSQL |
| `pymongo` | Azure Cosmos DB (MongoDB API) |
| `redis` | Azure Cache for Redis |
| `azure-servicebus` | Azure Service Bus |
| `azure-eventhub` | Azure Event Hubs |
| `azure-functions` | Azure Functions |
| Web frameworks (Flask, Express, etc.) | Azure App Service |

### Configuration Extraction

The command also reads your `.env` file to extract resource names:

```env
# .env file
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
AZURE_KEY_VAULT_NAME=mykeyvault
DATABASE_HOST=myserver.postgres.database.azure.com
REDIS_HOST=mycache.redis.cache.windows.net
```

These values are used to suggest resource names in the analysis.

---

## Complete Installation & Test Flow

### 1. Install

```powershell
# Option A: From source
git clone https://github.com/cristhianu/spec-kit-4applens.git
cd spec-kit-4applens
pip install -e ".[bicep]"

# Option B: From PyPI (future)
pip install specify-cli[bicep]
```

### 2. Verify

```powershell
# Check installation
specify --help

# Should see 'bicep' in the commands list
```

### 3. Test with Sample Project

```powershell
# Create a test project
mkdir C:\temp\test-azure-app
cd C:\temp\test-azure-app

# Create requirements.txt
@"
flask==3.0.0
azure-storage-blob==12.19.0
azure-keyvault-secrets==4.7.0
psycopg2-binary==2.9.9
"@ | Out-File -FilePath requirements.txt -Encoding utf8

# Create .env
@"
AZURE_STORAGE_ACCOUNT_NAME=teststorage
AZURE_KEY_VAULT_NAME=testvault
DATABASE_HOST=testdb.postgres.database.azure.com
"@ | Out-File -FilePath .env -Encoding utf8

# Run analysis
specify bicep --analyze-only
```

### 4. Expected Result

```
🏗️  Bicep Template Generator

📂 Analyzing project: C:\temp\test-azure-app

📋 Analysis Results:

[Table showing 5-6 detected Azure resources with 90-95% confidence]

✅ Detected X Azure resource(s)
```

---

## Troubleshooting

### Issue: `specify: command not found`

**Solution:**
```powershell
# Ensure Python Scripts are in PATH
python -m pip install --user specify-cli[bicep]

# Or use full path
python -m specify_cli bicep --analyze-only
```

### Issue: No resources detected

**Symptoms:**
```
⚠️  No Azure resources detected in the project.
```

**Solutions:**
1. **Add dependencies file:**
   - Python: Create `requirements.txt` with Azure SDK packages
   - Node.js: Add Azure SDKs to `package.json`

2. **Include Azure packages:**
   ```txt
   # requirements.txt
   azure-storage-blob==12.19.0
   azure-keyvault-secrets==4.7.0
   ```

3. **Add .env file:**
   ```env
   AZURE_STORAGE_ACCOUNT_NAME=myaccount
   ```

### Issue: Import errors when running

**Solution:**
```powershell
# Reinstall with dependencies
pip install -e ".[bicep]" --force-reinstall

# Or install missing dependencies
pip install pyyaml rich typer
```

---

## Using in CI/CD Pipeline

### GitHub Actions

```yaml
name: Analyze Azure Resources

on: [push]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Specify CLI
        run: pip install specify-cli[bicep]
      
      - name: Analyze project
        run: specify bicep --analyze-only
```

### Azure DevOps

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    pip install specify-cli[bicep]
    specify bicep --analyze-only
  displayName: 'Analyze Azure Resources'
```

---

## Next Steps After Analysis

Once you've analyzed your project:

1. **Review the detected resources** - Check if the analysis matches your expectations

2. **Manually create Bicep templates** - Use the detected resources as a guide

3. **Wait for template generation** - Full template generation is coming in the next release

4. **Use the Python API** - For advanced use cases, import the modules directly:
   ```python
   from specify_cli.bicep.cli_simple import SimpleBicepAnalyzer
   
   analyzer = SimpleBicepAnalyzer(Path("my-project"))
   resources, config = analyzer.analyze()
   ```

---

## Uninstall

```powershell
# Remove Specify CLI
pip uninstall specify-cli

# Remove all dependencies (optional)
pip uninstall -y typer rich pyyaml platformdirs readchar httpx
```

---

## Getting Help

- **Documentation**: `docs/bicep-generator/` in the repository
- **Issues**: https://github.com/cristhianu/spec-kit-4applens/issues
- **Command help**: `specify bicep --help`
- **CLI help**: `specify --help`

---

## Version Information

- **Specify CLI**: v0.0.21
- **Bicep Generator**: Phase 6 Complete (Analysis Feature)
- **Python Required**: 3.11+
- **Status**: Analysis fully working, template generation in progress

---

**Last Updated:** October 22, 2025
