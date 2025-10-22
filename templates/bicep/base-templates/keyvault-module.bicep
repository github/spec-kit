// Key Vault Bicep Module
// Reusable module for creating Azure Key Vaults with best practices

@description('Key Vault name (must be globally unique)')
param keyVaultName string

@description('Location for the Key Vault')
param location string = resourceGroup().location

@description('SKU for the Key Vault')
@allowed(['standard', 'premium'])
param sku string = 'standard'

@description('Enable Key Vault for template deployment')
param enabledForTemplateDeployment bool = true

@description('Enable Key Vault for VM deployment')
param enabledForDeployment bool = false

@description('Enable Key Vault for disk encryption')
param enabledForDiskEncryption bool = false

@description('Enable RBAC authorization (recommended)')
param enableRbacAuthorization bool = true

@description('Soft delete retention period in days')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 7

@description('Enable purge protection')
param enablePurgeProtection bool = false

@description('Network access rules')
param networkAcls object = {
  defaultAction: 'Allow'
  bypass: 'AzureServices'
}

@description('Tags for the Key Vault')
param tags object = {}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: sku
    }
    tenantId: subscription().tenantId
    enabledForTemplateDeployment: enabledForTemplateDeployment
    enabledForDeployment: enabledForDeployment
    enabledForDiskEncryption: enabledForDiskEncryption
    enableRbacAuthorization: enableRbacAuthorization
    publicNetworkAccess: 'Enabled'
    networkAcls: networkAcls
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enableSoftDelete: true
    enablePurgeProtection: enablePurgeProtection
  }
}

// Diagnostic Settings (if Log Analytics workspace is available)
resource diagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (length(tags) > 0 && contains(tags, 'WorkspaceId')) {
  name: '${keyVaultName}-diagnostics'
  scope: keyVault
  properties: {
    workspaceId: contains(tags, 'WorkspaceId') ? tags.WorkspaceId : null
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 30
        }
      }
      {
        categoryGroup: 'allLogs'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 30
        }
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
        retentionPolicy: {
          enabled: true
          days: 30
        }
      }
    ]
  }
}

// Outputs
@description('Key Vault resource ID')
output keyVaultId string = keyVault.id

@description('Key Vault name')
output keyVaultName string = keyVault.name

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Key Vault tenant ID')
output tenantId string = keyVault.properties.tenantId
