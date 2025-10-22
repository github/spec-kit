"""Enhanced Bicep template patterns for common Azure architectures.

This module provides advanced template patterns beyond the base templates,
including multi-tier applications, microservices, and enterprise patterns.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import json

from .models.resource_requirement import ResourceRequirement, ResourceType, PerformanceRequirement
from .models.bicep_template import BicepTemplate, BicepParameter, BicepResource
from .template_manager import TemplateManager

logger = logging.getLogger(__name__)


@dataclass
class ArchitecturePattern:
    """Represents a specific architecture pattern."""
    name: str
    description: str
    use_cases: List[str]
    components: List[str]
    template_files: List[str]
    parameters: List[str] = field(default_factory=list)
    estimated_cost: Optional[str] = None
    complexity_level: str = "medium"  # "simple", "medium", "complex"


class TemplatePatternGenerator:
    """Generates advanced template patterns for common Azure architectures."""
    
    def __init__(self, template_manager: TemplateManager):
        """Initialize the pattern generator."""
        self.template_manager = template_manager
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, ArchitecturePattern]:
        """Initialize available architecture patterns."""
        patterns = {}
        
        # Three-tier web application
        patterns["three-tier-webapp"] = ArchitecturePattern(
            name="Three-Tier Web Application",
            description="Traditional three-tier architecture with presentation, business, and data layers",
            use_cases=[
                "Enterprise web applications",
                "E-commerce platforms", 
                "Content management systems",
                "Business applications with complex workflows"
            ],
            components=[
                "Application Gateway with WAF",
                "App Service (Web Tier)",
                "App Service (API Tier)", 
                "Azure SQL Database (Data Tier)",
                "Key Vault for secrets",
                "Application Insights",
                "Storage Account for static content"
            ],
            template_files=["main.bicep", "network.bicep", "webapp.bicep", "api.bicep", "database.bicep"],
            parameters=["environmentName", "location", "sqlAdminLogin", "skuName", "enableWaf"],
            estimated_cost="$200-800/month",
            complexity_level="complex"
        )
        
        # Microservices architecture
        patterns["microservices"] = ArchitecturePattern(
            name="Microservices with Container Apps",
            description="Cloud-native microservices architecture using Azure Container Apps",
            use_cases=[
                "Modern cloud-native applications",
                "API-first architectures",
                "Event-driven systems",
                "Scalable distributed applications"
            ],
            components=[
                "Container Apps Environment",
                "Multiple Container Apps (services)",
                "Application Gateway",
                "Service Bus for messaging",
                "Cosmos DB",
                "Key Vault",
                "Application Insights",
                "Log Analytics Workspace"
            ],
            template_files=["main.bicep", "container-env.bicep", "services.bicep", "messaging.bicep", "data.bicep"],
            parameters=["environmentName", "location", "containerRegistry", "serviceCount"],
            estimated_cost="$300-1200/month",
            complexity_level="complex"
        )
        
        # Static web app with API
        patterns["static-webapp-api"] = ArchitecturePattern(
            name="Static Web App with Serverless API",
            description="Modern JAMstack architecture with static frontend and serverless backend",
            use_cases=[
                "Single-page applications (SPA)",
                "JAMstack websites",
                "Portfolio sites with dynamic features",
                "Event-driven web applications"
            ],
            components=[
                "Static Web Apps",
                "Function App (API backend)",
                "Cosmos DB or Storage Account",
                "CDN Profile",
                "Key Vault",
                "Application Insights"
            ],
            template_files=["main.bicep", "staticapp.bicep", "functions.bicep", "storage.bicep"],
            parameters=["environmentName", "location", "appName", "functionAppName"],
            estimated_cost="$50-200/month",
            complexity_level="simple"
        )
        
        # Data processing pipeline
        patterns["data-pipeline"] = ArchitecturePattern(
            name="Serverless Data Processing Pipeline",
            description="Event-driven data processing using Azure Functions and Storage",
            use_cases=[
                "ETL/ELT pipelines",
                "Real-time data processing",
                "File processing workflows",
                "IoT data ingestion"
            ],
            components=[
                "Storage Account (input/output)",
                "Function Apps (processing)",
                "Service Bus (orchestration)",
                "Cosmos DB or SQL Database",
                "Application Insights",
                "Key Vault"
            ],
            template_files=["main.bicep", "storage.bicep", "functions.bicep", "messaging.bicep"],
            parameters=["environmentName", "location", "storageAccountName", "functionAppName"],
            estimated_cost="$100-400/month",
            complexity_level="medium"
        )
        
        # API management
        patterns["api-management"] = ArchitecturePattern(
            name="Enterprise API Management",
            description="Comprehensive API management with security and monitoring",
            use_cases=[
                "API monetization",
                "Partner API integration",
                "Microservices API gateway",
                "Legacy system modernization"
            ],
            components=[
                "API Management Service",
                "App Service (backend APIs)",
                "Application Gateway",
                "Key Vault",
                "Application Insights",
                "Storage Account"
            ],
            template_files=["main.bicep", "apim.bicep", "backend.bicep", "security.bicep"],
            parameters=["environmentName", "location", "apimServiceName", "publisherName", "publisherEmail"],
            estimated_cost="$500-2000/month",
            complexity_level="complex"
        )
        
        return patterns
    
    def get_available_patterns(self) -> List[ArchitecturePattern]:
        """Get list of available architecture patterns."""
        return list(self.patterns.values())
    
    def get_pattern(self, pattern_name: str) -> Optional[ArchitecturePattern]:
        """Get a specific architecture pattern."""
        return self.patterns.get(pattern_name)
    
    def recommend_pattern(self, requirements: List[ResourceRequirement]) -> List[str]:
        """Recommend architecture patterns based on requirements."""
        recommendations = []
        
        # Analyze requirement characteristics
        has_web = any(req.resource_type == ResourceType.WEB_APP for req in requirements)
        has_api = any(req.resource_type == ResourceType.FUNCTION_APP for req in requirements) 
        has_database = any(req.resource_type == ResourceType.SQL_DATABASE for req in requirements)
        has_storage = any(req.resource_type == ResourceType.STORAGE_ACCOUNT for req in requirements)
        
        # Count of each type
        app_count = len([req for req in requirements if req.resource_type in [ResourceType.WEB_APP, ResourceType.FUNCTION_APP]])
        
        # Simple recommendations logic
        if has_web and has_database and not has_api:
            recommendations.append("three-tier-webapp")
        
        if has_web and has_api and not has_database:
            recommendations.append("static-webapp-api")
            
        if app_count >= 3:
            recommendations.append("microservices")
            
        if has_api and has_storage and not has_web:
            recommendations.append("data-pipeline")
        
        # Always consider simple patterns for basic setups
        if len(requirements) <= 2 and has_web:
            recommendations.append("static-webapp-api")
        
        return recommendations
    
    async def generate_pattern_template(self,
                                      pattern_name: str,
                                      project_name: str,
                                      environment: str = "dev",
                                      additional_params: Dict[str, Any] = None) -> Optional[BicepTemplate]:
        """Generate a template based on an architecture pattern."""
        
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            logger.error(f"Unknown pattern: {pattern_name}")
            return None
        
        logger.info(f"Generating template for pattern: {pattern.name}")
        
        additional_params = additional_params or {}
        
        try:
            if pattern_name == "three-tier-webapp":
                return await self._generate_three_tier_webapp(project_name, environment, additional_params)
            elif pattern_name == "microservices":
                return await self._generate_microservices(project_name, environment, additional_params)
            elif pattern_name == "static-webapp-api":
                return await self._generate_static_webapp_api(project_name, environment, additional_params)
            elif pattern_name == "data-pipeline":
                return await self._generate_data_pipeline(project_name, environment, additional_params)
            elif pattern_name == "api-management":
                return await self._generate_api_management(project_name, environment, additional_params)
            else:
                logger.error(f"Pattern generation not implemented: {pattern_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating pattern template: {e}")
            return None
    
    async def _generate_three_tier_webapp(self,
                                        project_name: str, 
                                        environment: str,
                                        params: Dict[str, Any]) -> BicepTemplate:
        """Generate three-tier web application template."""
        
        # Create main template
        template = BicepTemplate(
            name=f"{project_name}-three-tier",
            description="Three-tier web application with App Gateway, Web App, API, and SQL Database",
            version="1.0.0",
            author="Bicep Generator",
            created_at=datetime.now()
        )
        
        # Add parameters
        template.parameters.extend([
            BicepParameter(
                name="environmentName",
                type="string", 
                default_value=environment,
                description="Environment name (dev, test, prod)"
            ),
            BicepParameter(
                name="location",
                type="string",
                default_value="[resourceGroup().location]",
                description="Azure region for resources"
            ),
            BicepParameter(
                name="sqlAdminLogin", 
                type="string",
                description="SQL Server administrator login"
            ),
            BicepParameter(
                name="sqlAdminPassword",
                type="securestring",
                description="SQL Server administrator password"
            ),
            BicepParameter(
                name="webAppSkuName",
                type="string",
                default_value="B1",
                description="App Service plan SKU"
            ),
            BicepParameter(
                name="enableWaf",
                type="bool", 
                default_value="true",
                description="Enable Web Application Firewall"
            )
        ])
        
        # Add variables for naming
        template.variables = {
            "resourcePrefix": f"[concat(parameters('environmentName'), '-{project_name}')]",
            "appGatewayName": "[concat(variables('resourcePrefix'), '-agw')]",
            "webAppName": "[concat(variables('resourcePrefix'), '-web')]",
            "apiAppName": "[concat(variables('resourcePrefix'), '-api')]",
            "sqlServerName": "[concat(variables('resourcePrefix'), '-sql')]",
            "sqlDatabaseName": "[concat(variables('resourcePrefix'), '-db')]",
            "keyVaultName": "[concat(variables('resourcePrefix'), '-kv')]",
            "appInsightsName": "[concat(variables('resourcePrefix'), '-ai')]"
        }
        
        # Generate content for three-tier architecture
        content = self._generate_three_tier_bicep_content(project_name)
        template.content = content
        
        return template
    
    def _generate_three_tier_bicep_content(self, project_name: str) -> str:
        """Generate Bicep content for three-tier architecture."""
        
        return f"""// Three-Tier Web Application Architecture
// Generated for project: {project_name}
// Architecture: Presentation -> Business Logic -> Data Layer

targetScope = 'resourceGroup'

@description('Environment name (dev, test, prod)')
param environmentName string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('SQL Server administrator login')
param sqlAdminLogin string

@description('SQL Server administrator password')
@secure()
param sqlAdminPassword string

@description('App Service plan SKU')
@allowed(['B1', 'B2', 'S1', 'S2', 'P1V2', 'P2V2'])
param webAppSkuName string = 'B1'

@description('Enable Web Application Firewall')
param enableWaf bool = true

// Variables for consistent naming
var resourcePrefix = '${{environmentName}}-{project_name}'
var appGatewayName = '${{resourcePrefix}}-agw'
var webAppName = '${{resourcePrefix}}-web'
var apiAppName = '${{resourcePrefix}}-api'
var appServicePlanName = '${{resourcePrefix}}-plan'
var sqlServerName = '${{resourcePrefix}}-sql'
var sqlDatabaseName = '${{resourcePrefix}}-db'
var keyVaultName = '${{resourcePrefix}}-kv'
var appInsightsName = '${{resourcePrefix}}-ai'
var storageAccountName = replace('${{resourcePrefix}}st', '-', '')
var logAnalyticsName = '${{resourcePrefix}}-logs'

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {{
  name: logAnalyticsName
  location: location
  properties: {{
    sku: {{
      name: 'PerGB2018'
    }}
    retentionInDays: 30
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Monitoring'
  }}
}}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {{
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {{
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Monitoring'
  }}
}}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {{
  name: keyVaultName
  location: location
  properties: {{
    tenantId: subscription().tenantId
    sku: {{
      family: 'A'
      name: 'standard'
    }}
    accessPolicies: []
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    networkAcls: {{
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }}
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Security'
  }}
}}

// Storage Account for static content and diagnostics
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {{
  name: storageAccountName
  location: location
  sku: {{
    name: 'Standard_LRS'
  }}
  kind: 'StorageV2'
  properties: {{
    httpsOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Storage'
  }}
}}

// SQL Server
resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {{
  name: sqlServerName
  location: location
  properties: {{
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }}
  identity: {{
    type: 'SystemAssigned'
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Data'
  }}
}}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {{
  parent: sqlServer
  name: sqlDatabaseName
  location: location
  sku: {{
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }}
  properties: {{
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648 // 2GB
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Data'
  }}
}}

// SQL Firewall Rule for Azure Services
resource sqlFirewallRule 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {{
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {{
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }}
}}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {{
  name: appServicePlanName
  location: location
  sku: {{
    name: webAppSkuName
  }}
  properties: {{
    reserved: false // Windows
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Compute'
  }}
}}

// Web Application (Presentation Tier)
resource webApp 'Microsoft.Web/sites@2023-12-01' = {{
  name: webAppName
  location: location
  identity: {{
    type: 'SystemAssigned'
  }}
  properties: {{
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {{
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      healthCheckPath: '/health'
      appSettings: [
        {{
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }}
        {{
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }}
        {{
          name: 'API_BASE_URL'
          value: 'https://${{apiAppName}}.azurewebsites.net'
        }}
        {{
          name: 'KeyVaultUri'
          value: keyVault.properties.vaultUri
        }}
      ]
    }}
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Presentation'
  }}
}}

// API Application (Business Logic Tier)  
resource apiApp 'Microsoft.Web/sites@2023-12-01' = {{
  name: apiAppName
  location: location
  identity: {{
    type: 'SystemAssigned'
  }}
  properties: {{
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {{
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      healthCheckPath: '/api/health'
      cors: {{
        allowedOrigins: [
          'https://${{webAppName}}.azurewebsites.net'
        ]
      }}
      appSettings: [
        {{
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }}
        {{
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }}
        {{
          name: 'DATABASE_CONNECTION_STRING'
          value: '@Microsoft.KeyVault(VaultName=${{keyVaultName}};SecretName=DatabaseConnectionString)'
        }}
        {{
          name: 'KeyVaultUri'
          value: keyVault.properties.vaultUri
        }}
      ]
    }}
  }}
  tags: {{
    Environment: environmentName
    Project: '{project_name}'
    Tier: 'Business'
  }}
}}

// Key Vault Access Policies for Managed Identities
resource webAppKeyVaultAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {{
  name: guid(keyVault.id, webApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {{
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: webApp.identity.principalId
    principalType: 'ServicePrincipal'
  }}
}}

resource apiAppKeyVaultAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {{
  name: guid(keyVault.id, apiApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {{
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: apiApp.identity.principalId
    principalType: 'ServicePrincipal'
  }}
}}

// Store database connection string in Key Vault
resource databaseConnectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {{
  parent: keyVault
  name: 'DatabaseConnectionString'
  properties: {{
    value: 'Server=tcp:${{sqlServer.properties.fullyQualifiedDomainName}},1433;Initial Catalog=${{sqlDatabaseName}};Authentication=Active Directory Managed Identity;Encrypt=true;TrustServerCertificate=false;Connection Timeout=30;'
  }}
}}

// Outputs
output webAppUrl string = 'https://${{webApp.properties.defaultHostName}}'
output apiAppUrl string = 'https://${{apiApp.properties.defaultHostName}}'
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output keyVaultUri string = keyVault.properties.vaultUri
output applicationInsightsConnectionString string = appInsights.properties.ConnectionString
output resourceGroupName string = resourceGroup().name
"""
    
    async def _generate_static_webapp_api(self,
                                        project_name: str,
                                        environment: str, 
                                        params: Dict[str, Any]) -> BicepTemplate:
        """Generate static web app with serverless API template."""
        
        template = BicepTemplate(
            name=f"{project_name}-static-api",
            description="Static Web App with serverless API backend using Functions",
            version="1.0.0",
            author="Bicep Generator",
            created_at=datetime.now()
        )
        
        # Add parameters
        template.parameters.extend([
            BicepParameter(
                name="environmentName", 
                type="string",
                default_value=environment,
                description="Environment name"
            ),
            BicepParameter(
                name="location",
                type="string", 
                default_value="[resourceGroup().location]",
                description="Azure region"
            ),
            BicepParameter(
                name="appName",
                type="string",
                default_value=project_name,
                description="Application name"
            )
        ])
        
        # Generate content
        content = self._generate_static_webapp_bicep_content(project_name)
        template.content = content
        
        return template
    
    def _generate_static_webapp_bicep_content(self, project_name: str) -> str:
        """Generate Bicep content for static web app with API."""
        
        return f"""// Static Web App with Serverless API
// Generated for project: {project_name}
// Architecture: JAMstack with Azure Static Web Apps + Functions

targetScope = 'resourceGroup'

@description('Environment name (dev, test, prod)')
param environmentName string = 'dev'

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Application name')
param appName string = '{project_name}'

// Variables
var resourcePrefix = '${{environmentName}}-${{appName}}'
var staticWebAppName = '${{resourcePrefix}}-swa'
var functionAppName = '${{resourcePrefix}}-func'
var storageAccountName = replace('${{resourcePrefix}}st', '-', '')
var appInsightsName = '${{resourcePrefix}}-ai'
var keyVaultName = '${{resourcePrefix}}-kv'

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {{
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {{
    Application_Type: 'web'
  }}
  tags: {{
    Environment: environmentName
    Project: appName
  }}
}}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {{
  name: keyVaultName
  location: location
  properties: {{
    tenantId: subscription().tenantId
    sku: {{
      family: 'A'
      name: 'standard'
    }}
    accessPolicies: []
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }}
  tags: {{
    Environment: environmentName
    Project: appName
  }}
}}

// Storage Account for Functions
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {{
  name: storageAccountName
  location: location
  sku: {{
    name: 'Standard_LRS'
  }}
  kind: 'StorageV2'
  properties: {{
    httpsOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }}
  tags: {{
    Environment: environmentName
    Project: appName
  }}
}}

// Function App (Consumption Plan)
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {{
  name: functionAppName
  location: location
  kind: 'functionapp'
  identity: {{
    type: 'SystemAssigned'
  }}
  properties: {{
    serverFarmId: hostingPlan.id
    httpsOnly: true
    siteConfig: {{
      appSettings: [
        {{
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${{storageAccount.name}};EndpointSuffix=${{environment().suffixes.storage}};AccountKey=${{storageAccount.listKeys().keys[0].value}}'
        }}
        {{
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${{storageAccount.name}};EndpointSuffix=${{environment().suffixes.storage}};AccountKey=${{storageAccount.listKeys().keys[0].value}}'
        }}
        {{
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }}
        {{
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }}
        {{
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'node'
        }}
        {{
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '~18'
        }}
        {{
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }}
      ]
      cors: {{
        allowedOrigins: ['*']
        supportCredentials: false
      }}
    }}
  }}
  tags: {{
    Environment: environmentName
    Project: appName
  }}
}}

// Consumption Plan for Functions
resource hostingPlan 'Microsoft.Web/serverfarms@2023-12-01' = {{
  name: '${{resourcePrefix}}-plan'
  location: location
  sku: {{
    name: 'Y1'
    tier: 'Dynamic'
  }}
  properties: {{
    reserved: false
  }}
  tags: {{
    Environment: environmentName
    Project: appName
  }}
}}

// Static Web App
resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {{
  name: staticWebAppName
  location: location
  sku: {{
    name: 'Free'
    tier: 'Free'
  }}
  properties: {{
    repositoryUrl: 'https://github.com/your-org/{project_name}'
    branch: 'main'
    buildProperties: {{
      appLocation: '/src'
      apiLocation: '/api'
      outputLocation: '/dist'
    }}
  }}
  tags: {{
    Environment: environmentName
    Project: appName
  }}
}}

// Link Function App to Static Web App
resource staticWebAppFunctionAppLink 'Microsoft.Web/staticSites/linkedBackends@2023-12-01' = {{
  parent: staticWebApp
  name: 'functionapp-backend'
  properties: {{
    backendResourceId: functionApp.id
    region: location
  }}
}}

// Key Vault access for Function App
resource functionAppKeyVaultAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {{
  name: guid(keyVault.id, functionApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {{
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }}
}}

// Outputs
output staticWebAppUrl string = 'https://${{staticWebApp.properties.defaultHostname}}'
output functionAppUrl string = 'https://${{functionApp.properties.defaultHostName}}'
output keyVaultUri string = keyVault.properties.vaultUri
output applicationInsightsConnectionString string = appInsights.properties.ConnectionString
"""
    
    async def _generate_microservices(self,
                                    project_name: str,
                                    environment: str,
                                    params: Dict[str, Any]) -> BicepTemplate:
        """Generate microservices architecture template."""
        
        template = BicepTemplate(
            name=f"{project_name}-microservices",
            description="Microservices architecture with Container Apps",
            version="1.0.0",
            author="Bicep Generator", 
            created_at=datetime.now()
        )
        
        # Add parameters
        template.parameters.extend([
            BicepParameter(
                name="environmentName",
                type="string",
                default_value=environment,
                description="Environment name"
            ),
            BicepParameter(
                name="location",
                type="string",
                default_value="[resourceGroup().location]",
                description="Azure region"
            ),
            BicepParameter(
                name="serviceCount",
                type="int",
                default_value="3",
                description="Number of microservices"
            )
        ])
        
        content = self._generate_microservices_bicep_content(project_name)
        template.content = content
        
        return template
    
    def _generate_microservices_bicep_content(self, project_name: str) -> str:
        """Generate Bicep content for microservices architecture."""
        
        return f"""// Microservices Architecture with Container Apps
// Generated for project: {project_name}

targetScope = 'resourceGroup'

param environmentName string = 'dev'
param location string = resourceGroup().location
param serviceCount int = 3

var resourcePrefix = '${{environmentName}}-{project_name}'

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {{
  name: '${{resourcePrefix}}-cae'
  location: location
  properties: {{
    appLogsConfiguration: {{
      destination: 'log-analytics'
      logAnalyticsConfiguration: {{
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }}
    }}
  }}
}}

// Log Analytics for monitoring
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {{
  name: '${{resourcePrefix}}-logs'
  location: location
  properties: {{
    sku: {{
      name: 'PerGB2018'
    }}
  }}
}}

// Sample microservices
resource containerApps 'Microsoft.App/containerApps@2024-03-01' = [for i in range(0, serviceCount): {{
  name: '${{resourcePrefix}}-service-${{i + 1}}'
  location: location
  properties: {{
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {{
      ingress: {{
        external: true
        targetPort: 8080
      }}
    }}
    template: {{
      containers: [
        {{
          name: 'service-${{i + 1}}'
          image: 'nginx:latest'
          resources: {{
            cpu: json('0.25')
            memory: '0.5Gi'
          }}
        }}
      ]
      scale: {{
        minReplicas: 1
        maxReplicas: 5
      }}
    }}
  }}
}}]

output containerAppsEnvironmentFqdn string = containerAppsEnvironment.properties.defaultDomain
"""
    
    async def _generate_data_pipeline(self,
                                    project_name: str,
                                    environment: str,
                                    params: Dict[str, Any]) -> BicepTemplate:
        """Generate data processing pipeline template."""
        
        template = BicepTemplate(
            name=f"{project_name}-data-pipeline",
            description="Serverless data processing pipeline with Functions and Storage",
            version="1.0.0",
            author="Bicep Generator",
            created_at=datetime.now()
        )
        
        # Basic parameters
        template.parameters.extend([
            BicepParameter(
                name="environmentName",
                type="string", 
                default_value=environment,
                description="Environment name"
            ),
            BicepParameter(
                name="location",
                type="string",
                default_value="[resourceGroup().location]",
                description="Azure region"
            )
        ])
        
        content = self._generate_data_pipeline_bicep_content(project_name)
        template.content = content
        
        return template
    
    def _generate_data_pipeline_bicep_content(self, project_name: str) -> str:
        """Generate Bicep content for data pipeline."""
        
        return f"""// Data Processing Pipeline
// Generated for project: {project_name}

targetScope = 'resourceGroup'

param environmentName string = 'dev'  
param location string = resourceGroup().location

var resourcePrefix = '${{environmentName}}-{project_name}'

// Storage for data pipeline
resource dataStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {{
  name: replace('${{resourcePrefix}}data', '-', '')
  location: location
  sku: {{
    name: 'Standard_LRS'
  }}
  kind: 'StorageV2'
  properties: {{
    httpsOnly: true
    minimumTlsVersion: 'TLS1_2'
  }}
}}

// Function App for processing
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {{
  name: '${{resourcePrefix}}-func'
  location: location
  kind: 'functionapp'
  properties: {{
    serverFarmId: hostingPlan.id
    siteConfig: {{
      appSettings: [
        {{
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${{dataStorage.name}};AccountKey=${{dataStorage.listKeys().keys[0].value}}'
        }}
        {{
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }}
        {{
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }}
      ]
    }}
  }}
}}

resource hostingPlan 'Microsoft.Web/serverfarms@2023-12-01' = {{
  name: '${{resourcePrefix}}-plan'
  location: location
  sku: {{
    name: 'Y1'
    tier: 'Dynamic'
  }}
}}

output functionAppName string = functionApp.name
output storageAccountName string = dataStorage.name
"""
    
    async def _generate_api_management(self,
                                     project_name: str,
                                     environment: str, 
                                     params: Dict[str, Any]) -> BicepTemplate:
        """Generate API Management template."""
        
        template = BicepTemplate(
            name=f"{project_name}-api-management",
            description="Enterprise API Management with backend services",
            version="1.0.0",
            author="Bicep Generator",
            created_at=datetime.now()
        )
        
        # Add required parameters
        template.parameters.extend([
            BicepParameter(
                name="environmentName",
                type="string",
                default_value=environment,
                description="Environment name"
            ),
            BicepParameter(
                name="publisherName", 
                type="string",
                description="API publisher name"
            ),
            BicepParameter(
                name="publisherEmail",
                type="string", 
                description="API publisher email"
            )
        ])
        
        content = self._generate_api_management_bicep_content(project_name)
        template.content = content
        
        return template
    
    def _generate_api_management_bicep_content(self, project_name: str) -> str:
        """Generate Bicep content for API Management."""
        
        return f"""// Enterprise API Management
// Generated for project: {project_name}

targetScope = 'resourceGroup'

param environmentName string = 'dev'
param location string = resourceGroup().location
param publisherName string
param publisherEmail string

var resourcePrefix = '${{environmentName}}-{project_name}'

// API Management Service
resource apiManagement 'Microsoft.ApiManagement/service@2023-09-01-preview' = {{
  name: '${{resourcePrefix}}-apim'
  location: location
  sku: {{
    name: 'Developer'
    capacity: 1
  }}
  properties: {{
    publisherName: publisherName
    publisherEmail: publisherEmail
  }}
}}

// Backend App Service
resource backendApp 'Microsoft.Web/sites@2023-12-01' = {{
  name: '${{resourcePrefix}}-backend'
  location: location
  properties: {{
    serverFarmId: appServicePlan.id
    httpsOnly: true
  }}
}}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {{
  name: '${{resourcePrefix}}-plan'
  location: location
  sku: {{
    name: 'B1'
  }}
}}

output apiManagementName string = apiManagement.name
output backendAppUrl string = 'https://${{backendApp.properties.defaultHostName}}'
"""


# Export main class
__all__ = ["TemplatePatternGenerator", "ArchitecturePattern"]