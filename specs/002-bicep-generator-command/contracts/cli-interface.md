# CLI Command Interface: Bicep Generator

**Feature**: 002-bicep-generator-command  
**Date**: 2025-10-21  
**Type**: Command Line Interface Specification

## Command Structure

### Primary Command: `bicep-generate`

**Syntax**: 
```bash
/bicep-generate [options] [project-path]
```

**Description**: Generates Azure Bicep templates from project analysis with intelligent questionnaire and validation.

### Command Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `project-path` | string | No | current directory | Path to project root for analysis |
| `--output-dir` | string | No | ./bicep-templates | Output directory for generated templates |
| `--environments` | string[] | No | ["dev", "staging", "prod"] | Target deployment environments |
| `--region` | string | No | prompt user | Primary Azure region for deployment |
| `--subscription` | string | No | current context | Azure subscription ID |
| `--update-only` | boolean | No | false | Only update existing templates |
| `--validate` | boolean | No | true | Validate templates using ARM |
| `--backup` | boolean | No | true | Create backup files during updates |
| `--interactive` | boolean | No | true | Ask questions for missing information |
| `--verbose` | boolean | No | false | Enable detailed output logging |
| `--dry-run` | boolean | No | false | Show what would be generated without creating files |

### Interactive Questions Interface

**Project Analysis Questions**:

1. **Environment Configuration**
   - "Which environments do you plan to deploy to?" 
   - Options: [Development, Staging, Production, Custom...]
   - Default: [Development, Production]

2. **Regional Deployment**
   - "What is your primary Azure region?"
   - Options: [East US, West US 2, West Europe, East Asia, ...]
   - Default: East US

3. **Scale Requirements**
   - "What is your expected scale?"
   - Options: [Small (dev/test), Medium (production), Large (enterprise), Custom...]
   - Default: Medium

4. **Security Requirements**
   - "What security features do you need?"
   - Options: [Basic, Enhanced (Key Vault), Enterprise (Private Endpoints), Custom...]
   - Default: Enhanced

5. **Cost Optimization**
   - "What is your cost optimization preference?"
   - Options: [Cost-optimized, Balanced, Performance-optimized]
   - Default: Balanced

### Command Outputs

**Success Response**:
```json
{
  "status": "success",
  "generated_templates": [
    {
      "path": "bicep-templates/compute/app-service.bicep",
      "resource_type": "Microsoft.Web/sites",
      "validation_status": "valid"
    }
  ],
  "parameter_files": [
    "bicep-templates/parameters/dev.parameters.json",
    "bicep-templates/parameters/prod.parameters.json"
  ],
  "documentation": "bicep-templates/architecture.md",
  "summary": {
    "templates_generated": 5,
    "resources_detected": 8,
    "validation_passed": true,
    "generation_time_seconds": 45
  }
}
```

**Error Response**:
```json
{
  "status": "error",
  "error_code": "VALIDATION_FAILED",
  "message": "Template validation failed for Microsoft.Storage/storageAccounts",
  "details": {
    "failed_templates": [
      {
        "path": "bicep-templates/storage/storage-account.bicep",
        "errors": [
          "Parameter 'accountType' has invalid value 'StandardLRS'"
        ]
      }
    ]
  },
  "suggestion": "Review the template parameters and retry generation"
}
```

### Progress Indicators

**Analysis Phase**:
```text
🔍 Analyzing project files...
   ├── Configuration files: 12 found
   ├── Documentation files: 8 found  
   ├── Script files: 3 found
   └── Azure services detected: 5
```

**Generation Phase**:
```text
⚙️  Generating Bicep templates...
   ├── 📝 compute/app-service.bicep
   ├── 📝 storage/storage-account.bicep
   ├── 📝 security/key-vault.bicep
   └── ✅ 3 templates generated
```

**Validation Phase**:
```text
✅ Validating templates...
   ├── Syntax validation: ✅ Passed
   ├── Schema validation: ✅ Passed
   └── ARM validation: ✅ Passed
```

## PowerShell Script Interface

### Entry Point: `bicep-generate.ps1`

**Function Signature**:
```powershell
function New-BicepTemplates {
    param(
        [string]$ProjectPath = ".",
        [string]$OutputDir = "./bicep-templates",
        [string[]]$Environments = @("dev", "staging", "prod"),
        [string]$Region = $null,
        [string]$SubscriptionId = $null,
        [switch]$UpdateOnly,
        [switch]$Validate = $true,
        [switch]$Backup = $true,
        [switch]$Interactive = $true,
        [switch]$Verbose,
        [switch]$DryRun
    )
}
```

**Return Object**:
```powershell
@{
    Status = "Success" | "Error" | "Warning"
    GeneratedTemplates = @(
        @{
            Path = "string"
            ResourceType = "string"
            ValidationStatus = "Valid" | "Invalid" | "Warning"
        }
    )
    ParameterFiles = @("string[]")
    Documentation = "string"
    Summary = @{
        TemplatesGenerated = [int]
        ResourcesDetected = [int]
        ValidationPassed = [bool]
        GenerationTimeSeconds = [int]
    }
    Errors = @("string[]")
}
```

### Update Command: `bicep-update`

**Syntax**:
```bash
/bicep-update [project-path] [--templates-dir]
```

**Function**:
```powershell
function Update-BicepTemplates {
    param(
        [string]$ProjectPath = ".",
        [string]$TemplatesDir = "./bicep-templates",
        [switch]$Backup = $true,
        [switch]$Validate = $true
    )
}
```

## MCP Server Integration Interface

### Azure MCP Server Calls

**Schema Retrieval**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "bicepschema_get",
    "arguments": {
      "resource-type": "Microsoft.Storage/storageAccounts"
    }
  }
}
```

**Expected Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "@description('Storage account for application data')\nresource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {\n  name: storageAccountName\n  location: location\n  sku: {\n    name: 'Standard_LRS'\n  }\n  kind: 'StorageV2'\n  properties: {\n    supportsHttpsTrafficOnly: true\n  }\n}"
      }
    ]
  }
}
```

### Custom MCP Server Specification

For cases where Azure MCP Server is insufficient, provide specifications for custom Bicep MCP Server:

**Required Tools**:
- `bicep_analyze_project`: Analyze project files for Azure dependencies
- `bicep_generate_template`: Generate Bicep template for specific resource type
- `bicep_validate_template`: Validate Bicep template using ARM APIs
- `bicep_create_parameters`: Generate environment-specific parameter files

**Tool Interfaces**:
```json
{
  "tools": [
    {
      "name": "bicep_analyze_project",
      "description": "Analyze project files to detect Azure service requirements",
      "inputSchema": {
        "type": "object",
        "properties": {
          "project_path": {"type": "string"},
          "file_patterns": {"type": "array", "items": {"type": "string"}},
          "analysis_depth": {"type": "string", "enum": ["basic", "deep"]}
        },
        "required": ["project_path"]
      }
    },
    {
      "name": "bicep_generate_template", 
      "description": "Generate Bicep template for Azure resource type",
      "inputSchema": {
        "type": "object",
        "properties": {
          "resource_type": {"type": "string"},
          "requirements": {"type": "object"},
          "environment": {"type": "string"},
          "naming_convention": {"type": "string"}
        },
        "required": ["resource_type"]
      }
    }
  ]
}
```

## File System Interface

### Directory Structure Contract

**Input Expectations**:
- Project root directory with readable files
- Optional existing bicep-templates directory
- Write permissions for output directory

**Output Guarantees**:
```text
bicep-templates/
├── compute/           # Compute resources (App Service, Functions, VMs)
├── storage/           # Storage resources (Storage Accounts, Databases)
├── networking/        # Network resources (VNet, Load Balancers, etc.)
├── security/          # Security resources (Key Vault, Managed Identity)
├── parameters/        # Environment-specific parameter files
│   ├── dev.parameters.json
│   ├── staging.parameters.json
│   └── prod.parameters.json
├── backups/           # Backup files from updates (if enabled)
│   └── [timestamp]/
└── architecture.md    # Generated architecture documentation
```

### File Naming Conventions

**Template Files**: `{service-name}.bicep`
- Examples: `app-service.bicep`, `storage-account.bicep`, `key-vault.bicep`

**Parameter Files**: `{environment}.parameters.json`
- Examples: `dev.parameters.json`, `prod.parameters.json`

**Backup Files**: `{original-name}.{timestamp}.backup`
- Examples: `app-service.20251021143000.backup`

### File Format Contracts

**Bicep Template Format**:
```bicep
@description('Generated by Bicep Generator Command')
@metadata({
  generator: 'bicep-generator-command'
  version: '1.0.0'
  generated: '2025-10-21T14:30:00Z'
})

// CUSTOM: User customizations preserved between updates
param location string = resourceGroup().location
param environment string = 'dev'

// Template content follows Azure best practices
```

**Parameter File Format**:
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "metadata": {
    "generator": "bicep-generator-command",
    "environment": "dev",
    "generated": "2025-10-21T14:30:00Z"
  },
  "parameters": {
    "location": {
      "value": "eastus"
    }
  }
}
```

This interface specification provides comprehensive contracts for all integration points, ensuring consistent behavior across PowerShell scripts, MCP servers, and file system operations.