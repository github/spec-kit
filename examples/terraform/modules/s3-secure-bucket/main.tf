locals {
  required_tags = {
    "managed-by"          = "terraform"
    "environment"         = var.environment
    "project"             = var.project
    "cost-center"         = var.cost_center
    "team"                = var.team
    "data-classification" = var.data_classification
    "terraform-module"    = "s3-secure-bucket"
  }

  bucket_name = "${var.environment}-${var.team}-${var.name}-${random_id.suffix.hex}"
}

resource "random_id" "suffix" {
  byte_length = 2
}

# Customer-managed KMS key for bucket encryption.
# Required for confidential/restricted classifications; used for all classifications for consistency.
resource "aws_kms_key" "this" {
  description             = "S3 bucket encryption key for ${local.bucket_name}"
  deletion_window_in_days = var.kms_deletion_window_days
  enable_key_rotation     = true

  tags = merge(local.required_tags, var.tags)
}

resource "aws_kms_alias" "this" {
  name          = "alias/${local.bucket_name}"
  target_key_id = aws_kms_key.this.key_id
}

resource "aws_s3_bucket" "this" {
  bucket = local.bucket_name

  # Module defaults force_destroy=false. Deletion requires emptying the bucket
  # manually or temporarily setting this true through an explicit waiver.
  force_destroy = false

  tags = merge(local.required_tags, var.tags)
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.this.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Lifecycle rule: transition non-current versions to cheaper tiers, eventually expire.
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "noncurrent-version-lifecycle"
    status = "Enabled"

    filter {}

    dynamic "noncurrent_version_transition" {
      for_each = var.lifecycle_transition_to_ia_days > 0 ? [1] : []
      content {
        noncurrent_days = var.lifecycle_transition_to_ia_days
        storage_class   = "STANDARD_IA"
      }
    }

    dynamic "noncurrent_version_transition" {
      for_each = var.lifecycle_transition_to_glacier_days > 0 ? [1] : []
      content {
        noncurrent_days = var.lifecycle_transition_to_glacier_days
        storage_class   = "GLACIER"
      }
    }

    dynamic "noncurrent_version_expiration" {
      for_each = var.lifecycle_noncurrent_expiration_days > 0 ? [1] : []
      content {
        noncurrent_days = var.lifecycle_noncurrent_expiration_days
      }
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Deny non-TLS access. AWS Config rule s3-bucket-ssl-requests-only mandates this policy.
data "aws_iam_policy_document" "deny_insecure_transport" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.this.arn,
      "${aws_s3_bucket.this.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "deny_insecure_transport" {
  bucket = aws_s3_bucket.this.id
  policy = data.aws_iam_policy_document.deny_insecure_transport.json
}

# Replication: only enabled in prod, only to a caller-supplied destination bucket.
resource "aws_iam_role" "replication" {
  count = var.enable_cross_region_replication ? 1 : 0

  name = "${local.bucket_name}-replication"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "s3.amazonaws.com"
      }
    }]
  })

  tags = merge(local.required_tags, var.tags)
}

data "aws_iam_policy_document" "replication" {
  count = var.enable_cross_region_replication ? 1 : 0

  statement {
    sid    = "SourceBucketRead"
    effect = "Allow"
    actions = [
      "s3:GetReplicationConfiguration",
      "s3:ListBucket",
      "s3:GetObjectVersionForReplication",
      "s3:GetObjectVersionAcl",
      "s3:GetObjectVersionTagging",
    ]
    resources = [
      aws_s3_bucket.this.arn,
      "${aws_s3_bucket.this.arn}/*",
    ]
  }

  statement {
    sid    = "DestinationBucketWrite"
    effect = "Allow"
    actions = [
      "s3:ReplicateObject",
      "s3:ReplicateDelete",
      "s3:ReplicateTags",
    ]
    resources = ["${var.replication_destination_bucket_arn}/*"]
  }

  statement {
    sid       = "KMSDecryptSource"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.this.arn]
  }

  statement {
    sid       = "KMSEncryptDestination"
    effect    = "Allow"
    actions   = ["kms:Encrypt"]
    resources = [var.replication_destination_kms_key_arn]
  }
}

resource "aws_iam_role_policy" "replication" {
  count = var.enable_cross_region_replication ? 1 : 0

  name   = "${local.bucket_name}-replication"
  role   = aws_iam_role.replication[0].id
  policy = data.aws_iam_policy_document.replication[0].json
}

resource "aws_s3_bucket_replication_configuration" "this" {
  count = var.enable_cross_region_replication ? 1 : 0

  # Replication depends on versioning being enabled on the source bucket.
  depends_on = [aws_s3_bucket_versioning.this]

  role   = aws_iam_role.replication[0].arn
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "replicate-all"
    status = "Enabled"

    filter {}

    delete_marker_replication {
      status = "Enabled"
    }

    destination {
      bucket        = var.replication_destination_bucket_arn
      storage_class = "STANDARD_IA"

      encryption_configuration {
        replica_kms_key_id = var.replication_destination_kms_key_arn
      }
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }
  }
}
