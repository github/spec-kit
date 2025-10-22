// Base Parameter File for Web Application Deployment
using 'webapp-base.bicep'

// Required parameters
param location = 'eastus'
param environment = 'dev'
param appName = 'myapp'

// Optional parameters with defaults
param appServicePlanSku = 'B1'
param storageAccountSku = 'Standard_LRS'

// Tags
param tags = {
  Environment: 'dev'
  ApplicationName: 'myapp'
  ManagedBy: 'Bicep'
  CostCenter: 'Engineering'
  Owner: 'DevOps Team'
}
