# Infrastructure as Code (IaC) Templates for Spec-Kit

This directory contains templates and configurations for using Spec-Kit with Infrastructure as Code workflows across major cloud providers.

## Overview

Spec-Kit's IaC extension brings the power of Spec-Driven Development to infrastructure management, enabling you to:

- **Specify infrastructure requirements** using natural language
- **Connect to cloud providers** via MCP (Model Context Protocol) servers
- **Manage infrastructure** with AI assistance across AWS, Azure, GCP, and IBM Cloud
- **Follow IaC best practices** with built-in templates and guidelines
- **Maintain consistency** between infrastructure specs and actual deployments

## Directory Structure

```
templates/iac/
├── README.md                          # This file
├── mcp-configs/                       # MCP server configurations
│   ├── README.md                      # MCP configuration guide
│   ├── aws.mcp.json                   # AWS MCP servers
│   ├── azure.mcp.json                 # Azure MCP servers
│   ├── gcp.mcp.json                   # Google Cloud MCP servers
│   ├── ibm.mcp.json                   # IBM Cloud MCP servers
│   └── all-clouds.mcp.json            # Combined multi-cloud config
├── specs/                             # Infrastructure specification templates
│   └── infrastructure-spec-template.md # Infrastructure spec template
└── commands/                          # IaC-specific commands
    └── specify-infrastructure.md      # Infrastructure specification command
```

## Quick Start

### 1. Choose Your Cloud Provider

Select the cloud provider(s) you want to work with:
- **AWS** (Amazon Web Services)
- **Azure** (Microsoft Azure)
- **GCP** (Google Cloud Platform)
- **IBM Cloud**
- **Multi-Cloud** (combination of the above)

### 2. Configure MCP Servers

Copy the appropriate MCP configuration to your project:

```bash
# For AWS
cp templates/iac/mcp-configs/aws.mcp.json .mcp.json

# For Azure
cp templates/iac/mcp-configs/azure.mcp.json .mcp.json

# For Google Cloud
cp templates/iac/mcp-configs/gcp.mcp.json .mcp.json

# For IBM Cloud
cp templates/iac/mcp-configs/ibm.mcp.json .mcp.json

# For multi-cloud projects
cp templates/iac/mcp-configs/all-clouds.mcp.json .mcp.json
```

### 3. Set Environment Variables

Configure credentials for your cloud provider(s). See `mcp-configs/README.md` for detailed instructions.

**AWS Example:**
```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

**Azure Example:**
```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

**GCP Example:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
```

**IBM Cloud Example:**
```bash
export IBM_CLOUD_API_KEY="your-api-key"
export IBM_CLOUD_REGION="us-south"
```

### 4. Create an Infrastructure Specification

Use the infrastructure specification command:

```bash
/speckit.specify-infrastructure Deploy a scalable web application with load balancer, auto-scaling, and managed database
```

This will:
1. Analyze your infrastructure requirements
2. Generate a comprehensive infrastructure specification
3. Map requirements to cloud provider services
4. Create deployment and testing strategies
5. Define success criteria and monitoring

### 5. Implement Your Infrastructure

Follow the generated specification to implement your infrastructure using your preferred IaC tool:
- **Terraform** (recommended for multi-cloud)
- **AWS CloudFormation** (AWS-specific)
- **Azure ARM Templates** (Azure-specific)
- **Google Cloud Deployment Manager** (GCP-specific)
- **IBM Cloud Schematics** (IBM Cloud-specific)
- **Pulumi** or **Ansible** (alternatives)

## Features

### MCP Server Support

The IaC extension includes MCP server configurations for:

#### AWS Services
- AWS API (general access)
- AWS Lambda (serverless functions)
- AWS ECS (container orchestration)
- AWS EKS (Kubernetes)
- AWS S3 (object storage)
- AWS CloudFormation (IaC)
- AWS Pricing (cost estimation)

#### Azure Services
- Azure (general access)
- Azure Storage (blob/file storage)
- Azure Cosmos DB (NoSQL database)
- Azure Functions (serverless)
- Azure AKS (Kubernetes)
- Azure ARM (infrastructure deployment)

#### Google Cloud Services
- GCP (general access)
- Cloud Functions (serverless)
- Cloud Run (containers)
- GKE (Kubernetes)
- Cloud Storage (object storage)
- Deployment Manager (IaC)
- Firestore (NoSQL database)

#### IBM Cloud Services
- IBM Cloud (general access)
- Cloud Functions (serverless)
- Kubernetes Service
- Cloud Object Storage (COS)
- WatsonX (AI/ML)
- Schematics (Terraform-based IaC)
- MCP Context Forge (gateway & registry)

### Infrastructure Specification Template

The infrastructure specification template includes:

- **Infrastructure Overview**: Purpose, architecture, cloud provider selection
- **Requirements**: Functional and non-functional requirements
- **Cloud Resources**: Detailed resource definitions
- **Deployment Strategy**: Environment setup and deployment process
- **IaC Structure**: Code organization and state management
- **Testing Strategy**: Validation and compliance checks
- **Disaster Recovery**: Backup and recovery procedures
- **Monitoring**: Metrics and alerting configuration

## Use Cases

### 1. New Infrastructure Deployment

Create infrastructure from scratch for a new application:

```
/speckit.specify-infrastructure Deploy a three-tier web application on AWS with
CloudFront CDN, Application Load Balancer, EC2 auto-scaling group, and RDS PostgreSQL
database with multi-AZ deployment
```

### 2. Infrastructure Migration

Migrate existing infrastructure to a new cloud provider:

```
/speckit.specify-infrastructure Migrate our existing on-premises application to Azure
with AKS for containers, Azure SQL for the database, and Azure Blob Storage for assets
```

### 3. Multi-Cloud Architecture

Design infrastructure spanning multiple cloud providers:

```
/speckit.specify-infrastructure Create a multi-cloud setup with primary application
on AWS using EKS, secondary disaster recovery site on GCP using GKE, and centralized
monitoring via IBM Cloud
```

### 4. Serverless Infrastructure

Build serverless architecture:

```
/speckit.specify-infrastructure Design a serverless API on GCP using Cloud Functions,
API Gateway, Cloud Storage, and Firestore with global distribution
```

### 5. Data Platform

Create a data processing and analytics platform:

```
/speckit.specify-infrastructure Build a data platform on IBM Cloud with Cloud Object
Storage for data lake, IBM Cloud Databases for PostgreSQL, and WatsonX for ML workloads
```

## Best Practices

### Specification-Driven Infrastructure

1. **Start with the spec**: Define requirements before writing IaC code
2. **Iterate on requirements**: Refine specs based on feedback and constraints
3. **Version your specs**: Track specification changes alongside code changes
4. **Review specs collaboratively**: Get input from security, ops, and cost teams

### Security

1. **Never commit credentials**: Use environment variables and secrets management
2. **Encrypt everything**: Data at rest and in transit
3. **Least privilege**: Minimal IAM permissions for all resources
4. **Network segmentation**: Use VPCs, security groups, and firewalls
5. **Audit logging**: Enable comprehensive logging and monitoring

### Cost Management

1. **Right-size resources**: Match instance types to actual workload needs
2. **Use auto-scaling**: Scale resources based on demand
3. **Leverage spot/preemptible instances**: For non-critical workloads
4. **Set up budgets and alerts**: Monitor costs proactively
5. **Tag resources**: Enable cost allocation and tracking

### Reliability

1. **Multi-AZ deployment**: Distribute across availability zones
2. **Health checks**: Implement comprehensive health monitoring
3. **Auto-recovery**: Enable automatic recovery from failures
4. **Backup strategy**: Regular backups with tested recovery procedures
5. **Disaster recovery**: Define and test DR procedures

### IaC Development

1. **Modular design**: Create reusable infrastructure modules
2. **State management**: Secure and centralize state files
3. **Code review**: Peer review all infrastructure changes
4. **Testing**: Validate infrastructure code before applying
5. **Documentation**: Document architectural decisions and runbooks

## Workflow

### Typical IaC Workflow with Spec-Kit

```
1. Specify Infrastructure
   ↓
   /speckit.specify-infrastructure [description]
   ↓
2. Review Specification
   ↓
   Review generated spec, address clarifications
   ↓
3. Plan Implementation
   ↓
   /speckit.plan-infrastructure
   ↓
4. Set Up IaC Repository
   ↓
   Create directory structure, configure state backend
   ↓
5. Implement Infrastructure Code
   ↓
   Write Terraform/CloudFormation/ARM templates
   ↓
6. Validate and Test
   ↓
   Run static analysis, security scans, cost estimation
   ↓
7. Deploy to Development
   ↓
   Apply infrastructure to dev environment
   ↓
8. Test in Development
   ↓
   Run integration tests, verify functionality
   ↓
9. Deploy to Staging
   ↓
   Apply infrastructure to staging environment
   ↓
10. Deploy to Production
    ↓
    Follow deployment strategy, monitor metrics
    ↓
11. Monitor and Maintain
    ↓
    Track metrics, optimize costs, apply updates
```

## Integration with Spec-Kit Commands

The IaC extension integrates with standard Spec-Kit commands:

- **`/speckit.specify-infrastructure`**: Create infrastructure specification
- **`/speckit.plan`**: Generate implementation plan (works with infrastructure specs)
- **`/speckit.analyze`**: Check consistency across infrastructure artifacts
- **`/speckit.tasks`**: Break down infrastructure implementation into tasks
- **`/speckit.implement`**: Execute infrastructure deployment tasks

## MCP Server Management

### Installing MCP Servers

MCP servers are automatically installed via `npx` when first used. No manual installation required.

### Updating MCP Servers

To update to the latest versions:

```bash
# Clear npm cache
npm cache clean --force

# Servers will automatically update on next use
```

### Troubleshooting MCP Servers

If you encounter issues:

1. **Verify credentials**: Check environment variables are set correctly
2. **Test connectivity**: Ensure network access to cloud provider APIs
3. **Check permissions**: Verify IAM/RBAC permissions are sufficient
4. **Review logs**: Check Claude Code logs for error messages
5. **Update packages**: Clear npm cache and restart

See `mcp-configs/README.md` for detailed troubleshooting.

## Examples

### Example 1: AWS Three-Tier Application

```bash
/speckit.specify-infrastructure Deploy a three-tier web application on AWS:
- CloudFront CDN for content delivery
- Application Load Balancer in public subnets
- EC2 auto-scaling group (2-10 instances) in private subnets
- RDS PostgreSQL with multi-AZ for high availability
- ElastiCache Redis for session management
- S3 for static assets and backups
- CloudWatch for monitoring and logging
- All data encrypted at rest and in transit
- Total cost under $2000/month
```

### Example 2: Azure Microservices Platform

```bash
/speckit.specify-infrastructure Create a microservices platform on Azure:
- Azure Kubernetes Service (AKS) with 3-20 nodes
- Azure Container Registry for Docker images
- Azure SQL Database with geo-replication
- Azure Blob Storage for file uploads
- Azure Service Bus for message queuing
- Azure Monitor and Application Insights for observability
- Azure Key Vault for secrets management
- Support for blue-green deployments
- 99.9% uptime SLA requirement
```

### Example 3: GCP Data Processing Pipeline

```bash
/speckit.specify-infrastructure Build a data processing pipeline on GCP:
- Cloud Storage for data ingestion
- Cloud Dataflow for stream and batch processing
- BigQuery for data warehouse
- Cloud Functions for data transformation
- Cloud Pub/Sub for event streaming
- Cloud Monitoring for pipeline observability
- Automated data quality checks
- Support for 1TB+ daily data volume
- Sub-hour processing latency
```

### Example 4: IBM Cloud AI/ML Platform

```bash
/speckit.specify-infrastructure Deploy an AI/ML platform on IBM Cloud:
- IBM Kubernetes Service for model serving
- Cloud Object Storage for training data
- WatsonX for model training and inference
- IBM Cloud Databases for PostgreSQL for metadata
- IBM Cloud Functions for data preprocessing
- IBM Cloud Monitoring for platform observability
- GPU-enabled compute for training
- Model versioning and A/B testing support
```

## Additional Resources

- **MCP Configuration Guide**: `mcp-configs/README.md`
- **Infrastructure Spec Template**: `specs/infrastructure-spec-template.md`
- **Infrastructure Command**: `commands/specify-infrastructure.md`
- **Spec-Kit Documentation**: [Spec-Kit GitHub](https://github.com/github/spec-kit)
- **Model Context Protocol**: [MCP Documentation](https://modelcontextprotocol.io/)

## Cloud Provider Resources

### AWS
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS MCP Servers Guide](https://aws.amazon.com/solutions/guidance/deploying-model-context-protocol-servers-on-aws/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Azure
- [Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/)
- [Azure MCP Documentation](https://learn.microsoft.com/en-us/azure/ai/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)

### Google Cloud
- [Google Cloud Architecture Framework](https://cloud.google.com/architecture/framework)
- [GCP Best Practices](https://cloud.google.com/docs/enterprise/best-practices-for-enterprise-organizations)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### IBM Cloud
- [IBM Cloud Architecture Center](https://www.ibm.com/cloud/architecture)
- [IBM MCP Context Forge](https://github.com/IBM/mcp-context-forge)
- [Terraform IBM Provider](https://registry.terraform.io/providers/IBM-Cloud/ibm/latest/docs)

## Contributing

To contribute to the IaC templates:

1. Fork the Spec-Kit repository
2. Create a feature branch
3. Add new templates, MCP configurations, or documentation
4. Submit a pull request with clear description

## License

These templates are part of the Spec-Kit project and are licensed under the MIT License.

## Support

For questions or issues:
- Open an issue on [Spec-Kit GitHub](https://github.com/github/spec-kit/issues)
- Check the [Spec-Kit Discussions](https://github.com/github/spec-kit/discussions)
- Review the [MCP Configuration README](mcp-configs/README.md)

---

**Happy Infrastructure Building with Spec-Kit!** 🚀☁️
