# Bicep Generator - User Guide

## Overview

The Bicep Generator is a comprehensive tool for automatically generating Azure Bicep templates from your project analysis. It analyzes your codebase, detects Azure service dependencies, and creates production-ready infrastructure-as-code templates.

## Table of Contents

- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Usage Examples](#usage-examples)
- [Commands Reference](#commands-reference)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.11 or later
- Azure CLI (`az`)
- Bicep CLI (`bicep`)
- PowerShell 7.x or Bash (for scripts)

### Installation

```bash
# Install the Specify CLI with Bicep generator
pip install specify-cli

# Verify installation
specify --version
```

### Quick Start

Generate Bicep templates for your project in three simple steps:

```bash
# 1. Analyze your project
specify bicep analyze --project-path ./my-project

# 2. Generate templates
specify bicep generate --output-dir ./bicep-templates

# 3. Validate templates
specify bicep validate --template-dir ./bicep-templates
```

## Core Concepts

### Project Analysis

The Bicep Generator analyzes your project to detect:

- **Azure Service Dependencies**: Identifies required Azure resources (Storage, Web Apps, Key Vault, etc.)
- **Configuration Requirements**: Detects settings, connection strings, and secrets
- **Resource Relationships**: Maps dependencies between resources
- **Security Requirements**: Identifies authentication and authorization needs

### Template Generation

Templates are generated with:

- **Parameterization**: Environment-specific values as parameters
- **Best Practices**: Azure Well-Architected Framework compliance
- **Security**: Secure defaults (HTTPS only, TLS 1.2+, etc.)
- **Modularity**: Organized by resource type for maintainability

### Architecture Patterns

The generator supports multiple architecture patterns:

1. **Basic Web App**: App Service + Storage + Key Vault
2. **Microservices**: Container Instances + Container Registry + Networking
3. **Data Platform**: SQL Database + Cosmos DB + Data Lake
4. **Serverless**: Functions + Event Grid + Service Bus
5. **Custom**: Mix and match resources as needed

## Usage Examples

### Example 1: Web Application

Generate infrastructure for a typical web application:

```bash
# Analyze .NET web project
specify bicep analyze \
  --project-path ./MyWebApp \
  --output-dir ./analysis

# Generate templates
specify bicep generate \
  --analysis-file ./analysis/project-analysis.json \
  --output-dir ./bicep-templates \
  --environment production \
  --region eastus

# Deploy to Azure
specify bicep deploy \
  --template-dir ./bicep-templates \
  --resource-group my-rg \
  --subscription-id xxx-xxx-xxx
```

### Example 2: Container-Based Application

Generate infrastructure for containerized applications:

```bash
# Analyze project with container dependencies
specify bicep analyze \
  --project-path ./MyContainerApp \
  --detect-containers

# Generate with container infrastructure
specify bicep generate \
  --analysis-file ./analysis/project-analysis.json \
  --include-aci \
  --include-acr \
  --output-dir ./bicep-templates

# Review generated templates
specify bicep review \
  --template-dir ./bicep-templates \
  --check-security \
  --check-cost
```

### Example 3: Update Existing Templates

Update templates when your project changes:

```bash
# Analyze changes since last generation
specify bicep analyze \
  --project-path ./MyApp \
  --compare-to ./analysis/previous-analysis.json

# Update only affected templates
specify bicep update \
  --template-dir ./bicep-templates \
  --changes-file ./analysis/changes.json \
  --backup

# Sync across environments
specify bicep sync \
  --template-dir ./bicep-templates \
  --environments dev,staging,production
```

### Example 4: Cost Optimization

Analyze and optimize deployment costs:

```bash
# Estimate costs
specify bicep estimate-cost \
  --template-dir ./bicep-templates \
  --region eastus \
  --environment production

# Get optimization recommendations
specify bicep review \
  --template-dir ./bicep-templates \
  --check-cost \
  --suggest-optimizations

# Apply optimizations
specify bicep optimize \
  --template-dir ./bicep-templates \
  --strategy cost-optimized \
  --output-dir ./bicep-templates-optimized
```

### Example 5: Security Review

Perform comprehensive security analysis:

```bash
# Security scan
specify bicep security \
  --template-dir ./bicep-templates \
  --compliance-frameworks CIS,SOC2,HIPAA

# Generate security report
specify bicep security \
  --template-dir ./bicep-templates \
  --output-format html \
  --output-file security-report.html

# Fix security issues
specify bicep security \
  --template-dir ./bicep-templates \
  --auto-fix \
  --severity high,critical
```

## Commands Reference

### `analyze`

Analyze project for Azure resource requirements.

**Syntax:**
```bash
specify bicep analyze [OPTIONS]
```

**Options:**
- `--project-path PATH` - Path to project directory (default: current directory)
- `--output-dir PATH` - Output directory for analysis (default: ./bicep-analysis)
- `--detect-containers` - Enable container detection
- `--detect-databases` - Enable database detection
- `--exclude PATTERNS` - Exclude files/directories (glob patterns)
- `--config-file PATH` - Configuration file path

**Example:**
```bash
specify bicep analyze --project-path ./myapp --detect-containers
```

---

### `generate`

Generate Bicep templates from analysis.

**Syntax:**
```bash
specify bicep generate [OPTIONS]
```

**Options:**
- `--analysis-file PATH` - Analysis file path
- `--output-dir PATH` - Output directory for templates (default: ./bicep-templates)
- `--region REGION` - Target Azure region (default: eastus)
- `--environment ENV` - Target environment (dev/staging/production)
- `--template-style STYLE` - Template organization (modular/monolithic)
- `--include-monitoring` - Include monitoring resources

**Example:**
```bash
specify bicep generate --environment production --region westus2
```

---

### `validate`

Validate generated Bicep templates.

**Syntax:**
```bash
specify bicep validate [OPTIONS]
```

**Options:**
- `--template-dir PATH` - Template directory path
- `--subscription-id ID` - Azure subscription ID for validation
- `--resource-group NAME` - Resource group for deployment validation
- `--strict` - Enable strict validation mode

**Example:**
```bash
specify bicep validate --template-dir ./bicep-templates --strict
```

---

### `deploy`

Deploy Bicep templates to Azure.

**Syntax:**
```bash
specify bicep deploy [OPTIONS]
```

**Options:**
- `--template-dir PATH` - Template directory path
- `--resource-group NAME` - Target resource group
- `--subscription-id ID` - Azure subscription ID
- `--parameters-file PATH` - Parameters file path
- `--dry-run` - Simulate deployment without applying changes
- `--wait` - Wait for deployment completion

**Example:**
```bash
specify bicep deploy --resource-group my-rg --dry-run
```

---

### `update`

Update existing templates with project changes.

**Syntax:**
```bash
specify bicep update [OPTIONS]
```

**Options:**
- `--template-dir PATH` - Template directory path
- `--changes-file PATH` - Changes analysis file
- `--backup` - Create backup before updating
- `--preview` - Show changes without applying

**Example:**
```bash
specify bicep update --template-dir ./bicep-templates --backup
```

---

### `review`

Review architecture and get recommendations.

**Syntax:**
```bash
specify bicep review [OPTIONS]
```

**Options:**
- `--template-dir PATH` - Template directory path
- `--check-security` - Include security analysis
- `--check-cost` - Include cost analysis
- `--check-performance` - Include performance analysis
- `--suggest-optimizations` - Generate optimization recommendations

**Example:**
```bash
specify bicep review --check-security --check-cost
```

---

### `estimate-cost`

Estimate deployment costs.

**Syntax:**
```bash
specify bicep estimate-cost [OPTIONS]
```

**Options:**
- `--template-dir PATH` - Template directory path
- `--region REGION` - Target Azure region
- `--environment ENV` - Target environment
- `--billing-period PERIOD` - Billing period (monthly/annually)

**Example:**
```bash
specify bicep estimate-cost --region eastus --billing-period monthly
```

---

### `security`

Perform security analysis and compliance checks.

**Syntax:**
```bash
specify bicep security [OPTIONS]
```

**Options:**
- `--template-dir PATH` - Template directory path
- `--compliance-frameworks LIST` - Compliance frameworks (CIS,SOC2,HIPAA,etc.)
- `--output-format FORMAT` - Output format (text/json/html)
- `--auto-fix` - Automatically fix security issues
- `--severity LEVELS` - Filter by severity (low/medium/high/critical)

**Example:**
```bash
specify bicep security --compliance-frameworks CIS,SOC2 --auto-fix
```

---

### `explain`

Get explanations of template components.

**Syntax:**
```bash
specify bicep explain [OPTIONS]
```

**Options:**
- `--template-file PATH` - Template file to explain
- `--resource NAME` - Specific resource to explain
- `--detail-level LEVEL` - Detail level (basic/intermediate/advanced)
- `--output-format FORMAT` - Output format (text/markdown/html)

**Example:**
```bash
specify bicep explain --template-file main.bicep --detail-level intermediate
```

## Configuration

### Configuration File

Create `bicep_config.json` in your project root:

```json
{
  "project": {
    "name": "my-application",
    "type": "web",
    "language": "python"
  },
  "azure": {
    "subscription_id": "xxx-xxx-xxx",
    "default_region": "eastus",
    "resource_group_prefix": "rg-myapp"
  },
  "templates": {
    "style": "modular",
    "naming_convention": "azure-recommended",
    "include_monitoring": true,
    "include_networking": true
  },
  "security": {
    "enable_rbac": true,
    "enable_private_endpoints": true,
    "minimum_tls_version": "1.2",
    "require_https": true
  },
  "cost_optimization": {
    "strategy": "balanced",
    "reserved_instances": false,
    "autoscaling": true
  }
}
```

### Environment Variables

Configure using environment variables:

```bash
# Azure Configuration
export AZURE_SUBSCRIPTION_ID="xxx-xxx-xxx"
export AZURE_TENANT_ID="xxx-xxx-xxx"
export AZURE_DEFAULT_REGION="eastus"

# Bicep Generator Settings
export BICEP_TEMPLATE_STYLE="modular"
export BICEP_OUTPUT_DIR="./bicep-templates"
export BICEP_ENABLE_CACHING="true"

# Security Settings
export BICEP_REQUIRE_HTTPS="true"
export BICEP_MIN_TLS_VERSION="1.2"
```

## Best Practices

### 1. Version Control

Always version control your generated templates:

```bash
# Add to .gitignore
echo "bicep-analysis/" >> .gitignore

# Commit templates
git add bicep-templates/
git commit -m "Add Bicep infrastructure templates"
```

### 2. Environment Separation

Use separate parameter files for each environment:

```
bicep-templates/
├── main.bicep
├── parameters/
│   ├── dev.parameters.json
│   ├── staging.parameters.json
│   └── production.parameters.json
```

### 3. Modular Design

Organize templates by resource type:

```
bicep-templates/
├── main.bicep
├── modules/
│   ├── compute/
│   │   ├── app-service.bicep
│   │   └── container-instances.bicep
│   ├── storage/
│   │   └── storage-account.bicep
│   └── security/
│       └── key-vault.bicep
```

### 4. Security First

Always review security settings before deployment:

```bash
# Run security scan
specify bicep security --template-dir ./bicep-templates

# Fix critical issues
specify bicep security --auto-fix --severity critical,high
```

### 5. Cost Management

Estimate costs before deploying to production:

```bash
# Get cost estimate
specify bicep estimate-cost \
  --environment production \
  --billing-period monthly

# Get optimization suggestions
specify bicep review --check-cost --suggest-optimizations
```

### 6. Incremental Updates

Use the update command instead of regenerating from scratch:

```bash
# Update only what changed
specify bicep update \
  --template-dir ./bicep-templates \
  --backup \
  --preview
```

### 7. Documentation

Document your infrastructure decisions:

```bash
# Generate architecture documentation
specify bicep explain \
  --template-file main.bicep \
  --output-format markdown \
  --output-file docs/architecture.md
```

## Troubleshooting

See [Troubleshooting Guide](./troubleshooting.md) for detailed solutions to common issues.

### Quick Fixes

**Issue: Analysis fails with "No dependencies detected"**
```bash
# Solution: Ensure your project has recognizable patterns
specify bicep analyze --project-path . --verbose
```

**Issue: Templates fail validation**
```bash
# Solution: Check Bicep CLI version and update
bicep --version
az bicep upgrade
```

**Issue: Deployment fails with permission errors**
```bash
# Solution: Check Azure RBAC permissions
az role assignment list --assignee $(az account show --query user.name -o tsv)
```

## Additional Resources

- [API Reference](./api-reference.md)
- [Architecture Guide](./architecture.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Azure Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)

## Support

For issues and questions:

- GitHub Issues: [spec-kit-4applens/issues](https://github.com/cristhianu/spec-kit-4applens/issues)
- Documentation: [Full Documentation](./README.md)
