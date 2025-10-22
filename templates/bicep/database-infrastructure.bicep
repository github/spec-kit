@description('Database infrastructure with Azure SQL Database and optional Cosmos DB')

@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string = 'database'

@description('SQL Administrator login name')
param sqlAdminUsername string = 'sqladmin'

@description('SQL Administrator password')
@secure()
param sqlAdminPassword string

@description('Database SKU')
@allowed(['Basic', 'S0', 'S1', 'S2', 'P1', 'P2', 'P4'])
param sqlDatabaseSku string = environment == 'prod' ? 'S2' : 'Basic'

@description('Enable Cosmos DB')
param enableCosmosDB bool = false

@description('Cosmos DB API type')
@allowed(['SQL', 'MongoDB', 'Cassandra', 'Gremlin', 'Table'])
param cosmosDbApiType string = 'SQL'

@description('Enable database backup retention')
param enableBackupRetention bool = true

@description('Enable Transparent Data Encryption')
param enableTDE bool = true

@description('Enable Advanced Data Security')
param enableAdvancedSecurity bool = environment == 'prod'

// Variables
var resourceSuffix = '${baseName}-${environment}'
var sqlServerName = 'sql-${resourceSuffix}'
var sqlDatabaseName = 'sqldb-${resourceSuffix}'
var cosmosAccountName = 'cosmos-${resourceSuffix}'
var cosmosDatabaseName = 'cosmosdb-${resourceSuffix}'
var keyVaultName = 'kv-${take(replace(resourceSuffix, '-', ''), 21)}${uniqueString(resourceGroup().id)}'
var logAnalyticsName = 'law-${resourceSuffix}'

// Key Vault for storing secrets
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: environment == 'prod' ? 90 : 7
    enableRbacAuthorization: true
    publicNetworkAccess: environment == 'prod' ? 'Disabled' : 'Enabled'
    networkAcls: environment == 'prod' ? {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    } : {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Store SQL admin password in Key Vault
resource sqlPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'sql-admin-password'
  properties: {
    value: sqlAdminPassword
    attributes: {
      enabled: true
    }
    contentType: 'text/plain'
  }
}

// Log Analytics for monitoring
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: environment == 'prod' ? 'PerGB2018' : 'Free'
    }
    retentionInDays: environment == 'prod' ? 90 : 30
  }
}

// SQL Server
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: sqlAdminUsername
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    publicNetworkAccess: environment == 'prod' ? 'Disabled' : 'Enabled'
    minimalTlsVersion: '1.2'
    restrictOutboundNetworkAccess: environment == 'prod' ? 'Enabled' : 'Disabled'
  }
  
  // Azure AD Administrator (placeholder - would need actual AD user/group)
  resource sqlServerADAdmin 'administrators@2023-05-01-preview' = if (environment == 'prod') {
    name: 'ActiveDirectory'
    properties: {
      administratorType: 'ActiveDirectory'
      login: 'sql-admins' // This should be replaced with actual AD group
      sid: '00000000-0000-0000-0000-000000000000' // This should be replaced with actual AD group SID
      tenantId: tenant().tenantId
    }
  }
  
  // Firewall rules for development
  resource allowAzureServices 'firewallRules@2023-05-01-preview' = if (environment != 'prod') {
    name: 'AllowAllWindowsAzureIps'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '0.0.0.0'
    }
  }
  
  // Security Alert Policy
  resource securityAlertPolicy 'securityAlertPolicies@2023-05-01-preview' = if (enableAdvancedSecurity) {
    name: 'default'
    properties: {
      state: 'Enabled'
      emailAddresses: []
      emailAccountAdmins: true
      retentionDays: 90
      storageEndpoint: ''
      storageAccountAccessKey: ''
    }
  }
  
  // Vulnerability Assessment
  resource vulnerabilityAssessment 'vulnerabilityAssessments@2023-05-01-preview' = if (enableAdvancedSecurity) {
    name: 'default'
    properties: {
      storageContainerPath: ''
      recurringScans: {
        isEnabled: true
        emailSubscriptionAdmins: true
        emails: []
      }
    }
    dependsOn: [
      securityAlertPolicy
    ]
  }
  
  // Auditing
  resource auditing 'auditingSettings@2023-05-01-preview' = {
    name: 'default'
    properties: {
      state: 'Enabled'
      isAzureMonitorTargetEnabled: true
      retentionDays: enableBackupRetention ? (environment == 'prod' ? 90 : 30) : 0
    }
  }
}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  sku: {
    name: sqlDatabaseSku
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: environment == 'prod' ? 268435456000 : 2147483648 // 250GB for prod, 2GB for dev/staging
    catalogCollation: 'SQL_Latin1_General_CP1_CI_AS'
    zoneRedundant: environment == 'prod'
    readScale: environment == 'prod' ? 'Enabled' : 'Disabled'
    requestedBackupStorageRedundancy: environment == 'prod' ? 'Geo' : 'Local'
  }
  
  // Transparent Data Encryption
  resource tde 'transparentDataEncryption@2023-05-01-preview' = if (enableTDE) {
    name: 'current'
    properties: {
      state: 'Enabled'
    }
  }
  
}

// Diagnostic Settings for SQL Database
resource sqlDatabaseDiagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
    name: 'sqldb-diagnostics'
    properties: {
      workspaceId: logAnalytics.id
      logs: [
        {
          categoryGroup: 'allLogs'
          enabled: true
          retentionPolicy: {
            enabled: enableBackupRetention
            days: environment == 'prod' ? 90 : 30
          }
        }
      ]
      metrics: [
        {
          category: 'AllMetrics'
          enabled: true
          retentionPolicy: {
            enabled: enableBackupRetention
            days: environment == 'prod' ? 90 : 30
          }
        }
      ]
    }
  }
}

// Cosmos DB Account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-09-15' = if (enableCosmosDB) {
  name: cosmosAccountName
  location: location
  kind: cosmosDbApiType == 'MongoDB' ? 'MongoDB' : 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: environment == 'prod' ? 'Session' : 'Eventual'
      maxIntervalInSeconds: 300
      maxStalenessPrefix: 100000
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: environment == 'prod'
      }
    ]
    capabilities: cosmosDbApiType == 'SQL' ? [] : [
      {
        name: cosmosDbApiType == 'MongoDB' ? 'EnableMongo' : 'Enable${cosmosDbApiType}'
      }
    ]
    enableAutomaticFailover: environment == 'prod'
    enableMultipleWriteLocations: false
    publicNetworkAccess: environment == 'prod' ? 'Disabled' : 'Enabled'
    networkAclBypass: 'AzureServices'
    disableKeyBasedMetadataWriteAccess: environment == 'prod'
    enableFreeTier: environment == 'dev'
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: environment == 'prod' ? 240 : 1440
        backupRetentionIntervalInHours: environment == 'prod' ? 720 : 168
        backupStorageRedundancy: environment == 'prod' ? 'Geo' : 'Local'
      }
    }
  }
  
  // Diagnostic Settings for Cosmos DB
  resource cosmosdiagnosticSettings 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
    name: 'cosmos-diagnostics'
    properties: {
      workspaceId: logAnalytics.id
      logs: [
        {
          categoryGroup: 'allLogs'
          enabled: true
          retentionPolicy: {
            enabled: enableBackupRetention
            days: environment == 'prod' ? 90 : 30
          }
        }
      ]
      metrics: [
        {
          category: 'AllMetrics'
          enabled: true
          retentionPolicy: {
            enabled: enableBackupRetention
            days: environment == 'prod' ? 90 : 30
          }
        }
      ]
    }
  }
}

// Cosmos Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-09-15' = if (enableCosmosDB && cosmosDbApiType == 'SQL') {
  parent: cosmosAccount
  name: cosmosDatabaseName
  properties: {
    resource: {
      id: cosmosDatabaseName
    }
    options: {
      throughput: environment == 'prod' ? 1000 : 400
    }
  }
}

// Cosmos Container (for SQL API)
resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-09-15' = if (enableCosmosDB && cosmosDbApiType == 'SQL') {
  parent: cosmosDatabase
  name: 'defaultContainer'
  properties: {
    resource: {
      id: 'defaultContainer'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'Consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

// Store Cosmos DB connection string in Key Vault
resource cosmosConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (enableCosmosDB) {
  parent: keyVault
  name: 'cosmos-connection-string'
  properties: {
    value: enableCosmosDB ? cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString : ''
    attributes: {
      enabled: true
    }
    contentType: 'text/plain'
  }
}

// Outputs
output sqlServerName string = sqlServer.name
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output sqlDatabaseName string = sqlDatabase.name
output cosmosAccountName string = enableCosmosDB ? cosmosAccount.name : ''
output cosmosAccountEndpoint string = enableCosmosDB ? cosmosAccount.properties.documentEndpoint : ''
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
output resourceGroupName string = resourceGroup().name
