# Infrastructure as Code (IaC) MCP Server Configurations

This directory contains Model Context Protocol (MCP) server configurations for major cloud providers, enabling AI-assisted infrastructure management through Spec-Kit.

## Overview

These configurations allow you to connect Claude Code and other MCP-compatible AI assistants to cloud provider services for infrastructure management, deployment, and operations.

## Available Configurations

### Individual Cloud Provider Configurations

- **`aws.mcp.json`** - AWS services (Lambda, ECS, EKS, S3, CloudFormation, etc.)
- **`azure.mcp.json`** - Azure services (Functions, AKS, Storage, Cosmos DB, ARM, etc.)
- **`gcp.mcp.json`** - Google Cloud services (Cloud Functions, GKE, Storage, Deployment Manager, etc.)
- **`ibm.mcp.json`** - IBM Cloud services (Cloud Functions, Kubernetes, COS, WatsonX, Schematics, etc.)
- **`all-clouds.mcp.json`** - Combined configuration with main services from all cloud providers

## Usage

### Option 1: Project-Scoped Configuration (Recommended)

Copy the desired configuration file to your project root as `.mcp.json`:

```bash
# For AWS only
cp templates/iac/mcp-configs/aws.mcp.json .mcp.json

# For Azure only
cp templates/iac/mcp-configs/azure.mcp.json .mcp.json

# For all cloud providers
cp templates/iac/mcp-configs/all-clouds.mcp.json .mcp.json
```

### Option 2: Claude-Specific Configuration

Copy to `.claude/settings.local.json` in your project:

```bash
mkdir -p .claude
cp templates/iac/mcp-configs/aws.mcp.json .claude/settings.local.json
```

### Option 3: User-Wide Configuration

Copy to your home directory for global access:

```bash
cp templates/iac/mcp-configs/all-clouds.mcp.json ~/.claude/settings.local.json
```

## Environment Variables

Each cloud provider requires specific environment variables to be set. Create a `.env` file in your project or export them in your shell.

### AWS Configuration

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGION="us-east-1"  # Optional, defaults to us-east-1
```

### Azure Configuration

```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

# For Azure Storage
export AZURE_STORAGE_ACCOUNT="your-storage-account"
export AZURE_STORAGE_KEY="your-storage-key"

# For Azure Cosmos DB
export AZURE_COSMOS_ENDPOINT="your-cosmos-endpoint"
export AZURE_COSMOS_KEY="your-cosmos-key"
```

### Google Cloud Configuration

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"  # Optional, defaults to us-central1
```

### IBM Cloud Configuration

```bash
export IBM_CLOUD_API_KEY="your-api-key"
export IBM_CLOUD_REGION="us-south"  # Optional, defaults to us-south
export IBM_CLOUD_NAMESPACE="your-namespace"  # For Cloud Functions

# For IBM Cloud Object Storage
export IBM_COS_ENDPOINT="your-cos-endpoint"
export IBM_COS_BUCKET="your-bucket-name"

# For IBM WatsonX
export WATSONX_URL="your-watsonx-url"
export WATSONX_APIKEY="your-watsonx-apikey"
export WATSONX_PROJECT_ID="your-project-id"
export WATSONX_MODEL_ID="ibm/granite-13b-chat-v2"  # Optional

# For IBM MCP Context Forge (HTTP server)
export IBM_MCP_CONTEXT_FORGE_URL="https://your-context-forge-url"
```

## Security Best Practices

### 1. Never Commit Credentials

Add these files to `.gitignore`:

```gitignore
.env
.env.*
.mcp.json
.claude/settings.local.json
**/service-account-key.json
```

### 2. Use Environment-Specific Variables

The configurations use environment variable substitution (e.g., `${AWS_ACCESS_KEY_ID}`). Set these in your environment or use a `.env` file with a tool like `direnv`.

### 3. Principle of Least Privilege

- Create IAM users/service accounts with minimal required permissions
- Use role-based access control (RBAC) where available
- Regularly rotate credentials
- Enable MFA for cloud provider accounts

### 4. MCP Server Security

- Only connect to trusted MCP servers
- Use HTTPS for HTTP-based MCP servers
- Validate server certificates
- Review and restrict tool permissions
- Regularly update MCP server packages

## Available MCP Servers by Cloud Provider

### AWS Servers

| Server | Purpose | Package |
|--------|---------|---------|
| aws-api | General AWS API access | @modelcontextprotocol/server-aws-api |
| aws-lambda | Lambda function management | @modelcontextprotocol/server-aws-lambda |
| aws-ecs | ECS container orchestration | @modelcontextprotocol/server-aws-ecs |
| aws-eks | EKS Kubernetes management | @modelcontextprotocol/server-aws-eks |
| aws-s3 | S3 object storage | @modelcontextprotocol/server-aws-s3 |
| aws-cloudformation | CloudFormation IaC | @modelcontextprotocol/server-aws-cloudformation |
| aws-pricing | AWS pricing queries | @modelcontextprotocol/server-aws-pricing |

### Azure Servers

| Server | Purpose | Package |
|--------|---------|---------|
| azure | General Azure access | @modelcontextprotocol/server-azure |
| azure-storage | Blob and file storage | @modelcontextprotocol/server-azure-storage |
| azure-cosmos | Cosmos DB operations | @modelcontextprotocol/server-azure-cosmos |
| azure-functions | Serverless functions | @modelcontextprotocol/server-azure-functions |
| azure-aks | Kubernetes management | @modelcontextprotocol/server-azure-aks |
| azure-arm | ARM template deployment | @modelcontextprotocol/server-azure-arm |

### Google Cloud Servers

| Server | Purpose | Package |
|--------|---------|---------|
| gcp | General GCP access | @modelcontextprotocol/server-gcp |
| gcp-cloud-functions | Cloud Functions | @modelcontextprotocol/server-gcp-cloud-functions |
| gcp-cloud-run | Cloud Run containers | @modelcontextprotocol/server-gcp-cloud-run |
| gcp-gke | GKE Kubernetes | @modelcontextprotocol/server-gcp-gke |
| gcp-storage | Cloud Storage | @modelcontextprotocol/server-gcp-storage |
| gcp-deployment-manager | Deployment Manager IaC | @modelcontextprotocol/server-gcp-deployment-manager |
| gcp-firestore | Firestore database | @modelcontextprotocol/server-gcp-firestore |

### IBM Cloud Servers

| Server | Purpose | Package |
|--------|---------|---------|
| ibm-cloud | General IBM Cloud access | @modelcontextprotocol/server-ibm-cloud |
| ibm-cloud-functions | Cloud Functions | @modelcontextprotocol/server-ibm-cloud-functions |
| ibm-kubernetes | Kubernetes Service | @modelcontextprotocol/server-ibm-kubernetes |
| ibm-cos | Cloud Object Storage | @modelcontextprotocol/server-ibm-cos |
| ibm-watsonx | WatsonX AI/ML | @modelcontextprotocol/server-ibm-watsonx |
| ibm-schematics | Schematics (Terraform) | @modelcontextprotocol/server-ibm-schematics |
| ibm-mcp-context-forge | MCP Gateway & Registry | HTTP server |

## Installation

MCP servers are installed automatically when Claude Code first connects to them. The configurations use `npx -y` to automatically download and run the latest versions.

To pre-install servers manually:

```bash
# Install all AWS servers
npm install -g @modelcontextprotocol/server-aws-api
npm install -g @modelcontextprotocol/server-aws-lambda
# ... etc

# Or let npx handle installation on first use (recommended)
```

## Testing Your Configuration

1. Copy a configuration file to `.mcp.json` in your project
2. Set the required environment variables
3. Start Claude Code in your project directory
4. Try commands like:
   - "List my AWS Lambda functions"
   - "Show my Azure resource groups"
   - "What GCP projects do I have access to?"
   - "List my IBM Cloud Kubernetes clusters"

## Customization

You can combine, modify, or create custom configurations by editing the JSON files. Each MCP server entry follows this structure:

```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",              // or "http" for HTTP servers
      "command": "npx",              // command to run
      "args": ["-y", "package-name"], // command arguments
      "env": {                       // environment variables
        "VAR_NAME": "${ENV_VAR}"
      },
      "description": "Server purpose"
    }
  }
}
```

## Troubleshooting

### Server Not Found

If Claude Code can't find a server, ensure:
1. The MCP configuration file is in the correct location
2. Environment variables are set correctly
3. Node.js and npm are installed
4. You have network access to download packages

### Authentication Errors

If you get authentication errors:
1. Verify credentials are correct
2. Check that credentials have necessary permissions
3. Ensure credentials haven't expired
4. For GCP, verify the service account key file exists

### Connection Timeouts

For HTTP servers behind load balancers:
- AWS ALB: Set `SSE_KEEPALIVE_INTERVAL=60`
- Azure: Set `SSE_KEEPALIVE_INTERVAL=240`

Add these to the `env` section of the MCP server configuration.

## Multi-Cloud Scenarios

For projects spanning multiple clouds, use `all-clouds.mcp.json` and set environment variables for all providers you need:

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Set Azure credentials
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."

# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS="..."
export GCP_PROJECT_ID="..."

# Set IBM Cloud credentials
export IBM_CLOUD_API_KEY="..."
```

## Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Claude Code MCP Guide](https://docs.claude.com/en/docs/claude-code/mcp)
- [AWS MCP Servers](https://aws.amazon.com/solutions/guidance/deploying-model-context-protocol-servers-on-aws/)
- [Azure MCP Documentation](https://learn.microsoft.com/en-us/azure/ai/)
- [IBM MCP Context Forge](https://github.com/IBM/mcp-context-forge)

## Contributing

To add new cloud providers or services:

1. Create a new JSON file following the naming convention: `{provider}.mcp.json`
2. Add MCP server configurations for the provider
3. Update this README with configuration details
4. Include environment variable documentation
5. Add security best practices specific to the provider

## License

These configurations are provided as part of the Spec-Kit project under the MIT License.
