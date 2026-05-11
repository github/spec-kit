# Implementation Tasks: XPostgreSQLInstance

**Track**: `xpostgresql-instance-20260415-101500`
**Generated**: 2026-04-15
**Source Plan**: `.infrakit_tracks/tracks/xpostgresql-instance-20260415-101500/plan.md`

## Phase 1: definition.yaml (XRD)

- [x] T1.1: Write `apiVersion: apiextensions.crossplane.io/v1`, `kind: CompositeResourceDefinition`.
- [x] T1.2: Set `metadata.name = xpostgresqlinstances.database.platform.acme.com` and labels (`provider: aws`, `service: rds`).
- [x] T1.3: Set `spec.group = database.platform.acme.com`, names (`XPostgreSQLInstance` / `xpostgresqlinstances`), claim names (`PostgreSQLInstance` / `postgresqlinstances`).
- [x] T1.4: Declare `connectionSecretKeys = [host, port, username, password, database, endpoint]`.
- [x] T1.5: Set `defaultCompositionRef = postgres-aws`.
- [x] T1.6: Declare version `v1alpha1` with `served: true`, `referenceable: true`.
- [x] T1.7: Write OpenAPI v3 schema under `spec.versions[0].schema.openAPIV3Schema` covering all 14 parameters (with enums, patterns, min/max, defaults) plus `writeConnectionSecretToRef`.
- [x] T1.8: Declare `status` properties: `endpoint`, `port`, `arn`, `kmsKeyArn`, `ready`.

## Phase 2: composition.yaml

- [x] T2.1: Write `apiVersion: apiextensions.crossplane.io/v1`, `kind: Composition`, `metadata.name = postgres-aws`, labels.
- [x] T2.2: Set `compositeTypeRef = database.platform.acme.com/v1alpha1 / XPostgreSQLInstance`.
- [x] T2.3: Set `writeConnectionSecretsToNamespace = crossplane-system`.
- [x] T2.4: Set `mode: Pipeline`.
- [x] T2.5: Declare pipeline step `patch-and-transform` with `functionRef.name = function-patch-and-transform`.
- [x] T2.6: Declare input as `pt.fn.crossplane.io/v1beta1` `Resources`.

### Resource 1: kms-key

- [x] T2.7: Base = `kms.aws.upbound.io/v1beta1 Key`, `enableKeyRotation: true`, `deletionWindowInDays: 30`, `tags.managed-by = crossplane`.
- [x] T2.8: Patch region from `spec.parameters.region`.
- [x] T2.9: Tag patches: environment, team, cost-center, crossplane.io/claim-name, crossplane.io/claim-namespace.
- [x] T2.10: ToCompositeFieldPath: KMS `status.atProvider.arn` → `status.kmsKeyArn` (Optional).

### Resource 2: rds-instance

- [x] T2.11: Base = `rds.aws.upbound.io/v1beta1 Instance`, with `engine`, `username: dbadmin`, `autoGeneratePassword: true`, `passwordSecretRef`, `publiclyAccessible: false`, `storageEncrypted: true`, `storageType: gp3`, `copyTagsToSnapshot: true`, Performance Insights, CloudWatch log exports.
- [x] T2.12: Set `writeConnectionSecretToRef.namespace = crossplane-system` in base.
- [x] T2.13: Direct parameter patches: region, engineVersion, instanceClass, storageGB → allocatedStorage, storageType, backupRetentionPeriod, dbSubnetGroupName, vpcSecurityGroupIds.
- [x] T2.14: Patch `kmsKeyId` from composite `status.kmsKeyArn` with Required policy.
- [x] T2.15: Compute `multiAz` via CombineFromComposite (multiAZ, environment) with map transform; defaults from env when unset.
- [x] T2.16: Compute `deletionProtection` via the same CombineFromComposite pattern.
- [x] T2.17: Compute `identifier` via CombineFromComposite (environment, teamName) with `"%s-%s-pg-primary"` format.
- [x] T2.18: Tag patches: environment, team, cost-center, crossplane.io/claim-name, crossplane.io/claim-namespace.
- [x] T2.19: PatchSet `connection-secret-name` propagating `spec.writeConnectionSecretToRef.name`.
- [x] T2.20: ToCompositeFieldPath patches: status.endpoint, status.port, status.arn (all Optional).
- [x] T2.21: connectionDetails: `host` (FromFieldPath `status.atProvider.address`), `port`/`username`/`password`/`endpoint` (FromConnectionSecretKey), `database` (FromFieldPath `status.atProvider.dbName`).

## Phase 3: Example claims

- [x] T3.1: `examples/claim-dev.yaml` — minimal dev claim showing env defaults take effect.
- [x] T3.2: `examples/claim-prod.yaml` — prod claim with realistic `db.r6g.xlarge` + 500 GB.

## Phase 4: Documentation

- [x] T4.1: Write `compositions/xpostgresql-instance/README.md` with usage example, parameter table, output table, validation command.

## Phase 5: Validation

- [x] T5.1: `python3 -c "import yaml; list(yaml.safe_load_all(open('composition.yaml')))"` — pass (all 4 YAMLs valid).
- [ ] T5.2: `crossplane render examples/claim-dev.yaml composition.yaml functions.yaml` — to be run with the function image cached locally.
- [ ] T5.3: `kyverno test` against the `require-required-tags` policy — to be run in CI.
- [ ] T5.4: Apply XRD to a kind cluster with Crossplane installed and verify the CRDs come up — to be run in the platform-cluster CI job.
