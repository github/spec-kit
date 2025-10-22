"""Bicep template management and generation utilities.

This module provides functionality for managing Bicep templates,
including loading base templates, customization, and composition.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of Bicep templates."""
    BASE = "base"
    RESOURCE = "resource"
    MODULE = "module"
    ENVIRONMENT = "environment"


class ResourceTier(Enum):
    """Azure resource pricing tiers."""
    FREE = "Free"
    BASIC = "Basic"
    STANDARD = "Standard"
    PREMIUM = "Premium"


@dataclass
class TemplateMetadata:
    """Metadata for a Bicep template."""
    name: str
    description: str
    template_type: TemplateType
    azure_service: str
    resource_type: str
    version: str
    created_date: datetime
    updated_date: datetime
    tags: Set[str] = field(default_factory=set)
    parameters: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateCustomization:
    """Customization options for template generation."""
    environment: str = "dev"
    region: str = "eastus"
    resource_prefix: str = ""
    resource_suffix: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    tier: ResourceTier = ResourceTier.BASIC
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedTemplate:
    """Result of template generation."""
    content: str
    metadata: TemplateMetadata
    customization: TemplateCustomization
    file_path: Optional[Path] = None
    dependencies: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


class BicepTemplateManager:
    """Manager for Bicep template operations."""
    
    def __init__(self, templates_dir: Path):
        """Initialize the template manager.
        
        Args:
            templates_dir: Directory containing base Bicep templates.
        """
        self.templates_dir = templates_dir
        self.loaded_templates: Dict[str, TemplateMetadata] = {}
        self._ensure_templates_directory()
    
    def _ensure_templates_directory(self):
        """Ensure templates directory exists with required structure."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different resource categories
        subdirs = [
            'storage',
            'compute', 
            'networking',
            'web',
            'database',
            'security',
            'monitoring',
            'integration',
            'base'
        ]
        
        for subdir in subdirs:
            (self.templates_dir / subdir).mkdir(exist_ok=True)
    
    def load_templates(self) -> Dict[str, TemplateMetadata]:
        """Load all available templates and their metadata.
        
        Returns:
            Dictionary of template name to metadata.
        """
        logger.info(f"Loading templates from {self.templates_dir}")
        
        self.loaded_templates.clear()
        
        for template_path in self.templates_dir.rglob("*.bicep"):
            try:
                metadata = self._load_template_metadata(template_path)
                if metadata:
                    self.loaded_templates[metadata.name] = metadata
                    
            except Exception as e:
                logger.warning(f"Failed to load template {template_path}: {e}")
        
        logger.info(f"Loaded {len(self.loaded_templates)} templates")
        return self.loaded_templates.copy()
    
    def get_template_by_service(self, azure_service: str) -> List[TemplateMetadata]:
        """Get templates for a specific Azure service.
        
        Args:
            azure_service: Azure service type (e.g., 'Microsoft.Storage/storageAccounts').
            
        Returns:
            List of templates for the service.
        """
        if not self.loaded_templates:
            self.load_templates()
        
        return [
            template for template in self.loaded_templates.values()
            if template.azure_service == azure_service
        ]
    
    def get_base_templates(self) -> List[TemplateMetadata]:
        """Get all base templates.
        
        Returns:
            List of base templates.
        """
        if not self.loaded_templates:
            self.load_templates()
        
        return [
            template for template in self.loaded_templates.values()
            if template.template_type == TemplateType.BASE
        ]
    
    def generate_template(
        self,
        service_type: str,
        customization: TemplateCustomization,
        template_name: Optional[str] = None
    ) -> GeneratedTemplate:
        """Generate a customized Bicep template.
        
        Args:
            service_type: Azure service type to generate template for.
            customization: Customization options.
            template_name: Specific template to use (optional).
            
        Returns:
            Generated template with content and metadata.
        """
        logger.info(f"Generating template for {service_type}")
        
        # Find appropriate template
        templates = self.get_template_by_service(service_type)
        
        if not templates:
            # Generate basic template if none found
            return self._generate_basic_template(service_type, customization)
        
        # Use specified template or first available
        if template_name:
            template = next((t for t in templates if t.name == template_name), templates[0])
        else:
            template = templates[0]
        
        # Load template content
        template_content = self._load_template_content(template)
        
        # Apply customizations
        customized_content = self._customize_template(template_content, customization)
        
        # Create generated template
        generated = GeneratedTemplate(
            content=customized_content,
            metadata=template,
            customization=customization
        )
        
        # Validate template
        generated.validation_errors = self._validate_template_content(customized_content)
        
        logger.info(f"Generated template for {service_type} ({len(customized_content)} chars)")
        return generated
    
    def save_template(
        self,
        generated_template: GeneratedTemplate,
        output_path: Path,
        overwrite: bool = False
    ) -> Path:
        """Save a generated template to file.
        
        Args:
            generated_template: The template to save.
            output_path: Path where to save the template.
            overwrite: Whether to overwrite existing files.
            
        Returns:
            Path to the saved file.
        """
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Template file already exists: {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write template content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(generated_template.content)
        
        # Update generated template with file path
        generated_template.file_path = output_path
        
        logger.info(f"Saved template to {output_path}")
        return output_path
    
    def create_base_templates(self):
        """Create default base templates for common Azure services."""
        logger.info("Creating base templates")
        
        # Storage Account template
        storage_template = self._create_storage_template()
        self._save_base_template("storage-account.bicep", storage_template, "storage")
        
        # Web App template
        webapp_template = self._create_webapp_template()
        self._save_base_template("web-app.bicep", webapp_template, "web")
        
        # Key Vault template
        keyvault_template = self._create_keyvault_template()
        self._save_base_template("key-vault.bicep", keyvault_template, "security")
        
        # Base parameter file template
        param_template = self._create_parameter_template()
        self._save_base_template("parameters.bicepparam", param_template, "base")
        
        logger.info("Base templates created")
    
    def _load_template_metadata(self, template_path: Path) -> Optional[TemplateMetadata]:
        """Load metadata for a template file.
        
        Args:
            template_path: Path to the template file.
            
        Returns:
            TemplateMetadata or None if loading failed.
        """
        try:
            # Read template content to extract metadata
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse metadata from template comments
            metadata = self._parse_template_metadata(content, template_path)
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata for {template_path}: {e}")
            return None
    
    def _parse_template_metadata(self, content: str, template_path: Path) -> TemplateMetadata:
        """Parse metadata from template content and path.
        
        Args:
            content: Template file content.
            template_path: Path to the template file.
            
        Returns:
            Parsed TemplateMetadata.
        """
        # Extract metadata from comments
        name = template_path.stem
        description = "Bicep template"
        azure_service = "Unknown"
        resource_type = "Unknown"
        version = "1.0.0"
        tags = set()
        
        # Look for metadata comments
        lines = content.split('\n')
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line.startswith('//'):
                comment = line[2:].strip()
                
                if comment.startswith('@description'):
                    description = comment.replace('@description', '').strip(' \'"')
                elif comment.startswith('@azure-service'):
                    azure_service = comment.replace('@azure-service', '').strip(' \'"')
                elif comment.startswith('@resource-type'):
                    resource_type = comment.replace('@resource-type', '').strip(' \'"')
                elif comment.startswith('@version'):
                    version = comment.replace('@version', '').strip(' \'"')
                elif comment.startswith('@tags'):
                    tag_str = comment.replace('@tags', '').strip(' \'"')
                    tags.update(tag.strip() for tag in tag_str.split(',') if tag.strip())
        
        # Determine template type from path
        template_type = TemplateType.RESOURCE
        if 'base' in str(template_path).lower():
            template_type = TemplateType.BASE
        elif 'module' in str(template_path).lower():
            template_type = TemplateType.MODULE
        elif 'environment' in str(template_path).lower():
            template_type = TemplateType.ENVIRONMENT
        
        now = datetime.now()
        
        return TemplateMetadata(
            name=name,
            description=description,
            template_type=template_type,
            azure_service=azure_service,
            resource_type=resource_type,
            version=version,
            created_date=now,
            updated_date=now,
            tags=tags
        )
    
    def _load_template_content(self, metadata: TemplateMetadata) -> str:
        """Load the actual content of a template.
        
        Args:
            metadata: Template metadata.
            
        Returns:
            Template content as string.
        """
        # Find template file
        template_path = None
        
        for path in self.templates_dir.rglob(f"{metadata.name}.bicep"):
            template_path = path
            break
        
        if not template_path:
            raise FileNotFoundError(f"Template file not found for {metadata.name}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _customize_template(self, template_content: str, customization: TemplateCustomization) -> str:
        """Apply customizations to template content.
        
        Args:
            template_content: Original template content.
            customization: Customization options.
            
        Returns:
            Customized template content.
        """
        content = template_content
        
        # Replace common placeholders
        replacements = {
            '{ENVIRONMENT}': customization.environment,
            '{REGION}': customization.region,
            '{LOCATION}': customization.region,
            '{RESOURCE_PREFIX}': customization.resource_prefix,
            '{RESOURCE_SUFFIX}': customization.resource_suffix,
            '{TIER}': customization.tier.value
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        
        # Add custom tags
        if customization.tags:
            tags_json = json.dumps(customization.tags, indent=2)
            # Look for existing tags parameter and replace or add
            if 'param tags object' in content:
                # Replace default tags
                content = content.replace(
                    'param tags object = {}',
                    f'param tags object = {tags_json}'
                )
            else:
                # Add tags parameter
                param_section = f"\n// Tags\nparam tags object = {tags_json}\n"
                # Insert after other parameters
                if 'param ' in content:
                    lines = content.split('\n')
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('param '):
                            insert_idx = i + 1
                    lines.insert(insert_idx, param_section)
                    content = '\n'.join(lines)
        
        return content
    
    def _generate_basic_template(
        self,
        service_type: str,
        customization: TemplateCustomization
    ) -> GeneratedTemplate:
        """Generate a basic template when no template exists.
        
        Args:
            service_type: Azure service type.
            customization: Customization options.
            
        Returns:
            Basic generated template.
        """
        # Create basic template content
        content = f"""// Basic Bicep template for {service_type}
// Generated automatically - customize as needed

@description('Location for all resources')
param location string = resourceGroup().location

@description('Name for the resource')
param resourceName string

@description('Tags for the resource')
param tags object = {json.dumps(customization.tags, indent=2)}

// TODO: Replace with actual resource definition for {service_type}
resource exampleResource 'Microsoft.Resources/resourceGroups@2021-04-01' = {{
  name: resourceName
  location: location
  tags: tags
}}

@description('Resource ID')
output resourceId string = exampleResource.id
"""
        
        # Apply customizations
        customized_content = self._customize_template(content, customization)
        
        # Create metadata
        now = datetime.now()
        metadata = TemplateMetadata(
            name=f"basic-{service_type.lower().replace('/', '-').replace('.', '-')}",
            description=f"Basic template for {service_type}",
            template_type=TemplateType.RESOURCE,
            azure_service=service_type,
            resource_type=service_type,
            version="1.0.0",
            created_date=now,
            updated_date=now,
            tags={"auto-generated", "basic"}
        )
        
        return GeneratedTemplate(
            content=customized_content,
            metadata=metadata,
            customization=customization,
            validation_errors=["Template is auto-generated basic template - review and customize"]
        )
    
    def _validate_template_content(self, content: str) -> List[str]:
        """Basic validation of template content.
        
        Args:
            content: Template content to validate.
            
        Returns:
            List of validation errors.
        """
        errors = []
        
        # Check for basic Bicep structure
        if not content.strip():
            errors.append("Template content is empty")
        
        if 'resource ' not in content:
            errors.append("Template does not define any resources")
        
        if '@description' not in content:
            errors.append("Template lacks parameter descriptions")
        
        # Check for TODO comments
        if 'TODO' in content.upper():
            errors.append("Template contains TODO items that need completion")
        
        return errors
    
    def _save_base_template(self, filename: str, content: str, category: str):
        """Save a base template to the templates directory.
        
        Args:
            filename: Name of the template file.
            content: Template content.
            category: Category subdirectory.
        """
        template_path = self.templates_dir / category / filename
        template_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"Saved base template: {template_path}")
    
    def _create_storage_template(self) -> str:
        """Create a storage account template."""
        return """// @description Storage Account Bicep Template
// @azure-service Microsoft.Storage/storageAccounts
// @resource-type Microsoft.Storage/storageAccounts
// @version 1.0.0
// @tags storage, basic

@description('Location for all resources')
param location string = resourceGroup().location

@description('Storage account name')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Storage account SKU')
@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_RAGRS', 'Standard_ZRS', 'Premium_LRS'])
param storageAccountSku string = 'Standard_LRS'

@description('Tags for the storage account')
param tags object = {}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: storageAccountSku
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

@description('Storage account ID')
output storageAccountId string = storageAccount.id

@description('Storage account name')
output storageAccountName string = storageAccount.name

@description('Primary endpoints')
output primaryEndpoints object = storageAccount.properties.primaryEndpoints
"""
    
    def _create_webapp_template(self) -> str:
        """Create a web app template."""
        return """// @description Web App with App Service Plan
// @azure-service Microsoft.Web/sites
// @resource-type Microsoft.Web/sites
// @version 1.0.0
// @tags webapp, appservice

@description('Location for all resources')
param location string = resourceGroup().location

@description('Web app name')
param webAppName string

@description('App Service Plan name')
param appServicePlanName string

@description('App Service Plan SKU')
@allowed(['F1', 'B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1V2', 'P2V2', 'P3V2'])
param appServicePlanSku string = 'B1'

@description('Tags for resources')
param tags object = {}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: {
    name: appServicePlanSku
  }
  kind: 'app'
  properties: {
    reserved: false
  }
}

resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppName
  location: location
  tags: tags
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}

@description('Web app ID')
output webAppId string = webApp.id

@description('Web app URL')
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'

@description('App Service Plan ID')
output appServicePlanId string = appServicePlan.id
"""
    
    def _create_keyvault_template(self) -> str:
        """Create a Key Vault template."""
        return """// @description Key Vault Bicep Template
// @azure-service Microsoft.KeyVault/vaults
// @resource-type Microsoft.KeyVault/vaults
// @version 1.0.0
// @tags keyvault, security

@description('Location for all resources')
param location string = resourceGroup().location

@description('Key Vault name')
param keyVaultName string

@description('SKU for the Key Vault')
@allowed(['standard', 'premium'])
param keyVaultSku string = 'standard'

@description('Tags for the Key Vault')
param tags object = {}

@description('Object ID of the user/service principal to grant access')
param objectId string = ''

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: keyVaultSku
    }
    tenantId: subscription().tenantId
    enabledForTemplateDeployment: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

@description('Key Vault ID')
output keyVaultId string = keyVault.id

@description('Key Vault URI')
output keyVaultUri string = keyVault.properties.vaultUri

@description('Key Vault name')
output keyVaultName string = keyVault.name
"""
    
    def _create_parameter_template(self) -> str:
        """Create a parameter file template."""
        return """// Parameter file template for Bicep deployments
using 'main.bicep'

param location = '{REGION}'
param environment = '{ENVIRONMENT}'
param resourcePrefix = '{RESOURCE_PREFIX}'
param tags = {
  Environment: '{ENVIRONMENT}'
  Project: 'specify-bicep-generator'
  ManagedBy: 'Bicep'
}
"""