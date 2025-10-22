// Storage Account Bicep Module
// Reusable module for creating Azure Storage Accounts with best practices

@description('Storage account name (must be globally unique)')
param storageAccountName string

@description('Location for the storage account')
param location string = resourceGroup().location

@description('Storage account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_RAGRS', 'Standard_ZRS', 'Premium_LRS'])
param sku string = 'Standard_LRS'

@description('Storage account kind')
@allowed(['StorageV2', 'BlobStorage'])
param kind string = 'StorageV2'

@description('Access tier for blob storage')
@allowed(['Hot', 'Cool'])
param accessTier string = 'Hot'

@description('Enable hierarchical namespace (for Data Lake Gen2)')
param enableHierarchicalNamespace bool = false

@description('Allow blob public access')
param allowBlobPublicAccess bool = false

@description('Minimum TLS version')
@allowed(['TLS1_0', 'TLS1_1', 'TLS1_2'])
param minimumTlsVersion string = 'TLS1_2'

@description('Tags for the storage account')
param tags object = {}

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: kind
  properties: {
    accessTier: accessTier
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: minimumTlsVersion
    allowBlobPublicAccess: allowBlobPublicAccess
    allowSharedKeyAccess: true
    isHnsEnabled: enableHierarchicalNamespace
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

// Blob Service (with versioning and soft delete)
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: true
    changeFeed: {
      enabled: true
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// File Service
resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
  properties: {
    shareDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// Default containers
resource containerWeb 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: 'web'
  parent: blobServices
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'Web application assets'
    }
  }
}

resource containerData 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: 'data'
  parent: blobServices
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'Application data storage'
    }
  }
}

resource containerBackups 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: 'backups'
  parent: blobServices
  properties: {
    publicAccess: 'None'
    metadata: {
      purpose: 'Backup storage'
    }
  }
}

// Outputs
@description('Storage account resource ID')
output storageAccountId string = storageAccount.id

@description('Storage account name')
output storageAccountName string = storageAccount.name

@description('Primary blob endpoint')
output primaryBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('Primary file endpoint')
output primaryFileEndpoint string = storageAccount.properties.primaryEndpoints.file

@description('Primary web endpoint')
output primaryWebEndpoint string = storageAccount.properties.primaryEndpoints.web

@description('Storage account access keys (use with caution)')
output storageAccountKeys object = {
  key1: storageAccount.listKeys().keys[0].value
  key2: storageAccount.listKeys().keys[1].value
}
