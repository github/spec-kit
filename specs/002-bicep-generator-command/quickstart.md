# Quickstart Guide: Bicep Generator Command

**Feature**: 002-bicep-generator-command  
**Date**: 2025-10-21  
**Audience**: Developers using GitHub Copilot for Azure deployments

## Prerequisites

### Required Tools

- **GitHub Copilot**: Latest version with Specify CLI integration
- **Azure CLI**: Version 2.50.0 or later (`az --version`)
- **PowerShell**: 7.x recommended, 5.1 minimum on Windows
- **Bicep CLI**: Latest version (`bicep --version`)
- **Azure MCP Server**: Installed and configured

### Azure Authentication

Ensure you're authenticated with Azure using one of these methods:

```bash
# Option 1: Azure CLI (recommended)
az login

# Option 2: Azure PowerShell
Connect-AzAccount

# Option 3: Azure Developer CLI
azd auth login
```

Verify your authentication:
```bash
az account show
```

### MCP Server Setup

1. **Install Azure MCP Server** (if not already installed):
   ```bash
   npm install -g @azure/mcp-server
   ```

2. **Verify MCP Server availability**:
   ```bash
   azure-mcp-server --help
   ```

## Quick Start: Generate Templates for New Project

### Step 1: Navigate to Your Project

```bash
cd /path/to/your/azure-project
```

### Step 2: Run the Bicep Generator

In GitHub Copilot, use the slash command:

```
/bicep-generate
```

**Or with specific options**:
```
/bicep-generate --region "East US" --environments dev,prod --interactive
```

### Step 3: Answer Interactive Questions

The system will ask you questions about your deployment requirements:

1. **Environment Configuration**: Choose target environments (dev, staging, prod)
2. **Regional Deployment**: Select your primary Azure region
3. **Scale Requirements**: Specify expected usage scale
4. **Security Requirements**: Choose security feature level
5. **Cost Optimization**: Select cost vs. performance preference

### Step 4: Review Generated Templates

After generation, you'll find:

```text
bicep-templates/
├── compute/
│   └── app-service.bicep          # Your web application hosting
├── storage/
│   ├── storage-account.bicep      # Application data storage
│   └── key-vault.bicep           # Secrets management
├── parameters/
│   ├── dev.parameters.json        # Development environment settings
│   └── prod.parameters.json       # Production environment settings
└── architecture.md                # Generated documentation
```

### Step 5: Deploy Your Templates

```bash
# Deploy to development environment
az deployment group create \
  --resource-group myapp-dev-rg \
  --template-file bicep-templates/compute/app-service.bicep \
  --parameters @bicep-templates/parameters/dev.parameters.json

# Deploy to production environment  
az deployment group create \
  --resource-group myapp-prod-rg \
  --template-file bicep-templates/compute/app-service.bicep \
  --parameters @bicep-templates/parameters/prod.parameters.json
```

## Quick Start: Update Existing Templates

### When to Update

Run updates when you've made changes to your project that might affect infrastructure:

- Added new dependencies (databases, caches, external services)
- Changed application configuration
- Modified security requirements
- Updated scaling needs

### Step 1: Run the Update Command

```
/bicep-update
```

**Or with specific path**:
```
/bicep-update ./my-project --backup
```

### Step 2: Review Changes

The update process will:

1. **Analyze** what has changed since last generation
2. **Identify** templates that need updates
3. **Preserve** your custom modifications (marked with `// CUSTOM`)
4. **Create backups** of existing templates
5. **Generate** only the templates that need changes

### Step 3: Validate Updated Templates

```bash
# Validate all templates
az deployment group validate \
  --resource-group myapp-dev-rg \
  --template-file bicep-templates/compute/app-service.bicep \
  --parameters @bicep-templates/parameters/dev.parameters.json
```

## Common Project Patterns

### Web Application with Database

**Project indicators the system will detect**:
- `appsettings.json` with connection strings
- Entity Framework or database ORM references
- Web framework dependencies (ASP.NET, Express, Django)

**Generated templates**:
- `compute/app-service.bicep` for web hosting
- `storage/sql-database.bicep` for data storage
- `security/key-vault.bicep` for connection string storage

### Microservices Architecture

**Project indicators**:
- Multiple service directories
- Container configuration (Dockerfile, docker-compose.yml)
- Service discovery configuration
- API gateway configuration

**Generated templates**:
- `compute/container-apps.bicep` for microservice hosting
- `networking/application-gateway.bicep` for API gateway
- `storage/service-bus.bicep` for inter-service communication
- `monitoring/application-insights.bicep` for observability

### Static Website with API

**Project indicators**:
- Static website files (HTML, CSS, JS)
- Serverless function code
- CDN configuration
- Build/deployment scripts

**Generated templates**:
- `storage/static-website.bicep` for static content hosting
- `compute/function-app.bicep` for API backend
- `networking/cdn.bicep` for content delivery
- `security/managed-identity.bicep` for secure authentication

## Customization Guide

### Preserving Custom Changes

Mark your customizations with special comments to preserve them during updates:

```bicep
// CUSTOM: Custom security configuration for compliance
param allowedIpRanges array = [
  '10.0.0.0/8'
  '192.168.0.0/16'
]

// CUSTOM: Custom tags for billing tracking
param customTags object = {
  CostCenter: 'Engineering'
  Project: 'MyApp'
}

resource appService 'Microsoft.Web/sites@2023-01-01' = {
  name: appServiceName
  location: location
  // CUSTOM: Enhanced monitoring configuration
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    // Custom monitoring settings preserved
    siteConfig: {
      alwaysOn: true
      detailedErrorLoggingEnabled: true
    }
  }
  tags: union(defaultTags, customTags) // CUSTOM: Merge custom tags
}
```

### Environment-Specific Customization

Customize parameter files for each environment:

**dev.parameters.json**:
```json
{
  "parameters": {
    "appServicePlanSku": {
      "value": "B1"
    },
    "sqlDatabaseTier": {
      "value": "Basic"
    }
  }
}
```

**prod.parameters.json**:
```json
{
  "parameters": {
    "appServicePlanSku": {
      "value": "P2V2"
    },
    "sqlDatabaseTier": {
      "value": "Standard"
    }
  }
}
```

## Troubleshooting

### Common Issues

**Issue**: "Azure MCP Server not found"
```
Error: MCP server 'azure-mcp-server' not available
```

**Solution**: Install the Azure MCP Server:
```bash
npm install -g @azure/mcp-server
# Verify installation
azure-mcp-server --version
```

**Issue**: "Authentication failed"
```
Error: Unable to authenticate with Azure
```

**Solution**: Check your Azure authentication:
```bash
az account show
# If not authenticated:
az login
```

**Issue**: "Template validation failed"
```
Error: Template validation failed for Microsoft.Storage/storageAccounts
```

**Solution**: Check the validation details and update parameters:
```bash
# Validate specific template
bicep build bicep-templates/storage/storage-account.bicep
# Check parameter values
cat bicep-templates/parameters/dev.parameters.json
```

**Issue**: "No Azure services detected"
```
Warning: No Azure service dependencies found in project
```

**Solution**: Ensure your project has configuration files or add them:
- Add `appsettings.json` with Azure service references
- Include deployment scripts with Azure resource references
- Add documentation with architectural descriptions

### Getting Help

1. **Check the architecture documentation**: `bicep-templates/architecture.md`
2. **Review generated templates** for comments and explanations
3. **Use the verbose flag** for detailed generation logs: `/bicep-generate --verbose`
4. **Validate templates** before deployment using Azure CLI
5. **Check backup files** if updates don't work as expected: `bicep-templates/backups/`

## Next Steps

After generating your Bicep templates:

1. **Review the architecture documentation** to understand your infrastructure
2. **Test deployment** in a development environment first
3. **Set up CI/CD pipelines** using the generated templates
4. **Monitor your resources** using the suggested monitoring configuration
5. **Regularly update templates** as your application evolves

### Integration with Ev2 Deployment

The generated templates are designed to work with Ev2 deployment:

1. **Template Structure**: Organized for Ev2 service model requirements
2. **Parameter Files**: Environment-specific configurations
3. **Naming Conventions**: Follow Azure and Ev2 best practices
4. **Resource Organization**: Grouped by type for deployment orchestration

For Ev2 integration, use the generated templates as input to the next phase of your deployment pipeline configuration.

This quickstart guide will get you generating and deploying Azure infrastructure templates quickly and efficiently using the Bicep Generator Command.