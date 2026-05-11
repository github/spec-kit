# Specification: s3-secure-bucket

## Description

A reusable AWS S3 bucket module that meets the Northwind Platform security baseline out of the box.
The module produces a bucket suitable for storing application data of any classification, with
mandatory encryption, public-access blocks, lifecycle management of non-current object versions,
and optional cross-region replication for prod workloads. Consumers configure environment, team,
cost-center, and data-classification; the module derives a globally unique bucket name and applies
all required tags.

## Cloud Provider

**Provider**: AWS
**Service**: S3 (with KMS for encryption and IAM for replication role)

## Project Type

Greenfield (Create new)

## How It Should Work

A product team calls the module from a live config in `terraform-live/<env>/<team>/<resource>/`.
They pass identity inputs (`environment`, `team`, `name`, etc.). The module returns the bucket
ARN, regional DNS name, and KMS key ARN — enough for the caller to attach event notifications,
grant cross-account access, or wire up an event-driven consumer. No public-internet ingress to the
bucket is possible from defaults.

For production, the team also passes `enable_cross_region_replication = true` along with a
pre-provisioned destination bucket ARN and KMS key ARN in `us-west-2`. The module sets up the
replication IAM role and the replication configuration; the destination bucket itself is the
caller's responsibility (it's typically managed by a separate live config that lives in the
DR region).

## Input Variables

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | `string` | yes | — | Logical name (3-40 chars, kebab-case). |
| `environment` | `string` | yes | — | `dev`, `staging`, or `prod`. |
| `team` | `string` | yes | — | Owning team. |
| `cost_center` | `string` | yes | — | Billing code (`CC-NNNN`). |
| `project` | `string` | no | `"northwind-platform"` | Project identifier. |
| `data_classification` | `string` | yes | — | `public` / `internal` / `confidential` / `restricted`. |
| `kms_deletion_window_days` | `number` | no | `30` | KMS deletion window (7-30). |
| `lifecycle_transition_to_ia_days` | `number` | no | `30` | Non-current → IA (0 disables). |
| `lifecycle_transition_to_glacier_days` | `number` | no | `90` | Non-current → GLACIER (0 disables). |
| `lifecycle_noncurrent_expiration_days` | `number` | no | `365` | Non-current expiration (0 retains forever). |
| `enable_cross_region_replication` | `bool` | no | `false` | Replicate to us-west-2. Only allowed when `environment == "prod"`. |
| `replication_destination_bucket_arn` | `string` | no | `null` | Required when replication is enabled. |
| `replication_destination_kms_key_arn` | `string` | no | `null` | Required when replication is enabled. |
| `tags` | `map(string)` | no | `{}` | Additional tags merged with required tags. |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `bucket_id` | `string` | Bucket name. |
| `bucket_arn` | `string` | Bucket ARN. |
| `bucket_domain_name` | `string` | Bucket-style DNS name. |
| `bucket_regional_domain_name` | `string` | Regional DNS name. |
| `kms_key_arn` | `string` | ARN of the customer-managed KMS key. |
| `kms_key_id` | `string` | ID of the KMS key. |
| `replication_role_arn` | `string` | Replication IAM role ARN, or `null`. |

## Security Requirements

- Server-side encryption at rest with a customer-managed KMS key (rotation enabled).
- All four `block_public_*` flags set to `true`.
- Object ownership: `BucketOwnerEnforced` (ACLs disabled).
- Bucket policy denies any non-TLS request (`aws:SecureTransport == false`).
- Lifecycle expiration on non-current versions to bound storage cost.
- KMS key deletion window default 30 days (the maximum allowed).
- Replication uses an isolated IAM role scoped to source/destination ARNs only — no wildcards.

## Configuration Constraints

- `force_destroy` is hard-coded to `false` in the module; deletion requires manual bucket-emptying or a one-shot waiver patch.
- `enable_cross_region_replication = true` is rejected by variable validation unless `environment == "prod"`.
- Bucket name format `${environment}-${team}-${name}-${random_4_chars}` is fixed; a `random_id` provides a 4-char suffix for global uniqueness.
- `noncurrent_version_expiration_days >= 90` (or 0); `transition_to_ia_days >= 30` (or 0); `transition_to_glacier_days >= 90` (or 0). These match AWS S3 minimums.

## Acceptance Criteria

- [ ] Caller can use the module with the minimum required variables (`name`, `environment`, `team`, `cost_center`, `data_classification`).
- [ ] All required tags from `.infrakit/tagging-standard.md` are present on the bucket, the KMS key, and (when applicable) the replication role.
- [ ] No hardcoded secrets or credentials.
- [ ] All required security measures enforced from defaults (public access blocked, encryption at rest, TLS-only).
- [ ] `tofu validate` passes against the module.
- [ ] `tflint` passes with no errors against the AWS rule set.
- [ ] Outputs expose every value a downstream caller needs (bucket ARN, KMS ARN, regional DNS).
- [ ] Replication is rejected by validation outside `prod`.
- [ ] Errors are surfaced via Terraform variable validation messages.

## Out of Scope

- Provisioning the destination bucket for cross-region replication (caller's responsibility).
- Object lifecycle on *current* versions — only non-current versions transition/expire (current versions are application state and must not be silently deleted).
- Logging-bucket setup. Northwind ships a separate `s3-access-logs` module for that.
- Bucket policies beyond TLS enforcement. Application-specific policies (cross-account access, event-source roles) are added by the caller via `aws_s3_bucket_policy` outside this module.
