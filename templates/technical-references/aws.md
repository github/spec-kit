# AWS Cloud Context

AWS documentation and Crossplane provider context.

---

## MCP Tools

### Lookup Flow (Prioritized)

Follow this fallback chain for AWS documentation:

1. **aws-documentation MCP** (Primary)
2. **search_web** (Final fallback)

### 1. Primary: aws-documentation MCP

| Tool | Purpose | Example |
|------|---------|---------|
| `search_documentation` | Search AWS docs | `"RDS PostgreSQL encryption"` |
| `read_documentation` | Read full doc page | Use URL from search |
| `recommend` | Best practices | `"S3 bucket security"` |

**Usage:**
```
1. search_documentation
   Query: "AWS <service> <topic>"
   Example: "AWS RDS PostgreSQL instance configuration"

2. read_documentation
   URL: <from search results>

3. recommend (optional)
   Topic: "<service> security best practices"
```

### 2. Final Fallback: search_web

Use when aws-documentation MCP fails or is unavailable:

```
search_web("site:marketplace.upbound.io provider-aws-<family> <Resource> apiVersion")
search_web("site:docs.aws.amazon.com <service> <topic>")
search_web("site:doc.crds.dev provider-aws-<family> <Resource> v1beta1")

Examples:
- search_web("site:marketplace.upbound.io provider-aws-rds Instance apiVersion")
- search_web("site:docs.aws.amazon.com RDS encryption best practices")
- search_web("site:doc.crds.dev upbound provider-aws rds Instance v1beta1")
```

---

## Documentation URLs

| Source | URL Pattern |
|--------|-------------|
| AWS Docs | `https://docs.aws.amazon.com/<service>/` |
| Upbound Marketplace | `https://marketplace.upbound.io/providers/upbound/provider-aws-<family>` |
| GitHub Provider | `https://github.com/upbound/provider-aws` |
| CRD Docs | `https://doc.crds.dev/github.com/upbound/provider-aws` |

---

## Provider Packages

AWS uses family providers. Install only what you need:

| Family | Package | Common Resources |
|--------|---------|------------------|
| S3 | `provider-aws-s3` | Bucket, BucketPolicy, BucketPublicAccessBlock |
| RDS | `provider-aws-rds` | Instance, Cluster, SubnetGroup |
| EKS | `provider-aws-eks` | Cluster, NodeGroup, Addon |
| EC2 | `provider-aws-ec2` | VPC, Subnet, SecurityGroup, Instance |
| IAM | `provider-aws-iam` | Role, Policy, RolePolicyAttachment |
| Lambda | `provider-aws-lambda` | Function, Permission |
| DynamoDB | `provider-aws-dynamodb` | Table |
| ElastiCache | `provider-aws-elasticache` | Cluster, ReplicationGroup |

---

## API Patterns

### API Version Format

```
<family>.aws.upbound.io/v1beta1
```

**Examples**:
- `s3.aws.upbound.io/v1beta1`
- `rds.aws.upbound.io/v1beta1`
- `ec2.aws.upbound.io/v1beta1`

### Common forProvider Fields

| Field | Type | Description |
|-------|------|-------------|
| `region` | string | AWS region (e.g., `us-west-2`) |
| `tags` | map | Resource tags |

### Cross-Resource References

```yaml
# Selector (preferred in compositions)
bucketSelector:
  matchControllerRef: true

# Direct reference
bucketRef:
  name: my-bucket
```

### Common Status Fields

| Path | Description |
|------|-------------|
| `status.atProvider.arn` | Resource ARN |
| `status.atProvider.id` | Resource ID |
| `status.atProvider.endpoint` | Connection endpoint |

---

## Provider Configuration

```yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-secret
      key: creds
```
