# Implementation Plan: XPostgreSQLInstance

## Summary

Implement an `XPostgreSQLInstance` XR and its `postgres-aws` Composition using Crossplane Pipeline
mode with `function-patch-and-transform`. Maps a Claim to two AWS managed resources: a KMS key
(for storage encryption) and an RDS Instance (PostgreSQL). Publishes a connection Secret with
six keys into the claiming namespace.

## Infrastructure Context

| Property | Value |
|----------|-------|
| **Track** | `xpostgresql-instance-20260415-101500` |
| **API Group** | `database.platform.acme.com/v1alpha1` |
| **XRD Kind** | `XPostgreSQLInstance` (plural `xpostgresqlinstances`) |
| **Claim Kind** | `PostgreSQLInstance` |
| **Composition Name** | `postgres-aws` |
| **Composition Directory** | `compositions/xpostgresql-instance/` |

## Tech Stack

| Component | Version |
|-----------|---------|
| Crossplane | `v1.15.2` |
| Composition mode | `Pipeline` |
| Pipeline function | `function-patch-and-transform` `v0.6.0` |
| Provider | `upbound/provider-aws-rds` `v1.2.0` |
| Provider | `upbound/provider-aws-kms` `v1.2.0` |

## File Structure

```
compositions/xpostgresql-instance/
├── definition.yaml           # XRD: schema, claim names, connection secret keys
├── composition.yaml          # Pipeline Composition; KMS + RDS resources with patches
├── README.md                 # Usage docs, parameter reference, output keys
└── examples/
    ├── claim-dev.yaml        # Minimal dev claim
    └── claim-prod.yaml       # Production claim with overrides
```

## Schema Verification (Step 1, before any YAML)

Verified API versions against `doc.crds.dev`:

| Resource | apiVersion | kind | Source |
|----------|-----------|------|--------|
| XRD | `apiextensions.crossplane.io/v1` | `CompositeResourceDefinition` | crossplane.io v1 docs |
| Composition | `apiextensions.crossplane.io/v1` | `Composition` | crossplane.io v1 docs |
| KMS Key | `kms.aws.upbound.io/v1beta1` | `Key` | doc.crds.dev/crossplane-contrib/provider-aws |
| RDS Instance | `rds.aws.upbound.io/v1beta1` | `Instance` | doc.crds.dev/crossplane-contrib/provider-aws |
| Function input | `pt.fn.crossplane.io/v1beta1` | `Resources` | function-patch-and-transform README |

## XRD Schema Design

OpenAPI v3 schema under `spec.versions[0].schema.openAPIV3Schema`:

```yaml
properties:
  spec:
    properties:
      parameters:
        required: [environment, teamName, costCenter, subnetGroupName, securityGroupIds]
        properties:
          environment:       { type: string, enum: [dev, staging, prod] }
          teamName:          { type: string, enum: [payments, data, frontend, mobile, platform] }
          costCenter:        { type: string, pattern: "^CC-[0-9]{4}$" }
          region:            { type: string, default: us-east-1 }
          engineVersion:     { type: string, default: "16.3", pattern: "^[0-9]+\\.[0-9]+(\\.[0-9]+)?$" }
          instanceClass:     { type: string, default: db.t3.micro }
          storageGB:         { type: integer, minimum: 20, maximum: 16384, default: 20 }
          storageType:       { type: string, enum: [gp3, io2], default: gp3 }
          multiAZ:           { type: boolean }            # unset → defaults from env
          backupRetentionDays: { type: integer, minimum: 1, maximum: 35, default: 7 }
          deletionProtection: { type: boolean }           # unset → defaults from env
          subnetGroupName:   { type: string }
          securityGroupIds:  { type: array, items: { type: string } }
```

Connection secret keys declared in XRD: `host, port, username, password, database, endpoint`.

## Composition Pipeline

Single step (`patch-and-transform`) with two resources:

### Resource 1: `kms-key`

- Base: `kms.aws.upbound.io/v1beta1` `Key`, `enableKeyRotation: true`, `deletionWindowInDays: 30`.
- Patches:
  - `region` ← `spec.parameters.region`
  - Tag patches (`environment`, `team`, `cost-center`, `crossplane.io/claim-name`, `crossplane.io/claim-namespace`)
  - `status.kmsKeyArn` ← KMS `status.atProvider.arn` (Optional from-field-path)

### Resource 2: `rds-instance`

- Base: `rds.aws.upbound.io/v1beta1` `Instance`, `engine: postgres`, `username: dbadmin`,
  `autoGeneratePassword: true`, `passwordSecretRef: { namespace: crossplane-system, name: postgres-admin-credentials, key: password }`,
  `publiclyAccessible: false`, `storageEncrypted: true`, `storageType: gp3`, `copyTagsToSnapshot: true`,
  `performanceInsightsEnabled: true`, `performanceInsightsRetentionPeriod: 7`,
  `enabledCloudwatchLogsExports: [postgresql, upgrade]`.
- Patches:
  - Direct parameter mappings: `region`, `engineVersion`, `instanceClass`, `storageGB → allocatedStorage`,
    `storageType`, `backupRetentionPeriod`, `dbSubnetGroupName`, `vpcSecurityGroupIds`.
  - `kmsKeyId` ← `status.kmsKeyArn` from the KMS resource (Required policy).
  - `multiAZ`: CombineFromComposite of `(multiAZ, environment)` → map. Unset multiAZ defaults from env.
  - `deletionProtection`: same pattern as `multiAZ`.
  - `identifier`: CombineFromComposite of `(environment, teamName)` → `"%s-%s-pg-primary"`.
  - Tag patches (same 5 keys as KMS).
  - PatchSet `connection-secret-name`: propagates the claim's `writeConnectionSecretToRef.name`.
  - Status patches: `status.endpoint`, `status.port`, `status.arn` (all Optional from-field-path).
- Connection details:
  - `host` ← `status.atProvider.address` (via `FromFieldPath`)
  - `port`, `username`, `password`, `endpoint` ← from provider-managed connection secret keys
  - `database` ← `status.atProvider.dbName`

## Tagging Strategy

All managed resources carry these tag keys, set via patches on each resource (defense in depth —
no reliance on provider-level defaults):

| Tag Key | Source |
|---------|--------|
| `managed-by` | static `"crossplane"` (in base) |
| `environment` | `spec.parameters.environment` |
| `team` | `spec.parameters.teamName` |
| `cost-center` | `spec.parameters.costCenter` |
| `crossplane.io/claim-name` | label `crossplane.io/claim-name` |
| `crossplane.io/claim-namespace` | label `crossplane.io/claim-namespace` |

## Implementation Phases

1. **definition.yaml** — write the XRD with full OpenAPI schema, claim names, connection secret keys, default Composition ref.
2. **composition.yaml** — write the Composition with Pipeline mode, function-patch-and-transform, KMS + RDS resources, all patches and connection details.
3. **examples/claim-dev.yaml** — minimal dev claim showing env defaults.
4. **examples/claim-prod.yaml** — prod claim showing multi-AZ + deletion protection defaults.
5. **README.md** — usage docs, parameter reference table, output keys table, link to `crossplane render` validation command.

## Constraints from `coding-style.md`

- Pipeline mode (not Resources/legacy mode).
- All managed resources tagged with the required keys.
- `publiclyAccessible` and `storageEncrypted` are non-overridable; not exposed as parameters.
- Connection secrets must be published with the keys declared in the XRD.
- `kebab-case` for the composition file name; XRD plural lowercased.

## Notes

### Known Challenges

- `multiAZ` and `deletionProtection` defaults differ by environment. We model them as
  `CombineFromComposite` with a `map` transform across `(parameter, environment)` tuples, treating
  the `<nil>` literal as "unset". This is the cleanest pattern available in
  function-patch-and-transform; the alternative (a separate composition per environment) would
  triple the XRD/Composition surface.
- The KMS key must be `Ready` before the RDS instance can reference its ARN. The Required
  `fromFieldPath` policy on the `kmsKeyId` patch enforces this implicitly — the RDS resource will
  remain in `Creating` until the KMS resource reports its ARN.
- The `autoGeneratePassword + passwordSecretRef` pattern in provider-aws-rds v1.2.0 stores the
  generated password in a Secret that the provider itself creates. We point `passwordSecretRef`
  at a single shared Secret (`crossplane-system/postgres-admin-credentials`) so that all instances
  share the same admin password rotation cadence. (Document for ops: rotate by emptying this
  Secret; the provider will regenerate on next reconcile.)

### Design Decisions

- **Customer-managed KMS key per instance** (not shared). Per-instance keys allow per-database
  access auditing in CloudTrail and per-database revocation if a workload is decommissioned.
- **No VPC creation in this Composition.** Networking is centrally managed; product teams pass
  in the subnet group name and security group IDs. This keeps the blast radius of this composition
  small and avoids cross-resource-group dependencies.
- **No read replicas here.** A separate composition will model `XPostgreSQLReplica` so the
  primary instance lifecycle is independent of replica scaling.
