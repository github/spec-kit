# Northwind Platform Terraform Coding Style Guide

This document captures both universal Terraform standards (non-negotiable) and project-specific
conventions for the Northwind Platform. All Terraform engineers **MUST** follow these standards
when generating infrastructure code.

---

## 1. IaC Tool & Version

| Setting | Value |
|---------|-------|
| **Terraform Version** | `>= 1.7.0, < 2.0` |
| **Primary Cloud Provider** | AWS |
| **Provider Version(s)** | `hashicorp/aws ~> 5.0`, `hashicorp/random ~> 3.6` |

---

## 2. File Organization

**Module directory structure** (in `infra-modules` repo):

```
modules/
  s3-secure-bucket/
    main.tf
    variables.tf
    outputs.tf
    versions.tf
    README.md
  rds-postgres-multiaz/
    main.tf
    variables.tf
    outputs.tf
    versions.tf
    README.md
```

**Live config structure** (in `terraform-live` repo):

```
terraform-live/
  prod/
    orders/
      events-bucket/
        main.tf            # module call + provider config
        backend.tf         # S3 backend for state
        terraform.tfvars
  staging/
    ...
  dev/
    ...
```

**Non-negotiable rules:**
- File separation: resources in `main.tf`, variables in `variables.tf`, outputs in `outputs.tf`, provider/version constraints in `versions.tf`.
- One module per directory.
- Modules NEVER declare backends or providers — those belong to live configs.
- No inline variables; no inline outputs.

---

## 3. Naming Conventions

### Terraform Identifiers

| Element | Pattern | Example |
|---------|---------|---------|
| Resource name | `snake_case`, descriptive | `aws_s3_bucket.this` |
| Variable name | `snake_case` | `var.bucket_name` |
| Output name | `snake_case` | `bucket_arn` |
| Local value | `snake_case` | `local.required_tags` |
| Module call | `snake_case` | `module.events_bucket` |

### Cloud Resource Names

**Project prefix**: `northwind`

| Resource Category | Naming Pattern | Example |
|-------------------|----------------|---------|
| S3 buckets | `{env}-{team}-{purpose}-{random_suffix}` | `prod-orders-events-x7k2` |
| RDS | `{env}-{team}-{engine}-{purpose}` | `prod-orders-pg-primary` |
| VPCs | `{env}-vpc-main` | `prod-vpc-main` |

**Non-negotiable rules:**
- `snake_case` for Terraform identifiers.
- `kebab-case` for cloud resource `name` arguments.
- Use `var.name` or caller-provided prefix in resource name arguments.
- S3 bucket names append a 4-char `random_id` suffix for global uniqueness.

### API Versioning Policy

| Terraform | Policy |
|-----------|--------|
| `>= 1.7.0, < 2.0` | Minimum 1.7.0. All modules must set `required_version = ">= 1.7, < 2.0"`. Latest stable patch within the supported range. |

---

## 4. Provider Configuration

### Required Provider Block (in every module's `versions.tf`)

```hcl
terraform {
  required_version = ">= 1.7, < 2.0"

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

### Provider Pinning

**ALWAYS** use pessimistic constraint operator (`~>`):

- ✅ `~> 5.0` — allows patch and minor updates within 5.x
- ❌ `>= 5.0` — allows major version bumps
- ❌ `= 5.0.3` — too strict

### Default Tagging (AWS)

**Project standard**: Live configs configure `default_tags` on the `aws` provider using `local.required_tags`. Modules do NOT configure providers — they expect a caller-provided provider with default_tags already set, AND they also merge `local.common_tags` per-resource as a defense-in-depth.

```hcl
# In live config — NOT in modules:
provider "aws" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::${var.account_id}:role/atlantis-runner"
  }

  default_tags {
    tags = local.required_tags
  }
}
```

---

## 5. Variable Declarations

### Required Fields

Every variable **MUST** have:

```hcl
variable "example" {
  description = "<What this variable controls and valid values>"
  type        = <explicit type>
  default     = <value or omit if required>
  # sensitive = true  # for passwords/tokens/keys
}
```

**Non-negotiable rules:**
- `description` is MANDATORY.
- `type` is MANDATORY (no implicit `any`).
- Sensitive variables MUST be marked `sensitive = true`.
- NEVER set a plaintext default for sensitive variables.
- Use `validation` blocks for constrained inputs.

### Standard Validation Patterns

```hcl
variable "environment" {
  description = "Deployment environment: dev, staging, or prod"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "data_classification" {
  description = "Data classification: public, internal, confidential, or restricted"
  type        = string

  validation {
    condition     = contains(["public", "internal", "confidential", "restricted"], var.data_classification)
    error_message = "data_classification must be one of: public, internal, confidential, restricted."
  }
}
```

---

## 6. Resource Tagging

**ALWAYS** add tags to resources that support them.

### Required Tags (mandatory; mirrors `.infrakit/tagging-standard.md`)

| Tag Key | Value Source | Description |
|---------|--------------|-------------|
| `managed-by` | `"terraform"` (static) | Identifies Terraform-managed resources |
| `environment` | `var.environment` | Deployment environment |
| `project` | `var.project` (default `"northwind-platform"`) | Project identifier |
| `cost-center` | `var.cost_center` | Billing allocation code (e.g., `CC-3017`) |
| `team` | `var.team` | Owning team (e.g., `orders`) |
| `data-classification` | `var.data_classification` | `public` / `internal` / `confidential` / `restricted` |

### Project-Specific Tags

| Tag Key | Value Source | Description |
|---------|--------------|-------------|
| `terraform-module` | `path.module` | Module that created the resource (for traceability) |
| `compliance-scope` | `var.tags["compliance-scope"]` (optional) | `pci` / `sox` / `hipaa` — only when applicable |

### Required AWS Pattern

```hcl
locals {
  required_tags = {
    managed-by          = "terraform"
    environment         = var.environment
    project             = var.project
    cost-center         = var.cost_center
    team                = var.team
    data-classification = var.data_classification
    terraform-module    = "s3-secure-bucket"
  }
}

resource "aws_s3_bucket" "this" {
  # ...
  tags = merge(local.required_tags, var.tags)
}
```

---

## 7. Security Standards

### Non-Negotiable Rules

- **Secrets**: NEVER hardcode secrets, passwords, or API keys in any `.tf` file or `.tfvars`.
- **Secrets**: Mark all credential variables and outputs `sensitive = true`.
- **Secrets**: Retrieve at runtime from AWS Secrets Manager or SSM Parameter Store; pass to resources via `data` sources, not literal strings.
- **Public access**: NEVER default `publicly_accessible`, `public_network_access_enabled`, `block_public_acls = false`, etc. Default to the most-restrictive setting; expose an explicit override variable.
- **Encryption**: ALWAYS enable encryption at rest for S3, RDS, EBS, Secrets Manager, SQS, SNS — in every environment.
- **Encryption at rest for `confidential` / `restricted`**: Customer-managed KMS keys only. AWS-managed keys (`AES256` / `aws/s3`) only acceptable for `public` / `internal`.
- **Encryption in transit**: Enforce TLS via bucket policies (`aws:SecureTransport`), `require_ssl` on RDS, HTTPS-only on ALB listeners.

### Project-Specific Security Defaults

- `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets` all default to `true` for S3.
- `force_destroy` on S3 buckets defaults to `false`; must be explicitly opted in (and the spec must document why).
- RDS `storage_encrypted = true` on all instances regardless of environment.
- RDS `deletion_protection = true` when `var.environment == "prod"`; `false` otherwise.
- RDS `multi_az = true` REQUIRED in prod; optional in staging; off in dev.
- All IAM policies use specific ARNs — wildcards (`*`) prohibited in production resources.

---

## 8. Output Declarations

### Required Fields

```hcl
output "bucket_arn" {
  description = "ARN of the S3 bucket — pass to consumers needing IAM policy resource refs"
  value       = aws_s3_bucket.this.arn
}

output "kms_key_arn" {
  description = "ARN of the bucket's KMS key — required by consumers that publish events through SNS/SQS"
  value       = aws_kms_key.this.arn
}
```

**Non-negotiable rules:**
- `description` is MANDATORY.
- Sensitive outputs MUST be marked `sensitive = true`.
- Output specific attributes (e.g., `aws_s3_bucket.this.arn`), not full resource objects.

---

## 9. Backend Configuration

**Project standard**: S3 backend with DynamoDB state locking, configured in each live config — never in modules.

```hcl
# In live config — terraform-live/prod/orders/events-bucket/backend.tf:
terraform {
  backend "s3" {
    bucket         = "northwind-tfstate-prod"
    key            = "orders/events-bucket/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "northwind-tflock-prod"
    encrypt        = true
    kms_key_id     = "alias/northwind-tfstate-prod"
  }
}
```

**Non-negotiable rules:**
- NEVER commit `terraform.tfstate` or `*.tfstate.backup`.
- `.gitignore` must include `*.tfstate`, `*.tfstate.backup`, `.terraform/`, `.terraform.lock.hcl` (lockfile is committed at the LIVE config layer, not the module).
- State encryption MUST use a customer-managed KMS key (`kms_key_id`), not the AWS-managed default.

---

## 10. Reference Example

```hcl
# versions.tf
terraform {
  required_version = ">= 1.7, < 2.0"

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

# variables.tf
variable "environment" {
  description = "Deployment environment: dev, staging, or prod"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

# main.tf
locals {
  required_tags = {
    managed-by       = "terraform"
    environment      = var.environment
    project          = var.project
    cost-center      = var.cost_center
    team             = var.team
    terraform-module = "example"
  }
}

# outputs.tf
output "example_id" {
  description = "ID of the created resource"
  value       = aws_example_resource.this.id
}
```
