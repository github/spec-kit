# s3-secure-bucket

Provisions an AWS S3 bucket that meets the Northwind Platform security baseline:

- Server-side encryption with a customer-managed KMS key (rotation enabled, 30-day deletion window).
- Versioning enabled.
- All four `block_public_*` flags set to `true`.
- `BucketOwnerEnforced` object ownership (ACLs disabled).
- Lifecycle: non-current versions transition to STANDARD_IA at 30d, GLACIER at 90d, expire at 365d.
- Bucket policy denies any request without `aws:SecureTransport`.
- Optional cross-region replication to `us-west-2`, gated to `prod` only.

Standard tags from `.infrakit/coding-style.md` are applied to the bucket, the KMS key, and the
replication IAM role.

---

## Usage

```hcl
module "events_bucket" {
  source = "git::https://github.com/northwind/infra-modules.git//modules/s3-secure-bucket?ref=v1.0.0"

  name                = "events"
  environment         = "prod"
  team                = "orders"
  cost_center         = "CC-3017"
  data_classification = "confidential"

  enable_cross_region_replication     = true
  replication_destination_bucket_arn  = "arn:aws:s3:::prod-orders-events-dr-us-west-2"
  replication_destination_kms_key_arn = "arn:aws:kms:us-west-2:123456789012:key/abcd-..."

  tags = {
    owner = "orders-team@northwind.example.com"
  }
}
```

The actual bucket name is `${environment}-${team}-${name}-${random_4_chars}`, e.g.
`prod-orders-events-x7k2`. The random suffix guarantees global uniqueness on re-provisioning.

---

## Inputs

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | `string` | yes | — | Logical bucket name (3-40 chars, kebab-case). |
| `environment` | `string` | yes | — | `dev`, `staging`, or `prod`. |
| `team` | `string` | yes | — | Owning team. |
| `cost_center` | `string` | yes | — | Billing code (`CC-NNNN`). |
| `project` | `string` | no | `"northwind-platform"` | Project identifier. |
| `data_classification` | `string` | yes | — | `public` / `internal` / `confidential` / `restricted`. |
| `kms_deletion_window_days` | `number` | no | `30` | KMS deletion window (7-30). |
| `lifecycle_transition_to_ia_days` | `number` | no | `30` | Days before non-current → IA. `0` disables. |
| `lifecycle_transition_to_glacier_days` | `number` | no | `90` | Days before non-current → GLACIER. `0` disables. |
| `lifecycle_noncurrent_expiration_days` | `number` | no | `365` | Days before non-current versions expire. `0` retains forever. |
| `enable_cross_region_replication` | `bool` | no | `false` | Enable replication to us-west-2. Only allowed when `environment == "prod"`. |
| `replication_destination_bucket_arn` | `string` | no | `null` | Required when replication is enabled. |
| `replication_destination_kms_key_arn` | `string` | no | `null` | Required when replication is enabled. |
| `tags` | `map(string)` | no | `{}` | Additional tags merged with required tags. |

## Outputs

| Output | Description |
|--------|-------------|
| `bucket_id` | The ID (name) of the bucket. |
| `bucket_arn` | ARN. |
| `bucket_domain_name` | Bucket-style DNS name. |
| `bucket_regional_domain_name` | Regional bucket DNS name. |
| `kms_key_arn` | ARN of the bucket's KMS key. |
| `kms_key_id` | ID of the KMS key. |
| `replication_role_arn` | ARN of the replication IAM role; `null` if replication is disabled. |
