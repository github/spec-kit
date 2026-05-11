output "bucket_id" {
  description = "The ID (name) of the S3 bucket."
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket. Pass to consumers that need it in IAM policy resource references."
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "Bucket-style DNS name (e.g., bucket.s3.amazonaws.com)."
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional bucket DNS name (used by clients that should pin to a specific region)."
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "kms_key_arn" {
  description = "ARN of the bucket's KMS key. Required by consumers that publish events through SNS/SQS or grant cross-account access."
  value       = aws_kms_key.this.arn
}

output "kms_key_id" {
  description = "ID of the bucket's KMS key."
  value       = aws_kms_key.this.key_id
}

output "replication_role_arn" {
  description = "ARN of the IAM role used for cross-region replication. Null if replication is disabled."
  value       = var.enable_cross_region_replication ? aws_iam_role.replication[0].arn : null
}
