# Infrastructure Specification Command

## Command: `/speckit.specify-infrastructure`

Create or update infrastructure specifications for cloud deployments using Infrastructure as Code (IaC) principles.

## Usage

```
/speckit.specify-infrastructure <infrastructure-description>
```

### Examples

```
/speckit.specify-infrastructure Deploy a highly available web application on AWS with auto-scaling, RDS database, and CloudFront CDN

/speckit.specify-infrastructure Create a multi-region Azure infrastructure with AKS clusters, Azure SQL, and blob storage for a SaaS application

/speckit.specify-infrastructure Set up a GCP infrastructure for machine learning workloads with GKE, Cloud Storage, and BigQuery

/speckit.specify-infrastructure Deploy a hybrid cloud setup spanning AWS and IBM Cloud with VPN connectivity
```

## What This Command Does

1. **Analyzes Infrastructure Requirements**: Extracts compute, networking, storage, and database needs from your description
2. **Generates Infrastructure Specification**: Creates a comprehensive spec following IaC best practices
3. **Identifies Cloud Resources**: Maps requirements to specific cloud provider services
4. **Defines Success Criteria**: Establishes measurable infrastructure metrics
5. **Creates Deployment Strategy**: Outlines deployment process and rollback procedures

## MCP Server Integration

This command works seamlessly with MCP servers for cloud providers. Ensure you have configured the appropriate MCP servers:

- **AWS**: Use `templates/iac/mcp-configs/aws.mcp.json`
- **Azure**: Use `templates/iac/mcp-configs/azure.mcp.json`
- **GCP**: Use `templates/iac/mcp-configs/gcp.mcp.json`
- **IBM Cloud**: Use `templates/iac/mcp-configs/ibm.mcp.json`
- **Multi-Cloud**: Use `templates/iac/mcp-configs/all-clouds.mcp.json`

Copy the appropriate configuration to `.mcp.json` in your project root.

## Specification Template

The command uses the infrastructure specification template located at:
`templates/iac/specs/infrastructure-spec-template.md`

## Required Sections

Your infrastructure specification will include:

### 1. Infrastructure Overview
- Purpose and business need
- High-level architecture diagram
- Cloud provider selection

### 2. Infrastructure Requirements
- **Functional Requirements**: What the infrastructure must do
- **Non-Functional Requirements**:
  - Performance metrics
  - Scalability targets
  - Reliability and availability
  - Security requirements
  - Cost constraints

### 3. Cloud Provider Resources
- Compute resources (EC2, VMs, Compute Engine, VSI)
- Networking (VPC, subnets, load balancers)
- Storage (S3, Blob Storage, Cloud Storage, COS)
- Database (RDS, Azure SQL, Cloud SQL, Databases)
- Monitoring and logging
- Security components

### 4. Deployment Strategy
- Environment definitions (dev, staging, production)
- Deployment process
- Rollback strategy

### 5. Infrastructure as Code Structure
- Directory organization
- State management
- Module design

### 6. Testing Strategy
- Static analysis
- Security scanning
- Cost estimation
- Compliance validation

### 7. Disaster Recovery
- Backup strategy
- Recovery procedures
- RTO and RPO targets

### 8. Monitoring & Alerting
- Metrics to monitor
- Alert definitions
- Observability strategy

## Best Practices

### Security
- Always encrypt data at rest and in transit
- Use least privilege access (IAM roles, RBAC)
- Implement network segmentation
- Enable audit logging
- Use secrets management services

### Cost Optimization
- Right-size instances based on actual usage
- Use auto-scaling to match demand
- Leverage reserved instances or savings plans
- Implement resource tagging for cost allocation
- Set up cost alerts and budgets

### Reliability
- Deploy across multiple availability zones
- Implement health checks and auto-recovery
- Use managed services where possible
- Design for failure scenarios
- Maintain infrastructure versioning

### IaC Best Practices
- Use modules for reusable components
- Keep state files secure and encrypted
- Implement peer review for infrastructure changes
- Version control all infrastructure code
- Use consistent naming conventions
- Document architectural decisions

## Next Steps

After creating the infrastructure specification:

1. **Review and Clarify**: Address any `[NEEDS CLARIFICATION]` items
2. **Plan Implementation**: Use `/speckit.plan-infrastructure` to create detailed implementation plan
3. **Configure MCP Servers**: Set up cloud provider MCP servers for AI-assisted infrastructure management
4. **Set Up IaC Repository**: Organize infrastructure code following the defined structure
5. **Deploy to Development**: Start with non-production environment
6. **Validate and Test**: Run security scans, cost estimation, and compliance checks
7. **Deploy to Production**: Follow the defined deployment strategy

## Related Commands

- `/speckit.plan-infrastructure` - Generate infrastructure implementation plan
- `/speckit.analyze-infrastructure` - Analyze infrastructure specifications for consistency
- `/speckit.cost-estimate` - Estimate infrastructure costs
- `/speckit.security-scan` - Scan infrastructure for security issues

## Cloud Provider Specifics

### AWS
- Emphasizes CloudFormation or Terraform
- Use AWS Well-Architected Framework principles
- Leverage AWS-specific services (CloudWatch, Systems Manager, etc.)

### Azure
- Emphasizes ARM templates or Terraform
- Use Azure Advisor recommendations
- Leverage Azure-specific services (Azure Monitor, Key Vault, etc.)

### Google Cloud
- Emphasizes Deployment Manager or Terraform
- Use Google Cloud Architecture Framework
- Leverage GCP-specific services (Cloud Monitoring, Secret Manager, etc.)

### IBM Cloud
- Emphasizes Schematics (Terraform) or Ansible
- Use IBM Cloud Architecture Center guidance
- Leverage IBM-specific services (IBM Cloud Monitoring, Key Protect, etc.)

## Environment Variables

Ensure you have set up the required environment variables for your chosen cloud provider(s). See `templates/iac/mcp-configs/README.md` for details.

## Support

For issues or questions:
- Check the IaC MCP configurations README
- Review cloud provider documentation
- Consult the Spec-Kit documentation
- Open an issue on the Spec-Kit GitHub repository
