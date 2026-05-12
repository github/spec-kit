# xpostgresql-instance

A Crossplane composite resource that provisions an AWS RDS PostgreSQL instance with a
per-instance customer-managed KMS key. Product teams claim `PostgreSQLInstance` from their team
namespace; the platform team owns this Composition.

---

## Usage

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
    instanceClass: db.r6g.xlarge
    storageGB: 500
    subnetGroupName: prod-rds-private
    securityGroupIds: [sg-0fedcba9876543210]
  writeConnectionSecretToRef:
    name: orders-primary-pg
```

After the resource reports `Ready`, the connection Secret `payments/orders-primary-pg` will
contain the keys `host`, `port`, `username`, `password`, `database`, `endpoint`.

Two example claims are bundled:

- [`examples/claim-dev.yaml`](examples/claim-dev.yaml) — a minimal dev claim. Multi-AZ and deletion-protection both fall back to their env defaults (`false`).
- [`examples/claim-prod.yaml`](examples/claim-prod.yaml) — a realistic prod claim. Multi-AZ and deletion-protection both fall back to their env defaults (`true`).

---

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `environment` | string | yes | — | `dev` / `staging` / `prod` |
| `teamName` | string | yes | — | `payments` / `data` / `frontend` / `mobile` / `platform` |
| `costCenter` | string | yes | — | `CC-NNNN` |
| `region` | string | no | `us-east-1` | AWS region |
| `engineVersion` | string | no | `"16.3"` | PostgreSQL engine version |
| `instanceClass` | string | no | `db.t3.micro` | RDS instance class |
| `storageGB` | integer | no | `20` | Allocated storage (20-16384) |
| `storageType` | string | no | `gp3` | `gp3` / `io2` |
| `multiAZ` | bool | no | env-default | prod = `true`, else `false`; override permitted |
| `backupRetentionDays` | integer | no | `7` | 1-35 |
| `deletionProtection` | bool | no | env-default | prod = `true`, else `false`; override permitted |
| `subnetGroupName` | string | yes | — | Existing DB subnet group in the target VPC |
| `securityGroupIds` | []string | yes | — | VPC security group IDs |

---

## Connection Secret Keys

| Key | Source |
|-----|--------|
| `host` | RDS `status.atProvider.address` |
| `port` | provider-managed connection secret |
| `username` | provider-managed connection secret |
| `password` | provider-managed connection secret |
| `database` | RDS `status.atProvider.dbName` |
| `endpoint` | provider-managed connection secret |

---

## Status

| Field | Description |
|-------|-------------|
| `endpoint` | RDS endpoint DNS name |
| `port` | Port (5432) |
| `arn` | RDS instance ARN |
| `kmsKeyArn` | ARN of the per-instance KMS key |
| `ready` | True when both KMS and RDS are Ready |

---

## Constraints (non-overridable)

- `publiclyAccessible: false` — RDS is never internet-reachable from this Composition.
- `storageEncrypted: true` — always SSE-KMS with a per-instance customer-managed key.
- `enableKeyRotation: true` on the KMS key, 30-day deletion window.
- `copyTagsToSnapshot: true` so snapshots inherit the resource tags.
- `enabledCloudwatchLogsExports: [postgresql, upgrade]`.
- `performanceInsightsEnabled: true` with 7-day retention.

---

## Validation

Validate the Composition locally (requires `crossplane` CLI and the function image cached):

```bash
crossplane render \
  examples/claim-dev.yaml \
  composition.yaml \
  functions.yaml
```

(`functions.yaml` declares `function-patch-and-transform` for `crossplane render`. The cluster
itself loads the function from the platform's package registry, not from this file.)

YAML syntactic validation runs on every push via:

```bash
python3 -c 'import yaml,sys; [list(yaml.safe_load_all(open(f))) for f in sys.argv[1:]]' \
  definition.yaml composition.yaml examples/claim-dev.yaml examples/claim-prod.yaml
```
