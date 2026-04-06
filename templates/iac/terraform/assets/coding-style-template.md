# [PROJECT_NAME] Terraform Coding Style Guide
<!-- Example: Acme Platform Terraform Coding Style Guide -->

> This document captures both universal Terraform standards (non-negotiable) and
> project-specific conventions for this platform. Run `/infrakit:setup` to populate
> the placeholder sections.

All Terraform engineers **MUST** follow these standards when generating infrastructure code.

---

## 1. IaC Tool & Version

| Setting | Value |
|---------|-------|
| **Terraform Version** | [TERRAFORM_VERSION] |
| **Primary Cloud Provider** | [PRIMARY_PROVIDER] |
| **Provider Version(s)** | [PROVIDER_VERSIONS] |

<!-- Example:
| Terraform Version | >= 1.6.0 |
| Primary Cloud Provider | AWS |
| Provider Version(s) | hashicorp/aws ~> 5.0, hashicorp/random ~> 3.6 |
-->

---

## 2. File Organization

**Module directory structure:**

```
[PROJECT_FILE_STRUCTURE]
```

<!-- Example:
modules/
  database/
    main.tf
    variables.tf
    outputs.tf
    versions.tf
    README.md
  vpc/
    main.tf
    variables.tf
    outputs.tf
    versions.tf
    README.md
environments/
  dev/
    main.tf
    terraform.tfvars
  staging/
    main.tf
    terraform.tfvars
  prod/
    main.tf
    terraform.tfvars
-->

**Non-negotiable rules (apply to all projects):**
- **File separation**: Resources in `main.tf`, variables in `variables.tf`, outputs in `outputs.tf`, provider/version constraints in `versions.tf`.
- **One module per directory**: Never place multiple unrelated modules in the same directory.
- **No inline variables**: All variable declarations must be in `variables.tf`.
- **No inline outputs**: All output declarations must be in `outputs.tf`.

---

## 3. Naming Conventions

### Resources

| Element | Pattern | Example |
|---------|---------|---------|
| Resource name | `snake_case`, descriptive | `aws_db_instance.primary` |
| Variable name | `snake_case` | `var.database_instance_class` |
| Output name | `snake_case` | `database_endpoint` |
| Local value | `snake_case` | `local.common_tags` |
| Module call | `snake_case` | `module.database` |

### Identifier Pattern

**Project prefix**: `[PROJECT_PREFIX]`
<!-- Example: acme_platform — use as prefix for top-level resources to avoid naming conflicts -->

| Resource Category | Naming Pattern | Example |
|-------------------|----------------|---------|
| Databases | `[PREFIX]-[name]-[env]` | `[PROJECT_PREFIX]-postgres-prod` |
| Storage | `[PREFIX]-[name]-[env]` | `[PROJECT_PREFIX]-logs-staging` |
| Networks | `[PREFIX]-[name]-[env]` | `[PROJECT_PREFIX]-vpc-prod` |

**Non-negotiable rules:**
- **snake_case** for all Terraform identifiers (resource names, variable names, output names).
- **kebab-case** for cloud resource names (the `name` argument passed to the cloud API).
- Use `var.name` or a caller-provided prefix in resource name arguments to avoid conflicts on multiple instantiations.

### API Versioning Policy

| Terraform | Policy |
|-----------|--------|
| `>= 1.6.0` | [TF_VERSION_POLICY] |

<!-- Example:
>= 1.6.0: Minimum supported; use latest stable patch. All new modules must set required_version = ">= 1.6, < 2.0".
-->

---

## 4. Provider Configuration (MANDATORY STANDARDS)

### Required Provider Block

All modules **MUST** declare provider requirements in `versions.tf`:

```hcl
terraform {
  required_version = "[TF_VERSION_CONSTRAINT]"

  required_providers {
    [PROVIDER] = {
      source  = "hashicorp/[PROVIDER]"
      version = "[PROVIDER_VERSION_CONSTRAINT]"
    }
  }
}
```

<!-- Example:
terraform {
  required_version = ">= 1.6, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
-->

### Provider Pinning

**ALWAYS** use pessimistic constraint operator (`~>`) for provider versions:

- ✅ `~> 5.0` — allows patch updates only (5.0.x)
- ✅ `~> 5.0.3` — locks to 5.0.x, minimum 5.0.3
- ❌ `>= 5.0` — dangerous, allows major version bumps
- ❌ `= 5.0.3` — too strict, prevents security patches

### Default Tagging (AWS)

**Project standard**: `[DEFAULT_TAGS_STRATEGY]`
<!-- Example: Use default_tags block in the provider configuration to enforce common tags across all resources -->

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
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
  # sensitive = true  # Add for passwords, tokens, keys
}
```

**Non-negotiable rules:**
- `description` is **MANDATORY** for all variables.
- `type` constraint is **MANDATORY** for all variables.
- Sensitive variables (passwords, tokens, API keys) **MUST** be marked `sensitive = true`.
- **NEVER** set a plaintext default for sensitive variables.
- Use `validation` blocks for constrained inputs (environments, sizes, regions).

### Validation Pattern

```hcl
variable "environment" {
  description = "Deployment environment: dev, staging, or prod"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}
```

---

## 6. Resource Tagging

**ALWAYS add tags/labels to resources that support them.**

### Required Tags (MANDATORY for all tagged resources)

Every tagged resource MUST include these tags (either via `default_tags`, `local.common_tags`, or explicitly):

| Tag Key | Value | Description |
|---------|-------|-------------|
| `managed-by` | `"terraform"` | Indicates resource is managed by Terraform |
| `environment` | `var.environment` | Deployment environment |
| `<project-tag>` | `"[PROJECT_NAME]"` | Project identifier |

### Project-Specific Tags

In addition to the required tags above, this project requires:

| Tag Key | Value Source | Description |
|---------|-------------|-------------|
[PROJECT_SPECIFIC_TAGS]

<!-- Example:
| `cost-center` | `var.cost_center` | Billing allocation code |
| `team` | `var.team` | Owning team name |
| `terraform-module` | path.module | Module that created the resource |
-->

### Provider-Specific Tag Field

| Provider | Field | Notes |
|----------|-------|-------|
| **AWS** | `tags = {}` map or `default_tags` block | `default_tags` in provider is preferred |
| **Azure** | `tags = {}` map | Per resource or resource group |
| **GCP** | `labels = {}` map | GCP uses labels, not tags |

### Recommended AWS Pattern

```hcl
locals {
  common_tags = {
    managed-by  = "terraform"
    environment = var.environment
    project     = "[PROJECT_NAME]"
  }
}

# Then merge caller-provided tags:
resource "aws_instance" "example" {
  # ...
  tags = merge(local.common_tags, var.tags)
}
```

---

## 7. Security Standards

### Non-Negotiable Rules

- **Secrets**: NEVER hardcode secrets, passwords, or API keys in any `.tf` file.
- **Secrets**: Use `sensitive = true` on all variables and outputs containing credentials.
- **Secrets**: Retrieve secrets at runtime from a secrets manager (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager) or inject via environment variables (`TF_VAR_*`).
- **Public access**: NEVER default `publicly_accessible`, `public_network_access_enabled`, or equivalent arguments to `true`. Default to `false`; expose an explicit override variable.
- **Encryption**: ALWAYS enable encryption at rest for storage resources (S3, RDS, EBS, Azure Disk, GCS, etc.) in staging and prod.
- **Encryption in transit**: ALWAYS enforce TLS/HTTPS for endpoints; set `require_ssl = true` where applicable.

### Project-Specific Security Defaults

[PROJECT_SECURITY_DEFAULTS]
<!-- Example:
- storage_encrypted = true on all RDS instances regardless of environment
- publicly_accessible = false always; override variable requires security team sign-off tracked in spec.md
- deletion_protection = true for prod; false for dev/staging
- multi_az = true required in prod for all RDS; not required in dev/staging
-->

---

## 8. Output Declarations

### Required Fields

Every output **MUST** have a `description`:

```hcl
output "database_endpoint" {
  description = "The DNS endpoint of the RDS instance"
  value       = aws_db_instance.primary.endpoint
  # sensitive = true  # Add for passwords, tokens, connection strings with credentials
}
```

**Non-negotiable rules:**
- `description` is **MANDATORY** for all outputs.
- Sensitive outputs (connection strings with passwords, tokens) **MUST** be marked `sensitive = true`.
- Output specific attributes (e.g., `aws_db_instance.primary.endpoint`) not full resource objects.

---

## 9. Backend Configuration

**Project standard**: `[BACKEND_TYPE]`
<!-- Example: S3 backend with DynamoDB state locking for all environments -->

```hcl
terraform {
  backend "[BACKEND_TYPE]" {
    [BACKEND_CONFIGURATION]
  }
}
```

<!-- Example for S3:
terrain {
  backend "s3" {
    bucket         = "acme-terraform-state"
    key            = "modules/database/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "acme-terraform-locks"
    encrypt        = true
  }
}
-->

**Non-negotiable rules:**
- **NEVER** commit `terraform.tfstate` or `*.tfstate.backup` files to version control.
- Ensure `.gitignore` includes `*.tfstate`, `*.tfstate.backup`, `.terraform/`.
- Enable state encryption for all backends that support it.

---

## 10. Reference Example

```hcl
# versions.tf
terraform {
  required_version = ">= 1.6, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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

variable "instance_class" {
  description = "RDS instance class (e.g., db.t3.micro)"
  type        = string
  default     = "db.t3.micro"
}

variable "tags" {
  description = "Additional tags to merge with module defaults"
  type        = map(string)
  default     = {}
}

# main.tf
locals {
  common_tags = {
    managed-by  = "terraform"
    environment = var.environment
    project     = "[PROJECT_NAME]"
  }
}

resource "aws_db_instance" "primary" {
  identifier        = "[PROJECT_PREFIX]-db-${var.environment}"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = var.instance_class
  allocated_storage = 20

  storage_encrypted   = true
  publicly_accessible = false
  deletion_protection = var.environment == "prod"

  tags = merge(local.common_tags, var.tags)
}

# outputs.tf
output "db_endpoint" {
  description = "The DNS endpoint of the RDS instance"
  value       = aws_db_instance.primary.endpoint
}
```
