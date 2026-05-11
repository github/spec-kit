# Specification: XPostgreSQLInstance

## Description

A Crossplane composite resource that provisions a production-ready AWS RDS PostgreSQL instance
with an isolated, customer-managed KMS key for storage encryption. Product teams claim
`PostgreSQLInstance` from their team namespace; the platform team owns the Composition that maps
the Claim onto `kms.aws.upbound.io/v1beta1/Key` and `rds.aws.upbound.io/v1beta1/Instance` managed
resources. Connection details are published as a Kubernetes Secret in the claiming namespace.

## Cloud Provider

**Provider**: AWS
**Service**: RDS PostgreSQL (encrypted with a per-instance customer-managed KMS key)

## Project Type

Greenfield (Create new)

## Resource Type

- [x] Claim (namespace-scoped, backed by cluster-scoped XR)
- [ ] XR only — cluster-scoped

## How It Should Work

A team writes a Claim like:

```yaml
apiVersion: database.platform.acme.com/v1alpha1
kind: PostgreSQLInstance
metadata:
  name: orders-primary
  namespace: payments
spec:
  parameters:
    environment: prod
    teamName: payments
    costCenter: CC-1042
    storageGB: 500
    instanceClass: db.r6g.xlarge
    subnetGroupName: prod-rds-private
    securityGroupIds: [sg-0fedcba9876543210]
  writeConnectionSecretToRef:
    name: orders-primary-pg
```

The Composition produces a KMS key and an RDS instance. When both are `Ready`, the connection
Secret `payments/orders-primary-pg` contains keys `host`, `port`, `username`, `password`,
`database`, `endpoint`. Multi-AZ and deletion protection default `true` in prod, `false`
elsewhere; both can be overridden via Claim parameters.

## User Inputs (Parameters)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `environment` | string (enum) | yes | — | `dev` / `staging` / `prod` |
| `teamName` | string (enum) | yes | — | `payments` / `data` / `frontend` / `mobile` / `platform` |
| `costCenter` | string (pattern) | yes | — | `CC-NNNN` |
| `region` | string | no | `us-east-1` | AWS region |
| `engineVersion` | string | no | `"16.3"` | PostgreSQL engine version |
| `instanceClass` | string | no | `db.t3.micro` | RDS instance class |
| `storageGB` | integer (20-16384) | no | `20` | Allocated storage |
| `storageType` | string (enum) | no | `gp3` | `gp3` / `io2` |
| `multiAZ` | boolean | no | — | Override Multi-AZ. Defaults from environment (prod=true, else false). |
| `backupRetentionDays` | integer (1-35) | no | `7` | Backup retention period |
| `deletionProtection` | boolean | no | — | Override deletion protection. Defaults from environment. |
| `subnetGroupName` | string | yes | — | Name of existing DB subnet group in target VPC |
| `securityGroupIds` | []string | yes | — | VPC security group IDs |

## Expected Outputs (Status)

| Field | Type | Description |
|-------|------|-------------|
| `endpoint` | string | RDS endpoint DNS name (e.g., `prod-payments-pg-primary.xxxxx.us-east-1.rds.amazonaws.com`). |
| `port` | integer | Port (5432). |
| `arn` | string | ARN of the RDS instance. |
| `kmsKeyArn` | string | ARN of the KMS key encrypting storage. |
| `ready` | boolean | True when KMS key and RDS instance are both Ready. |

## Connection Secret Keys

| Key | Description |
|-----|-------------|
| `host` | RDS endpoint hostname (from `status.atProvider.address`). |
| `port` | Database port (always `5432`). |
| `username` | Admin username (`dbadmin`). |
| `password` | Admin password (auto-generated, stored in `crossplane-system/postgres-admin-credentials`). |
| `database` | Initial database name (from `status.atProvider.dbName`). |
| `endpoint` | RDS endpoint DNS in `host:port` form. |

## Security Requirements

- Storage encrypted at rest with a customer-managed KMS key, rotation enabled, 30-day deletion window.
- `publiclyAccessible = false` always — no override variable.
- Engine logs (`postgresql`, `upgrade`) exported to CloudWatch.
- Performance Insights enabled, 7-day retention.
- Admin password auto-generated and stored in Secrets Manager via the provider's `autoGeneratePassword` + `passwordSecretRef` pattern; never inline in YAML.
- All required tags propagated to KMS key and RDS instance (from claim labels + spec parameters).
- VPC-only — caller must provide `subnetGroupName` (in a private subnet) and `securityGroupIds`. The Composition does not provision networking.

## Configuration Constraints

- `engineVersion` must match `^[0-9]+\.[0-9]+(\.[0-9]+)?$`.
- `storageGB` between 20 and 16384.
- `backupRetentionDays` between 1 and 35.
- `costCenter` must match `^CC-[0-9]{4}$`.
- `teamName` restricted to an enum of allowed team names.
- `subnetGroupName` and `securityGroupIds` are required — Composition does not create network resources.

## Acceptance Criteria

- [ ] Claim with only the required parameters produces a working PostgreSQL instance.
- [ ] All required tags from `.infrakit/tagging-standard.md` appear on the KMS key AND the RDS instance.
- [ ] No hardcoded credentials anywhere in Composition or Claim YAML.
- [ ] `publiclyAccessible = false` is non-overridable.
- [ ] Multi-AZ defaults to `true` in prod, `false` elsewhere; can be overridden via `spec.parameters.multiAZ`.
- [ ] Deletion protection defaults to `true` in prod, `false` elsewhere; can be overridden via `spec.parameters.deletionProtection`.
- [ ] Connection secret published with all six keys when the claim's RDS instance is `Ready`.
- [ ] `crossplane render` succeeds against `claim-dev.yaml` and `claim-prod.yaml`.
- [ ] XRD schema validation rejects out-of-range parameters (storageGB, engineVersion format, costCenter format).

## Out of Scope

- VPC, subnet groups, and security groups (consumer's responsibility — the Composition expects them as inputs).
- Read replicas (a separate `XPostgreSQLReplica` resource is planned).
- Cross-region DR. RDS automated backups + 30-day retention is the baseline; cross-region DR for in-scope databases is handled by a separate `XPostgreSQLDR` composition.
- Schema migrations / database initialization (application-team responsibility).
