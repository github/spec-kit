# Implementation Tasks: s3-secure-bucket

**Track**: `s3-secure-bucket-20260415-093000`
**Generated**: 2026-04-15
**Source Plan**: `.infrakit_tracks/tracks/s3-secure-bucket-20260415-093000/plan.md`

## Phase 1: versions.tf

- [x] T1.1: Write `terraform { required_version = ">= 1.7, < 2.0" }` block.
- [x] T1.2: Write `required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" }, random = { source = "hashicorp/random", version = "~> 3.6" } }`.

## Phase 2: variables.tf

- [x] T2.1: Declare `name` (string, required) with regex validation `^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$`.
- [x] T2.2: Declare `environment` (string, required) with `contains(["dev","staging","prod"], ...)` validation.
- [x] T2.3: Declare `team` (string, required) with enum validation across the 6 allowed teams.
- [x] T2.4: Declare `cost_center` (string, required) with regex `^CC-[0-9]{4}$`.
- [x] T2.5: Declare `project` (string, default `"northwind-platform"`).
- [x] T2.6: Declare `data_classification` (string, required) with enum validation.
- [x] T2.7: Declare `kms_deletion_window_days` (number, default `30`) with range check `>= 7 && <= 30`.
- [x] T2.8: Declare `lifecycle_transition_to_ia_days` (number, default `30`) with `== 0 || >= 30`.
- [x] T2.9: Declare `lifecycle_transition_to_glacier_days` (number, default `90`) with `== 0 || >= 90`.
- [x] T2.10: Declare `lifecycle_noncurrent_expiration_days` (number, default `365`) with `== 0 || >= 90`.
- [x] T2.11: Declare `enable_cross_region_replication` (bool, default `false`) with validation `!var.enable_cross_region_replication || var.environment == "prod"`.
- [x] T2.12: Declare `replication_destination_bucket_arn` (string, default `null`).
- [x] T2.13: Declare `replication_destination_kms_key_arn` (string, default `null`).
- [x] T2.14: Declare `tags` (map(string), default `{}`).

## Phase 3: main.tf

- [x] T3.1: Declare `locals { required_tags = { ... }, bucket_name = "..." }`.
- [x] T3.2: Write `resource "random_id" "suffix" { byte_length = 2 }`.
- [x] T3.3: Write `aws_kms_key.this` with `enable_key_rotation = true` and tags.
- [x] T3.4: Write `aws_kms_alias.this`.
- [x] T3.5: Write `aws_s3_bucket.this` with `force_destroy = false` and tags.
- [x] T3.6: Write `aws_s3_bucket_versioning.this` with `status = "Enabled"`.
- [x] T3.7: Write `aws_s3_bucket_server_side_encryption_configuration.this` referencing the KMS key ARN with `bucket_key_enabled = true`.
- [x] T3.8: Write `aws_s3_bucket_public_access_block.this` with all four flags `true`.
- [x] T3.9: Write `aws_s3_bucket_ownership_controls.this` with `BucketOwnerEnforced`.
- [x] T3.10: Write `aws_s3_bucket_lifecycle_configuration.this` with `noncurrent_version_transition` (IA), `noncurrent_version_transition` (GLACIER), `noncurrent_version_expiration` (all dynamic, gated on `>0`), and `abort_incomplete_multipart_upload { days_after_initiation = 7 }`.
- [x] T3.11: Write `data "aws_iam_policy_document" "deny_insecure_transport"` with the `aws:SecureTransport == false` deny statement.
- [x] T3.12: Write `aws_s3_bucket_policy.deny_insecure_transport` applying the policy.
- [x] T3.13: Write `aws_iam_role.replication` (`count = var.enable_cross_region_replication ? 1 : 0`) with S3 service assume-role.
- [x] T3.14: Write `data "aws_iam_policy_document" "replication"` (count-gated) with the four required statements.
- [x] T3.15: Write `aws_iam_role_policy.replication` (count-gated).
- [x] T3.16: Write `aws_s3_bucket_replication_configuration.this` (count-gated) with `depends_on = [aws_s3_bucket_versioning.this]`, the destination block including KMS, and `source_selection_criteria.sse_kms_encrypted_objects.status = "Enabled"`.

## Phase 4: outputs.tf

- [x] T4.1: Declare `bucket_id` from `aws_s3_bucket.this.id`.
- [x] T4.2: Declare `bucket_arn` from `aws_s3_bucket.this.arn`.
- [x] T4.3: Declare `bucket_domain_name` from `aws_s3_bucket.this.bucket_domain_name`.
- [x] T4.4: Declare `bucket_regional_domain_name` from `aws_s3_bucket.this.bucket_regional_domain_name`.
- [x] T4.5: Declare `kms_key_arn` from `aws_kms_key.this.arn`.
- [x] T4.6: Declare `kms_key_id` from `aws_kms_key.this.key_id`.
- [x] T4.7: Declare `replication_role_arn` conditional on `var.enable_cross_region_replication`.

## Phase 5: README.md

- [x] T5.1: Document all 14 inputs in a table (name, type, required, default, description).
- [x] T5.2: Document all 7 outputs in a table (name, description).
- [x] T5.3: Add a usage example showing the module call with all required variables, replication enabled, and a `tags` override.
- [x] T5.4: Document the bucket-name format and the `random_id` suffix.

## Phase 6: Validation

- [x] T6.1: Run `tofu fmt -check` — pass.
- [x] T6.2: Run `tofu init -backend=false && tofu validate` — pass.
- [ ] T6.3: Run `tflint --init && tflint` against the AWS rule set — to be run in CI.
- [ ] T6.4: Run `checkov --directory modules/s3-secure-bucket/` — to be run in CI.
