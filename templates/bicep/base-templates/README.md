# Base Bicep Templates

This directory contains foundational Bicep templates and modules for common Azure deployment patterns.

## Templates

### Web Application Base Template (`webapp-base.bicep`)

A comprehensive template for deploying web applications to Azure, including:

- **App Service Plan** - Scalable hosting for web apps
- **Web App** - Main application hosting with system-assigned identity
- **Storage Account** - File and data storage with secure configuration
- **Key Vault** - Secure secrets and configuration management
- **Application Insights** - Application performance monitoring
- **Log Analytics Workspace** - Centralized logging

**Features:**
- RBAC permissions configured between services
- Security best practices applied (HTTPS-only, TLS 1.2, etc.)
- Monitoring and logging integrated
- Scalable across environments (dev/staging/prod)

**Usage:**
```bash
az deployment group create \
  --resource-group myapp-dev-rg \
  --template-file webapp-base.bicep \
  --parameters @webapp-base.bicepparam
```

### Storage Module (`storage-module.bicep`)

Reusable module for creating Azure Storage Accounts with enterprise-grade configuration:

- **Security**: HTTPS-only, TLS 1.2, restricted public access
- **Data Protection**: Soft delete, versioning, change feed
- **Organization**: Pre-configured containers for web, data, and backups
- **Compliance**: Encryption at rest, audit trails

### Key Vault Module (`keyvault-module.bicep`)

Secure secrets management module with:

- **Access Control**: RBAC-based permissions (recommended)
- **Security**: Soft delete, optional purge protection
- **Monitoring**: Diagnostic settings for audit logging
- **Flexibility**: Configurable network access policies

## Parameter Files

### `webapp-base.bicepparam`

Sample parameter file showing recommended values for different environments.

**Environment-specific deployment:**
```bash
# Development
az deployment group create --template-file webapp-base.bicep --parameters appName=myapp environment=dev location=eastus

# Production
az deployment group create --template-file webapp-base.bicep --parameters appName=myapp environment=prod location=westus2 appServicePlanSku=P1V2
```

## Usage Patterns

### 1. Direct Deployment
Deploy the base template directly for simple web applications:

```bicep
// Custom template using the base
module webApp 'base-templates/webapp-base.bicep' = {
  name: 'webAppDeployment'
  params: {
    appName: 'mycompany-api'
    environment: 'prod'
    location: 'eastus'
    appServicePlanSku: 'P1V2'
  }
}
```

### 2. Modular Composition
Use individual modules for custom architectures:

```bicep
// Custom composition
module storage 'base-templates/storage-module.bicep' = {
  name: 'storageDeployment'
  params: {
    storageAccountName: 'myappstorage'
    sku: 'Standard_GRS'
    location: location
  }
}

module keyVault 'base-templates/keyvault-module.bicep' = {
  name: 'keyVaultDeployment'
  params: {
    keyVaultName: 'myapp-keyvault'
    location: location
    enablePurgeProtection: true
  }
}
```

### 3. Environment Variations
Customize for different environments:

```bicep
// Environment-specific parameters
var environmentConfig = {
  dev: {
    appServicePlanSku: 'F1'
    storageAccountSku: 'Standard_LRS'
  }
  prod: {
    appServicePlanSku: 'P2V2'
    storageAccountSku: 'Standard_GRS'
  }
}
```

## Best Practices Applied

### Security
- ✅ HTTPS-only enforcement
- ✅ TLS 1.2 minimum version
- ✅ System-assigned managed identities
- ✅ RBAC-based access control
- ✅ No hardcoded secrets in templates
- ✅ Network access restrictions

### Reliability
- ✅ Soft delete protection
- ✅ Data versioning and retention
- ✅ Health monitoring integration
- ✅ Diagnostic logging enabled

### Cost Optimization
- ✅ Appropriate sizing for environments
- ✅ Resource tagging for cost tracking
- ✅ Auto-scaling capabilities
- ✅ Efficient resource allocation

### Operational Excellence
- ✅ Consistent naming conventions
- ✅ Comprehensive output values
- ✅ Modular and reusable design
- ✅ Environment-specific configurations

## Extension Points

These templates can be extended with additional resources:

- **Database**: Add SQL Database or Cosmos DB modules
- **CDN**: Include Azure Front Door or CDN profiles
- **Networking**: Add VNet, subnet, and NSG configurations
- **Security**: Include Security Center and threat protection
- **Backup**: Add backup and disaster recovery solutions

## Validation

Before deployment, validate templates using:

```bash
# Bicep validation
bicep build webapp-base.bicep

# ARM deployment validation
az deployment group validate \
  --resource-group myapp-dev-rg \
  --template-file webapp-base.bicep \
  --parameters @webapp-base.bicepparam

# What-if analysis
az deployment group what-if \
  --resource-group myapp-dev-rg \
  --template-file webapp-base.bicep \
  --parameters @webapp-base.bicepparam
```