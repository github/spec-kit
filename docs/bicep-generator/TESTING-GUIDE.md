# Bicep Generator - Testing Guide

## Quick Start: Test in an Existing Project

This guide walks you through testing the Bicep Generator command in a real project.

---

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.11+** installed
   ```powershell
   python --version  # Should show 3.11 or higher
   ```

2. **Azure CLI** installed
   ```powershell
   az --version
   ```

3. **Bicep CLI** installed
   ```powershell
   bicep --version
   ```

4. **An existing project** to test with (web app, Python API, Node.js app, etc.)

---

## Step 1: Install Specify CLI with Bicep Generator

### Option A: Install from Source (Development/Testing)

```powershell
# Clone or navigate to the spec-kit-4applens repository
cd c:\git\spec-kit-4applens

# Install in development mode with Bicep dependencies
pip install -e ".[bicep]"

# Verify installation
specify --version
```

### Option B: Install from PyPI (Once Published)

```powershell
# Install with Bicep Generator support
pip install specify-cli[bicep]

# Verify installation
specify --version
```

---

## Step 2: Navigate to Your Test Project

```powershell
# Example: Navigate to your existing project
cd C:\Projects\my-web-app

# Or create a simple test project
mkdir C:\temp\bicep-test-project
cd C:\temp\bicep-test-project
```

---

## Step 3: Create Sample Project Files (Optional)

If testing with a new/empty project, create some sample files:

### Example: Python Web App

```powershell
# Create a simple Python web app structure
New-Item -ItemType Directory -Path "app" -Force
New-Item -ItemType File -Path "requirements.txt" -Force
New-Item -ItemType File -Path "app.py" -Force
New-Item -ItemType File -Path ".env" -Force
```

**requirements.txt:**
```plaintext
flask==3.0.0
python-dotenv==1.0.0
azure-storage-blob==12.19.0
azure-identity==1.15.0
psycopg2-binary==2.9.9
```

**app.py:**
```python
from flask import Flask
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Azure!"

if __name__ == '__main__':
    app.run()
```

**.env:**
```plaintext
AZURE_STORAGE_ACCOUNT_NAME=mystorageaccount
AZURE_KEY_VAULT_NAME=mykeyvault
DATABASE_HOST=myserver.postgres.database.azure.com
DATABASE_NAME=mydb
```

---

## Step 4: Run Bicep Generator Analysis

### Basic Analysis (Dry Run)

```powershell
# Analyze the project and show what would be generated
specify bicep --analyze-only
```

**What this does:**
- Scans your project files
- Detects Azure resources needed
- Shows detection confidence scores
- **Does NOT generate any files**

**Expected output:**
```
🔍 Analyzing project at: C:\temp\bicep-test-project

📦 Detected Resources:
  - Azure App Service (Web App) - Confidence: 95%
  - Azure Storage Account (Blob) - Confidence: 90%
  - Azure Key Vault - Confidence: 85%
  - Azure Database for PostgreSQL - Confidence: 88%

📋 Configuration Extracted:
  - Storage Account: mystorageaccount
  - Key Vault: mykeyvault
  - Database: myserver/mydb

✅ Analysis complete. Run without --analyze-only to generate templates.
```

---

## Step 5: Generate Bicep Templates

### Generate All Templates (Default)

```powershell
# Generate Bicep templates in ./bicep directory
specify bicep
```

**What this creates:**
```
bicep/
├── main.bicep              # Main orchestrator
├── parameters.json         # Parameter values
├── modules/
│   ├── app-service.bicep   # Web app module
│   ├── storage.bicep       # Storage account module
│   ├── key-vault.bicep     # Key Vault module
│   └── postgres.bicep      # PostgreSQL database module
└── README.md               # Deployment instructions
```

### Generate to Custom Directory

```powershell
# Generate templates in a custom location
specify bicep --output infrastructure/azure
```

### Generate with Environment-Specific Parameters

```powershell
# Generate for development environment
specify bicep --environment dev

# Generate for production environment
specify bicep --environment prod
```

---

## Step 6: Review Generated Templates

### Examine the Main Template

```powershell
# Open the main orchestrator
code bicep/main.bicep
```

**Check for:**
- ✅ Correct resource types
- ✅ Proper dependencies between resources
- ✅ Parameter definitions
- ✅ Output values for connection strings

### Review Parameters File

```powershell
# Open parameters
code bicep/parameters.json
```

**Verify:**
- ✅ Resource names extracted from your project
- ✅ SKUs match your requirements
- ✅ Locations set correctly

### Check Modular Files

```powershell
# List all generated modules
Get-ChildItem bicep/modules/*.bicep
```

---

## Step 7: Validate Templates with Bicep CLI

### Syntax Validation

```powershell
# Navigate to bicep directory
cd bicep

# Validate main template
bicep build main.bicep

# Check for errors
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Template is valid!" -ForegroundColor Green
} else {
    Write-Host "❌ Template has errors" -ForegroundColor Red
}
```

### What-If Deployment (Preview Changes)

```powershell
# Login to Azure
az login

# Set your subscription
az account set --subscription "Your-Subscription-Name"

# Run what-if analysis
az deployment group what-if `
  --resource-group "rg-bicep-test" `
  --template-file main.bicep `
  --parameters parameters.json
```

**Expected output shows:**
- Resources that will be created (green +)
- Resources that will be modified (orange ~)
- Resources that will be deleted (red -)

---

## Step 8: Deploy to Azure (Optional)

### Create Resource Group

```powershell
# Create a test resource group
az group create `
  --name "rg-bicep-test" `
  --location "eastus"
```

### Deploy Templates

```powershell
# Deploy with verbose output
az deployment group create `
  --resource-group "rg-bicep-test" `
  --template-file main.bicep `
  --parameters parameters.json `
  --verbose
```

### Monitor Deployment

```powershell
# Watch deployment progress
az deployment group show `
  --resource-group "rg-bicep-test" `
  --name "main" `
  --query "properties.provisioningState"
```

---

## Step 9: Test Advanced Features

### Use MCP Integration for Schemas

```powershell
# Generate with real-time Azure schema validation
specify bicep --use-mcp
```

**Benefits:**
- Gets latest Azure resource schemas
- Validates against current API versions
- Ensures template compatibility

### Generate with Custom Naming Conventions

```powershell
# Apply custom prefix to all resources
specify bicep --prefix "myapp"

# Result: app-service-myapp, st-myapp, kv-myapp, etc.
```

### Generate with Tags

```powershell
# Add tags to all resources
specify bicep --tags "Environment=Dev,Project=BicepTest,Owner=YourName"
```

### Update Existing Templates

```powershell
# Update templates when project changes
specify bicep --update
```

**What this does:**
- Detects new dependencies
- Adds new resources to existing templates
- Preserves manual customizations in comments

---

## Step 10: Clean Up Test Resources

### Delete Resource Group

```powershell
# Delete all test resources
az group delete `
  --name "rg-bicep-test" `
  --yes `
  --no-wait
```

---

## Common Testing Scenarios

### Scenario 1: Web App + Storage + Key Vault

**Project Setup:**
```powershell
# requirements.txt or package.json with:
# - flask/express (web framework)
# - azure-storage-blob (storage SDK)
# - azure-keyvault-secrets (Key Vault SDK)
```

**Expected Resources:**
- App Service (Web App)
- App Service Plan
- Storage Account
- Key Vault

### Scenario 2: Python API + PostgreSQL + Redis

**Project Setup:**
```powershell
# requirements.txt with:
# - fastapi (API framework)
# - psycopg2 (PostgreSQL)
# - redis (caching)
```

**Expected Resources:**
- App Service (API)
- Azure Database for PostgreSQL
- Azure Cache for Redis

### Scenario 3: Container App + ACR + Cosmos DB

**Project Setup:**
```powershell
# Files:
# - Dockerfile
# - requirements.txt with azure-cosmos
```

**Expected Resources:**
- Azure Container Registry
- Container Apps Environment
- Container App
- Cosmos DB Account

---

## Troubleshooting

### Issue: No Resources Detected

**Symptoms:**
```
⚠️ No Azure resources detected in project
```

**Solutions:**
1. Ensure you have dependency files (requirements.txt, package.json, etc.)
2. Add Azure SDK imports to your code
3. Create .env file with Azure service names
4. Use `--force` flag to manually specify resources

### Issue: Confidence Scores Low

**Symptoms:**
```
📦 Detected Resources:
  - Azure Storage Account - Confidence: 45%
```

**Solutions:**
1. Add more explicit Azure SDK imports
2. Include connection strings in .env
3. Add comments referencing Azure services
4. Use `--resources` flag to specify explicitly

### Issue: Template Validation Fails

**Symptoms:**
```
❌ Template has errors
```

**Solutions:**
1. Check Bicep CLI version: `bicep --version`
2. Review error messages in output
3. Validate each module individually
4. Check parameter file for typos
5. Run: `specify bicep --validate-only`

### Issue: MCP Integration Fails

**Symptoms:**
```
⚠️ MCP Server not available, using cached schemas
```

**Solutions:**
1. Ensure Azure MCP server is running
2. Check VS Code extension installation
3. Verify Azure CLI is authenticated
4. Use `--skip-mcp` to disable MCP temporarily

---

## Testing Checklist

Before considering testing complete:

- [ ] Analysis detects all expected resources
- [ ] Confidence scores are above 70%
- [ ] Generated templates pass `bicep build` validation
- [ ] Parameters file contains correct values
- [ ] What-if deployment shows expected resources
- [ ] Manual review shows no security issues
- [ ] Templates follow Azure naming conventions
- [ ] Resource dependencies are correct
- [ ] Outputs include necessary connection strings
- [ ] Templates include proper tags
- [ ] Modular structure is logical and maintainable

---

## Next Steps

After successful testing:

1. **Integrate into CI/CD Pipeline**
   - Add `specify bicep` to build scripts
   - Automate template validation
   - Set up automated deployments

2. **Customize Templates**
   - Add project-specific configurations
   - Implement custom naming patterns
   - Add monitoring and diagnostics

3. **Share with Team**
   - Document project-specific conventions
   - Create environment-specific parameter files
   - Set up template repository

4. **Provide Feedback**
   - Report issues on GitHub
   - Suggest improvements
   - Share success stories

---

## Additional Resources

- **Documentation**: `docs/bicep-generator/`
- **Examples**: `docs/bicep-generator/examples/`
- **API Reference**: `docs/bicep-generator/API.md`
- **Troubleshooting**: `docs/bicep-generator/TROUBLESHOOTING.md`
- **GitHub Issues**: https://github.com/cristhianu/spec-kit-4applens/issues

---

**Happy Testing! 🚀**

*Last Updated: October 22, 2025*
