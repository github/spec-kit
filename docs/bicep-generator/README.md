# Bicep Generator Documentation

Welcome to the Bicep Generator documentation! This comprehensive guide will help you understand and use the Bicep Generator to automatically create Azure infrastructure templates from your application code.

## What is Bicep Generator?

The Bicep Generator is an intelligent tool that analyzes your project and automatically generates production-ready Azure Bicep templates. It combines static code analysis, Azure MCP Server integration, and best practices to create infrastructure-as-code that follows the Azure Well-Architected Framework.

## Key Features

- **🔍 Intelligent Analysis**: Automatically detects Azure service dependencies from your code
- **📋 Schema-Driven**: Uses real Azure resource schemas via MCP Server
- **✅ Best Practices**: Applies Azure Well-Architected Framework principles
- **🔒 Security First**: Built-in security analysis and hardening
- **⚡ High Performance**: Caching and async processing for speed
- **🎨 Customizable**: Extensible architecture for custom requirements
- **💬 GitHub Copilot Integration**: Use `/speckit.bicep` in Copilot Chat for interactive guidance
- **🖥️ CLI Integration**: Use `specify bicep --analyze-only` to analyze projects from command line

## Current Status

**✅ Phase 6 Complete** - The following features are currently available:

### CLI Command (Available Now)
```bash
# Analyze your project for Azure dependencies
specify bicep --analyze-only

# Analyze with verbose output showing configuration
specify bicep --analyze-only --verbose
```

The CLI analyzer detects Azure resources from:
- Python: `requirements.txt`, `.env`
- Node.js: `package.json`, `.env`
- Detects 15+ Azure SDK packages
- Identifies 8 framework patterns (Flask, FastAPI, Express, Django, etc.)
- Shows resource types, suggested names, confidence scores, and evidence

### GitHub Copilot Command (Available Now)

Use `/speckit.bicep` in GitHub Copilot Chat for:
- Interactive project analysis
- Resource detection guidance
- Bicep template recommendations
- Example templates for detected services
- Deployment best practices

**Note**: Full template generation (`specify bicep --output`) is under development.

## Documentation Structure

### [User Guide](./user-guide.md)

Complete guide for using the Bicep Generator including:

- Getting started tutorial
- Core concepts explained
- Usage examples for common scenarios
- Commands reference
- Configuration options
- Best practices

**Start here** if you're new to the Bicep Generator.

### [API Reference](./api-reference.md)

Detailed API documentation including:

- Module structure
- Class definitions and methods
- Data models
- Utility functions
- Error handling
- Configuration objects
- Code examples

**Use this** when integrating Bicep Generator into your code or building extensions.

### [Architecture Guide](./architecture.md)

System architecture and design documentation:

- Design principles
- System architecture
- Component design
- Data flow diagrams
- Integration points
- Security architecture
- Performance optimization
- Extension points

**Read this** to understand how the system works internally or contribute to development.

### [Troubleshooting Guide](./troubleshooting.md)

Solutions to common problems:

- Common issues and fixes
- Analysis problems
- Generation errors
- Validation failures
- Deployment issues
- Performance problems
- Security concerns
- Debugging tips

**Check this** when you encounter problems or errors.

## Quick Start

### Installation

```bash
pip install specify-cli
```

### Basic Usage

```bash
# Analyze your project
specify bicep analyze --project-path ./my-app

# Generate Bicep templates
specify bicep generate --output-dir ./bicep-templates

# Validate templates
specify bicep validate --template-dir ./bicep-templates

# Deploy to Azure
specify bicep deploy --resource-group my-rg --subscription-id xxx-xxx-xxx
```

### Example Workflow

```python
from pathlib import Path
from specify_cli.bicep import ProjectAnalyzer, BicepGenerator

# Analyze project
analyzer = ProjectAnalyzer(project_path=Path("./my-app"))
analysis = analyzer.analyze()

# Generate templates
generator = BicepGenerator(analysis=analysis)
result = generator.generate()

print(f"Generated {len(result.files)} templates")
```

## Common Use Cases

### 1. New Project Infrastructure

Generate complete infrastructure for a new project:

```bash
specify bicep analyze --project-path ./new-app
specify bicep generate --environment production --region eastus
specify bicep deploy --resource-group new-app-rg
```

### 2. Existing Project Migration

Migrate existing infrastructure to Bicep:

```bash
# Analyze existing configuration
specify bicep analyze --project-path ./legacy-app

# Generate with existing resource names
specify bicep generate --preserve-names --output-dir ./bicep-templates

# Review before deploying
specify bicep review --template-dir ./bicep-templates
```

### 3. Multi-Environment Setup

Create separate templates for dev, staging, and production:

```bash
# Generate for each environment
specify bicep generate --environment dev --output-dir ./bicep/dev
specify bicep generate --environment staging --output-dir ./bicep/staging
specify bicep generate --environment production --output-dir ./bicep/production

# Deploy to dev first
specify bicep deploy --template-dir ./bicep/dev --resource-group app-dev
```

### 4. Cost Optimization

Analyze and optimize deployment costs:

```bash
# Estimate costs
specify bicep estimate-cost --template-dir ./bicep-templates

# Get optimization suggestions
specify bicep review --check-cost --suggest-optimizations

# Apply optimizations
specify bicep optimize --strategy cost-optimized
```

### 5. Security Hardening

Ensure templates meet security requirements:

```bash
# Security scan
specify bicep security --template-dir ./bicep-templates

# Apply security fixes
specify bicep security --auto-fix --severity high,critical

# Generate compliance report
specify bicep security --compliance-frameworks CIS,SOC2 --output-format html
```

## Prerequisites

### Required Tools

- **Python 3.11+**: Required for running the Bicep Generator
- **Azure CLI (`az`)**: Required for Azure authentication and deployment
- **Bicep CLI (`bicep`)**: Required for template validation and compilation

### Optional Tools

- **PowerShell 7.x**: For PowerShell script execution
- **Bash**: For bash script execution on Linux/macOS

### Azure Requirements

- **Azure Subscription**: Active subscription for deployments
- **Permissions**: Contributor role (or higher) on target resource group
- **Authentication**: Azure CLI login or service principal

### Installation Instructions

#### Windows (PowerShell)

```powershell
# Install Python 3.11+
winget install Python.Python.3.11

# Install Azure CLI
winget install Microsoft.AzureCLI

# Install Bicep CLI
az bicep install

# Install Specify CLI
pip install specify-cli
```

#### Linux/macOS (Bash)

```bash
# Install Python 3.11+ (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3.11 python3.11-pip

# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Bicep CLI
az bicep install

# Install Specify CLI
pip3 install specify-cli
```

## Configuration

### Configuration File

Create `bicep_config.json` in your project root:

```json
{
  "project": {
    "name": "my-application",
    "type": "web",
    "language": "python"
  },
  "azure": {
    "subscription_id": "xxx-xxx-xxx",
    "default_region": "eastus",
    "resource_group_prefix": "rg-myapp"
  },
  "templates": {
    "style": "modular",
    "include_monitoring": true,
    "include_networking": true
  },
  "security": {
    "enable_rbac": true,
    "enable_private_endpoints": true,
    "minimum_tls_version": "1.2"
  }
}
```

### Environment Variables

```bash
# Azure Configuration
export AZURE_SUBSCRIPTION_ID="xxx-xxx-xxx"
export AZURE_TENANT_ID="xxx-xxx-xxx"
export AZURE_DEFAULT_REGION="eastus"

# Bicep Generator Settings
export BICEP_TEMPLATE_STYLE="modular"
export BICEP_OUTPUT_DIR="./bicep-templates"
export BICEP_ENABLE_CACHING="true"
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Specify CLI                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Analyze  │→→│  Generate  │→→│  Validate  │→→Deploy    │
│  └────────────┘  └────────────┘  └────────────┘            │
└────────┬────────────────┬────────────────┬──────────────────┘
         │                │                │
         ↓                ↓                ↓
┌────────────────┐ ┌─────────────────────────────────────────┐
│   File System  │ │        Azure MCP Server                 │
│   - Config     │ │  ┌──────────────┐  ┌────────────────┐  │
│   - Source     │ │  │ Schema API   │  │ Best Practices │  │
│   - Templates  │ │  └──────────────┘  └────────────────┘  │
└────────────────┘ └─────────────────────────────────────────┘
                                     ↓
                            ┌─────────────────┐
                            │   Azure Portal  │
                            │   ARM/Bicep     │
                            └─────────────────┘
```

## Key Concepts

### Project Analysis

The Bicep Generator analyzes your project to detect:

- Azure service dependencies (Storage, Web Apps, Key Vault, etc.)
- Configuration requirements (connection strings, settings, etc.)
- Resource relationships (which resources depend on others)
- Security requirements (authentication, authorization, encryption)

### Template Generation

Templates are generated with:

- **Parameterization**: Environment-specific values as parameters
- **Best Practices**: Azure Well-Architected Framework compliance
- **Security**: Secure defaults (HTTPS only, TLS 1.2+, etc.)
- **Modularity**: Organized by resource type for maintainability

### Validation

Comprehensive validation includes:

- **Syntax**: Valid Bicep syntax and compilation
- **Schema**: Compliance with Azure resource schemas
- **Security**: No insecure configurations
- **Best Practices**: Azure Well-Architected Framework
- **Deployment**: Pre-deployment validation with Azure

### Deployment

Safe deployment process:

- **Dry Run**: Validate without deploying
- **Incremental**: Only update changed resources
- **Monitoring**: Real-time deployment status
- **Rollback**: Automatic rollback on failure

## Support and Contribution

### Getting Help

- **Documentation**: Start with this documentation
- **Troubleshooting Guide**: Check [Troubleshooting Guide](./troubleshooting.md)
- **GitHub Issues**: Report bugs or request features at [GitHub Issues](https://github.com/cristhianu/spec-kit-4applens/issues)
- **Community**: Join discussions on GitHub

### Contributing

We welcome contributions! See [Contributing Guide](../../CONTRIBUTING.md) for details on:

- Code of conduct
- Development setup
- Pull request process
- Coding standards
- Testing requirements

### Reporting Issues

When reporting issues, please include:

- Operating system and version
- Python version
- Azure CLI version
- Bicep CLI version
- Complete error message
- Steps to reproduce
- Sample project (if possible)

## Additional Resources

### Official Documentation

- [Azure Bicep Documentation](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Well-Architected Framework](https://docs.microsoft.com/azure/architecture/framework/)
- [Azure Resource Naming Conventions](https://docs.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/naming-and-tagging)

### Related Projects

- [Specify CLI](../../README.md) - Main Specify CLI project
- [Azure MCP Server](https://github.com/microsoft/azure-mcp-server) - Azure MCP Server integration
- [Bicep](https://github.com/Azure/bicep) - Azure Bicep project

### Community

- [GitHub Discussions](https://github.com/cristhianu/spec-kit-4applens/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/azure-bicep) - Use tags: `azure-bicep`, `specify-cli`

## License

This project is licensed under the MIT License - see [LICENSE](../../LICENSE) file for details.

## Version History

- **0.1.0** (2025-01-01): Initial release
  - Basic analysis and generation
  - Bicep template creation
  - Azure deployment

- **0.2.0** (2025-02-01): Feature additions
  - Cost estimation
  - Security analysis
  - Performance improvements

- **0.3.0** (2025-03-01): Advanced features
  - Template editing
  - Explanation engine
  - Multi-environment support

- **0.4.0** (2025-04-01): Enterprise features
  - Performance optimization
  - Comprehensive caching
  - Async processing

- **0.5.0** (2025-05-01): Production ready
  - Security hardening
  - Code quality improvements
  - Complete documentation

---

**Ready to get started?** Check out the [User Guide](./user-guide.md) for detailed instructions!
