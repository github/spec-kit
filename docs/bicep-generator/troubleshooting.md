# Bicep Generator - Troubleshooting Guide

## Table of Contents

- [Common Issues](#common-issues)
- [Analysis Issues](#analysis-issues)
- [Generation Issues](#generation-issues)
- [Validation Issues](#validation-issues)
- [Deployment Issues](#deployment-issues)
- [Performance Issues](#performance-issues)
- [Security Issues](#security-issues)
- [Debugging Tips](#debugging-tips)

## Common Issues

### Issue: Command Not Found

**Symptoms:**
```
'specify' is not recognized as an internal or external command
```

**Solution:**

1. Verify installation:
```bash
pip show specify-cli
```

2. Check Python PATH:
```bash
# Windows PowerShell
$env:PATH -split ';' | Select-String python

# Bash/Linux
echo $PATH | tr ':' '\n' | grep python
```

3. Reinstall if needed:
```bash
pip uninstall specify-cli
pip install specify-cli
```

---

### Issue: Azure CLI Not Authenticated

**Symptoms:**
```
ERROR: Azure CLI authentication required
Please run: az login
```

**Solution:**

```bash
# Interactive login
az login

# Service principal login
az login --service-principal \
  --username <app-id> \
  --password <password-or-cert> \
  --tenant <tenant-id>

# Managed identity login (on Azure VM)
az login --identity

# Verify authentication
az account show
```

---

### Issue: Missing Dependencies

**Symptoms:**
```
ModuleNotFoundError: No module named 'azure.identity'
```

**Solution:**

```bash
# Install all dependencies
pip install specify-cli[all]

# Or install specific dependencies
pip install azure-identity azure-mgmt-resource rich typer
```

---

## Analysis Issues

### Issue: No Dependencies Detected

**Symptoms:**
```
WARNING: No Azure dependencies detected in project
Analysis complete but no resources identified
```

**Diagnosis:**

```bash
# Run with verbose output
specify bicep analyze --project-path . --verbose

# Check what files are being analyzed
specify bicep analyze --project-path . --dry-run
```

**Solutions:**

1. **Ensure configuration files are present:**
   - `appsettings.json` (for .NET)
   - `requirements.txt` or `setup.py` (for Python)
   - `package.json` (for Node.js)

2. **Add explicit hints in configuration:**
```json
// bicep_config.json
{
  "hints": {
    "services": ["storage", "webapp", "keyvault"]
  }
}
```

3. **Check file patterns:**
```bash
# Include specific files
specify bicep analyze \
  --include "**/*.config" \
  --include "**/*.json"
```

---

### Issue: Analysis Timeout

**Symptoms:**
```
ERROR: Analysis timed out after 300 seconds
```

**Solution:**

```bash
# Increase timeout
specify bicep analyze \
  --timeout 600 \
  --project-path ./large-project

# Exclude large directories
specify bicep analyze \
  --exclude "**/node_modules/**" \
  --exclude "**/bin/**" \
  --exclude "**/obj/**"

# Use incremental analysis
specify bicep analyze \
  --incremental \
  --cache-dir ./.bicep-cache
```

---

### Issue: Permission Denied Reading Files

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: './file.txt'
```

**Solution:**

```bash
# Windows: Run as administrator
# or adjust file permissions

# Linux/macOS: Fix permissions
chmod -R +r ./project-directory

# Skip inaccessible files
specify bicep analyze \
  --skip-permission-errors \
  --project-path .
```

---

## Generation Issues

### Issue: Template Generation Fails

**Symptoms:**
```
ERROR: Failed to generate template for resource 'storageAccount'
```

**Diagnosis:**

```bash
# Enable debug logging
specify bicep generate \
  --debug \
  --log-file bicep-debug.log

# Validate analysis file
specify bicep validate-analysis \
  --analysis-file ./analysis/project-analysis.json
```

**Solutions:**

1. **Check analysis file integrity:**
```bash
# Verify JSON structure
cat ./analysis/project-analysis.json | python -m json.tool
```

2. **Use fallback templates:**
```bash
specify bicep generate \
  --fallback-on-errors \
  --analysis-file ./analysis/project-analysis.json
```

3. **Generate incrementally:**
```bash
# Generate one resource type at a time
specify bicep generate \
  --resource-types storage \
  --output-dir ./bicep-templates/storage

specify bicep generate \
  --resource-types compute \
  --output-dir ./bicep-templates/compute
```

---

### Issue: Invalid Bicep Syntax Generated

**Symptoms:**
```
Error BCP057: The name "resourceName" does not exist in the current context
```

**Solution:**

```bash
# Validate Bicep CLI version
bicep --version
# Ensure version >= 0.15.0

# Upgrade if needed
az bicep upgrade

# Regenerate with specific Bicep version
specify bicep generate \
  --bicep-version "0.30.0" \
  --analysis-file ./analysis/project-analysis.json

# Use compatibility mode
specify bicep generate \
  --compatibility-mode strict \
  --target-bicep-version "0.15.0"
```

---

### Issue: Missing Resource Dependencies

**Symptoms:**
```
ERROR: Resource 'webapp' depends on 'storageAccount' which was not generated
```

**Solution:**

```bash
# Force dependency resolution
specify bicep generate \
  --resolve-dependencies \
  --analysis-file ./analysis/project-analysis.json

# Manual dependency specification
specify bicep generate \
  --dependencies webapp:storageAccount,keyvault \
  --analysis-file ./analysis/project-analysis.json
```

---

## Validation Issues

### Issue: Bicep Validation Fails

**Symptoms:**
```
Error: Template validation failed with 3 errors
```

**Diagnosis:**

```bash
# Validate manually with Azure CLI
az deployment group validate \
  --resource-group my-rg \
  --template-file ./bicep-templates/main.bicep \
  --parameters @./parameters/dev.parameters.json

# Use bicep CLI directly
bicep build ./bicep-templates/main.bicep
```

**Solutions:**

1. **Check parameter types:**
```bicep
// Ensure parameter types match usage
param storageAccountName string // not object or array
param location string = resourceGroup().location
```

2. **Verify resource API versions:**
```bash
# Check available API versions
az provider show \
  --namespace Microsoft.Storage \
  --query "resourceTypes[?resourceType=='storageAccounts'].apiVersions"
```

3. **Fix circular dependencies:**
```bicep
// Avoid:
// resourceA depends on resourceB
// resourceB depends on resourceA

// Use explicit dependencies instead
resource resourceB 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'storage'
  // ...
}

resource resourceA 'Microsoft.Web/sites@2023-01-01' = {
  name: 'webapp'
  dependsOn: [resourceB]
  // ...
}
```

---

### Issue: Schema Validation Errors

**Symptoms:**
```
ERROR: Schema validation failed: 'sku' is a required property
```

**Solution:**

```bash
# Regenerate with schema validation
specify bicep generate \
  --validate-schema \
  --analysis-file ./analysis/project-analysis.json

# Get latest schemas
specify bicep update-schemas \
  --force

# Use specific API version
specify bicep generate \
  --api-version "2023-01-01" \
  --resource-type "Microsoft.Storage/storageAccounts"
```

---

## Deployment Issues

### Issue: Deployment Fails with Permission Error

**Symptoms:**
```
ERROR: The client '...' does not have authorization to perform action
'Microsoft.Resources/deployments/write'
```

**Solution:**

```bash
# Check current permissions
az role assignment list \
  --assignee $(az account show --query user.name -o tsv) \
  --resource-group my-rg

# Required roles for deployment:
# - Contributor (for resource creation)
# - User Access Administrator (for RBAC assignments)

# Request access from subscription administrator
# Or use service principal with proper permissions
```

---

### Issue: Resource Already Exists

**Symptoms:**
```
ERROR: Resource 'storageaccount123' already exists in resource group
```

**Solutions:**

1. **Use incremental deployment mode:**
```bash
specify bicep deploy \
  --mode incremental \
  --template-dir ./bicep-templates \
  --resource-group my-rg
```

2. **Update existing resources:**
```bash
specify bicep update \
  --template-dir ./bicep-templates \
  --resource-group my-rg \
  --merge-existing
```

3. **Delete and recreate (CAUTION!):**
```bash
# DANGER: This will delete data!
az group delete --name my-rg --yes
az group create --name my-rg --location eastus

specify bicep deploy \
  --template-dir ./bicep-templates \
  --resource-group my-rg
```

---

### Issue: Deployment Timeout

**Symptoms:**
```
ERROR: Deployment timed out waiting for resources to provision
```

**Solution:**

```bash
# Increase deployment timeout
specify bicep deploy \
  --timeout 1800 \
  --template-dir ./bicep-templates \
  --resource-group my-rg

# Deploy in stages
specify bicep deploy \
  --stage infrastructure \
  --template-dir ./bicep-templates \
  --resource-group my-rg

specify bicep deploy \
  --stage applications \
  --template-dir ./bicep-templates \
  --resource-group my-rg \
  --wait-for infrastructure
```

---

## Performance Issues

### Issue: Slow Analysis

**Symptoms:**
- Analysis takes > 5 minutes for small projects

**Solutions:**

```bash
# Enable caching
specify bicep analyze \
  --enable-cache \
  --cache-dir ./.bicep-cache \
  --project-path .

# Exclude large directories
specify bicep analyze \
  --exclude "**/node_modules/**" \
  --exclude "**/.git/**" \
  --exclude "**/venv/**"

# Use parallel processing
specify bicep analyze \
  --parallel \
  --workers 4 \
  --project-path .
```

---

### Issue: High Memory Usage

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

```bash
# Reduce batch size
specify bicep analyze \
  --batch-size 100 \
  --project-path ./large-project

# Stream processing mode
specify bicep analyze \
  --streaming \
  --project-path ./large-project

# Clear cache
specify bicep clear-cache --all
```

---

### Issue: Cache Issues

**Symptoms:**
- Stale analysis results
- Incorrect resource detection

**Solution:**

```bash
# Clear cache
specify bicep clear-cache --all

# Disable cache temporarily
specify bicep analyze \
  --no-cache \
  --project-path .

# Rebuild cache
specify bicep rebuild-cache \
  --project-path .
```

---

## Security Issues

### Issue: Credential Exposure Warning

**Symptoms:**
```
WARNING: Potential credential found in analysis
File: config.json, Line: 42
```

**Solution:**

```bash
# Scan for credentials
specify bicep security-scan \
  --project-path . \
  --fix-credentials

# Use Azure Key Vault
specify bicep generate \
  --use-keyvault \
  --keyvault-name my-keyvault \
  --analysis-file ./analysis/project-analysis.json

# Exclude sensitive files from analysis
specify bicep analyze \
  --exclude "**/*.secret" \
  --exclude "**/credentials.json" \
  --project-path .
```

---

### Issue: Insecure Template Generated

**Symptoms:**
```
WARNING: Template contains security issues:
- Public access enabled on storage account
- HTTPS not enforced
```

**Solution:**

```bash
# Enable security hardening
specify bicep generate \
  --security-level high \
  --analysis-file ./analysis/project-analysis.json

# Fix security issues
specify bicep security \
  --template-dir ./bicep-templates \
  --auto-fix \
  --severity high,critical

# Generate with compliance framework
specify bicep generate \
  --compliance CIS-Azure-v1.4.0 \
  --analysis-file ./analysis/project-analysis.json
```

---

## Debugging Tips

### Enable Verbose Logging

```bash
# Maximum verbosity
specify bicep analyze \
  --verbose \
  --debug \
  --log-file debug.log \
  --project-path .

# View logs in real-time
tail -f debug.log
```

### Use Dry Run Mode

```bash
# Preview operations without executing
specify bicep generate \
  --dry-run \
  --analysis-file ./analysis/project-analysis.json

specify bicep deploy \
  --dry-run \
  --template-dir ./bicep-templates \
  --resource-group my-rg
```

### Check System Requirements

```bash
# Run diagnostic check
specify bicep check-requirements

# Test Azure connectivity
specify bicep test-connection \
  --subscription-id xxx-xxx-xxx
```

### Validate Configuration

```bash
# Validate configuration file
specify bicep validate-config \
  --config-file bicep_config.json

# Show effective configuration
specify bicep show-config \
  --merged
```

### Export Diagnostic Information

```bash
# Generate diagnostic report
specify bicep diagnostics \
  --output diagnostic-report.json

# Include in bug reports
cat diagnostic-report.json
```

## Getting Help

If you're still experiencing issues:

1. **Check GitHub Issues**: [spec-kit-4applens/issues](https://github.com/cristhianu/spec-kit-4applens/issues)

2. **Search Documentation**: [Full Documentation](./README.md)

3. **Enable Debug Mode**: Include `--debug --verbose` output in bug reports

4. **Provide Context**:
   - Operating System
   - Python version
   - Azure CLI version
   - Bicep CLI version
   - Full error message
   - Steps to reproduce

5. **Create Minimal Reproduction**: Simplify to smallest case that reproduces the issue

## Additional Resources

- [User Guide](./user-guide.md)
- [API Reference](./api-reference.md)
- [Architecture Guide](./architecture.md)
- [Azure Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
