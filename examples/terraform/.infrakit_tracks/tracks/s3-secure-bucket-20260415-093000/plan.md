# Implementation Plan: s3-secure-bucket

## Summary

Build a reusable AWS S3 bucket module that ships the Northwind security baseline by default
(customer-managed KMS encryption, public-access blocks, lifecycle, TLS-only policy) and supports
an opt-in cross-region replication mode for production.

## Infrastructure Context

| Property | Value |
|----------|-------|
| **Track** | `s3-secure-bucket-20260415-093000` |
| **Cloud Provider** | AWS (from `.infrakit/context.md`) |
| **Module Directory** | `modules/s3-secure-bucket/` |

## Tech Stack

| Component | Version |
|-----------|---------|
| Terraform | `>= 1.7, < 2.0` |
| Provider | `hashicorp/aws ~> 5.0` |
| Provider | `hashicorp/random ~> 3.6` |

## File Structure

```
modules/s3-secure-bucket/
├── versions.tf       # required_version + required_providers
├── variables.tf      # 14 input variables with descriptions, types, validations
├── main.tf           # KMS key + alias, bucket + 5 supporting resources, optional replication
├── outputs.tf        # 7 outputs (bucket_id, arn, domain names, kms_*, replication_role_arn)
└── README.md         # Usage example + inputs/outputs reference
```

## Input Variables Design

| Variable | Type | Required | Default | Description | Validation |
|----------|------|----------|---------|-------------|------------|
| `name` | `string` | yes | — | Logical name | 3-40 lower-kebab |
| `environment` | `string` | yes | — | Env | `dev`/`staging`/`prod` |
| `team` | `string` | yes | — | Owning team | one of 6 allowed |
| `cost_center` | `string` | yes | — | Billing code | `^CC-[0-9]{4}$` |
| `project` | `string` | no | `"northwind-platform"` | Project id | — |
| `data_classification` | `string` | yes | — | Classification | one of 4 |
| `kms_deletion_window_days` | `number` | no | `30` | KMS deletion window | 7..30 |
| `lifecycle_transition_to_ia_days` | `number` | no | `30` | Non-current → IA | 0 or `>= 30` |
| `lifecycle_transition_to_glacier_days` | `number` | no | `90` | Non-current → GLACIER | 0 or `>= 90` |
| `lifecycle_noncurrent_expiration_days` | `number` | no | `365` | Non-current expire | 0 or `>= 90` |
| `enable_cross_region_replication` | `bool` | no | `false` | Enable CRR | true only in prod |
| `replication_destination_bucket_arn` | `string` | no | `null` | CRR dest bucket | — |
| `replication_destination_kms_key_arn` | `string` | no | `null` | CRR dest KMS | — |
| `tags` | `map(string)` | no | `{}` | Additional tags | — |

## Resources to Provision

| # | Resource Type | Name | Arguments | Purpose |
|---|---------------|------|-----------|---------|
| 1 | `random_id` | `suffix` | `byte_length = 2` | 4-char hex suffix for unique bucket name |
| 2 | `aws_kms_key` | `this` | `enable_key_rotation = true`, `deletion_window_in_days = var.kms_deletion_window_days` | Customer-managed key for bucket encryption |
| 3 | `aws_kms_alias` | `this` | `target_key_id = aws_kms_key.this.key_id` | Human-readable alias |
| 4 | `aws_s3_bucket` | `this` | `bucket = local.bucket_name`, `force_destroy = false` | The bucket itself |
| 5 | `aws_s3_bucket_versioning` | `this` | `status = "Enabled"` | Enable versioning |
| 6 | `aws_s3_bucket_server_side_encryption_configuration` | `this` | `sse_algorithm = "aws:kms"`, `kms_master_key_id = aws_kms_key.this.arn`, `bucket_key_enabled = true` | Encryption at rest |
| 7 | `aws_s3_bucket_public_access_block` | `this` | All four `block_*` flags `true` | Block public access |
| 8 | `aws_s3_bucket_ownership_controls` | `this` | `object_ownership = "BucketOwnerEnforced"` | Disable ACLs |
| 9 | `aws_s3_bucket_lifecycle_configuration` | `this` | 3 dynamic transitions + abort-multipart | Non-current version lifecycle |
| 10 | `data.aws_iam_policy_document` | `deny_insecure_transport` | `aws:SecureTransport == false` deny-all | Build TLS-only policy |
| 11 | `aws_s3_bucket_policy` | `deny_insecure_transport` | `policy = data.aws_iam_policy_document.deny_insecure_transport.json` | Apply TLS-only policy |
| 12 | `aws_iam_role` | `replication` (count = 0 or 1) | `s3.amazonaws.com` assume role | Replication role |
| 13 | `data.aws_iam_policy_document` | `replication` (count = 0 or 1) | 4 statements: source read, dest write, KMS decrypt, KMS encrypt | Build replication policy |
| 14 | `aws_iam_role_policy` | `replication` (count = 0 or 1) | Attach replication policy | Attach role policy |
| 15 | `aws_s3_bucket_replication_configuration` | `this` (count = 0 or 1) | `role`, `rule { destination { ... } }` | Configure replication |

## Output Values Design

| Output | Source | Description |
|--------|--------|-------------|
| `bucket_id` | `aws_s3_bucket.this.id` | Bucket name |
| `bucket_arn` | `aws_s3_bucket.this.arn` | Bucket ARN |
| `bucket_domain_name` | `aws_s3_bucket.this.bucket_domain_name` | Bucket-style DNS |
| `bucket_regional_domain_name` | `aws_s3_bucket.this.bucket_regional_domain_name` | Regional DNS |
| `kms_key_arn` | `aws_kms_key.this.arn` | KMS key ARN |
| `kms_key_id` | `aws_kms_key.this.key_id` | KMS key ID |
| `replication_role_arn` | conditional on `var.enable_cross_region_replication` | IAM role ARN or null |

## Tagging Strategy

Module builds `local.required_tags` from inputs (`managed-by`, `environment`, `project`,
`cost-center`, `team`, `data-classification`, `terraform-module`) and sets
`tags = merge(local.required_tags, var.tags)` on the bucket, the KMS key, and the replication
role. Live configs additionally set `default_tags` on the AWS provider for defense in depth.

## Implementation Phases

1. **versions.tf** — declare `required_version = ">= 1.7, < 2.0"` and providers (`aws ~> 5.0`, `random ~> 3.6`).
2. **variables.tf** — declare all 14 input variables with descriptions, types, and validation blocks.
3. **main.tf** — declare `locals` (required_tags, bucket_name), `random_id`, KMS key+alias, bucket, versioning, encryption, public-access block, ownership controls, lifecycle, TLS-deny policy, and the optional replication chain (role, policy doc, role policy, replication config).
4. **outputs.tf** — declare all 7 outputs.
5. **README.md** — document inputs, outputs, and a usage example.

## Constraints from `coding-style.md`

- All resources tagged with `merge(local.required_tags, var.tags)`.
- No hardcoded secrets or account IDs.
- `block_public_*` flags all default to `true`.
- `force_destroy = false` hard-coded; not exposed as a variable.
- Provider pinning uses `~> 5.0` (pessimistic constraint).
- All variables have `description` and explicit `type`.
- Validations enforce enum membership and numeric bounds.
- snake_case for HCL identifiers; kebab-case for the AWS bucket name.

## Notes

### Known Challenges

- The `aws_s3_bucket_lifecycle_configuration` `noncurrent_version_transition` resource requires `>= 30` days for IA and `>= 90` for GLACIER. The validation blocks mirror these minimums and allow `0` to disable. Forgetting these limits would cause apply failures with a cryptic AWS API error.
- The `aws_s3_bucket_replication_configuration` resource has an implicit dependency on versioning; we add an explicit `depends_on = [aws_s3_bucket_versioning.this]` to avoid race conditions on first apply.
- Cross-region replication requires the destination bucket and its KMS key to already exist. Variable validation cannot reach across regions to verify, so we rely on AWS API errors at apply time if the inputs are wrong.

### Design Decisions

- **Customer-managed KMS for all classifications** (not just `confidential`/`restricted`). One code path is simpler to audit than two, and the extra KMS cost is negligible compared to bucket-level audit overhead.
- **`force_destroy` not exposed as a variable**. Accidental destroy on a populated bucket is a recoverable-only-via-versioning event; we make the operator do this manually as a circuit breaker.
- **Replication scoped to prod via variable validation**, not a separate module. Keeping it in one module avoids module-graph drift but means dev/staging callers must not pass the flag — the validation message says so explicitly.
- **`source_selection_criteria.sse_kms_encrypted_objects.status = "Enabled"`** is required because the source bucket uses SSE-KMS. Without it, the replication-config plan succeeds but apply fails with `KMS encryption is not supported on replication source bucket`.
