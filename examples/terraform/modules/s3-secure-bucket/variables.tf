variable "name" {
  description = "Logical name of the bucket. Combined with environment, team, and a random 4-char suffix to form the actual bucket name. Must be 3-40 chars, lowercase, kebab-case."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$", var.name))
    error_message = "name must be 3-40 lowercase characters; kebab-case; start and end alphanumeric."
  }
}

variable "environment" {
  description = "Deployment environment: dev, staging, or prod."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "team" {
  description = "Owning team. Allowed values: orders, fulfillment, returns, analytics, customer-portal, platform."
  type        = string

  validation {
    condition     = contains(["orders", "fulfillment", "returns", "analytics", "customer-portal", "platform"], var.team)
    error_message = "team must be one of: orders, fulfillment, returns, analytics, customer-portal, platform."
  }
}

variable "cost_center" {
  description = "Billing allocation code. Format: CC-NNNN."
  type        = string

  validation {
    condition     = can(regex("^CC-[0-9]{4}$", var.cost_center))
    error_message = "cost_center must match the pattern CC-NNNN (e.g., CC-3017)."
  }
}

variable "project" {
  description = "Project identifier."
  type        = string
  default     = "northwind-platform"
}

variable "data_classification" {
  description = "Data classification: public, internal, confidential, or restricted. Drives KMS key choice and access-review cadence."
  type        = string

  validation {
    condition     = contains(["public", "internal", "confidential", "restricted"], var.data_classification)
    error_message = "data_classification must be one of: public, internal, confidential, restricted."
  }
}

variable "kms_deletion_window_days" {
  description = "KMS key deletion window in days. Must be 7-30."
  type        = number
  default     = 30

  validation {
    condition     = var.kms_deletion_window_days >= 7 && var.kms_deletion_window_days <= 30
    error_message = "kms_deletion_window_days must be between 7 and 30."
  }
}

variable "lifecycle_transition_to_ia_days" {
  description = "Number of days before non-current versions transition to STANDARD_IA. Set to 0 to disable IA transition."
  type        = number
  default     = 30

  validation {
    condition     = var.lifecycle_transition_to_ia_days == 0 || var.lifecycle_transition_to_ia_days >= 30
    error_message = "lifecycle_transition_to_ia_days must be 0 (disabled) or >= 30."
  }
}

variable "lifecycle_transition_to_glacier_days" {
  description = "Number of days before non-current versions transition to GLACIER. Set to 0 to disable."
  type        = number
  default     = 90

  validation {
    condition     = var.lifecycle_transition_to_glacier_days == 0 || var.lifecycle_transition_to_glacier_days >= 90
    error_message = "lifecycle_transition_to_glacier_days must be 0 (disabled) or >= 90."
  }
}

variable "lifecycle_noncurrent_expiration_days" {
  description = "Number of days before non-current versions are permanently deleted. Set to 0 to retain forever."
  type        = number
  default     = 365

  validation {
    condition     = var.lifecycle_noncurrent_expiration_days == 0 || var.lifecycle_noncurrent_expiration_days >= 90
    error_message = "lifecycle_noncurrent_expiration_days must be 0 (retain forever) or >= 90."
  }
}

variable "enable_cross_region_replication" {
  description = "Enable cross-region replication to us-west-2. Required for prod; disallowed for dev/staging by policy."
  type        = bool
  default     = false

  validation {
    condition     = !var.enable_cross_region_replication || var.environment == "prod"
    error_message = "enable_cross_region_replication is only permitted when environment is prod."
  }
}

variable "replication_destination_bucket_arn" {
  description = "ARN of the destination bucket in us-west-2. Required when enable_cross_region_replication is true. Must be a customer-managed S3 bucket — this module does not create the destination."
  type        = string
  default     = null
}

variable "replication_destination_kms_key_arn" {
  description = "ARN of the KMS key in us-west-2 used to encrypt replicated objects. Required when enable_cross_region_replication is true."
  type        = string
  default     = null
}

variable "tags" {
  description = "Additional tags to merge with the module's required tags."
  type        = map(string)
  default     = {}
}
