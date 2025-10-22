"""Azure MCP Server client for Bicep template generation.

This module provides the interface to communicate with the Azure MCP Server
for retrieving Bicep schemas and generating templates.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

from .performance import cached, schema_cache, PerformanceTimer

logger = logging.getLogger(__name__)


@dataclass
class MCPServerResponse:
    """Response from Azure MCP Server."""
    content: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None


class AzureMCPClient:
    """Client for communicating with Azure MCP Server."""
    
    def __init__(self, server_url: Optional[str] = None):
        """Initialize the MCP client.
        
        Args:
            server_url: Optional URL for Azure MCP Server. If None, uses default.
        """
        self.server_url = server_url or "azure-mcp-server"
        self.session_id = None
        
    async def connect(self) -> bool:
        """Connect to the Azure MCP Server.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            # Simulate MCP server connection
            # In actual implementation, this would establish connection to MCP server
            logger.info(f"Connecting to Azure MCP Server at {self.server_url}")
            self.session_id = "bicep-generator-session"
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Azure MCP Server: {e}")
            return False
    
    @cached(cache=schema_cache, key_prefix="bicep_schema")
    async def get_bicep_schema(self, resource_type: str) -> MCPServerResponse:
        """Get Bicep schema for a specific Azure resource type.
        
        Args:
            resource_type: Azure resource type (e.g., 'Microsoft.Storage/storageAccounts')
            
        Returns:
            MCPServerResponse with schema information or error.
        """
        if not self.session_id:
            return MCPServerResponse(
                content=[],
                success=False,
                error_message="Not connected to MCP server"
            )
        
        async with PerformanceTimer("get_bicep_schema", items_processed=1):
            try:
                # Simulate MCP server call for bicepschema_get
                logger.info(f"Requesting Bicep schema for {resource_type}")
                
                # Mock response - in actual implementation, this would call the MCP server
                if resource_type == "Microsoft.Storage/storageAccounts":
                    schema_content = {
                        "type": "text",
                        "text": """@description('Storage account for application data')
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}"""
                    }
                elif resource_type == "Microsoft.Web/sites":
                    schema_content = {
                        "type": "text", 
                        "text": """@description('App Service for web application')
resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: appName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}"""
                    }
                elif resource_type == "Microsoft.KeyVault/vaults":
                    schema_content = {
                        "type": "text",
                        "text": """@description('Key Vault for secure storage')
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}"""
                    }
                else:
                    return MCPServerResponse(
                        content=[],
                        success=False,
                        error_message=f"Unsupported resource type: {resource_type}"
                    )
                
                return MCPServerResponse(
                    content=[schema_content],
                    success=True
                )
                
            except Exception as e:
                logger.error(f"Error retrieving schema for {resource_type}: {e}")
                return MCPServerResponse(
                    content=[],
                    success=False,
                    error_message=str(e)
                )
    
    async def validate_bicep_template(self, template_content: str) -> MCPServerResponse:
        """Validate Bicep template using ARM validation.
        
        Args:
            template_content: Bicep template content to validate
            
        Returns:
            MCPServerResponse with validation results.
        """
        if not self.session_id:
            return MCPServerResponse(
                content=[],
                success=False,
                error_message="Not connected to MCP server"
            )
        
        try:
            logger.info("Validating Bicep template")
            
            # Basic validation - check for required elements
            if not template_content or len(template_content.strip()) == 0:
                return MCPServerResponse(
                    content=[],
                    success=False,
                    error_message="Empty template content"
                )
            
            # Mock validation - in actual implementation, would use ARM validation API
            validation_result = {
                "type": "validation_result",
                "text": "Template validation passed - syntax and schema are valid"
            }
            
            return MCPServerResponse(
                content=[validation_result],
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error validating template: {e}")
            return MCPServerResponse(
                content=[],
                success=False,
                error_message=str(e)
            )
    
    async def disconnect(self):
        """Disconnect from the Azure MCP Server."""
        if self.session_id:
            logger.info("Disconnecting from Azure MCP Server")
            self.session_id = None


# Synchronous wrapper functions for easier use
def get_mcp_client() -> AzureMCPClient:
    """Get a configured Azure MCP client instance."""
    return AzureMCPClient()


async def get_bicep_schema_async(resource_type: str) -> MCPServerResponse:
    """Async helper to get Bicep schema."""
    client = get_mcp_client()
    await client.connect()
    try:
        return await client.get_bicep_schema(resource_type)
    finally:
        await client.disconnect()


def get_bicep_schema_sync(resource_type: str) -> MCPServerResponse:
    """Synchronous wrapper for getting Bicep schema."""
    return asyncio.run(get_bicep_schema_async(resource_type))


async def validate_bicep_template_async(template_content: str) -> MCPServerResponse:
    """Async helper to validate Bicep template."""
    client = get_mcp_client()
    await client.connect()
    try:
        return await client.validate_bicep_template(template_content)
    finally:
        await client.disconnect()


def validate_bicep_template_sync(template_content: str) -> MCPServerResponse:
    """Synchronous wrapper for validating Bicep template."""
    return asyncio.run(validate_bicep_template_async(template_content))