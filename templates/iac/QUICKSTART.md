# IaC Quick Start Guide

Get started with Infrastructure as Code using Spec-Kit in 5 minutes!

## Prerequisites

- Spec-Kit installed (`specify` command available)
- Claude Code or another MCP-compatible AI assistant
- Cloud provider account (AWS, Azure, GCP, or IBM Cloud)
- Node.js and npm installed (for MCP servers)

## Step-by-Step Setup

### 1. Initialize Your Project

If you haven't already initialized Spec-Kit in your project:

```bash
cd your-project
specify init --agent claude
```

### 2. Copy MCP Configuration

Choose your cloud provider and copy the MCP configuration:

**For AWS:**
```bash
cp templates/iac/mcp-configs/aws.mcp.json .mcp.json
```

**For Azure:**
```bash
cp templates/iac/mcp-configs/azure.mcp.json .mcp.json
```

**For Google Cloud:**
```bash
cp templates/iac/mcp-configs/gcp.mcp.json .mcp.json
```

**For IBM Cloud:**
```bash
cp templates/iac/mcp-configs/ibm.mcp.json .mcp.json
```

**For Multi-Cloud:**
```bash
cp templates/iac/mcp-configs/all-clouds.mcp.json .mcp.json
```

### 3. Set Up Credentials

Create a `.env` file in your project root (add to `.gitignore`!):

**AWS (.env):**
```bash
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
```

**Azure (.env):**
```bash
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

**GCP (.env):**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
```

**IBM Cloud (.env):**
```bash
IBM_CLOUD_API_KEY=your-api-key
IBM_CLOUD_REGION=us-south
```

### 4. Load Environment Variables

```bash
source .env
# or
export $(cat .env | xargs)
```

### 5. Start Claude Code

```bash
claude
```

### 6. Create Your First Infrastructure Spec

In Claude Code, use the infrastructure specification command:

```
/speckit.specify-infrastructure Deploy a web application on AWS with:
- Application Load Balancer
- EC2 auto-scaling group (2-5 instances)
- RDS PostgreSQL database
- S3 bucket for static assets
- CloudWatch monitoring
```

Claude Code will:
1. Analyze your requirements
2. Generate a comprehensive infrastructure specification
3. Create a feature branch
4. Save the spec to `specs/###-your-infrastructure/spec.md`

### 7. Review the Specification

Open the generated specification file and review:
- Infrastructure requirements
- Cloud resources
- Deployment strategy
- Success criteria

### 8. Ask Questions Using MCP Servers

Now you can interact with your cloud provider through Claude Code:

**AWS Examples:**
```
List my current EC2 instances
Show me my RDS databases
What's my current AWS bill this month?
```

**Azure Examples:**
```
Show my Azure resource groups
List my AKS clusters
What VMs are currently running?
```

**GCP Examples:**
```
List my GCP projects
Show my GKE clusters
What's my current GCP spending?
```

**IBM Cloud Examples:**
```
List my IBM Cloud resources
Show my Kubernetes clusters
What Cloud Functions do I have?
```

### 9. Implement Your Infrastructure

Create an `infrastructure/` directory in your project:

```bash
mkdir -p infrastructure/{modules,environments}
```

Use Terraform, CloudFormation, or your preferred IaC tool to implement the specification:

**Terraform Example:**
```bash
cd infrastructure

# Create main configuration
cat > main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Your infrastructure code here
EOF

# Initialize Terraform
terraform init

# Plan infrastructure
terraform plan

# Apply infrastructure
terraform apply
```

### 10. Validate Your Infrastructure

Run validation and security checks:

```bash
# Terraform validation
terraform validate

# Security scanning
tfsec .

# Cost estimation
infracost breakdown --path .
```

## Next Steps

### Plan Your Implementation

Create a detailed implementation plan:

```
/speckit.plan
```

### Break Down Into Tasks

Generate actionable tasks:

```
/speckit.tasks
```

### Implement Step by Step

Execute the implementation:

```
/speckit.implement
```

### Monitor and Iterate

Use MCP servers to monitor your infrastructure:

```
Check the health of my infrastructure
Show me any CloudWatch alarms
What's the current resource utilization?
```

## Common Workflows

### Create New Environment

```
/speckit.specify-infrastructure Set up a staging environment that mirrors
production but with smaller instance sizes
```

### Add New Service

```
/speckit.specify-infrastructure Add a Redis cache layer to our existing
infrastructure for session management
```

### Implement Disaster Recovery

```
/speckit.specify-infrastructure Create a disaster recovery setup in a
different AWS region with cross-region replication
```

### Optimize Costs

```
/speckit.specify-infrastructure Optimize our current AWS infrastructure to
reduce costs by 30% while maintaining performance
```

### Enhance Security

```
/speckit.specify-infrastructure Add AWS WAF, Shield, and GuardDuty to our
existing infrastructure for enhanced security
```

## Troubleshooting

### MCP Server Connection Issues

**Problem:** Can't connect to MCP servers

**Solution:**
1. Verify `.mcp.json` is in project root
2. Check environment variables are set
3. Ensure Node.js and npm are installed
4. Restart Claude Code

### Authentication Errors

**Problem:** Authentication failed with cloud provider

**Solution:**
1. Verify credentials in `.env` file
2. Check credential expiration
3. Verify IAM permissions
4. Test credentials with cloud provider CLI

### Package Installation Issues

**Problem:** MCP server package won't install

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Manually install package
npm install -g @modelcontextprotocol/server-aws-api

# Restart Claude Code
```

## Tips and Tricks

### 1. Use .gitignore

Always ignore sensitive files:

```gitignore
.env
.env.*
.mcp.json
.terraform/
*.tfstate
*.tfstate.backup
service-account*.json
```

### 2. Use Terraform Workspaces

Separate environments using workspaces:

```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace new production
```

### 3. Use Remote State

Store Terraform state remotely:

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}
```

### 4. Tag Everything

Use consistent tagging:

```hcl
tags = {
  Environment = var.environment
  Project     = "my-project"
  ManagedBy   = "terraform"
  CostCenter  = "engineering"
}
```

### 5. Use Modules

Create reusable modules:

```
infrastructure/
├── modules/
│   ├── vpc/
│   ├── compute/
│   └── database/
└── environments/
    ├── dev/
    ├── staging/
    └── production/
```

## Resources

- **IaC README**: `templates/iac/README.md`
- **MCP Configuration Guide**: `templates/iac/mcp-configs/README.md`
- **Infrastructure Template**: `templates/iac/specs/infrastructure-spec-template.md`
- **Spec-Kit Docs**: https://github.com/github/spec-kit

## Getting Help

- Open an issue: https://github.com/github/spec-kit/issues
- Discussions: https://github.com/github/spec-kit/discussions
- Check the FAQ: `templates/iac/FAQ.md`

---

**You're ready to build infrastructure with AI assistance!** 🚀

Start with a simple infrastructure spec and iterate. The MCP servers will help you understand your current infrastructure, estimate costs, and deploy changes safely.
