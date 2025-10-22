@description('Container-based application infrastructure with Azure Container Instances')

@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for resources')
param baseName string = 'containerapp'

@description('Container image to deploy')
param containerImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

@description('Number of CPU cores (1, 2, 4)')
@allowed([1, 2, 4])
param cpuCores int = 1

@description('Memory in GB (1, 2, 4, 8, 16)')
@allowed([1, 2, 4, 8, 16])
param memoryGb int = 2

@description('Container port to expose')
param containerPort int = 80

@description('Restart policy for containers')
@allowed(['Always', 'OnFailure', 'Never'])
param restartPolicy string = 'Always'

@description('Enable Application Insights monitoring')
param enableMonitoring bool = true

@description('Enable Azure Container Registry')
param enableACR bool = true

// Variables
var resourceSuffix = '${baseName}-${environment}'
var containerGroupName = 'cg-${resourceSuffix}'
var acrName = replace('acr${resourceSuffix}', '-', '')
var logAnalyticsName = 'law-${resourceSuffix}'
var appInsightsName = 'ai-${resourceSuffix}'

// Log Analytics Workspace (for monitoring)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = if (enableMonitoring) {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: environment == 'prod' ? 'PerGB2018' : 'Free'
    }
    retentionInDays: environment == 'prod' ? 90 : 30
    features: {
      searchVersion: 1
      legacy: 0
    }
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = if (enableMonitoring) {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: enableMonitoring ? logAnalytics.id : null
    IngestionMode: 'LogAnalytics'
  }
}

// Azure Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = if (enableACR) {
  name: acrName
  location: location
  sku: {
    name: environment == 'prod' ? 'Premium' : 'Basic'
  }
  properties: {
    adminUserEnabled: environment != 'prod'
    policies: {
      quarantinePolicy: {
        status: 'enabled'
      }
      trustPolicy: {
        status: environment == 'prod' ? 'enabled' : 'disabled'
        type: 'Notary'
      }
      retentionPolicy: {
        status: 'enabled'
        days: environment == 'prod' ? 90 : 7
      }
    }
    encryption: {
      status: 'disabled'
    }
    dataEndpointEnabled: false
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
  }
}

// Container Group
resource containerGroup 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: containerGroupName
  location: location
  properties: {
    containers: [
      {
        name: '${baseName}-container'
        properties: {
          image: containerImage
          ports: [
            {
              port: containerPort
              protocol: 'TCP'
            }
          ]
          environmentVariables: [
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
              value: enableMonitoring ? appInsights!.properties.InstrumentationKey : ''
            }
          ]
          resources: {
            requests: {
              cpu: cpuCores
              memoryInGB: memoryGb
            }
            limits: {
              cpu: cpuCores
              memoryInGB: memoryGb
            }
          }
          livenessProbe: {
            httpGet: {
              path: '/'
              port: containerPort
              scheme: 'HTTP'
            }
            initialDelaySeconds: 60
            periodSeconds: 30
            failureThreshold: 3
            successThreshold: 1
            timeoutSeconds: 10
          }
          readinessProbe: {
            httpGet: {
              path: '/'
              port: containerPort
              scheme: 'HTTP'
            }
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 3
            successThreshold: 1
            timeoutSeconds: 5
          }
        }
      }
    ]
    osType: 'Linux'
    restartPolicy: restartPolicy
    ipAddress: {
      type: 'Public'
      ports: [
        {
          port: containerPort
          protocol: 'TCP'
        }
      ]
      dnsNameLabel: '${containerGroupName}-${uniqueString(resourceGroup().id)}'
    }
    diagnostics: enableMonitoring ? {
      logAnalytics: {
        workspaceId: logAnalytics!.properties.customerId
        workspaceKey: logAnalytics!.listKeys().primarySharedKey
      }
    } : null
  }
}

// Outputs
output containerGroupName string = containerGroup.name
output containerGroupFQDN string = containerGroup.properties.ipAddress.fqdn
output containerGroupIP string = containerGroup.properties.ipAddress.ip
output containerRegistryName string = enableACR ? containerRegistry.name : ''
output containerRegistryLoginServer string = enableACR ? containerRegistry!.properties.loginServer : ''
output logAnalyticsWorkspaceId string = enableMonitoring ? logAnalytics!.properties.customerId : ''
output appInsightsInstrumentationKey string = enableMonitoring ? appInsights!.properties.InstrumentationKey : ''
output resourceGroupName string = resourceGroup().name
