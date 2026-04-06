# Terraform Technical Context

Core Terraform concepts, patterns, and best practices for module development.

---

## Core Concepts

### Module Structure

A reusable Terraform module consists of:

| File | Purpose |
|------|---------|
| `main.tf` | Resource definitions |
| `variables.tf` | Input variable declarations |
| `outputs.tf` | Output value declarations |
| `versions.tf` | Terraform and provider version constraints |
| `README.md` | Documentation |

### Terminology

| Term | Description |
|------|-------------|
| **Root module** | The working directory where `terraform` commands are run |
| **Child module** | A module called by another module using `module` blocks |
| **Resource** | A cloud infrastructure object managed by Terraform |
| **Data source** | Read-only reference to existing infrastructure |
| **Provider** | Plugin that interfaces with cloud APIs |
| **State** | Terraform's record of managed infrastructure |
| **Workspace** | Named state container for managing multiple environments |

---

## Variable Declarations

### Type Constraints

| Type | Example | Notes |
|------|---------|-------|
| `string` | `type = string` | Most common for names, IDs |
| `number` | `type = number` | Integer or float |
| `bool` | `type = bool` | true/false |
| `list(string)` | `type = list(string)` | Ordered list |
| `map(string)` | `type = map(string)` | String key-value pairs |
| `object({...})` | `type = object({ name = string })` | Structured type |
| `any` | `type = any` | Avoid — use explicit types |

### Validation Blocks

```hcl
variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}
```

### Sensitive Variables

```hcl
variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}
```

---

## Resource Arguments vs. Computed Attributes

Understanding the distinction is essential for writing correct HCL:

| Category | Description | Used In |
|----------|-------------|---------|
| **Arguments** | Inputs you provide to configure the resource | Resource block body |
| **Computed** | Values known only after apply (set by the provider) | `output` values, other resource references |

### Example

```hcl
resource "aws_db_instance" "primary" {
  # Arguments (you set these):
  engine         = "postgres"
  instance_class = var.instance_class

  # Terraform sets these after apply (computed):
  # endpoint — reference as: aws_db_instance.primary.endpoint
  # arn      — reference as: aws_db_instance.primary.arn
  # id       — reference as: aws_db_instance.primary.id
}

output "db_endpoint" {
  description = "Database connection endpoint"
  value       = aws_db_instance.primary.endpoint  # computed attribute
}
```

---

## Outputs

### Standard Pattern

```hcl
output "resource_id" {
  description = "The unique identifier of the resource"
  value       = aws_resource_type.name.id
}

output "resource_endpoint" {
  description = "The connection endpoint"
  value       = aws_resource_type.name.endpoint
}

output "connection_string" {
  description = "Full connection string (sensitive)"
  value       = "postgresql://${aws_db_instance.primary.endpoint}:5432/${var.db_name}"
  sensitive   = true
}
```

---

## Tagging

### AWS — default_tags (Preferred)

Apply tags to all resources via the provider block:

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      managed-by  = "terraform"
      environment = var.environment
      project     = var.project_name
    }
  }
}
```

Per-resource tags merge with default_tags:

```hcl
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project}-logs-${var.environment}"

  tags = {
    purpose = "application-logs"  # merges with default_tags
  }
}
```

### AWS — Per-Resource Tags (Alternative)

```hcl
locals {
  common_tags = {
    managed-by  = "terraform"
    environment = var.environment
  }
}

resource "aws_instance" "web" {
  # ...
  tags = merge(local.common_tags, var.tags, {
    Name = "${var.project}-web-${var.environment}"
  })
}
```

### Azure — Per-Resource Tags

```hcl
resource "azurerm_resource_group" "main" {
  name     = "${var.project}-${var.environment}-rg"
  location = var.location

  tags = merge(local.common_tags, var.tags)
}
```

### GCP — Labels (Not Tags)

GCP uses `labels`, not `tags`:

```hcl
resource "google_sql_database_instance" "main" {
  name             = "${var.project}-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.tier

    user_labels = merge(local.common_labels, var.labels)
  }
}
```

---

## Provider Version Pinning

### Version Constraint Operators

| Operator | Example | Meaning |
|----------|---------|---------|
| `~>` (pessimistic) | `~> 5.0` | `>= 5.0, < 6.0` — allows minor/patch |
| `~>` (patch-only) | `~> 5.0.3` | `>= 5.0.3, < 5.1.0` — allows only patch |
| `>=` | `>= 5.0` | Any version 5.0 or higher — avoid |
| `=` | `= 5.0.3` | Exact version — too restrictive |

**Always use `~>` with at least major.minor for providers.**

```hcl
terraform {
  required_version = ">= 1.6, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
```

---

## Backend Configuration

### S3 Backend (AWS)

```hcl
terraform {
  backend "s3" {
    bucket         = "<project>-terraform-state"
    key            = "<path>/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "<project>-terraform-locks"
    encrypt        = true
  }
}
```

### Azure Blob Storage Backend

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "<rg-name>"
    storage_account_name = "<storage-account>"
    container_name       = "tfstate"
    key                  = "<path>/terraform.tfstate"
  }
}
```

### GCS Backend (GCP)

```hcl
terraform {
  backend "gcs" {
    bucket = "<project>-terraform-state"
    prefix = "terraform/state"
  }
}
```

---

## Locals

Use `locals` for computed values and DRY patterns:

```hcl
locals {
  # Common tags for all resources
  common_tags = {
    managed-by  = "terraform"
    environment = var.environment
    project     = var.project_name
  }

  # Computed name prefix
  name_prefix = "${var.project_name}-${var.environment}"

  # Conditional value
  is_production = var.environment == "prod"
}
```

---

## Data Sources

Reference existing infrastructure without managing it:

```hcl
# Look up an existing VPC by tag
data "aws_vpc" "main" {
  tags = {
    Name = "${var.project}-${var.environment}-vpc"
  }
}

# Reference in a resource
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = data.aws_vpc.main.private_subnet_ids
}
```

---

## Security Patterns

### No Hardcoded Secrets

```hcl
# ❌ Never do this
resource "aws_db_instance" "bad" {
  password = "mysecretpassword"
}

# ✅ Use a variable with sensitive = true
variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

resource "aws_db_instance" "good" {
  password = var.db_password
}
```

### Retrieve Secrets from Secrets Manager

```hcl
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "${var.project}/db/master-password"
}

resource "aws_db_instance" "primary" {
  password = jsondecode(data.aws_secretsmanager_secret_version.db_password.secret_string)["password"]
}
```

### Encryption at Rest

```hcl
# AWS RDS
resource "aws_db_instance" "primary" {
  storage_encrypted = true
  kms_key_id        = var.kms_key_arn  # optional; uses AWS default key if omitted
}

# AWS S3
resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# AWS EBS
resource "aws_ebs_volume" "data" {
  encrypted = true
}
```

### Block Public Access

```hcl
# AWS S3 — block all public access
resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# AWS RDS — no public access
resource "aws_db_instance" "primary" {
  publicly_accessible = false
}
```

---

## Schema Lookup

### How to Find Resource Arguments

**CRITICAL**: Never guess argument names. Use the Terraform Registry.

#### Primary: registry.terraform.io

```
search_web("site:registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance")
```

URL pattern:
```
https://registry.terraform.io/providers/hashicorp/<provider>/latest/docs/resources/<resource_type>
```

| Provider | Example Resource | URL Pattern |
|----------|-----------------|-------------|
| **AWS** | `aws_db_instance` | `registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance` |
| **Azure** | `azurerm_mssql_database` | `registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/mssql_database` |
| **GCP** | `google_sql_database_instance` | `registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_database_instance` |

#### What to Extract

From the registry docs extract:
- **Argument Reference**: all supported arguments, which are required vs. optional
- **Attributes Reference**: computed attributes available for outputs and cross-resource references
- **Example Usage**: canonical usage patterns

---

## Common Naming Patterns

### AWS Resource Names

```hcl
# Include project + environment in resource names for uniqueness
locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_db_instance" "primary" {
  identifier = "${local.name_prefix}-postgres"
  # ...
}

resource "aws_s3_bucket" "logs" {
  bucket = "${local.name_prefix}-logs"
  # ...
}
```

### Azure Resource Names

```hcl
resource "azurerm_sql_server" "main" {
  name                = "${var.project}-${var.environment}-sql"
  resource_group_name = azurerm_resource_group.main.name
  # ...
}
```

---

## Best Practices Summary

### Module Design

| Practice | Description |
|----------|-------------|
| **One resource domain per module** | `database` module, not `database-and-networking` |
| **Accept tags/labels as variable** | `variable "tags" { type = map(string) }` for caller merging |
| **Provide sensible defaults** | Reduce required variables; use safe defaults |
| **Use validation blocks** | Constrain inputs; fail early with clear messages |
| **Pin provider versions** | Use `~>` — protect callers from unexpected changes |

### Security

| Practice | Description |
|----------|-------------|
| **Sensitive variables** | Mark passwords, tokens, keys as `sensitive = true` |
| **Encryption by default** | Enable `encrypted = true`, `storage_encrypted = true` by default |
| **No public access by default** | Default `publicly_accessible = false`; expose override variable |
| **No hardcoded secrets** | Use `sensitive` variables or data sources from secrets managers |

### Operations

| Practice | Description |
|----------|-------------|
| **Remote state** | Never use local state for shared infrastructure |
| **State locking** | Use DynamoDB (S3 backend) or equivalent |
| **Gitignore state files** | Always include `*.tfstate`, `.terraform/` in `.gitignore` |
| **`terraform validate`** | Run before every PR; catches syntax and type errors |
| **`terraform fmt`** | Format HCL consistently using canonical style |

### Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| Hardcoded regions | Inflexible, blocks multi-region | Use `var.region` |
| Hardcoded account IDs | Breaks across accounts/environments | Use data sources |
| No output descriptions | Self-documenting code is essential | Always set `description` |
| Unpinned providers | Unexpected breaking changes on `init` | Use `~> major.minor` |
| Monolithic root modules | Hard to reuse and test | Extract to child modules |
| `terraform.tfvars` in version control | May contain secrets | Use `.gitignore`; use env vars for secrets |
