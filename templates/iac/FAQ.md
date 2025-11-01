# Infrastructure as Code - Frequently Asked Questions

## General Questions

### What is the IaC extension for Spec-Kit?

The IaC extension brings Infrastructure as Code workflows to Spec-Kit, allowing you to use specification-driven development for cloud infrastructure. It includes MCP (Model Context Protocol) server configurations for major cloud providers, enabling AI-assisted infrastructure management.

### Which cloud providers are supported?

The IaC extension supports:
- **AWS** (Amazon Web Services)
- **Azure** (Microsoft Azure)
- **GCP** (Google Cloud Platform)
- **IBM Cloud**
- **Multi-cloud** scenarios combining multiple providers

### What is MCP (Model Context Protocol)?

MCP is an open standard created by Anthropic that enables AI assistants to securely connect to external tools and services. In the context of IaC, MCP servers provide Claude Code with the ability to interact with cloud provider APIs.

### Do I need to install MCP servers manually?

No! The configurations use `npx` which automatically downloads and runs the MCP servers when needed. No manual installation is required.

## Setup and Configuration

### Where should I put the MCP configuration file?

You have three options:

1. **Project-scoped** (recommended): `.mcp.json` in your project root
2. **Claude-specific**: `.claude/settings.local.json` in your project
3. **User-wide**: `~/.claude/settings.local.json` in your home directory

For infrastructure projects, we recommend project-scoped configuration that can be version-controlled (without credentials).

### How do I secure my cloud credentials?

**DO:**
- Use environment variables (`.env` file)
- Add `.env`, `.mcp.json`, and credential files to `.gitignore`
- Use cloud provider IAM roles when possible
- Rotate credentials regularly
- Use least privilege access

**DON'T:**
- Hardcode credentials in configuration files
- Commit credential files to version control
- Share credentials via email or chat
- Use root/admin credentials for infrastructure deployment

### Can I use multiple cloud providers in one project?

Yes! Use the `all-clouds.mcp.json` configuration and set environment variables for all cloud providers you need. The MCP servers will be available for all configured providers.

### What permissions do my cloud credentials need?

This depends on your infrastructure needs, but follow the principle of least privilege:

**AWS**: Create an IAM user with policies matching your infrastructure resources (e.g., `AmazonEC2FullAccess`, `AmazonRDSFullAccess` for EC2 and RDS management)

**Azure**: Create a service principal with role assignments matching your resources (e.g., `Contributor` role scoped to specific resource groups)

**GCP**: Create a service account with roles matching your resources (e.g., `Compute Admin`, `Storage Admin`)

**IBM Cloud**: Create an API key with access policies matching your resources

Start with minimal permissions and add more as needed.

## Using MCP Servers

### How do I test if my MCP servers are working?

Start Claude Code in your project and try simple queries:

```
List my EC2 instances
Show my resource groups
What GCP projects do I have access to?
```

If the MCP servers are configured correctly, Claude Code will return actual data from your cloud provider.

### What can I do with MCP servers?

MCP servers enable Claude Code to:
- **Query** current infrastructure state
- **List** resources across your cloud accounts
- **Get** pricing and cost information
- **Check** resource configurations
- **Analyze** infrastructure for optimization opportunities
- **Assist** with infrastructure planning and troubleshooting

**Note**: The level of control (read vs. write) depends on the specific MCP server implementation.

### Are MCP servers safe to use?

Yes, when configured properly:
- MCP servers use your existing cloud credentials (same as CLI tools)
- They respect IAM/RBAC permissions
- They don't introduce new security vectors beyond your cloud provider's API
- You control what credentials are provided

**Security tips**:
- Only use official MCP servers from trusted sources
- Review MCP server permissions before use
- Monitor API usage in your cloud provider console
- Audit logs for unusual activity

### Can MCP servers modify my infrastructure?

This depends on the specific MCP server and your credentials. Most MCP servers are read-only for safety. Check the MCP server documentation and test with read-only credentials first.

## Infrastructure Specifications

### How is an infrastructure spec different from a feature spec?

Infrastructure specs focus on:
- **Non-functional requirements**: Performance, scalability, reliability
- **Cloud resources**: Specific services and configurations
- **Deployment strategy**: How infrastructure is deployed
- **Cost constraints**: Budget and optimization
- **Disaster recovery**: Backup and recovery procedures

Feature specs focus on:
- **User scenarios**: What users can do
- **Functional requirements**: What the system must do
- **Success criteria**: How to measure success

### Do I need to know IaC tools to use this?

Not to create specifications! You can specify infrastructure requirements in natural language. However, to implement the infrastructure, you'll need to use an IaC tool like:
- Terraform (recommended, works with all providers)
- AWS CloudFormation (AWS only)
- Azure ARM Templates (Azure only)
- Google Cloud Deployment Manager (GCP only)
- IBM Cloud Schematics (IBM Cloud only)

### Can I use existing infrastructure code with Spec-Kit?

Yes! You can:
1. Create specs from existing infrastructure (reverse engineering)
2. Use specs to validate existing infrastructure
3. Generate specs as documentation for existing code
4. Use MCP servers to query existing infrastructure

### How do I specify multi-cloud infrastructure?

In your infrastructure description, specify which services run on which cloud:

```
/speckit.specify-infrastructure Create a multi-cloud setup:
- Primary application on AWS using EKS in us-east-1
- Disaster recovery site on GCP using GKE in us-central1
- CDN using CloudFront (AWS)
- Centralized logging using IBM Cloud Log Analysis
- Cross-cloud VPN connectivity
```

## IaC Tools and Workflows

### Which IaC tool should I use?

**Terraform** (recommended for most cases):
- ✅ Multi-cloud support
- ✅ Large ecosystem and community
- ✅ Supports all major cloud providers
- ✅ Reusable modules
- ✅ State management

**CloudFormation** (AWS only):
- ✅ Native AWS integration
- ✅ No state management needed
- ✅ Good for AWS-only projects
- ❌ AWS-specific syntax

**ARM Templates** (Azure only):
- ✅ Native Azure integration
- ✅ Azure-specific features
- ❌ Complex syntax
- ❌ Azure only

**Pulumi** (alternative):
- ✅ Use programming languages (Python, TypeScript, etc.)
- ✅ Multi-cloud support
- ✅ Type safety
- ❌ Smaller ecosystem than Terraform

### How do I organize my IaC code?

Recommended structure:

```
infrastructure/
├── modules/           # Reusable modules
│   ├── networking/
│   ├── compute/
│   └── database/
├── environments/      # Environment-specific configs
│   ├── dev/
│   ├── staging/
│   └── production/
├── variables/         # Variable files
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── production.tfvars
└── backend.tf        # State backend configuration
```

### How do I manage state files?

**Best practices**:
1. **Use remote state**: S3, Azure Storage, GCS, or Terraform Cloud
2. **Enable encryption**: Encrypt state at rest
3. **Use locking**: Prevent concurrent modifications
4. **Backup state**: Regular backups of state files
5. **Version state**: Keep state file history

**Example Terraform backend configuration (AWS)**:
```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### How do I test infrastructure changes?

**Pre-deployment testing**:
1. **Syntax validation**: `terraform validate`
2. **Security scanning**: `tfsec .` or `checkov -d .`
3. **Cost estimation**: `infracost breakdown --path .`
4. **Compliance**: `terraform-compliance` or `OPA`
5. **Plan review**: `terraform plan`

**Post-deployment testing**:
1. **Smoke tests**: Verify basic functionality
2. **Integration tests**: Test service connectivity
3. **Performance tests**: Verify performance requirements
4. **Monitoring**: Check metrics and logs

## Cost Management

### How do I estimate infrastructure costs?

Use cost estimation tools:

**Infracost** (Terraform):
```bash
# Install
brew install infracost

# Estimate costs
infracost breakdown --path infrastructure/

# Compare changes
infracost diff --path infrastructure/
```

**AWS Pricing Calculator**: https://calculator.aws.amazon.com/
**Azure Pricing Calculator**: https://azure.microsoft.com/en-us/pricing/calculator/
**GCP Pricing Calculator**: https://cloud.google.com/products/calculator
**IBM Cloud Cost Estimator**: https://cloud.ibm.com/estimator

You can also query pricing via MCP servers:
```
What's the cost of a t3.medium EC2 instance in us-east-1?
Estimate the monthly cost for 100GB of S3 storage
```

### How do I optimize infrastructure costs?

**Strategies**:
1. **Right-size instances**: Match instance types to workload
2. **Use auto-scaling**: Scale based on demand
3. **Reserved instances**: Commit for 1-3 years for discounts
4. **Spot instances**: Use for fault-tolerant workloads
5. **Delete unused resources**: Regular cleanup
6. **Use managed services**: Often cheaper than self-managed
7. **Optimize storage**: Use appropriate storage tiers
8. **Monitor and alert**: Set up cost alerts

Ask Claude Code via MCP servers:
```
Analyze my infrastructure for cost optimization opportunities
What are my most expensive resources?
Suggest cheaper alternatives for my current setup
```

### How do I set up cost alerts?

**AWS**:
```
Set up a CloudWatch budget alert for $1000 monthly spend
Configure AWS Budgets with email notifications
```

**Azure**:
```
Create an Azure budget with alert rules
Set up cost alerts in Azure Cost Management
```

**GCP**:
```
Configure GCP budget alerts
Set up billing export to BigQuery for analysis
```

## Security and Compliance

### How do I ensure my infrastructure is secure?

**Security checklist**:
- ✅ Encrypt data at rest and in transit
- ✅ Use security groups/firewalls
- ✅ Enable audit logging
- ✅ Use secrets management (not hardcoded secrets)
- ✅ Implement least privilege access
- ✅ Enable multi-factor authentication
- ✅ Regular security scanning
- ✅ Compliance validation

**Tools**:
- `tfsec` - Terraform security scanner
- `checkov` - Policy-as-code scanner
- `terrascan` - Detect compliance violations
- Cloud provider security services (GuardDuty, Security Center, etc.)

### What compliance standards are supported?

Common standards:
- **SOC 2**: Security and availability controls
- **HIPAA**: Healthcare data protection
- **PCI-DSS**: Payment card security
- **ISO 27001**: Information security management
- **GDPR**: Data privacy and protection

Use compliance scanning tools:
```bash
# Check compliance
terraform-compliance -f compliance-policies/ -p plan.out

# Or use OPA (Open Policy Agent)
conftest test infrastructure/
```

### How do I manage secrets?

**DO**:
- Use cloud provider secrets services:
  - AWS: Secrets Manager or Parameter Store
  - Azure: Key Vault
  - GCP: Secret Manager
  - IBM: Key Protect or Secrets Manager
- Reference secrets in IaC, don't include values
- Rotate secrets regularly
- Use environment variables for local development

**DON'T**:
- Hardcode secrets in code
- Commit secrets to version control
- Share secrets via email or chat
- Use the same secrets across environments

**Example Terraform reference**:
```hcl
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/db/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

## Troubleshooting

### MCP server won't connect

**Checklist**:
1. ✅ Is `.mcp.json` in the correct location?
2. ✅ Are environment variables set? (`echo $AWS_ACCESS_KEY_ID`)
3. ✅ Is Node.js installed? (`node --version`)
4. ✅ Can you access the cloud provider? (try CLI: `aws sts get-caller-identity`)
5. ✅ Are credentials valid and not expired?
6. ✅ Do credentials have required permissions?

**Debug steps**:
```bash
# Check environment variables
env | grep AWS
env | grep AZURE
env | grep GCP
env | grep IBM

# Clear npm cache
npm cache clean --force

# Restart Claude Code
```

### Terraform apply fails

**Common causes**:
1. **Insufficient permissions**: Add required IAM permissions
2. **Resource conflicts**: Check for existing resources with same name
3. **Invalid configuration**: Run `terraform validate`
4. **State lock**: Wait for lock release or force unlock (carefully!)
5. **API rate limits**: Add retry logic or wait

**Debug steps**:
```bash
# Validate syntax
terraform validate

# Format code
terraform fmt

# Show plan
terraform plan

# Enable debug logging
TF_LOG=DEBUG terraform apply
```

### State file is corrupted

**Recovery steps**:
1. **Restore from backup**: Use latest known good state
2. **Import resources**: Manually import existing resources
3. **Recreate state**: Last resort, carefully reconstruct state

**Prevention**:
- Use remote state with versioning
- Regular backups
- Use state locking
- Never manually edit state files

### Cost exceeds budget

**Immediate actions**:
1. Identify expensive resources: Check cloud provider console
2. Stop non-essential resources
3. Review auto-scaling configurations
4. Check for resource leaks (unattached volumes, unused IPs, etc.)

**Long-term solutions**:
1. Set up cost alerts
2. Regular cost reviews
3. Implement auto-shutdown for dev/test environments
4. Use cost allocation tags
5. Review and optimize regularly

## Best Practices

### What are the infrastructure code review best practices?

**Review checklist**:
- ✅ Security: No hardcoded secrets, proper encryption, least privilege
- ✅ Cost: Appropriate instance sizes, no waste
- ✅ Reliability: Multi-AZ deployment, backups, monitoring
- ✅ Naming: Consistent resource naming
- ✅ Tagging: Proper resource tags
- ✅ Documentation: Clear comments and README
- ✅ Testing: Plan reviewed, validation passed
- ✅ Compliance: Meets security/compliance requirements

### How do I handle multiple environments?

**Approaches**:

**1. Terraform Workspaces**:
```bash
terraform workspace new dev
terraform workspace new staging
terraform workspace new production
```

**2. Separate directories**:
```
environments/
├── dev/
├── staging/
└── production/
```

**3. Variable files**:
```bash
terraform apply -var-file="environments/dev.tfvars"
```

**Recommendation**: Use separate directories for production isolation.

### How do I handle infrastructure dependencies?

**Strategies**:
1. **Module dependencies**: Use explicit `depends_on`
2. **Data sources**: Reference existing resources
3. **Remote state**: Share outputs between stacks
4. **Service discovery**: Use DNS or service mesh

**Example**:
```hcl
# Reference remote state
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-terraform-state"
    key    = "network/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use outputs from network stack
resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.subnet_id
}
```

## Getting Help

### Where can I get help?

- **Spec-Kit Issues**: https://github.com/github/spec-kit/issues
- **Discussions**: https://github.com/github/spec-kit/discussions
- **Documentation**: Check `templates/iac/README.md`
- **MCP Guide**: Check `templates/iac/mcp-configs/README.md`
- **Quick Start**: Check `templates/iac/QUICKSTART.md`

### How do I report bugs or request features?

1. Check existing issues: https://github.com/github/spec-kit/issues
2. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, cloud provider, tool versions)
   - Configuration files (sanitized, no credentials!)

### How do I contribute?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

See the main Spec-Kit CONTRIBUTING.md for details.

---

**Still have questions?** Open a discussion: https://github.com/github/spec-kit/discussions
